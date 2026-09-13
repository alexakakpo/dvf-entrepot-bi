-- LE test du projet.
--
-- Il compare le chiffre d'affaires calculé au grain « vente » avec la somme
-- naïve de la colonne brute, sur le même périmètre. Si la déduplication de la
-- valeur foncière était cassée, les deux totaux coïncideraient — et c'est
-- précisément l'erreur que ce projet prétend éviter.
--
-- Le test échoue si l'écart est nul ou négatif, c'est-à-dire si la
-- déduplication n'a rien dédupliqué.

with au_grain_vente as (

    select sum(valeur_fonciere) as total_correct
    from {{ ref('fct_mutation') }}

),

somme_naive as (

    select sum(l.valeur_fonciere) as total_gonfle
    from {{ ref('stg_mutations') }} as l
    inner join {{ ref('fct_mutation') }} as f on l.id_mutation = f.id_mutation

)

select
    total_correct,
    total_gonfle,
    total_gonfle - total_correct as surestimation
from au_grain_vente, somme_naive
where total_gonfle <= total_correct
