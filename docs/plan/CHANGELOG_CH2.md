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

## 2026-07-05 — Itérations 1+2 lancées (chaîne de 2 runs, décision PO : durcir)

**Bug découvert en préparant It.2** : le flip horizontal de la v0 ne retournait pas les bboxes
(moitié de la supervision décalée). Corrigé (tv_tensors) — la v0 est donc invalidée comme référence
fine ; la chaîne repart proprement :
- `det_v0_1` : bugfix + early stopping sur val PHOTOS seules (It.1) — 60 epochs max, aug light.
  Relance : `caffeinate -i .venv/bin/python ml/det/train_baseline.py --epochs 60 --batch 16 --patience 10 --aug light --val-photos-only --out ml/runs/det_v0_1`
- `det_v1` : + augmentation FORTE (rotations 90° exactes + ±20°, zoom-out petites cibles,
  photométrie éclairage/flou — reco audit + demande PO) — 80 epochs max.
  Relance : idem avec `--epochs 80 --patience 12 --aug strong --out ml/runs/det_v1`
Chaque run est suivi d'une éval test automatique (`eval_test.json`). Comparaison attendue :
v0→v0_1 = effet bugfix+métrique ; v0_1→v1 = effet augmentation.

### Bilan chaîne (2026-07-05 après-midi) — rapport : `ml/runs/det_v1/EVAL_DET_V1.md`
- Test (179 photos jamais vues) : v0 0.679 → v0.1 0.763 (bugfix, +8,4 pts) → v1 0.773, avec
  **rappel max 0.985** (le modèle voit quasi tout ; le goulot = la confiance, pas la vision).
- Balayage de seuil : point de fonctionnement produit recommandé **0.20-0.25 + vote multi-frames
  CH-5** (rappel 0.77-0.81 single-frame) au lieu du 0.35 initial — à valider au jalon 5.5.
- Budget d'itérations : 2/6 consommées (bugfix hors budget).

### Prochaines étapes
1. **It.3 — scènes synthétiques réalistes multi-pièces avec occlusions** (levier principal :
   domain gap + occlusions + le cas produit "tas"). Blender + ldr_tools_blender prêts.
2. Jalon 1.2 (scope classes) dès réception des CSV Rebrickable (action PO)
3. Realworld test maison (jalon 1.6) — le seul juge final

## 2026-07-06 — Jalon 2.2 PRÉPARÉ : pipeline classification prêt à tirer

- Livrables : `ml/cls/{dataset,train_cls,eval_cls,make_splits}.py` + chaîne `ml/runs/run_cls_baseline.sh`
  + manifests `classes_cls_v0.json` (1 000 classes, ordre des labels HF conservé comme contrat)
  et `splits_cls.json` (stratifiés, seedés).
- Stratégie v0 : classes = les 1 000 de legobricks (socle synthétique) ; gdansk réel mappé sur
  l'intersection et mélangé à 20 % pour l'ancrage réel (même logique que la victoire DET S.5).
- Smoke test : concluant après un correctif de métrique de validation (1er run : val toujours à 0,
  bug du split — patché) : **top-1 val 57 % / top-5 83 % après 2 epochs sur 2 000 images et
  1 000 classes** (hasard = 0,1 %). La loss descend proprement (4,26 → 2,87).
- Projection M1 : ~120 s / 2 000 images ⇒ epoch complète 400 k ≈ 6-7 h → l'entraînement v0
  utilisera une fenêtre par classe (`--window 64` ≈ 64 000 images/epoch ≈ 1 h/epoch) — écart au
  plan (« 50 epochs ») consigné : 30 epochs max avec early stopping, la patience tranchera.
- Note d'exécution : l'agent développeur a laissé le compte-rendu inachevé (attentes passives
  répétées) — section rédigée par l'orchestrateur à partir des artefacts réels, tous vérifiés.
- **À lancer dès que le M1 est libre** (det_v3/It.4 en cours) : `nohup caffeinate -ims ml/runs/run_cls_baseline.sh &`
