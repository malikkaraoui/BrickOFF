# D04 — Budgets de taille : ceux du plan détaillé font foi

**Statut : ✅ Tranché (2026-07-04)**

## Contexte & sources en conflit

- `Sans titre.md` §5 : "Taille modèle cible : **< 300 Mo**".
- `00_MASTER_PLAN.md` §0 & §5 : modèles "**< 50 Mo total**", app complète "**< 350 Mo**".
- `04_CH3_EXPORT_MOBILE.md` jalon 3.3 : DET ≤ 15 Mo, CLS ≤ 25 Mo, palette+configs < 1 Mo, SQLite Rebrickable ≤ 80 Mo → **assets data ≤ 120 Mo**.

## Analyse

Il n'y a pas de vrai conflit, mais un piège de lecture : le "< 300 Mo" de `Sans titre.md` a été écrit
dans le contexte de l'évaluation d'un **VLM compressé** (LocateAnything-3B, §3 du même doc) — approche
**rejetée** au profit du 2-stages YOLO+MobileNet. Un exécutant qui reprendrait ce chiffre comme budget
"disponible" pour les modèles se tromperait d'un ordre de grandeur (×6) et ruinerait les cibles de
latence et de taille d'IPA.

## Décision

**Les budgets de référence sont ceux de CH-3 jalon 3.3, hiérarchie contractuelle :**

| Composant | Budget dur |
|---|---|
| DET .mlpackage | ≤ 15 Mo |
| CLS .mlpackage | ≤ 25 Mo |
| Palette + configs | < 1 Mo |
| rebrickable.sqlite | ≤ 80 Mo |
| **Total assets data** | **≤ 120 Mo** |
| **App installée (IPA)** | **< 350 Mo** (DoD Master Plan) |

Le "< 300 Mo modèle" de `Sans titre.md` est **déclaré obsolète** et ne doit plus être cité.

## Justification

- Les cibles de latence CH-3 (DET ≤ 80 ms/frame sur device médian) ne sont crédibles qu'avec des modèles nano ; 300 Mo de modèle impliquerait une autre architecture entière.
- La marge entre 120 Mo d'assets et 350 Mo d'app absorbe le binaire, les assets UI et l'inflation inévitable — la garder large est volontaire.

## Impacts

- `Sans titre.md` §5 : obsolète (voir D07).
- Aucun fichier de chantier à modifier — CH-3 est la référence.
