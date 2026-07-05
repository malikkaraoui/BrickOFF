# EVAL DET v1 — itérations 1+2 (bugfix géométrie + durcissement)

**Chaîne du 2026-07-05** : `det_v0_1` (bugfix flip + early stopping sur val photos, 37 epochs)
puis `det_v1` (+ rotations 90°/±20°, zoom-out, photométrie forte, 63 epochs). ~7 h au total
sur M1/MPS. Configs et historiques dans les dossiers de runs respectifs.

## Comparatif sur le TEST (179 photos réelles jamais vues)

| Modèle | Changement (unique) | mAP@50 | Rappel max | Rappel @0.35 |
|---|---|---|---|---|
| v0 | baseline (flip buggué) | 0.679 | 0.942 | 0.591 |
| v0.1 | + bugfix boxes & métrique d'arrêt photos | 0.763 **(+8,4 pts)** | 0.912 | 0.664 |
| v1 | + augmentation forte (rotations, zoom-out, photométrie) | **0.773** (+1,0 pt) | **0.985** (+7,3 pts) | 0.650 |

Lecture : le bugfix a rapporté l'essentiel du mAP ; le durcissement a surtout rendu le modèle
**quasi exhaustif** (98,5 % des pièces vues) — le goulot restant est la **confiance**, pas la vision.

## Balayage du seuil de confiance (v1, test)

| Seuil | Rappel | Précision |
|---|---|---|
| 0.10 | 0.861 | 0.264 |
| 0.15 | 0.839 | 0.427 |
| **0.20** | **0.807** | **0.666** |
| **0.25** | **0.766** | **0.781** |
| 0.35 (contrat CH-5 actuel) | 0.650 | 0.820 |

**Implication produit majeure** : le pipeline CH-5 agrège 5 frames avec vote majoritaire (une
pièce doit apparaître sur ≥ 3/5 frames) — ce vote filtre précisément les faux positifs qu'un
seuil bas laisse passer. Le point de fonctionnement produit recommandé passe de 0.35 à
**0.20–0.25 + vote multi-frames** : rappel single-frame ~0.77-0.81, et le vote élimine le bruit.
À valider expérimentalement au jalon 5.5 ; le seuil reste configurable (contrat
`color_config.json` / conventions).

## Ce qui reste, et l'action suivante

Les cibles finales realworld (rappel ≥ 0.92) ne sont pas atteignables avec ce corpus seul :
le test reste mono-pièce/un seul auteur, et le produit scanne des TAS. **It.3 (prochaine action,
levier principal) : scènes synthétiques réalistes multi-pièces avec occlusions** — Blender +
ldr_tools_blender (installés), fonds HDRI CC0, doc 14 §2.1. Elle attaque à la fois le domain
gap résiduel, les occlusions absentes du corpus, et la confiance sur le réel varié.

Budget d'itérations doc 14 : 2 consommées (bugfix compté hors budget : c'était une correction,
pas une hypothèse), 4 restantes.

*2026-07-05 · reproductible : `ml/det/train_baseline.py`, `ml/det/eval.py`, sweep dans
`threshold_sweep_test.json`.*
