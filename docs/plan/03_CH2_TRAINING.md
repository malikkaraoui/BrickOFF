# CH-2 — Entraînement des modèles

> Durée : 2–4 semaines selon GPU. Dépend de CH-1.
> Deux modèles distincts : DET (détection 1 classe) et CLS (classification 1000 classes).

---

## Rappel architecture 2 stages

```
Image → [DET: localise toutes les pièces, classe unique "lego_piece"]
      → pour chaque bbox: crop → [CLS: identifie le part_id parmi 1000]
                                → [COLOR: pipeline LAB, pas un modèle ML]
```

Pourquoi 2 stages plutôt qu'un YOLO 1000 classes :
1. La détection mono-classe est beaucoup plus robuste (rappel élevé)
2. Le classifier sur crop 224×224 voit la pièce en grand → précision fine supérieure
3. Les deux modèles s'améliorent indépendamment (maintenance)

---

## Jalon 2.1 — Baseline détection (DET v0)

### Config d'entraînement
| Paramètre | Valeur initiale |
|---|---|
| Modèle | YOLO nano du framework retenu en CH-0 (YOLOX-nano si Apache exigée) |
| Input size | 640×640 |
| Classes | 1 ("lego_piece") |
| Epochs | 100 (early stopping patience 15) |
| Batch | max tenant en VRAM (typiquement 32–64) |
| Optim | défauts du framework (ne pas tuner en v0) |

### Tâches
1. Lancer l'entraînement sur `processed/detection/`
2. Logger : loss curves, mAP@50, mAP@50-95, précision, rappel (TensorBoard ou W&B)
3. Évaluer sur le test split ET sur `realworld_test/`

### Livrable
- `ml/runs/det_v0/` : poids + logs + rapport `EVAL_DET_V0.md`

### Critères d'acceptation (baseline, pas la cible finale)
- [ ] mAP@50 ≥ 0.85 sur test split
- [ ] Rappel ≥ 0.90 sur test split (on préfère détecter trop que rater des pièces)
- [ ] Évaluation realworld documentée (même si plus basse — c'est attendu)

---

## Jalon 2.2 — Baseline classification (CLS v0)

### Config d'entraînement
| Paramètre | Valeur initiale |
|---|---|
| Modèle | MobileNetV3-Large pré-entraîné ImageNet |
| Input | 224×224 |
| Classes | 1000 (mapping `classes_v1.json`) |
| Epochs | 50, early stopping patience 10 |
| LR | 1e-3 (head) puis fine-tuning full à 1e-4 |
| Loss | CrossEntropy + label smoothing 0.1 |
| Augmentation | incl. hue shift agressif (cf. CH-1 jalon 1.4) |

### Tâches
1. Phase 1 : freeze backbone, entraîner la tête seule (5 epochs)
2. Phase 2 : unfreeze, fine-tuning complet
3. Métriques : top-1, top-5, matrice de confusion, accuracy par classe

### Livrable
- `ml/runs/cls_v0/` : poids + `EVAL_CLS_V0.md` incluant les 20 pires classes

### Critères d'acceptation
- [ ] Top-1 ≥ 0.80, Top-5 ≥ 0.95 sur test split
- [ ] Liste des classes < 0.50 accuracy identifiée avec hypothèses (classes visuellement quasi identiques ? → documenter les paires confondues)

---

## Jalon 2.3 — Pipeline couleur (COLOR v0)

> Pas un modèle ML. Algorithme déterministe, développé en Python pour validation, qui sera réimplémenté en Swift (CH-5).

### Algorithme de référence
1. Input : crop bbox (depuis DET)
2. Segmentation grossière fond/pièce : seuillage par distance au coin de l'image (le fond domine les bords) OU GrabCut initialisé par la bbox
3. Pixels "pièce" → conversion sRGB → LAB (D65)
4. Médiane LAB (plus robuste que la moyenne aux reflets)
5. Distance ΔE (CIE76 suffisant en v0) contre chaque entrée de `lego_colors_lab.json`
6. Output : `{color_id, confidence}` où confidence = fonction inverse de ΔE ; si ΔE min > seuil (à calibrer, départ : 20) → "unknown"

### Tâches
1. Implémenter en Python : `ml/color/color_matcher.py`
2. Évaluer sur `realworld_test/` (qui a les color_id annotés)
3. Calibrer le seuil "unknown" : compromis précision/couverture
4. Documenter les confusions systématiques (ex : gris clair vs blanc sous lumière chaude)

### Livrable
- `ml/color/color_matcher.py` + tests unitaires
- `EVAL_COLOR_V0.md` : accuracy par condition d'éclairage, matrice de confusion couleurs

### Critères d'acceptation
- [ ] Accuracy couleur ≥ 0.75 sur realworld toutes conditions confondues
- [ ] ≥ 0.85 en condition "lumière du jour"
- [ ] Spécification de l'algo suffisamment précise pour réimplémentation Swift à l'identique (valeurs de seuils figées dans un JSON de config partagé)

---

## Jalon 2.4 — Itérations d'amélioration

> Boucle : analyser les erreurs → corriger data ou config → réentraîner. Max 3 itérations cadrées en V1.

### Méthode (à chaque itération)
1. Extraire les 100 pires prédictions sur realworld
2. Catégoriser les erreurs : occlusion / flou / éclairage / classe ambiguë / annotation fausse
3. Action ciblée selon la catégorie dominante :
   - Annotation fausse → corriger le dataset
   - Éclairage → renforcer l'augmentation correspondante
   - Classes ambiguës → envisager fusion de classes (avec mise à jour de `classes_v1.json` v1.1 ET du mapping Rebrickable)
4. Réentraîner, comparer aux métriques précédentes — ne garder que si amélioration

### Cibles finales V1 (sortie de chantier)
| Métrique | Cible |
|---|---|
| DET rappel (realworld, pièces étalées) | ≥ 0.92 |
| DET mAP@50 (realworld) | ≥ 0.80 |
| CLS top-1 (realworld, scope 1000) | ≥ 0.75 |
| CLS top-5 (realworld) | ≥ 0.92 |
| COLOR accuracy (realworld) | ≥ 0.78 |
| Pipeline complet (part_id + color corrects) | ≥ 0.65 |

### Livrable
- `ml/runs/det_final/`, `ml/runs/cls_final/` : poids gelés + rapports
- `docs/MODEL_CARD.md` : carte de modèle complète (données, métriques, limites connues)

### Critères d'acceptation
- [ ] Toutes les cibles du tableau atteintes OU écart documenté + accepté par le product owner
- [ ] Reproductibilité : seed fixé, configs versionnées, commande d'entraînement exacte dans le rapport

---

## Sortie de chantier CH-2

- Poids finaux DET + CLS gelés et tagués (git tag `models-v1.0`)
- `lego_colors_lab.json` + config seuils couleur figés
- `CHANGELOG_CH2.md`
- Handoff CH-3 : chemins des poids, formats d'entrée/sortie exacts des deux modèles
