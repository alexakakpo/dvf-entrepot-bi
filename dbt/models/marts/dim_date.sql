-- Dimension calendaire, générée pour couvrir toute la période observée.
--
-- Indispensable en Power BI : sans table de dates continue, les fonctions de
-- time intelligence (SAMEPERIODLASTYEAR, DATESYTD…) renvoient des résultats
-- faux dès qu'un mois ne contient aucune vente. On la génère donc en continu,
-- y compris les jours sans transaction.

with bornes as (

    select
        date_trunc('year', min(date_mutation))  as debut,
        date_trunc('year', max(date_mutation))
            + interval 1 year - interval 1 day  as fin
    from {{ ref('fct_mutation') }}

),

calendrier as (

    select cast(unnest(generate_series(debut, fin, interval 1 day)) as date) as jour
    from bornes

)

select
    jour                                                as date_key,
    jour                                                as date,
    extract(year from jour)                             as annee,
    extract(quarter from jour)                          as trimestre,
    extract(month from jour)                            as mois,
    strftime(jour, '%B')                                as nom_mois,
    extract(day from jour)                              as jour_du_mois,
    extract(dow from jour)                              as jour_semaine,
    extract(dow from jour) in (0, 6)                    as est_week_end,

    -- Clés de tri : sans elles, Power BI classe les mois par ordre
    -- alphabétique (avril, août, décembre…).
    cast(strftime(jour, '%Y%m') as integer)             as annee_mois,
    printf('%d-T%d', extract(year from jour), extract(quarter from jour)) as annee_trimestre

from calendrier
