# CH-3 — Export & optimisation mobile (CoreML)

> Durée : 1 semaine. Dépend de CH-2.
> Objectif : 2 fichiers `.mlpackage` validés en parité avec PyTorch, < 50 Mo cumulés.

---

## Jalon 3.1 — Conversion CoreML

### Chaîne de conversion
```
PyTorch (.pt) → TorchScript/ONNX → coremltools → .mlpackage
```

### Tâches
1. **DET** : export via coremltools, input 640×640 RGB, sorties = boxes + scores
   - Décision à prendre et documenter : NMS embarqué dans le modèle CoreML (plus simple côté Swift) ou NMS en Swift (plus de contrôle). **Recommandé : NMS dans le modèle** si le framework retenu le supporte proprement à l'export.
2. **CLS** : export MobileNetV3 → input 224×224, output logits 1000 + softmax intégré
3. Cibler `compute_units = ALL` (laisse CoreML router CPU/GPU/ANE)
4. Embarquer les métadonnées dans le mlpackage : version, date, classes_v1 version, normalisation d'entrée attendue

### ⚠️ Pièges connus
- La normalisation d'entrée (mean/std) DOIT être embarquée dans le modèle CoreML (paramètres scale/bias de l'image input) — sinon divergence silencieuse Swift vs Python
- Vérifier l'ordre des canaux (RGB vs BGR) — source d'erreur classique
- Les opérations non supportées par l'ANE basculent silencieusement sur GPU/CPU → profiler avec Xcode Instruments (CoreML template) pour vérifier où tourne le modèle

### Livrable
- `ml/export/DetModel.mlpackage`, `ml/export/ClsModel.mlpackage`
- `ml/export/export_det.py`, `export_cls.py` (scripts reproductibles)

### Critères d'acceptation
- [ ] Les deux mlpackages se chargent dans Xcode sans warning bloquant
- [ ] Métadonnées présentes et correctes

---

## Jalon 3.2 — Validation de parité numérique

> Étape NON négociable. Un modèle converti peut diverger silencieusement.

### Protocole
1. Sélectionner 100 images du test split + 50 du realworld
2. Inférer avec PyTorch (référence) ET avec CoreML (via script Python coremltools `predict`, puis sur device via une app de test minimale)
3. Comparer :
   - DET : IoU des boxes appariées ≥ 0.95, écart de score < 0.02
   - CLS : top-1 identique sur ≥ 98% des images, écart max softmax < 0.05

### Livrable
- `ml/export/PARITY_REPORT.md` : tableaux de comparaison, images divergentes analysées

### Critères d'acceptation
- [ ] Seuils de parité atteints
- [ ] Toute divergence > seuil expliquée (et corrigée si systématique)

---

## Jalon 3.3 — Quantization & taille

### Tâches
1. Baseline : poids FP16 (défaut CoreML) → mesurer taille + accuracy
2. Tester quantization INT8 (palettization/linear quantization coremltools) sur CLS d'abord
3. Pour chaque variante : re-dérouler le protocole de parité (jalon 3.2)
4. Décision : garder la variante la plus petite qui ne perd pas plus de 1 point d'accuracy realworld

### Budget taille
| Composant | Budget |
|---|---|
| DET .mlpackage | ≤ 15 Mo |
| CLS .mlpackage | ≤ 25 Mo |
| Palette + configs | < 1 Mo |
| Base Rebrickable SQLite (CH-7) | ≤ 80 Mo |
| **Total assets data app** | **≤ 120 Mo** |

### Livrable
- mlpackages finaux + `QUANTIZATION_REPORT.md`

### Critères d'acceptation
- [ ] Budgets respectés
- [ ] Perte accuracy ≤ 1 pt vs FP16

---

## Jalon 3.4 — Benchmark on-device

### Protocole
1. App de test minimale Xcode (un écran, charge le modèle, infère sur images bundle)
2. Mesurer sur les 2 devices de test (médian + ancien) :
   - Latence DET par frame (médiane sur 100 inférences, après 10 de warmup)
   - Latence CLS par crop
   - Latence pipeline complet pour une scène à 30 pièces
   - Pic mémoire
3. Profiler avec Instruments : vérifier l'utilisation effective de l'ANE

### Cibles
| Métrique | Device médian | Device ancien |
|---|---|---|
| DET / frame | ≤ 80 ms | ≤ 200 ms |
| CLS / crop | ≤ 15 ms | ≤ 40 ms |
| Scène 30 pièces (DET + 30×CLS + 30×COLOR) | ≤ 600 ms | ≤ 1.5 s |
| Pic mémoire | ≤ 400 Mo | ≤ 400 Mo |

### Livrable
- `ml/export/BENCHMARK_DEVICE.md`

### Critères d'acceptation
- [ ] Cibles atteintes OU plan d'optimisation documenté (résolution réduite, batch crops, etc.)

---

## Sortie de chantier CH-3

- 2 mlpackages tagués `coreml-v1.0` + rapports parité/quantization/benchmark
- `CHANGELOG_CH3.md`
- **Handoff CH-5** : mlpackages + spécification exacte des I/O (voir contrat dans `12_CONVENTIONS_AI.md` §Modèles)
