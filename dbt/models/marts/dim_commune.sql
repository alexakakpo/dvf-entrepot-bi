-- Dimension commune.
--
-- DVF expose `ancien_code_commune` / `ancien_nom_commune` quand une commune a
-- fusionné : le fichier garde alors la trace de l'entité d'origine. On s'en
-- sert pour signaler les communes concernées, ce qui évite de comparer sans
-- le savoir un territoire de 2020 avec un territoire redécoupé en 2024.
--
-- Une véritable dimension à évolution lente (SCD2) demanderait le Code
-- Officiel Géographique de l'INSEE, qui date chaque fusion. C'est la suite
-- logique du projet, documentée dans docs/modele.md — pas un oubli.

with lignes as (

    select * from {{ ref('stg_mutations') }}

),

communes as (

    select
        code_commune,
        any_value(nom_commune)      as nom_commune,
        any_value(code_departement) as code_departement,
        count(*)                    as nb_lignes_source,
        min(date_mutation)          as premiere_mutation,
        max(date_mutation)          as derniere_mutation
    from lignes
    where code_commune is not null
    group by code_commune

),

fusions as (

    select
        code_commune,
        count(distinct ancien_code_commune) as nb_anciennes_communes
    from lignes
    where ancien_code_commune is not null
      and ancien_code_commune <> ''
    group by code_commune

)

select
    c.code_commune                              as commune_key,
    c.code_commune,
    c.nom_commune,
    c.code_departement,
    c.premiere_mutation,
    c.derniere_mutation,
    c.nb_lignes_source,
    coalesce(f.nb_anciennes_communes, 0)        as nb_anciennes_communes,
    coalesce(f.nb_anciennes_communes, 0) > 0    as issue_de_fusion
from communes as c
left join fusions as f using (code_commune)
