-- Typage explicite des fichiers DVF.
-- C'EST LE SEUL FICHIER où les noms de colonnes de la source sont écrits en
-- dur. `make explore` affiche les colonnes réelles ; en cas d'écart, tout se
-- corrige ici.
--
-- Grain de cette vue : UNE LIGNE DU FICHIER, c'est-à-dire un lot d'une vente.
-- Ce n'est pas encore le grain métier — voir fct_mutation.

with brut as (

    select * from {{ source('brut', 'dvf') }}

)

select
    id_mutation,
    try_cast(date_mutation as date)                        as date_mutation,
    nature_mutation,

    -- Le séparateur décimal est le point dans les fichiers Etalab, mais on
    -- passe par replace pour rester robuste si un millésime utilise la virgule.
    try_cast(replace(valeur_fonciere, ',', '.') as double)  as valeur_fonciere,

    code_commune,
    nom_commune,
    code_departement,
    code_postal,
    ancien_code_commune,
    ancien_nom_commune,

    type_local,
    try_cast(surface_reelle_bati as double)                 as surface_reelle_bati,
    try_cast(nombre_pieces_principales as integer)          as nombre_pieces,
    try_cast(surface_terrain as double)                     as surface_terrain,
    try_cast(nombre_lots as integer)                        as nombre_lots,

    try_cast(longitude as double)                           as longitude,
    try_cast(latitude as double)                            as latitude

from brut
where id_mutation is not null
