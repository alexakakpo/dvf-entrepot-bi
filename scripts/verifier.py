"""Quelques chiffres de contrôle, à lire avant de brancher Power BI.

    make verifier

Sert à deux choses : vérifier que l'entrepôt a du sens, et te donner les
chiffres que tu commenteras dans le README (et en entretien).
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb

RACINE = Path(__file__).resolve().parents[1]
BASE = Path(os.getenv("DVF_DATA_DIR", RACINE / "data")) / "warehouse" / "dvf.duckdb"


def titre(texte: str) -> None:
    print(f"\n=== {texte} ===")


def main() -> None:
    if not BASE.exists():
        raise SystemExit(f"Entrepôt introuvable : {BASE}\nLance d'abord : make dbt")

    con = duckdb.connect(str(BASE), read_only=True)

    titre("Effet de la déduplication")
    lignes = con.execute("select count(*) from main_staging.stg_mutations").fetchone()[0]
    ventes = con.execute("select count(*) from main_marts.fct_mutation").fetchone()[0]
    naif, correct = con.execute("""
        select
            sum(l.valeur_fonciere),
            (select sum(valeur_fonciere) from main_marts.fct_mutation)
        from main_staging.stg_mutations l
        inner join main_marts.fct_mutation f on l.id_mutation = f.id_mutation
    """).fetchone()
    print(f"  Lignes brutes           : {lignes:>12,}".replace(",", " "))
    print(f"  Ventes retenues         : {ventes:>12,}".replace(",", " "))
    print(f"  Somme naïve             : {naif / 1e9:>12.2f} Md€")
    print(f"  Somme au grain vente    : {correct / 1e9:>12.2f} Md€")
    print(f"  Surestimation évitée    : {(naif / correct - 1) * 100:>11.1f} %")

    titre("Prix au m² médian par année et type de bien")
    for ligne in con.execute("""
        select d.annee, f.type_bien_key,
               median(f.prix_m2) as prix_m2_median,
               count(*) as ventes
        from main_marts.fct_mutation f
        join main_marts.dim_date d on f.date_key = d.date_key
        group by 1, 2 order by 1, 2
    """).fetchall():
        print(f"  {ligne[0]}  {ligne[1]:<12} {ligne[2]:>8.0f} €/m²   ({ligne[3]:>6,} ventes)".replace(",", " "))

    titre("Dix communes les plus chères (min. 50 ventes)")
    for nom, prix, nb in con.execute("""
        select c.nom_commune, median(f.prix_m2) as prix, count(*) as nb
        from main_marts.fct_mutation f
        join main_marts.dim_commune c on f.commune_key = c.commune_key
        group by 1 having count(*) >= 50
        order by prix desc limit 10
    """).fetchall():
        print(f"  {nom:<28} {prix:>8.0f} €/m²   ({nb:>5,} ventes)".replace(",", " "))

    titre("Communes issues d'une fusion")
    fusions = con.execute(
        "select count(*) from main_marts.dim_commune where issue_de_fusion"
    ).fetchone()[0]
    print(f"  {fusions} commune(s) portent la trace d'une ancienne entité dans DVF.")
    if fusions:
        print("  → à garder en tête avant toute comparaison pluriannuelle.")


if __name__ == "__main__":
    main()
