# Convention d'annotation — visibilité des pièces (v1, 2026-07-05)

> **Unique et commune aux trois mondes** : scènes synthétiques (générateur CH-S), set réel TAS
> (S.0), futur corpus réel d'entraînement (jalon 1.7). Écrite AVANT toute annotation
> (revue CH-S, constat 3). Toute évolution = nouvelle version ici, jamais un écart local.

## Règles

1. **Une bbox par pièce dont ≥ 25 % de la surface est visible** (estimation visuelle pour
   l'humain ; ratio de pixels visibles/total pour le synthétique).
2. **Zone grise 10-25 % visible → bbox avec flag `hard`** : ces pièces ne comptent NI comme
   positifs d'entraînement NI comme faux positifs/négatifs à l'évaluation.
3. **< 10 % visible → pas de bbox.**
4. La bbox couvre **la partie VISIBLE** de la pièce (pas l'étendue supposée sous l'occlusion).
5. Pièces coupées par le bord du cadre : mêmes règles, appliquées à la partie dans le cadre
   (cohérent avec la convention observée du corpus gdansk).
6. Une pièce = une bbox, même si l'occlusion la coupe visuellement en plusieurs fragments
   (bbox englobante des fragments visibles).
7. Objets non-LEGO (distracteurs) : jamais annotés.

## Formats

- Réel (Label Studio) : export COCO/VOC avec attribut `hard` (checkbox par bbox).
- Synthétique : YOLO txt + manifest JSON par scène (`coverage` exact par pièce, `hard` si 0,10 ≤ coverage < 0,25).
