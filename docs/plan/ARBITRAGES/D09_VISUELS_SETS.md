# D09 — Visuels de sets et de pièces dans l'app : jamais d'images officielles, rendus maison

**Statut : ✅ Tranché (2026-07-04) — lève la remédiation R7 (constats adversaires 5 et 6)**

## Problème

L'app doit montrer des sets (écran matching CH-7) et des pièces (inventaire CH-6, revue de scan
CH-5). Les sources d'images évidentes sont interdites ou risquées :
- **Images officielles LEGO** (boîtes, visuels produits) : copyright LEGO, tolérance limitée au
  non-commercial (Fair Play, brochure p. 10) → exclu pour une app commerciale.
- **Images hébergées par Rebrickable** : licence distincte des données CSV, non couverte par le
  "any purpose" (les ToS §5.2 les traitent à part), et l'offline interdit le hotlinking de toute
  façon → exclu.

## Décision

**Aucune image officielle LEGO ni image Rebrickable dans l'app, à aucun palier. La filière
visuelle est 100 % maison, en trois niveaux :**

1. **V1 — pièces** : rendus LDraw maison. Le pipeline synthétique (doc 14 §2.1, outillé par
   `ldr_tools_blender`) sert déjà à l'entraînement : le même outillage produit les vignettes des
   1000 pièces du scope (fond neutre, angle 3/4, ~64-128 px). Coût marginal quasi nul, licence
   propre (LDraw CC BY, attribution déjà prévue dans l'app). Fallback si retard : pictos
   génériques par catégorie + pastille couleur (option "V1 recommandé" de CH-6 jalon 6.3).
2. **V1 — sets** : PAS d'image de set. La carte set = nom, année, thème, nombre de pièces,
   badge coverage — plus la **liste visuelle des pièces requises** (vignettes LDraw du point 1).
   C'est honnête, léger, et différenciant ("voici ce qu'il te faut" plutôt qu'une photo de boîte).
3. **V1.5+ — constructions blueprints** : rendus 3D maison des blueprints (nos propres modèles,
   aucun droit tiers) — c'est déjà l'architecture du guidage pas-à-pas (doc 13 amendé).

## Règle screenshots store & marketing (constat 6)

- Les captures App Store montrent **l'UI réelle de l'app** (usage fonctionnel) — autorisé.
- **Jamais de rendu de brique à tenons comme visuel marketing héros** (icône, bannière, feature
  graphic) : la forme "brick and knobs" est revendiquée par LEGO. Les illustrations marketing
  utilisent des formes stylisées non-tenons (règle déjà dans le brief design §2.3).
- Photos de vraies pièces LEGO dans le marketing : uniquement en contexte d'usage de l'app
  (main + téléphone qui scanne), jamais en packshot produit. Relecture PI au moment de CH-10.

## Pourquoi c'est la bonne décision

Elle transforme une contrainte légale en cohérence technique : un seul pipeline de rendu LDraw
alimente l'entraînement, les vignettes d'inventaire ET le guidage pas-à-pas. Zéro dépendance à
des droits tiers révocables, zéro téléchargement d'images, 100 % offline par construction.

## Impacts

- CH-6 jalon 6.3 : la note "visuels de pièces" est tranchée → vignettes LDraw maison (fallback pictos).
- CH-7 jalon 7.4 : "visuel placeholder" devient définitif → carte set sans image de boîte.
- CH-1 : ajouter la génération des vignettes au pipeline de rendu (tâche marginale, même outillage).
- `legal/ML_LICENSES.md` : l'attribution LDraw couvre aussi les vignettes UI (déjà prévue).
