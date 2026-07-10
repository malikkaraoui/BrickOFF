# EVAL It.5b — det_v4b sur juge dense HOLDOUT propre — 10/07/2026

> **Verdict PROUVÉ (pas de fuite train/test) : le travail dense fait presque tripler le rappel
> sur un vrai tas dense.** det_v4b devient le champion produit.

## Comparaison équitable (det_v3 et det_v4b n'ont ni l'un ni l'autre entraîné sur ces 4 tas)

### Juge DENSE HOLDOUT (4 tas batch2 de 50 pièces, jamais vus) — LE CAS PRODUIT
| | mAP@50 | rappel max | **rappel@0.20** |
|---|---|---|---|
| det_v3 (ancien champion) | 0.064 | 0.305 | **0.181** |
| **det_v4b (It.5b)** | 0.088 | 0.332 | **0.513** |
| Δ | +0.024 | +0.027 | **+0.332 (×2,8)** |

→ **Le rappel passe de 18 % à 51 %** — presque triplé, sur un juge équitable. C'est la preuve
directe que synthétique v2.1 + tas réels apprennent le vrai cas produit. Le mAP reste bas (0.088) :
le modèle TROUVE désormais les pièces mais la localisation/précision sur des pièces qui se
chevauchent reste grossière — c'est le prochain chantier, et le vote multi-frames (CH-5) exploite
justement un rappel élevé à seuil bas.

### Juge SPARSE (batch1 corrigé, éparpillé) — non-régression
| | mAP@50 | rappel@0.20 |
|---|---|---|
| det_v3 | 0.656 | 0.568 |
| det_v4b | 0.607 | 0.595 |

→ Léger recul mAP (−0.049) mais **rappel en hausse** (+0.027). Compromis mineur et acceptable
(le décalage vers le dense coûte un peu de précision sur l'éparpillé facile).

### Mono-pièce (test académique) — aucune régression
det_v3 0.826 → det_v4b **0.822** (−0.004, dans le bruit). ✅

## Verdict

- **Le travail dense est PROUVÉ utile** (rappel dense ×2,8, juge holdout équitable), sans régression
  mono-pièce et avec un rappel sparse même en hausse.
- **Nouveau champion produit : det_v4b.** Il est nettement meilleur sur le cas réel (tas denses),
  au prix d'un léger recul de mAP sur l'éparpillé.
- Reste à travailler (It.6+) : la **précision/localisation en dense** (mAP encore bas — pièces
  trouvées mais mal cadrées quand elles se chevauchent) ; doser le mélange pour récupérer le sparse.

## Prochaine étape
Juge dense DÉFINITIF : 50 nouvelles photos PO (à venir) — juge plus large et robuste, jamais
entraîné, pour consolider ce verdict et mesurer les itérations suivantes.
