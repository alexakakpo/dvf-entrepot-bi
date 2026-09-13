-- Petite dimension, mais elle a sa place : elle porte les libellés destinés
-- à l'affichage et un ordre de tri maîtrisé, plutôt que de laisser Power BI
-- trier « Appartement » avant « Maison » par hasard alphabétique.

select
    type_bien_key,
    type_bien_key       as libelle,
    case type_bien_key
        when 'Maison'      then 1
        when 'Appartement' then 2
        else 99
    end                 as ordre_affichage
from (
    select distinct type_bien_key
    from {{ ref('fct_mutation') }}
    where type_bien_key is not null
) as types
