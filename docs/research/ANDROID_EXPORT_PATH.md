# Voie d'export Android — dry-run de validation (garde-fou D01)

> **Date** : 2026-07-07 · **Contexte** : décision D01 = Android en V2, mais l'amendement D01
> impose de garantir la portabilité DÈS MAINTENANT. Ce document est le pendant Android du
> dry-run CoreML (CHANGELOG_CH3.md du 2026-07-07). Champion testé : `ml/runs/det_v3/best.pt`
> (SSDLite320-MobileNetV3, mono-classe).

## VERDICT : voie Android **VALIDÉE** ✅

Le même wrapper de traçage que la voie iOS (`SSDLiteDetCore` d'`export_det.py` : backbone +
head + decode SSD tensoriel + anchors précalculées) s'exporte vers ONNX **sans aucune
modification**, avec une **parité numérique parfaite** PyTorch CPU vs onnxruntime CPU.
Runtime recommandé : **ONNX Runtime (onnxruntime-android) + XNNPACK EP**, NMS embarqué
dans le graphe. Aucun blocage identifié ; risques restants listés en fin de document.

## 1. Artefacts et scripts

| Artefact | Rôle |
|---|---|
| `ml/export/export_det_onnx.py` | Export `best.pt` → `DetModel.onnx` (opset 18, TorchScript exporter). Réutilise `build_core`/`SSDLiteDetCore` d'`export_det.py` (mêmes asserts de normalisation). Variantes `--nms embedded` (défaut) / `--nms external`. |
| `ml/export/DetModel.onnx` | FP32, NMS embarqué, **14,91 Mo**, métadonnées `brickoff.*` (metadata_props). |
| `ml/export/parity_check_onnx.py` | Protocole de parité IDENTIQUE à `parity_check.py` (CoreML). |
| `ml/export/parity_report_det_onnx.json` | Rapport de parité (PASS). |
| `ml/export/parity_report_det_onnx_int8dyn.json` | Rapport de parité de la quantization dynamique (FAIL — voir §4). |

```bash
.venv/bin/python ml/export/export_det_onnx.py          # DetModel.onnx (NMS embarqué)
.venv/bin/python ml/export/parity_check_onnx.py        # 50 images, rapport JSON + exit code
```

## 2. Parité numérique (50 images test split, seed 42, CPU des deux côtés, seuil 0.35)

| Critère (seuils du protocole CoreML) | ONNX FP32 | Rappel CoreML FP32 | Rappel CoreML FP16 |
|---|---|---|---|
| IoU boxes appariées (min / moyenne) | **1.000 / 1.000** | 1.000 / 1.000 | 0.944 / 0.993 |
| Écart de score (max / moyen) | **0.000 / 0.000** | 0.000 | 0.017 / 0.002 |
| Top-1 identique | **39/39** | 39/39 | 38/39 |
| Boxes orphelines | **0** | 0 | 1 |
| Verdict (IoU ≥ 0.95, Δscore < 0.02) | **PASS** | PASS | FAIL (de justesse) |

Parité **bit-fidèle** : la chaîne wrapper + normalisation in-graph + `NonMaxSuppression`
ONNX reproduit exactement le postprocess torchvision. C'est la preuve de portabilité
demandée par l'amendement D01.

## 3. Décisions d'export (miroir des pièges CoreML)

- **NMS : EMBARQUÉ** (op ONNX standard `NonMaxSuppression`, généré depuis
  `torchvision::nms` par le symbolic torchvision, opset ≥ 11). Justification :
  ONNX Runtime le supporte nativement (CPU EP, opset ≥ 10) ⇒ **même contrat de sortie
  qu'iOS** (`boxes [N≤300,4]` XYXY normalisé 0-1 + `scores [N]` post-NMS iou 0.55 ;
  le client filtre juste `score ≥ 0.35`). Fallback `--nms external` validé aussi
  (3234 sorties brutes à taille FIXE) : requis si on bascule un jour vers TFLite/LiteRT
  (convertisseurs fragiles sur NonMaxSuppression) ou si un délégué NPU rejette l'op.
- **Normalisation : DANS LE GRAPHE.** ONNX n'a pas d'équivalent `ct.ImageType(scale, bias)`,
  donc le premier op du graphe fait `x*2/255 - 1` (mean=std=0.5, PAS ImageNet).
  **Spec d'entrée Android** : `image` float32 `[1,3,320,320]`, CHW, **RGB**, pixels bruts
  0-255, resize **scaleFill** (pas d'aspect ratio — même contrat qu'iOS). Zéro constante
  de normalisation à maintenir côté Kotlin.
- **Exporter** : TorchScript (`dynamo=False`, explicite car legacy/déprécié) — mais le
  nouvel exporter `dynamo=True` (défaut PyTorch ≥ 2.9) a été testé et **passe aussi** avec
  `NonMaxSuppression` dans le graphe ⇒ pas d'impasse quand le legacy disparaîtra.
- **Shapes dynamiques post-NMS** (N variable, `dynamic_axes`) : OK sur CPU/XNNPACK ;
  même famille de piège que l'ANE côté iOS pour les délégués NPU — d'où le fallback
  external à taille fixe.

## 4. Taille

| Variante | Taille | Parité |
|---|---|---|
| `DetModel.onnx` FP32 | **14,91 Mo** | PASS (parfaite) |
| INT8 dynamique (`onnxruntime.quantization.quantize_dynamic`, QInt8) | 4,18 Mo | **FAIL massif** (IoU moy. 0.79, Δscore max 0.54, top-1 1/38) — modèle supprimé, rapport conservé |

