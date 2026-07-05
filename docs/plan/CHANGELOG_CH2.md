# CHANGELOG CH-2 — Entraînement des modèles

> Journal du chantier. Méthode gouvernée par le doc 14 (décision D05) : audit d'abord,
> baselines time-boxées, une hypothèse à la fois, 6 itérations max, portes de sortie chiffrées.

## 2026-07-04 — Jalon 2.0 (audit dataset, doc 14 Phase 1) ✅ CLOS

- **Statut : ✅** — livrable `ml/AUDIT_DATASET.md`
- **Critères de bascule : aucun déclenché.** Annotations douteuses 2–6 % (seuil 10 %), zéro boîte
  fantôme ; fonds réels variés (28 % studio strict seulement).
- **Découverte structurelle** (plus importante que les critères) : le corpus réel gdansk_det est
  à 82 % mono-pièce, sans scènes de tas ni occlusions. Conséquence actée : la détection de TAS
  (le cas produit) repose sur (a) les scènes synthétiques multi-pièces à générer (doc 14 §2.1)
  et (b) le corpus réel maison du jalon 1.7 ; gdansk_det sert d'ancrage réel mono-pièce et de
  sanity check — pas de socle.
- Recommandations transmises aux jalons 1.3 (préserver le split `-test` des noms de fichiers,
  flagger les pièces coupées au bord) et 1.4 (occlusions synthétiques, petites cibles,
  renforcement éclairage chaud).

## 2026-07-05 — Jalon 2.1 (baseline DET v0) ✅ TERMINÉ — diagnostic obtenu

- Modèle : SSDLite320-MobileNetV3 (torchvision, BSD-3), mono-classe, backbone pré-entraîné.
  **Écart au plan consigné** : le plan visait "YOLO nano du framework CH-0" — SSDLite est retenu
  pour la baseline v0 (compatibilité MPS immédiate, philosophie doc 14 : la baseline localise le
  problème, elle ne fixe pas l'architecture de production, qui reste YOLOX/RT-DETR par D02).
- Config : 50 epochs max, early stopping patience 8, batch 16, AdamW 1e-3 cosine, seed 42.
- Smoke test : 39 s/epoch sur 200 images → run complet projeté 10-14 h. Critère D10 (< 48 h) OK,
  entraînement local M1 confirmé.
- Run en cours : `ml/runs/det_v0/` (config.json, history.json par epoch, best.pt).
  **Pour vérifier en reprenant** : `tail data/…/ml/runs/det_v0/history.json` ou relancer
  `caffeinate -i .venv/bin/python ml/det/train_baseline.py --epochs 50 --batch 16 --patience 8`
  (le run repart de zéro — pas de resume implémenté en v0, choix assumé de simplicité baseline).

### Verdict (rapport complet : `ml/runs/det_v0/EVAL_DET_V0.md`)
- 35 epochs (~3,5 h M1). mAP@50 : **0.998 rendus / 0.786 photos val / 0.679 test** — le domain
  gap rendus→photos est LE problème, mesuré. Pièces trouvées (rappel max 0.94) mais scores trop
  bas au seuil produit (rappel@0.35 = 0.59). Critères baseline non atteints sur test — attendu :
  la baseline sert au diagnostic, qui est net.
- Boucle d'itérations ouverte (budget : 6) : It.1 early stopping sur val photos seules ;
  It.2 augmentation photométrique forte ; It.3 (levier principal) scènes synthétiques réalistes.

### Prochaines étapes
1. It.1 (un seul changement : métrique d'arrêt sur photos) → réentraîner, comparer
2. Pipeline de scènes synthétiques réalistes multi-pièces (doc 14 §2.1) — attaque le gap ET prépare le scan de tas
3. Jalon 1.2 (scope classes) dès réception des CSV Rebrickable (action PO)
