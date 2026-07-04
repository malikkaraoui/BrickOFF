# D02 — Framework de détection : licence permissive par défaut

**Statut : ✅ Tranché (2026-07-04) — choix nominatif final à confirmer en CH-0 jalon 0.3**

## Contexte & sources en conflit

Contradiction **interne au plan** :

- `Sans titre.md` §6 : "Option A — YOLO / YOLOv8 small (RECOMMANDÉ)".
- `00_MASTER_PLAN.md` §0 (décision actée) : "**YOLOv8n** détection + MobileNetV3 classification".
- `01_CH0_PREALABLES.md` jalon 0.3 : YOLOv8 (Ultralytics) est **AGPL-3.0** → incompatible avec une app
  propriétaire fermée si le modèle est considéré comme dérivé ; "Alternative permissive recommandée
  par défaut : YOLOX (Apache-2.0) ou RT-DETR".

Le Master Plan fige donc un composant que son propre chantier CH-0 identifie comme juridiquement risqué.

## Options

| Option | Licence | Risque |
|---|---|---|
| A. YOLOv8n Ultralytics | AGPL-3.0 (ou Enterprise payante) | Juridique : l'AGPL sur les poids/le code d'inférence est un vrai sujet pour une app commerciale fermée ; coût Enterprise inconnu |
| B. **Framework permissif (YOLOX Apache-2.0, RT-DETR, ou équivalent à date)** ✅ | Apache-2.0/MIT | Technique marginal : perfs nano comparables sur une tâche mono-classe simple |
| C. Trancher plus tard | — | Le choix conditionne CH-1 (format labels), CH-2 (config), CH-3 (chaîne d'export) → le laisser ouvert propage l'incertitude sur 3 chantiers |

## Décision

1. **La ligne "YOLOv8n" du tableau des décisions actées du Master Plan est amendée en : "détecteur nano à licence permissive (YOLOX-nano par défaut), 2 stages, < 50 Mo total".**
2. Le choix nominatif final (YOLOX vs RT-DETR vs successeur permissif apparu depuis) est fait en **CH-0 jalon 0.3**, sur l'état réel de l'écosystème à la date d'exécution — comme CH-0 le prévoit déjà.
3. YOLOv8/Ultralytics ne redevient éligible **que si** le coût de la licence Enterprise est chiffré, budgété et accepté par écrit par le product owner.

## Justification

- Le risque AGPL est asymétrique : gain marginal de mAP éventuel vs blocage possible à la release (CH-0 le dit lui-même : "souvent ignoré et bloque à la release").
- La tâche DET est volontairement simple (mono-classe "lego_piece", cf. CH-2) : la marge entre détecteurs nano modernes est faible sur ce cas ; le critère différenciant est la licence, pas les 2 points de mAP.
- Cohérence documentaire : un exécutant qui lit seulement le Master Plan partait sur YOLOv8 et découvrait le mur en CH-0. L'ordre correct est l'inverse : la contrainte légale prime sur la préférence technique.

## Impacts

- `00_MASTER_PLAN.md` §0 : ligne "Modèle vision" à lire comme amendée ci-dessus (note ajoutée en tête du Master Plan renvoyant vers ARBITRAGES/).
- `03_CH2_TRAINING.md` jalon 2.1 : déjà compatible ("YOLO nano du framework retenu en CH-0 (YOLOX-nano si Apache exigée)") — aucun changement.
- `Sans titre.md` §6 : obsolète sur ce point.
- MobileNetV3 (classification) : **non affecté**, licence permissive, décision maintenue.