La quantization **dynamique** est inadaptée aux convnets (elle re-quantifie les activations
sans calibration) : résultat attendu, documenté comme repoussoir. **Étapes futures** (équivalent
jalon 3.3, au vrai chantier Android) : (a) conversion **FP16** ONNX (~7,5 Mo attendus, comme le
mlpackage FP16) ; (b) quantization **statique QDQ** avec jeu de calibration + re-parité.
14,91 Mo FP32 respecte déjà le budget plan (≤ 15 Mo), sans marge — le FP16 la restaurera.

## 5. Étude courte : ONNX → déploiement Android en 2026

1. **ONNX Runtime Mobile** (recommandé) : mature (Microsoft), AAR standard sur Maven Central
   avec CPU + XNNPACK EP ; `NonMaxSuppression` supporté nativement
   ([operator kernels](https://onnxruntime.ai/docs/reference/operators/OperatorKernels.html),
   [mobile](https://onnxruntime.ai/docs/tutorials/mobile/)). AAR complet ~5-15 Mo/ABI,
   réductible par [custom build](https://onnxruntime.ai/docs/build/custom.html) (format ORT,
   ops limités au modèle). ⚠️ **NNAPI est déprécié au niveau Android depuis Android 15**
   ([AOSP](https://source.android.com/docs/core/ota/modular-system/nnapi)) : ne pas activer
   le NNAPI EP ; le QNN EP (NPU Qualcomm) exige un build custom + SDK.
2. **TFLite / LiteRT** : la voie officielle PyTorch→TFLite est **litert-torch**
   (ex ai-edge-torch, [repo](https://github.com/google-ai-edge/litert-torch)) ;
   [onnx2tf](https://github.com/PINTO0309/onnx2tf) reste maintenu mais son auteur annonce sa
   fin de vie sous 1-2 ans. Meilleure accélération du marché (GPU + delegates NPU
   Qualcomm/MediaTek/Tensor, [LiteRT NPU](https://ai.google.dev/edge/litert/next/npu)),
   runtime le plus léger (~1 Mo), mais chaîne de conversion fragile sur le NMS.
3. **ExecuTorch** : [1.0 GA depuis oct. 2025](https://pytorch.org/blog/introducing-executorch-1-0/),
   backends XNNPACK/Vulkan/Hexagon « production », runtime très compact — mais
   `torchvision.ops.nms` **hors op-set portable** (NMS à réécrire en kernel custom ou côté
   Kotlin) et un an de recul seulement : le choix le plus coûteux pour de la détection.

**Recommandation BrickOFF V2 : ONNX Runtime + XNNPACK EP, NMS dans le graphe.** Zéro étape
de conversion supplémentaire (l'artefact de ce dry-run est directement consommable), parité
prouvée, symétrie de contrat avec le mlpackage iOS. Plan B si le CPU ne suffit pas au
benchmark device : LiteRT via litert-torch, en repartant du wrapper `--nms external`.

## 6. Écarts vs voie iOS

| Aspect | iOS (CoreML) | Android (ONNX) |
|---|---|---|
| Normalisation | Hors graphe (`ImageType` scale/bias) | **In-graph** (op Mul/Add) |
| Entrée | Image RGB 320×320 (pixels, type image) | Tensor float32 CHW 0-255 (conversion Bitmap→float côté Kotlin) |
| NMS | `torchvision::nms` → op CoreML | op ONNX `NonMaxSuppression` |
| Précision livrée | FP16 (7,63 Mo) — parité tangente | FP32 (14,91 Mo) — parité parfaite ; FP16 = étape future |
| Accélérateur | ANE refusé (shapes dynamiques), GPU/CPU OK | NPU non testé ; CPU/XNNPACK OK, NNAPI à proscrire |
| Métadonnées | `user_defined_metadata` | `metadata_props` (mêmes clés `brickoff.*`) |

## 7. Risques restants (aucun bloquant)

1. **Pas de test on-device Android** : parité validée sur onnxruntime CPU desktop uniquement.
   L'AAR onnxruntime-android utilise les mêmes kernels CPU — risque faible, mais latence,
   chaîne Bitmap→tensor (resize scaleFill, RGB) et comportement XNNPACK restent à valider
   sur device au vrai chantier (miroir du jalon 3.2 complet / 3.4).
2. **Taille** : FP32 au ras du budget 15 Mo ; FP16 ou quantization statique QDQ requis
   (la dynamique est prouvée KO ici). AAR runtime en sus (~5-15 Mo/ABI, réductible).
3. **Accélération NPU/GPU** : non couverte par l'AAR standard (NNAPI déprécié, QNN = build
   custom). Si le CPU/XNNPACK rate le budget latence, bascule LiteRT = nouvelle chaîne de
   conversion à re-valider (fallback `--nms external` déjà prêt pour ça).
4. **Exporter TorchScript déprécié** (PyTorch ≥ 2.9 pousse dynamo) : mitigé — le chemin
   dynamo a été testé OK sur ce wrapper ; migrer l'export au vrai chantier.
5. **Changement d'architecture CH-2** (YOLOX/RT-DETR, D02) : comme pour CoreML, seul le
   wrapper de decode change ; chaîne, protocole de parité et choix de runtime restent valables.
