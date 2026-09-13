"""Inspecte les fichiers DVF téléchargés avant de construire quoi que ce soit.

    make explore

Affiche les colonnes réellement présentes, le volume, la période couverte et
la répartition des types de biens. À lancer AVANT le premier `make dbt` :
c'est ce qui permet de vérifier que les colonnes attendues par les modèles
existent bien.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

RAW_GLOB = str(Path(__file__).resolve().parents[1] / "data" / "raw" / "*.csv.gz")

COLONNES_ATTENDUES = [
    "id_mutation",
    "date_mutation",
    "nature_mutation",
    "valeur_fonciere",
    "code_commune",
    "nom_commune",
    "code_departement",
    "type_local",
    "surface_reelle_bati",
    "nombre_pieces_principales",
    "surface_terrain",
    "longitude",
    "latitude",
]


def main() -> None:
    con = duckdb.connect()
    source = f"read_csv_auto('{RAW_GLOB}', union_by_name = true, all_varchar = true)"

    try:
        colonnes = [
            ligne[0]
            for ligne in con.execute(f"describe select * from {source}").fetchall()
        ]
    except duckdb.IOException:
        print("Aucun fichier dans data/raw/. Lance d'abord : make download", file=sys.stderr)
        raise SystemExit(1) from None

    print(f"=== {len(colonnes)} colonnes dans les fichiers DVF ===\n")
    for nom in colonnes:
        print(f"  {nom}")

    manquantes = [nom for nom in COLONNES_ATTENDUES if nom not in colonnes]
    print("\n=== Colonnes attendues par les modèles dbt ===")
    if manquantes:
        print("  MANQUANTES :", ", ".join(manquantes))
        print("  → à corriger dans dbt/models/staging/stg_mutations.sql")
    else:
        print("  Toutes présentes. Les modèles dbt peuvent tourner tels quels.")

    print("\n=== Volume et période ===")
    resume = con.execute(f"""
        select
            count(*)                          as lignes,
            count(distinct id_mutation)       as mutations,
            min(date_mutation)                as debut,
            max(date_mutation)                as fin
        from {source}
    """).fetchone()
    print(f"  {resume[0]:,} lignes pour {resume[1]:,} mutations distinctes".replace(",", " "))
    print(f"  du {resume[2]} au {resume[3]}")
    print(
        f"\n  Ratio {resume[0] / max(resume[1], 1):.2f} ligne(s) par mutation : c'est le "
        "piège principal de DVF.\n  Une vente est éclatée sur plusieurs lignes (une par lot), "
        "et la valeur foncière\n  est répétée à l'identique sur chacune. Sommer la colonne "
        "brute gonfle le total."
    )

    print("\n=== Répartition des types de biens ===")
    for type_local, nb in con.execute(f"""
        select coalesce(type_local, '(non bâti)') as type_local, count(*) as nb
        from {source} group by 1 order by nb desc
    """).fetchall():
        print(f"  {type_local:<30} {nb:>10,}".replace(",", " "))

    print("\n=== Natures de mutation ===")
    for nature, nb in con.execute(f"""
        select nature_mutation, count(*) as nb
        from {source} group by 1 order by nb desc limit 8
    """).fetchall():
        print(f"  {nature:<30} {nb:>10,}".replace(",", " "))


if __name__ == "__main__":
    main()
