# D11 — Modèle de détection de production : SSDLite candidat V1, YOLOX/RT-DETR en escalade

**Statut : ✅ Tranché (2026-07-07) — amende le choix nominatif de D02, pas son critère**

## Contexte

D02 (2026-07-04) exigeait une licence permissive et proposait YOLOX/RT-DETR par défaut, le choix
final étant renvoyé à l'exécution. Depuis : 8 runs d'entraînement, un chantier synthétique et
deux dry-runs d'export ont été menés avec SSDLite320-MobileNetV3 (torchvision, BSD-3), choisi
initialement comme simple baseline (écart consigné au CHANGELOG_CH2).

## Ce que l'expérience a prouvé (recul du 07/07)

| Critère D02/plan | SSDLite mesuré |
|---|---|
| Licence permissive | BSD-3 ✅ (torchvision) |
| mAP@50 photos réelles jamais vues | 0.826 (et rappel max 0.99) |
| Entraînable sur l'infra retenue (D10, M1) | 4-7 min/epoch ✅ |
| Export CoreML | 7,6 Mo (budget ≤15), parité FP32 parfaite, NMS natif ✅ |
| Export Android | validation ONNX en cours (dry-run) |
| Taille/latence | dans les budgets CH-3 avec marge ×2 |

## Décision

1. **SSDLite320-MobileNetV3 est le modèle de détection de production candidat pour la V1.**
2. **YOLOX/RT-DETR deviennent l'option d'escalade**, déclenchée uniquement si les cibles
   realworld du jalon 2.4 (rappel ≥ 0.92 sur étalement, pipeline ≥ 0.65) ne sont pas atteintes
   après intégration du verdict TAS et du corpus réel 1.7. Le patron d'export (wrapper de
   traçage) est réutilisable pour cette escalade.
3. Le contrat `12_CONVENTIONS_AI.md` §1.5 (DET input 640×640) sera amendé à **320×320** au vrai
   CH-3 si SSDLite est confirmé (le dry-run a validé ce format de bout en bout).

## Pourquoi

Changer de framework maintenant re-paierait toute la validation (entraînement, augmentations,
export, parité, benchmarks) pour un gain non démontré — exactement le genre de pari non chiffré
que la méthode du projet interdit. L'architecture à deux étages absorbe de toute façon un
remplacement ultérieur du DET sans toucher au reste.

## Impacts

- `17_BILAN_ENTRAINEMENTS.md` §3 (source de cette décision) ; index ARBITRAGES mis à jour.
- CH-3 réel : partir des scripts d'export existants (déjà écrits pour SSDLite).
- CH-0 jalon 0.3 / `legal/ML_LICENSES.md` : aucun changement (BSD-3 déjà tableau-vert via torchvision).
