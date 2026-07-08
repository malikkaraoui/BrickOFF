# Fournée 2 (tas denses) — stratégie post-pilote (08/07/2026)

> 59 photos PO de TAS DENSES (le vrai cas produit : "je verse ma boîte et je scanne"), ingérées
> dans `data/processed/piles_batch2/`. Statut : **données d'entraînement It.5** (batch 1 reste le juge).

## Découverte du pilote d'annotation (3 photos)

Le facteur limitant de l'annotation n'est **pas la densité ni le nombre de pièces**, c'est le
**contraste de couleur entre pièces voisines** :
- Tas **multicolore** (~50 pièces) → chaque frontière inter-pièces est visible → **annotable de façon fiable** par agent.
- Tas **monochrome** (~40 pièces vertes) → les frontières entre deux pièces de même teinte qui se
  chevauchent sont **invisibles** → l'agent devine les boîtes (±15-20 % d'erreur de comptage) →
  **inexploitable comme ground-truth d'entraînement**.

Autres limites d'agent confirmées : lecture d'image sous-résolue (frontières fines perdues),
seuil de visibilité 25 % estimé à l'œil, risque de fusionner deux pièces même-couleur.

## Classification automatique du corpus (hue spread pondéré saturation, centre 60 %)

- **26 multicolores** (spread ≥ 0,35) → annotation agent fiable.
- **33 monochromes / faible-contraste** (spread < 0,35) → annotation agent non fiable.

## Stratégie décidée

| Sous-corpus | Rôle | Méthode |
|---|---|---|
| 26 multicolores | Ancrage réel d'entraînement It.5 | Annotation agent (passe aveugle + candidates) — fiable |
| 33 monochromes | **Juge par le décompte** | PAS d'annotation par boîtes ; PO fournit le nombre de pièces/photo → métrique "le modèle détecte-t-il ~N pièces ?" |
| **Générateur synthétique v2** | **Levier principal It.5** | Le synthétique connaît chaque frontière par construction → produit des labels PARFAITS de tas monochromes/denses, exactement le cas que le réel ne peut pas annoter |

## Générateur synthétique v2 — évolutions ciblées (issues de batch 2)

1. **Pièces articulées / à pivot** posées à angles d'ouverture variés (LDraw décrit les sous-parties).
   Objectif : corriger la fragmentation du détecteur sur ces pièces (constat PO).
2. **Tas plus denses** (occlusion accrue) — le générateur v1 était trop aéré vs le vrai cas produit.
3. **Scènes monochromes** — pièces de même couleur qui se chevauchent, le cas inannotable en réel.

## Diagnostic détecteur (visuel batch 2)

det_v3 **sur-fragmente** massivement sur les tas denses (112-185 boîtes @0.20 pour ~40-50 pièces
réelles). Confirme que le goulot It.5 = densité + occlusion + pièces articulées. Le vote
multi-frames (CH-5) atténuera en production, mais l'entraînement doit apprendre la bonne
granularité.

## ⭐ Vérité de comptage (PO, 08/07)

**Chaque tas VARIÉ (multicolore) contient EXACTEMENT 50 pièces.** Exceptions : les photos de pièces
articulées (bleu) et les tas de pièces identiques (monochromes), à comptage variable. Conséquence :
- Les 26 multicolores ont une **cible de complétude = 50** → l'annotation est vérifiable (l'agent
  doit atteindre 50 boîtes ; tout écart = pièces manquées à corriger).
- Devient aussi une **métrique de comptage** directe (le modèle détecte-t-il ~50 pièces ?).

## Action PO restante

**Décompte des tas MONOCHROMES** (les variés = 50, connu). Pour les tas de pièces identiques,
un nombre approximatif par photo suffit → les transforme en juge par le décompte.

## Métadonnée de capture (PO)

**Fournée 2 prise au zoom ×2** (focale équiv. ~50 mm, téléobjectif) sur toutes les photos — vs
fournée 1 en ×1 grand-angle (~24-28 mm). Effets : perspective plus plate, pièces plus grandes,
moins de fond (globalement plus facile). Sans impact sur l'annotation. Conséquence pour le
**générateur v2** : randomiser la focale sur **24-56 mm équiv.** (couvre ×1 et ×2), sinon le
synthétique n'apprendrait qu'une seule perspective. Le crop-zoom (It.4) couvre déjà une partie de
la variété d'échelle.

## Structure réelle de la fournée 2 (PO, clarification)

La fournée 2 n'est pas homogène — elle a 3 composantes :
1. **~15 photos "étude 360°"** (pas des tas) : 2 pièces PROBLÉMATIQUES posées à plat, photographiées
   sous tous les angles et éclairages (méthode "portrait 360°"). But : apprendre au modèle que ces
   formes = UNE pièce quel que soit l'angle. Les 2 pièces cibles :
   - **(a) l'articulée bleu clair** (charnière multi-lobes) — le détecteur la fragmente ;
   - **(b) une pièce à ~60° (pente/wedge)** — souvent confondue avec PLUSIEURS pièces à cause de son angle.
   Ce sont les photos 8254-8273 (annotées agents A/B : chaque pièce = 1 bbox, 6-11 pièces/photo).
2. **Tas multicolores variés = 50 pièces** (agents C/D) : ancrage d'entraînement dense.
3. **Tas monochromes** (33 classés, mais recouvrement avec 1.) : juge par décompte.

### Implication générateur synthétique v2
Générer les 2 pièces cibles (a) et (b) à **orientations/angles d'ouverture variés** → démultiplie
l'étude 360° réelle par des milliers de vues synthétiques annotées parfaitement. Correction
ciblée PAR PIÈCE = stratégie la plus efficace pour ces cas durs (plutôt que noyés dans des tas).
