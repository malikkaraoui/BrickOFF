# CHANGELOG CH-3 — Export & optimisation mobile (CoreML)

> Journal du chantier. Le CH-3 réel démarre quand CH-2 livre le modèle de production ;
> cette entrée documente un DRY-RUN complet de la chaîne d'export sur le champion courant.

## 2026-07-07 — DRY-RUN jalons 3.1 + 3.2 sur det_v3 (SSDLite320, mono-classe) ✅ CHAÎNE VALIDÉE

**Objectif** : dé-risquer la chaîne PyTorch → CoreML maintenant (et donner à CH-5 un vrai
mlpackage à brancher) sans attendre le modèle de production. Aucun engagement d'architecture :
si CH-2 livre un YOLOX/RT-DETR, seul le wrapper de decode change, la chaîne et le protocole
de parité sont réutilisables tels quels.

### Ce qui est validé
- **Conversion OK** : `ml/export/export_det.py` — `best.pt` → torch.jit.trace → coremltools 9.0
  → ML Program, cible iOS 17. Deux variantes produites :
  | Variante | Taille | Budget plan (≤ 15 Mo) |
  |---|---|---|
  | `DetModel.mlpackage` (FP16, défaut) | **7,63 Mo** | ✅ (marge ×2) |
  | `DetModel_fp32.mlpackage` (référence debug) | 15,01 Mo | limite |
- **Parité numérique (jalon 3.2 adapté : 50 images test split, seed 42, CPU des deux côtés,
  seuil produit 0.35)** — rapports `ml/export/parity_report_det*.json` :
  | Critère | FP16 | FP32 |
  |---|---|---|
  | IoU boxes appariées (min / moyenne) | 0.944 / **0.993** | **1.000 / 1.000** |
  | Écart de score (max / moyen) | 0.017 / 0.002 | **0.000** |
  | Top-1 identique | 38/39 | **39/39** |
  | Boxes orphelines | 1 | **0** |
  | Verdict (seuils plan : IoU ≥ 0.95, Δscore < 0.02) | FAIL (de justesse) | **PASS** |
  La parité FP32 **parfaite** prouve que la chaîne (normalisation embarquée, decode
  ré-implémenté, NMS) est exactement correcte. Les 2 divergences FP16 sur 50 images sont de la
  pure quantization : (a) un score 0.348→0.361 qui chevauche le seuil 0.35 (box « orpheline »
  par effet de seuil, Δ réel 0.013 < 0.02), (b) une box décalée de ~2 px (IoU 0.944, Δscore 0.0001).
- **Métadonnées embarquées** : version, date, poids source, contrat I/O, normalisation,
  mode NMS, seuil produit, mapping classes (`user_defined_metadata`, préfixe `brickoff.`).
- **Environnement** : `coremltools==9.0` ajouté à `ml/requirements.txt` (+ deps attrs, cattrs,
  protobuf, pyaml). Torch 2.12.1 non officiellement supporté par coremltools (testé ≤ 2.7) —
  simple warning, conversion et parité OK.

### Décision NMS : **EMBEDDED** (dans le mlpackage) — conforme à la reco du plan
- coremltools 9.0 convertit `torchvision::nms` nativement. Le mlpackage sort directement
  `boxes [N≤300, 4]` XYXY **normalisé 0-1** + `scores [N]` post-NMS (iou 0.55, topk 300),
  N dynamique. Côté Swift : un simple filtre `score ≥ 0.35`, zéro NMS à porter.
- Fallback conservé : `--nms external` exporte les 3234 anchors décodées brutes
  (NMS à faire côté client) si l'embedded posait problème on-device.

### Architecture d'export (le point non trivial, réutilisable pour le modèle de production)
Le forward torchvision embarque transform (resize+normalisation, tailles variables) et
postprocess (boucles Python) → non traçable tel quel. `export_det.py` exporte un **wrapper
cœur** : backbone + head + decode SSD ré-implémenté en ops tensorielles (box_coder weights
(10,10,5,5), clip log(1000/16), anchors précalculées — constantes à 320×320) + topk + NMS.
Parité FP32 = 1.0 ⇒ la ré-implémentation est bit-fidèle au postprocess torchvision.

### Pièges rencontrés (à rejouer au vrai CH-3)
1. **Normalisation embarquée** (piège n°1 du plan) : mean=std=0.5 pour SSDLite (PAS ImageNet
   0.485/0.229 !) ⇒ `ImageType(scale=2/255, bias=[-1,-1,-1])`. À relire dans
   `model.transform.image_mean/std` du modèle réel — `export_det.py` a un assert qui casse
   si la normalisation change.
2. **RGB confirmé** (`color_layout=RGB`) ; vérifié par la parité (une inversion BGR
   effondrerait les scores, pas un écart de 0.002).
3. **Resize NON aspect-preserving** : le transform SSDLite fait un scaleFill 320×320.
   Côté Swift, il faudra le même mode (pas scaleFit). La parité ici isole le modèle
   (même image 320×320 pré-redimensionnée des deux côtés) — la parité resize Swift vs
   Python reste à valider on-device (jalon 3.2 complet).
