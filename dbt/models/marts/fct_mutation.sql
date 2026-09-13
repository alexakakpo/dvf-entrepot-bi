-- Table de faits : grain = UNE VENTE (une mutation), pas une ligne de fichier.
--
-- C'est le cœur du projet. DVF éclate chaque vente sur plusieurs lignes — une
-- par lot, par parcelle ou par local — et répète la valeur foncière à
-- l'identique sur chacune. Sommer la colonne brute gonfle le chiffre d'affaires
-- d'un facteur 2 à 3. C'est l'erreur la plus courante sur ce jeu de données.
--
-- On ramène donc au grain « une mutation », et le test `unique` sur
-- mutation_key rend cette garantie vérifiable plutôt que déclarative.
--
-- Règles de gestion, volontairement explicites et discutables :
--   1. on ne garde que les ventes (hors adjudications, échanges, expropriations) ;
--   2. on ne garde que les mutations portant sur UN SEUL local bâti, sans quoi
--      un prix au m² n'a pas de sens (on ne sait pas répartir le prix entre
--      une maison et son garage vendus ensemble) ;
--   3. on écarte les prix au m² aberrants, bornes exposées en variables dbt.

with lignes as (

    select * from {{ ref('stg_mutations') }}

),

lignes_baties as (

    select *
    from lignes
    where type_local in ('Maison', 'Appartement')
      and surface_reelle_bati > {{ var('surface_bati_min', 9) }}

),

par_mutation as (

    select
        id_mutation,

        count(*)                         as nb_locaux_batis,
        any_value(date_mutation)         as date_mutation,
        any_value(nature_mutation)       as nature_mutation,

        -- La valeur foncière est identique sur toutes les lignes d'une
        -- mutation : on la prend UNE fois. C'est tout l'enjeu.
        max(valeur_fonciere)             as valeur_fonciere,

        any_value(type_local)            as type_local,
        sum(surface_reelle_bati)         as surface_bati,
        max(nombre_pieces)               as nombre_pieces,
        sum(coalesce(surface_terrain, 0)) as surface_terrain,

        any_value(code_commune)          as code_commune,
        any_value(nom_commune)           as nom_commune,
        any_value(code_departement)      as code_departement,
        avg(longitude)                   as longitude,
        avg(latitude)                    as latitude

    from lignes_baties
    group by id_mutation

),

filtre as (

    select
        *,
        valeur_fonciere / nullif(surface_bati, 0) as prix_m2
    from par_mutation
    where nb_locaux_batis = 1
      and nature_mutation = 'Vente'
      and valeur_fonciere is not null
      and valeur_fonciere > 0

)

select
    md5(id_mutation)                          as mutation_key,
    id_mutation,
    date_mutation,
    cast(date_mutation as date)               as date_key,
    code_commune                              as commune_key,
    type_local                                as type_bien_key,

    valeur_fonciere,
    surface_bati,
    surface_terrain,
    nombre_pieces,
    prix_m2,

    longitude,
    latitude

from filtre
where prix_m2 between {{ var('prix_m2_min', 300) }} and {{ var('prix_m2_max', 20000) }}
