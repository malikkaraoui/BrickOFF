# EVAL It.5 — det_v4 (réel batch1+2 / synthétique v2.1) — 09/07/2026

> Résultat honnête et nuancé : It.5 **ne bat pas** le champion sur le juge mesurable (léger recul),
> **mais** révèle que ce juge nous trompait — le champion est en réalité mauvais sur le vrai cas
> produit (tas denses), et le travail dense aide clairement, sans qu'on puisse encore le PROUVER
> proprement (fuite train/test). C'est un résultat de méthode, pas un échec.

## Les 3 mesures

### 1. Juge SPARSE (batch1 corrigé PO, 50 photos éparpillées 4-10 pièces)
| | mAP@50 | rappel max | rappel@0.20 |
|---|---|---|---|
| det_v3 (champion) | **0.656** | 0.847 | 0.568 |
| det_v4 (It.5) | 0.576 | 0.839 | 0.572 |
| Δ | **−0.080** | −0.008 | +0.004 |

→ **Léger RECUL en mAP.** En s'entraînant beaucoup sur du dense, det_v4 s'est décalé et sur-prédit
un peu sur les scènes éparpillées → précision en baisse. Le rappel est stable.

### 2. Non-régression mono-pièce (test académique)
det_v3 0.826 → det_v4 **0.802** (−0.024). Légère régression, cohérente avec le décalage vers le dense.

### 3. Juge DENSE (les 9 tas batch2 de 50 pièces) — LA RÉVÉLATION
| | mAP@50 | rappel max | rappel@0.20 |
|---|---|---|---|
| det_v3 (JAMAIS vu = **juste**) | 0.079 | 0.305 | **0.203** |
| det_v4 (a vu en entraînement = **biaisé optimiste**) | 0.143 | 0.387 | 0.566 |

→ **Le champion det_v3 ne trouve que 20 % des pièces d'un vrai tas dense.** On ne le savait pas
parce que notre juge (batch1) est éparpillé, pas dense. det_v4 monte à 57 % de rappel — mais il a
vu ces tas à l'entraînement, donc le chiffre est gonflé par la mémorisation. La DIRECTION est
néanmoins forte (0.20 → 0.57).

## Ce qu'on apprend (plus important que le score)

1. **Notre juge mesurait le mauvais cas.** batch1 est éparpillé (facile) ; le produit scanne des
   TAS denses, où le champion est faible. On optimisait/mesurait à côté.
2. **Le travail dense (synthétique v2.1 + batch2) aide le cas dense** — mais impossible à PROUVER
   proprement : les tas denses annotés sont dans l'entraînement de det_v4 (fuite train/test).
3. **Compromis dense↔sparse** : pousser fort vers le dense coûte un peu sur l'éparpillé. À doser.

## Décision & prochaine action (It.6)

- **Champion mesuré conservé : det_v3** (det_v4 ne le bat pas sur le mesurable). det_v4 = candidat
  dense prometteur mais NON PROUVÉ.
- **Action bloquante : il faut un JUGE DENSE propre**, jamais vu à l'entraînement. Options :
  (a) le PO fournit ~10 tas denses dédiés HOLDOUT (jamais entraînés) ;
  (b) les décomptes physiques des 23 tas monochromes → juge par comptage ;
  (c) on réserve une partie des tas batch2 hors entraînement.
  Sans ça, on ne saura pas si le dense progresse vraiment.
- Doser le mélange (moins de sur-échantillonnage batch2, garder un peu de sparse) pour ne pas
  régresser sur l'éparpillé.
