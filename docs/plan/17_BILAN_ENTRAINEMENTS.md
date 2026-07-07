# 17 — Bilan des entraînements & revue du plan de vol (07/07/2026)

> **Statut : NORMATIF (revue d'étape).** Rédigé à la demande du PO après 8 runs de détection et
> pendant la baseline de classification. Objet : ce que les entraînements ont PROUVÉ, ce qui
> change dans le plan, ce qui est gelé en attendant le verdict TAS.

## 1. Journal des entraînements (tous sur M1, tous reproductibles)

| Run | Date | Changement unique | mAP@50 test¹ | Rappel @0.35 | Leçon |
|---|---|---|---|---|---|
| det_v0 | 05/07 | baseline SSDLite (flip buggué) | 0.679 | 0.591 | La val mélangée (rendus+photos) trompe l'early stopping |
| det_v0.1 | 05/07 | bugfix boxes + val photos seules | 0.763 | 0.664 | **La supervision propre vaut plus que tout tuning** (+8,4 pts) |
| det_v1 | 05/07 | augmentation forte (rot. 90°/±20°, zoom-out, photométrie) | 0.773 | 0.650 | Rappel max 0.985 : le modèle VOIT, il manque de confiance |
| det_v2C | 06/07 | synthétique SEUL (10 k scènes) | 0.666 | 0.686 | **Le rendu transfère** ; l'échec spot-the-fake n'était pas prédictif |
| det_v2B | 06/07 | pré-entraînement synth → fine-tuning réel | 0.809 | 0.631 | Le séquentiel marche mais ne gagne pas |
| det_v2A | 06/07 | mélange 70 réel / 30 synth | 0.820 | 0.650 | **La voie nominale doc 14 validée** |
| **det_v3** ⭐ | 06/07 | + tilt ±45° + crop-zoom (idées PO) | **0.826** | **0.686** | Cadrages variés → confiance ; champion courant |
| cls_v0 | 07/07 (en cours) | MobileNetV3 1000 classes, mix 80/20 | top-1 74,4 / top-5 95,7² | — | Cible top-5 (95) ✅ atteinte ; top-1 (80) en approche |

¹ 179 photos réelles jamais vues (mono-pièce majoritaire — le verdict TAS reste dû).
² val synthétique ; sur photos réelles : top-1 83,6 %.

**Trajectoire globale DET : 0.679 → 0.826 en 4 jours, chaque gain attribué à sa cause.**

## 2. Les 7 leçons qui gouvernent la suite

1. **Supervision propre d'abord** : le bugfix géométrique a rapporté plus que toute augmentation.
2. **La métrique d'arrêt doit regarder la cible** (val photos seules) — une val flattée arrête mal.
3. **Le synthétique fonctionne, mesurablement** — et la diversité compte plus que le photoréalisme
   parfait (spot-the-fake raté, transfert réussi). Ne plus investir dans le réalisme sans signal du terrain.
4. **Mélange 70/30 = recette maison de référence** (validée sur DET, appliquée d'emblée sur CLS).
5. **Le goulot DET est la calibration, pas la vision** → point de fonctionnement produit :
   seuil 0.20-0.25 + vote multi-frames (l'agrégateur CH-5, déjà codé et testé, est la réponse).
6. **D10 validée** : le M1 a tout absorbé (DET 4-7 min/epoch, CLS 1-2 h/epoch, jamais près des 48 h
   d'escalade cloud). Les interruptions de session, pas la puissance, ont été le vrai risque
   → tout run long vit en démon détaché avec script versionné.
7. **La chaîne export est dé-risquée** : CoreML 7,6 Mo parité parfaite (voie Android en cours de
   validation pratique — voir `docs/research/ANDROID_EXPORT_PATH.md`).

## 3. Décision D11 — SSDLite devient candidat production V1 (amende D02)

D02 exigeait un détecteur à licence permissive et proposait YOLOX/RT-DETR par défaut. Le recul
dit : **SSDLite320-MobileNetV3 (torchvision, BSD-3) satisfait le critère licence ET a fait ses
preuves de bout en bout** — entraînement M1 rapide, 0.826 de mAP, export CoreML 7,6 Mo en parité
parfaite, NMS convertible nativement. Changer de framework maintenant coûterait la re-validation
de TOUTE la chaîne pour un gain hypothétique.

**Décision** : SSDLite = modèle de production candidat V1. YOLOX/RT-DETR = **option d'escalade**,
déclenchée uniquement si les cibles realworld (CH-2 jalon 2.4) ne sont pas atteintes après
l'intégration du verdict TAS et du corpus 1.7. Le critère de D02 (licence permissive) reste
inchangé — c'est le choix nominatif qui évolue, entériné dans `ARBITRAGES/D11_MODELE_PRODUCTION.md`.

Conséquence contractuelle : l'entrée DET du contrat §1.5 (640×640) sera amendée à **320×320**
(natif SSDLite, validé par le dry-run CH-3) lors du vrai CH-3.

## 4. Plan de vol adapté (prochaines étapes, dans l'ordre)

| # | Étape | Déclencheur |
|---|---|---|
| 1 | **Verdict TAS** : ingestion photos PO → pilote annotation → baseline det_v3 vs critère recalibré | Photos PO (attendues) |
| 2 | Bilan CLS + éval pires classes/paires confondues → décision fusion de molds (doc 14 §2.3) | Fin cls_v0 (imminente) |
| 3 | Selon verdict TAS : It.5-6 DET (corpus 1.7 réel-tas en mélange) OU scale-up synthétique ciblé | 1 |
| 4 | CH-5 : brancher DetModel.mlpackage réel (remplace le mock) + validation device PO | Déjà possible |
| 5 | Jalons 1.2/1.5 + CH-7 (matching) | **CSV Rebrickable (action PO, toujours en attente)** |
| 6 | CH-3 réel (DET+CLS finaux, quantization, benchmark device) | Modèles gelés post-TAS |
| **Gelé** | 3 itérations DET restantes : AUCUN nouveau run avant le verdict TAS (éviter l'optimisation à l'aveugle) | — |

## 5. Voie Android (validation en cours)

**✅ VALIDÉE (07/07)** : DetModel.onnx 14,9 Mo, parité PyTorch↔onnxruntime PARFAITE (IoU 1.000,
50 images, protocole identique au CoreML), NMS embarqué en op standard, normalisation in-graph.
Runtime V2 recommandé : ONNX Runtime Mobile + XNNPACK (NNAPI déprécié — piège évité). INT8
dynamique testé et rejeté avec preuve. Détail : `docs/research/ANDROID_EXPORT_PATH.md`.
Le plan de base Android (D01) est CONFIRMÉ : mêmes poids, même wrapper, deux exports.
