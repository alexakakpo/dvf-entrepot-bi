# Mesures DAX

À créer dans Power BI : sélectionne `fct_mutation` → **Nouvelle mesure**, puis
colle chaque bloc. Crée-les dans l'ordre : certaines en réutilisent d'autres.

> **Avant tout :** `dim_date` doit être marquée comme table de dates
> (Modélisation → Marquer comme table de dates → colonne `date`). Sans ça,
> toutes les mesures de comparaison temporelle ci-dessous sont fausses.

## Mesures de base

```dax
Nombre de ventes = COUNTROWS ( fct_mutation )
```

```dax
Volume de transactions = SUM ( fct_mutation[valeur_fonciere] )
```

```dax
Prix médian = MEDIAN ( fct_mutation[valeur_fonciere] )
```

```dax
Prix m2 médian = MEDIAN ( fct_mutation[prix_m2] )
```

```dax
Surface médiane = MEDIAN ( fct_mutation[surface_bati] )
```

**Pourquoi la médiane et pas la moyenne.** La distribution des prix immobiliers
est fortement asymétrique : quelques ventes à plusieurs millions tirent la
moyenne vers le haut et décrivent un marché que personne ne rencontre. La
médiane répond à « combien paie un acheteur ordinaire ». C'est une question
qu'on te posera — sache y répondre.

## Comparaison temporelle

```dax
Prix m2 médian N-1 =
CALCULATE (
    [Prix m2 médian],
    SAMEPERIODLASTYEAR ( dim_date[date] )
)
```

```dax
Évolution N/N-1 =
VAR Actuel = [Prix m2 médian]
VAR Precedent = [Prix m2 médian N-1]
RETURN
    DIVIDE ( Actuel - Precedent, Precedent )
```
Format : pourcentage, 1 décimale.

```dax
Indice base 100 =
VAR Reference =
    CALCULATE (
        [Prix m2 médian],
        ALL ( dim_date ),
        dim_date[annee] = 2020
    )
RETURN
    DIVIDE ( [Prix m2 médian], Reference ) * 100
```
Change `2020` si ta première année complète est différente. L'indice base 100
permet de comparer sur un même graphique des communes dont les niveaux de prix
n'ont rien à voir — c'est l'écart d'évolution qui devient lisible.

## Mesures de structure

```dax
Part des maisons =
DIVIDE (
    CALCULATE ( [Nombre de ventes], dim_type_bien[libelle] = "Maison" ),
    [Nombre de ventes]
)
```

```dax
Écart au département =
VAR PrixCommune = [Prix m2 médian]
VAR PrixDepartement =
    CALCULATE ( [Prix m2 médian], ALL ( dim_commune ) )
RETURN
    DIVIDE ( PrixCommune - PrixDepartement, PrixDepartement )
```
Se lit « cette commune est X % au-dessus ou en dessous du département ».
C'est la mesure qui rend une carte réellement parlante.

## Mesure de fiabilité

```dax
Prix m2 médian fiable =
IF ( [Nombre de ventes] >= 30, [Prix m2 médian] )
```

À utiliser dans les visuels par commune. Une médiane calculée sur 4 ventes n'a
aucune valeur statistique, mais s'affiche exactement comme une médiane calculée
sur 4 000 — et c'est ainsi qu'on produit une carte spectaculaire et fausse.
Masquer les communes sous le seuil est un choix d'analyste, pas une limite
technique : c'est le genre de détail qui distingue un tableau de bord d'une
jolie image.

## Trois pages suggérées

1. **Vue d'ensemble** — cartes de synthèse (nombre de ventes, prix m² médian,
   évolution N/N-1), courbe de l'indice base 100 par type de bien, histogramme
   des ventes par mois.
2. **Géographie** — carte des communes colorée par `Écart au département`
   (en utilisant `Prix m2 médian fiable`), classement des dix communes les plus
   chères et des dix moins chères.
3. **Typologie** — prix m² médian croisé type de bien × nombre de pièces,
   distribution des surfaces, part des maisons par commune.
