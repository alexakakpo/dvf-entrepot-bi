"""Télécharge les fichiers DVF géolocalisés d'un département.

Source : https://files.data.gouv.fr/geo-dvf/latest/csv/{annee}/departements/{dep}.csv.gz
Publiée par Etalab. Pas de clé d'API, pas d'inscription.

    python scripts/download.py                 # Haute-Garonne, 2020 à 2025
    python scripts/download.py --dep 34        # un autre département
    python scripts/download.py --annees 2023 2024

Le téléchargement est idempotent : un fichier déjà présent et non vide est
conservé. Relancer la commande ne retélécharge donc rien.
"""

from __future__ import annotations

import argparse
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

# macOS livre un Python dont le magasin de certificats racine est vide :
# urllib echoue alors avec CERTIFICATE_VERIFY_FAILED sur toute URL en HTTPS.
# On s'appuie sur le bundle de certifi, installe avec les dependances.
try:
    import certifi

    CONTEXTE_SSL = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CONTEXTE_SSL = ssl.create_default_context()

BASE_URL = "https://files.data.gouv.fr/geo-dvf/latest/csv"
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

DEFAULT_DEPARTEMENT = "31"  # Haute-Garonne
DEFAULT_ANNEES = [2020, 2021, 2022, 2023, 2024, 2025]


def human(nb_octets: int) -> str:
    for unite in ("o", "Ko", "Mo", "Go"):
        if nb_octets < 1024:
            return f"{nb_octets:.0f} {unite}"
        nb_octets /= 1024
    return f"{nb_octets:.1f} To"


def telecharger(annee: int, departement: str) -> bool:
    """Renvoie True si le fichier est disponible localement à la fin."""
    cible = RAW_DIR / f"dvf_{departement}_{annee}.csv.gz"

    if cible.exists() and cible.stat().st_size > 0:
        print(f"  {annee} : déjà présent ({human(cible.stat().st_size)})")
        return True

    url = f"{BASE_URL}/{annee}/departements/{departement}.csv.gz"
    provisoire = cible.with_suffix(".gz.tmp")

    try:
        with urllib.request.urlopen(url, timeout=120, context=CONTEXTE_SSL) as reponse:
            provisoire.write_bytes(reponse.read())
    except urllib.error.HTTPError as erreur:
        if erreur.code == 404:
            # Une année pas encore publiée n'est pas une erreur : on continue.
            print(f"  {annee} : pas encore publiée (404), ignorée")
            return False
        print(f"  {annee} : échec HTTP {erreur.code}", file=sys.stderr)
        return False
    except OSError as erreur:
        print(f"  {annee} : échec réseau ({erreur})", file=sys.stderr)
        return False

    # Renommage final : un fichier partiel ne peut jamais être pris pour un
    # téléchargement réussi si la commande est interrompue.
    provisoire.replace(cible)
    print(f"  {annee} : téléchargé ({human(cible.stat().st_size)})")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dep", default=DEFAULT_DEPARTEMENT, help="Code département (ex. 31)")
    parser.add_argument("--annees", nargs="+", type=int, default=DEFAULT_ANNEES)
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Département {args.dep} — années {min(args.annees)} à {max(args.annees)}")

    disponibles = [annee for annee in sorted(args.annees) if telecharger(annee, args.dep)]

    if not disponibles:
        print("\nAucun fichier disponible. Vérifie le code département.", file=sys.stderr)
        raise SystemExit(1)

    print(f"\n{len(disponibles)} année(s) disponibles dans {RAW_DIR}")


if __name__ == "__main__":
    main()
