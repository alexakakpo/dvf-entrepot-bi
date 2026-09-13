# Entrepôt décisionnel DVF : le marché immobilier de la Haute-Garonne

Projet personnel réalisé pendant mon M2 MIAGE (parcours Ingénierie des Données
et Analyses) à Toulouse Capitole.

Je voulais un projet complet plutôt qu'un notebook : prendre un vrai jeu de
données public, le modéliser en étoile, le tester, et le restituer dans Power
BI. Le tout doit pouvoir se relancer chez quelqu'un d'autre en trois commandes.

Les données viennent des **Demandes de Valeurs Foncières** publiées par Etalab,
c'est-à-dire toutes les ventes immobilières enregistrées en France. J'ai pris la
Haute-Garonne, 2021 à 2025, soit 409 358 lignes.

## Aperçu

![Tableau de bord Power BI](docs/images/dashboard.png)

Le modèle tel qu'il est monté dans Power BI : une table de faits, trois
dimensions, relations en plusieurs-à-un et sens unique.

![Modèle en étoile](docs/images/modele-etoile.png)

## Stack

| | |
|---|---|
| Données | DVF géolocalisées (Etalab), 5 millésimes, département paramétrable |
| Moteur | DuckDB, qui lit les CSV compressés directement sans étape d'import |
| Modélisation | dbt, 5 modèles et 24 tests |
| Restitution | Power BI Desktop |
| CI | GitHub Actions : télécharge une année, reconstruit l'étoile, relance les tests |

## Lancer le projet

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export DVF_DATA_DIR=$PWD/data
make download     # ~10 Mo
make explore      # affiche les colonnes réelles et le volume
make dbt          # construit l'étoile + lance les tests
make verifier     # quelques chiffres de contrôle
make export       # génère les Parquet pour Power BI
```

Pour un autre département : `python scripts/download.py --dep 34`.

## Le problème que j'ai trouvé dans les données

C'est la partie que je trouve la plus intéressante.

En explorant les fichiers avec `make explore`, je suis tombé sur un ratio de
**2,58 lignes par vente**. En creusant, j'ai compris pourquoi : DVF découpe
chaque vente en plusieurs lignes (une par lot, par parcelle ou par local) et
**recopie la valeur foncière à l'identique sur chacune**.

Donc si on fait un simple `SUM(valeur_fonciere)`, on annonce un marché deux à
trois fois plus gros qu'il n'est. Et rien ne le signale : le chiffre obtenu
reste crédible.

J'ai donc construit `fct_mutation` au grain « une vente » plutôt qu'au grain
« une ligne de fichier ». Sur mon périmètre :

| | |
|---|---|
| Lignes brutes | 409 358 |
| Ventes retenues après nettoyage | 92 971 |
| Somme naïve de la valeur foncière | 47,40 Md€ |
| Somme au grain vente | 20,70 Md€ |
| Écart | **129 %** |

Ces chiffres sortent de `make verifier`, je ne les ai pas recopiés à la main.

Pour être sûr que ça ne casse pas si je modifie le SQL plus tard, j'ai écrit
trois contrôles :

- `unique` sur `mutation_key` : garantit qu'une ligne correspond bien à une vente
- `assert_valeur_fonciere_non_dupliquee` : compare les deux totaux et échoue si
  la déduplication ne déduplique plus
- `assert_prix_m2_dans_les_bornes` : vérifie qu'aucun prix aberrant n'est passé

## Mes choix, et pourquoi

**Je type les colonnes à la main plutôt que de laisser DuckDB deviner.** Les CSV
sont lus en `all_varchar`, puis convertis un par un dans `stg_mutations`. La
détection automatique marche sur un échantillon, mais elle plante sur la ligne
bizarre au bout de 500 000 enregistrements, et en général au mauvais moment.

**Les règles de nettoyage sont des variables dbt, pas du SQL caché.** Nature de
mutation, surface minimale, bornes de prix au m² : tout est en haut de
`dbt_project.yml`. On voit en dix secondes ce que j'ai filtré, et on peut le
changer sans toucher aux modèles.

**Je n'ai pas mis d'orchestrateur.** DVF est publié deux fois par an. Brancher
Airflow ou Dagster là-dessus aurait fait joli sur le CV mais n'aurait servi à
rien. `make tout` suffit.

**J'utilise la médiane, pas la moyenne.** Les prix immobiliers sont très étalés
vers le haut : quelques ventes à plusieurs millions décalent la moyenne vers un
marché que personne ne rencontre. La médiane répond à « combien paie un acheteur
normal ».

**J'ai mis un seuil de fiabilité dans les visuels.** Une médiane calculée sur 4
ventes s'affiche exactement comme une médiane calculée sur 4 000. La mesure
`Prix m2 médian fiable` masque les communes sous 30 ventes. Sans ça, le
classement des communes les plus chères serait occupé par des villages où il
s'est vendu trois maisons.

## Ce que montrent les données

Le prix au m² monte jusqu'à fin 2022, puis se retourne. Les maisons décrochent
plus vite que les appartements. En parallèle, le volume de ventes passe de
21 760 en 2021 à 14 974 en 2024.

Prix au m² médian en 2025 : 2 952 € pour un appartement, 2 738 € pour une
maison. La commune la plus chère est Balma, devant Toulouse.

## Organisation du dépôt

```
├── scripts/          téléchargement, exploration, export Power BI
├── dbt/
│   ├── models/
│   │   ├── staging/  typage de la source
│   │   └── marts/    fct_mutation + dim_date, dim_commune, dim_type_bien
│   └── tests/        contrôles de grain et de plausibilité
├── docs/             modèle de données et mesures DAX
└── powerbi/          le rapport .pbix et les exports Parquet
```

`docs/modele.md` décrit le schéma et les relations à créer dans Power BI.
`docs/mesures_dax.md` contient les 11 mesures que j'ai écrites.

## Limites

- DVF ne couvre ni l'Alsace-Moselle ni Mayotte, qui ont un régime cadastral
  différent.
- Les ventes en VEFA (logement neuf sur plan) sont exclues par mon filtre sur
  `nature_mutation`. Ça représente 11 % du volume : c'est un choix assumé, mais
  il faut le savoir.
- Etalab ne garde que cinq millésimes, donc l'historique se décale d'une année à
  chaque publication.
- Les fusions de communes sont détectées mais pas historisées. Sur la
  Haute-Garonne le contrôle ne remonte rien ; il servira si j'élargis le
  périmètre.

## La suite

- Historiser les communes en SCD2 avec le Code Officiel Géographique de l'INSEE
- Étendre à toute l'Occitanie pour comparer les territoires
- Publier le dashboard sous forme de site consultable, pour ne pas dépendre d'un
  fichier `.pbix`

## Sources

- [Demandes de valeurs foncières géolocalisées sur data.gouv.fr](https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres-geolocalisees)
- [Fichiers Etalab](https://files.data.gouv.fr/geo-dvf/latest/csv/)
