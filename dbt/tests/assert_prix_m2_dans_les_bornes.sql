-- Aucun prix au m² ne doit sortir des bornes appliquées en amont. Si ce test
-- échoue, c'est que le filtre de fct_mutation a été contourné ou que le calcul
-- a changé — pas qu'une vente est bizarre.

select
    mutation_key,
    id_mutation,
    prix_m2
from {{ ref('fct_mutation') }}
where prix_m2 is null
   or prix_m2 < {{ var('prix_m2_min', 300) }}
   or prix_m2 > {{ var('prix_m2_max', 20000) }}
