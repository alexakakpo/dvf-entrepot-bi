"""Exporte le modèle en étoile vers des fichiers que Power BI sait lire.

    make export          # Parquet (recommandé : 5 à 10× plus léger)
    make export-csv      # CSV, si le connecteur Parquet fait des siennes

Les fichiers atterrissent dans powerbi/exports/. Côté Power BI Desktop :
Accueil → Obtenir des données → Dossier → sélectionner powerbi/exports.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import duckdb

RACINE = Path(__file__).resolve().parents[1]
BASE = Path(os.getenv("DVF_DATA_DIR", RACINE / "data")) / "warehouse" / "dvf.duckdb"
SORTIE = RACINE / "powerbi" / "exports"

# dbt préfixe les schémas personnalisés par le schéma cible : `marts` devient
# `main_marts`. C'est le comportement par défaut, on s'aligne dessus.
TABLES = [
    "main_marts.fct_mutation",
    "main_marts.dim_commune",
    "main_marts.dim_date",
    "main_marts.dim_type_bien",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["parquet", "csv"], default="parquet")
    args = parser.parse_args()

    if not BASE.exists():
        raise SystemExit(f"Entrepôt introuvable : {BASE}\nLance d'abord : make dbt")

    SORTIE.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(BASE), read_only=True)

    print(f"Export {args.format} vers {SORTIE}\n")
    for table in TABLES:
        nom = table.split(".")[-1]
        cible = SORTIE / f"{nom}.{args.format}"

        if args.format == "parquet":
            con.execute(
                f"copy (select * from {table}) to '{cible}' (format parquet, compression snappy)"
            )
        else:
            con.execute(
                f"copy (select * from {table}) to '{cible}' (format csv, header true)"
            )

        lignes = con.execute(f"select count(*) from {table}").fetchone()[0]
        taille = cible.stat().st_size / 1024 / 1024
        print(f"  {nom:<18} {lignes:>10,} lignes   {taille:>7.2f} Mo".replace(",", " "))

    print(
        "\nDans Power BI Desktop :"
        "\n  Obtenir des données → Parquet → charger CHAQUE fichier séparément"
        "\nPuis crée les relations décrites dans docs/modele.md."
    )


if __name__ == "__main__":
    main()
