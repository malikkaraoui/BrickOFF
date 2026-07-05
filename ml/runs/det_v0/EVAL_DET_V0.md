# EVAL DET v0 — baseline détection (jalon 2.1)

**Run** : `ml/runs/det_v0/` · SSDLite320-MobileNetV3 mono-classe · 35 epochs (early stopping,
~3,5 h sur M1/MPS) · seed 42 · config exacte : `config.json`, historique : `history.json`.

## Résultats

| Split | Contenu | mAP@50 | Rappel max (mar100) | Rappel @ seuil produit 0,35 |
|---|---|---|---|---|
| val (early stopping) | photos + rendus mélangés | **0.883** | 0.968 | — |
| val · rendus seuls | 292 rendus studio | **0.998** | 1.000 | 0.918 |
| val · photos seules | 274 photos réelles | **0.786** | 0.954 | 0.629 |
| **test** (jamais vu) | 179 photos réelles (split d'origine du dataset) | **0.679** | 0.942 | **0.591** |

**Critères du jalon 2.1 (baseline) : mAP@50 ≥ 0.85 ✗ (0.68 sur test) · rappel ≥ 0.90 ✗ au seuil
produit (0.59)** — mais c'est précisément le diagnostic que la baseline devait produire.

## Diagnostic (doc 14 Phase 3)

1. **Le domain gap rendus→photos est LE problème, mesuré et quantifié** : 0.998 sur rendus vs
   0.786/0.679 sur photos. Le modèle a "résolu" les rendus studio (fond gris uniforme — trop
   faciles, cf. audit) et transfère mal vers les photos réelles. C'est la confirmation
   expérimentale de la prédiction du doc 14 §0 et du constat adversaire n°3.
2. **Les pièces SONT trouvées mais avec des scores trop bas** : rappel max 0.94-0.95 sur photos,
   mais 0.59-0.63 au seuil 0.35. Catégorie d'erreur dominante : sous-confiance sur le domaine
   réel, pas cécité. → Les remèdes de robustesse/calibration s'appliquent, pas un changement
   d'architecture.
3. La métrique d'early stopping (val mélangée) est **gonflée par les rendus faciles** : elle a
   arrêté l'entraînement sur un signal partiellement trompeur.

## Actions (une à la fois, mesurées — doc 14 Phase 4)

| # | Hypothèse | Action unique | Mesure de succès |
|---|---|---|---|
| It.1 | La métrique val mélangée fausse l'arrêt et le choix du best | Early stopping sur **val photos seules** + réentraîner (aucun autre changement) | mAP@50 test ↑ |
| It.2 | Sous-robustesse photométrique | Augmentation forte (éclairage/bruit/flou/fonds) | rappel @0.35 photos ↑ |
| It.3 (levier principal) | Les rendus studio n'attaquent pas le gap | **Scènes synthétiques réalistes multi-pièces** (fonds HDRI variés, doc 14 §2.1) en pré-entraînement | mAP@50 test ↑↑ + prépare le scan de TAS |

Le realworld test maison (jalon 1.6) reste le juge final — ces métriques test restent des photos
"un même auteur, une même collection".

*Rapport généré le 2026-07-05 · évaluations reproductibles : `ml/det/eval.py`.*
