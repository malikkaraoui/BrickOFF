# 18 — Principe de visibilité : on ne compte que ce qui se voit (08/07/2026)

> **Statut : NORMATIF.** Principe fondateur issu d'une observation du PO. Gouverne l'annotation,
> l'évaluation ET l'UX produit. Prime sur toute consigne contraire.

## L'observation

Dans un tas non étalé, des pièces sont **entièrement enfouies** sous d'autres. Les détecter est
**physiquement impossible** — pour un humain comme pour un modèle. Ce n'est pas une erreur à
corriger, c'est une limite du réel. Les apps qui demandent "étalez, évitez tout chevauchement"
demandent l'impossible : une pièce peut toujours en cacher une autre.

## Le principe

**Nombre PHYSIQUE de pièces = pièces VISIBLES (≥ 25 %) + pièces ENFOUIES (invisibles).**

- **Annotation** : on n'annote QUE les pièces visibles. On n'invente JAMAIS une boîte pour
  atteindre un décompte cible. Le décompte physique du PO (ex. 50) sert à mesurer l'écart, pas
  à forcer l'annotation.
- **Évaluation** : le modèle n'est jugé que sur les pièces visibles. L'écart (physique − visible)
  est une **métrique en soi** : le taux d'enfouissement du tas (proxy de sa difficulté / de son
  étalement). Un modèle qui "rate" une pièce enfouie n'est pas fautif.
- **UX produit** : l'app ne prétend jamais voir sous les pièces. Réponse honnête après un scan :
  « J'ai trouvé N pièces. Étale-les ou re-scanne sous un autre angle pour trouver les autres. »
  → c'est la raison d'être de l'**agrégateur multi-frames (CH-5)** : plusieurs angles réduisent
  les angles morts, sans jamais mentir sur l'invisible.

## Stratégie de données « du plus dur au moins dur » (PO)

Le PO fournit délibérément les cas les plus durs d'abord :
- **Densité** : tas entremêlés / empilés (pièces qui se chevauchent et s'enfouissent) → puis tas plus plats.
- **Couleur** : tas monochromes (frontières inter-pièces invisibles, cas rare en réalité) → puis multicolores.

Usage selon la finalité :
- **Juge / stress-test** : commencer par le dur révèle le plafond. Si ça tient sur l'entremêlé
  monochrome, le reste est acquis.
- **Entraînement** : un **mélange dur + facile** (curriculum) entraîne mieux qu'uniquement du dur.
  Le générateur synthétique couvre toute la gamme gratuitement, en connaissant par construction
  quelles pièces sont enfouies (donc en les excluant proprement — chose qu'aucune annotation
  humaine ne peut faire sur un tas réel).

## Conséquences concrètes

1. Consigne d'annotation batch 2 corrigée : « visible seulement, ne pas forcer 50 » (08/07).
2. Nouvelle métrique à produire : **taux de visibilité** = pièces visibles / physiques, par photo.
3. Le générateur synthétique v2 doit exporter, par scène, la liste des pièces **totalement
   occluses** (coverage ≈ 0) pour ne PAS les compter comme cibles de détection ratées.
4. UX (CH-8) : formuler le résultat de scan en « trouvées / à découvrir en étalant », jamais un
   nombre absolu présenté comme exhaustif.