4. **NMS embarqué ⇒ shapes dynamiques ⇒ pas d'ANE** : au chargement, E5RT logge
   « Data-dependent shapes were disabled » et l'ANE refuse le graphe ; `compute_units=ALL`
   fonctionne (fallback GPU/CPU silencieux — piège n°3 du plan, confirmé en vrai). À profiler
   au jalon 3.4 ; si la latence dépasse le budget (80 ms device médian), basculer
   `--nms external` + NMS Swift pour récupérer l'ANE, ou sortir topk-300 à taille fixe.
5. **FP16 vs seuils de parité** : les seuils du plan (IoU ≥ 0.95 par box, top-1 strict) sont
   atteignables mais tangents en FP16 sur les scores qui chevauchent le seuil produit et les
   petites boxes. Pour le vrai CH-3 : soit précision mixte (decode/head en FP32 via
   `op_selector`), soit assouplir le critère en l'exprimant hors effet de seuil
   (comparer les paires au-dessus de 0.30 par ex.). À trancher au jalon 3.3 avec la
   quantization.
6. `torch.load` du state_dict exige de reconstruire l'architecture exacte
   (`num_classes=2`, convention fond+classe) — pas de modèle sérialisé complet.

### Reste pour le vrai CH-3 (non couvert par ce dry-run)
- Jalon 3.1 : export CLS (`export_cls.py`) ; vérification chargement Xcode sans warning.
- Jalon 3.2 complet : 100 images test + 50 realworld ; validation **on-device** (app de test),
  y compris la chaîne de resize Swift ; `PARITY_REPORT.md`.
- Jalon 3.3 : quantization INT8/palettization + re-parité.
- Jalon 3.4 : benchmark device (latence, ANE via Instruments, mémoire).
- Adapter le wrapper de decode à l'architecture de production (YOLOX/RT-DETR, D02) ;
  le contrat §1.5 (12_CONVENTIONS_AI.md) prévoit 640×640 — ce dry-run est à 320×320
  (taille native SSDLite) : mettre à jour le contrat ou la taille d'entrée au vrai CH-3.

### Reproduction
```bash
.venv/bin/python ml/export/export_det.py                 # FP16 embedded NMS (défaut)
.venv/bin/python ml/export/export_det.py --precision fp32 --out ml/export/DetModel_fp32.mlpackage
.venv/bin/python ml/export/parity_check.py               # 50 images, rapport JSON + exit code
```

## 2026-07-07 — Voie Android — dry-run (garde-fou amendement D01) ✅ VALIDÉE

Pendant Android du dry-run ci-dessus, même champion det_v3. Détails, étude des runtimes
2026 et risques : **`docs/research/ANDROID_EXPORT_PATH.md`**.

- **Export OK** : `ml/export/export_det_onnx.py` — le wrapper `SSDLiteDetCore` d'
  `export_det.py` est réutilisé TEL QUEL → `DetModel.onnx` (opset 18, FP32, **14,91 Mo**,
  budget ≤ 15 Mo tenu sans marge — FP16/quantization statique = étape future).
  NMS **embarqué** via l'op ONNX standard `NonMaxSuppression` (même contrat de sortie
  qu'iOS) ; fallback `--nms external` (3234 sorties fixes) validé aussi. Normalisation
  **in-graph** (`x*2/255 - 1` — pas d'équivalent ImageType en ONNX) : le client Android
  envoie des pixels RGB bruts 0-255, CHW, resize scaleFill.
- **Parité PARFAITE** (`parity_check_onnx.py`, protocole identique à `parity_check.py` :
  50 images test, seed 42, CPU vs CPU) : IoU min/moy **1.000/1.000**, Δscore max **0.000**,
  top-1 **39/39**, 0 orpheline → **PASS** (rapport `parity_report_det_onnx.json`).
- **Quantization dynamique testée et REJETÉE** : 4,18 Mo mais parité effondrée
  (IoU moy 0.79, top-1 1/38 — rapport `parity_report_det_onnx_int8dyn.json` conservé,
  modèle supprimé). La voie taille = FP16 ou QDQ statique calibrée (jalon 3.3 Android).
- **Runtime recommandé (étude sourcée dans le doc)** : **ONNX Runtime Mobile + XNNPACK EP**
  (NonMaxSuppression natif, zéro conversion en plus). NNAPI déprécié depuis Android 15 —
  à proscrire. Plan B GPU/NPU : LiteRT via litert-torch, en repartant de `--nms external`.
- Env : `onnx`, `onnxruntime`, `onnxscript` (+ deps) ajoutés à `ml/requirements.txt`.
  Exporter TorchScript legacy utilisé, mais chemin dynamo testé OK (pas d'impasse).
- Reste (vrai chantier Android, V2) : validation on-device (AAR onnxruntime-android,
  chaîne Bitmap→tensor, latence XNNPACK), FP16/QDQ + re-parité, taille de l'AAR (custom
  build si besoin).

```bash
.venv/bin/python ml/export/export_det_onnx.py            # DetModel.onnx (NMS embarqué)
.venv/bin/python ml/export/parity_check_onnx.py          # 50 images, rapport JSON + exit code
```
