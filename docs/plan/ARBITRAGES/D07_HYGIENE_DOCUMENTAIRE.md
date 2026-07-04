# D07 — Hygiène documentaire : statut de chaque fichier du corpus

**Statut : ✅ Tranché (2026-07-04) — 3 actions manuelles restantes (déplacement/suppression, laissées au product owner)**

## Problème

Le dossier `LEGO_AI_Plan_Complet/` mélange des documents de statuts différents (plan normatif,
exploration historique, extensions, doublons, et **un document d'un autre projet**). Sans registre
de statuts, un exécutant ne sait pas ce qui fait foi.

## Registre des statuts

| Fichier | Statut | Détail |
|---|---|---|
| `00_MASTER_PLAN.md` | **NORMATIF** (racine) | Amendé par les arbitrages D02, D03, D05, D06 |
| `01_CH0` → `11_CH10` | **NORMATIF** | Plans de chantier ; CH-2 se lit avec le doc 14 (D05) |
| `12_CONVENTIONS_AI.md` | **NORMATIF** (contrats) | Source de vérité des contrats inter-modules |
| `13_GENERATION_FIGURES.md` | **NORMATIF différé** | Roadmap V1.5/V3 officialisée par D06 |
| `14_APPRENTISSAGE_RENFORCE.md` | **NORMATIF** | Gouverne la méthode de CH-2 (D05) |
| `../Sans titre.md` (racine BrickOFF) | **ARCHIVE historique** | Exploration initiale ; obsolète sur : plateforme (D01), YOLOv8 (D02), pub (D03), 300 Mo (D04). Ne jamais l'utiliser comme référence d'exécution |
| `00_MASTER_PLAN copie.md` | **DOUBLON strict** (diff vide) | À supprimer |
| `12_CONVENTIONS_AI copie.md` | **DOUBLON strict** (diff vide) | À supprimer |
| `1RR-brief-design.md` | **HORS PROJET** | Voir ci-dessous |

## Cas `1RR-brief-design.md`

Ce fichier est le brief de design d'un **autre produit** : "1RR", une plateforme de paris/prédiction
orientée créateurs (métaphore verre/givre/bar, deck de cartes swipe, réputation double anneau).
**Aucun lien avec le projet LEGO.** Sa présence ici est dangereuse : il parle lui aussi de
"liquid glass" et un exécutant pressé pourrait contaminer la direction artistique de CH-8 avec
(le brief 1RR affirme d'ailleurs que "le liquid glass seul ne différencie plus" — position qui ne
s'applique **pas** à BrickOFF, où le glass natif iOS est un choix de sobriété, pas de signature).

**Décision :** le fichier est exclu du corpus BrickOFF. Il référence un proto `deck-1rr.html` absent
du dossier — il appartient vraisemblablement au projet du dossier `~/Documents/Partie politique/`.

## Actions manuelles recommandées (non exécutées — suppression/déplacement = décision du propriétaire)

1. Supprimer `00_MASTER_PLAN copie.md` et `12_CONVENTIONS_AI copie.md` (doublons vérifiés octet pour octet).
2. Déplacer `1RR-brief-design.md` hors de `LEGO_AI_Plan_Complet/` (vers le projet 1RR, où qu'il vive).
3. Renommer `Sans titre.md` en `ARCHIVE_synthese_initiale.md` (ou le déplacer dans un sous-dossier `archive/`) pour matérialiser son statut.

## Règle pour la suite

Tout nouveau document entre dans le dossier avec un statut explicite (en-tête "NORMATIF / ARCHIVE /
EXPLORATOIRE") et une entrée dans l'index du Master Plan ou dans `ARBITRAGES/00_INDEX.md`.
