# 15 — Veille GitHub : repos exploitables par chantier

> **Statut : RESSOURCE (non normatif).** Recensement effectué le **2026-07-04** via l'API GitHub
> (étoiles, licence, date de dernier push vérifiés à cette date — à re-vérifier au moment de l'exécution).
> Règle de lecture : ⚠️ **un repo sans licence est juridiquement non réutilisable** (tous droits réservés) —
> il ne sert que d'inspiration d'approche, jamais de code copié.

---

## 1. Frameworks de détection — conforte l'arbitrage [D02](ARBITRAGES/D02_FRAMEWORK_DETECTION.md)

| Repo | ⭐ | Licence | Activité | Verdict |
|---|---|---|---|---|
| [Megvii-BaseDetection/YOLOX](https://github.com/Megvii-BaseDetection/YOLOX) | 10 519 | **Apache-2.0** | dernier push 2025-06, ~770 issues ouvertes | Éprouvé, export ONNX natif, mais **maintenance ralentie** |
| [lyuwenyu/RT-DETR](https://github.com/lyuwenyu/RT-DETR) | 5 339 | **Apache-2.0** | actif (2026-06) | Officiel CVPR 2024, PyTorch, **activement maintenu** |

**Enseignement pour CH-0 jalon 0.3** : les deux candidats permissifs de D02 sont confirmés Apache-2.0.
À date, **RT-DETR part favori** (maintenance active) ; YOLOX reste valable si la variante nano de RT-DETR
s'avère trop lourde pour la cible ANE. Décision finale en CH-0 comme prévu.

---

## 2. Voie synthétique LDraw → Blender — outille le doc 14 §2.1 (et D05)

**Constat majeur : la chaîne complète existe déjà en open source.** Le pipeline "importer les pièces
LDraw dans Blender → rendre des scènes annotées" a été démontré plusieurs fois :

| Repo | ⭐ | Licence | Rôle |
|---|---|---|---|
| [TobyLobster/ImportLDraw](https://github.com/TobyLobster/ImportLDraw) | 367 | GPL-2.0 | Plugin Blender d'import LDraw, **actif (2026-04)**, le standard de fait |
| [ScanMountGoat/ldr_tools_blender](https://github.com/ScanMountGoat/ldr_tools_blender) | 43 | **MIT** | Alternative d'import LDraw, active (2026-05) — préférable si on veut forker |
| [jtheiner/LegoBrickClassification](https://github.com/jtheiner/LegoBrickClassification) | 114 | ⚠️ aucune | **Le pattern exact du besoin** : génération d'images de classification par part_id depuis LDraw+Blender. Inspiration d'architecture uniquement (pas de licence) |
| [mantyni/Multi-object-detection-lego](https://github.com/mantyni/Multi-object-detection-lego) | 16 | MIT | Détection multi-pièces entraînée sur scènes Blender générées — mini-référence bout-en-bout |
| [spencerhhubert/brick-renderer](https://github.com/spencerhhubert/brick-renderer) | 4 | ⚠️ aucune | "Render realistic training images of ldraw pieces", récent (2025-07) — à regarder pour les astuces de réalisme |
| [gkjohnson/ldraw-parts-library](https://github.com/gkjohnson/ldraw-parts-library) | 15 | (miroir) | Miroir de la bibliothèque de pièces LDraw. Licence officielle LDraw = CC-BY (à vérifier précisément en CH-0) |

**Note licence importante** : un plugin Blender GPL utilisé comme **outil interne de génération de données**
n'impose rien à l'app (les images rendues ne sont pas des œuvres dérivées du plugin). Le GPL n'est un
problème que pour du code embarqué dans l'app — ce qui n'est pas le cas ici.

**Impact planning** : le doc 14 estimait "1–2 semaines de mise en place" du pipeline synthétique ;
avec ImportLDraw/ldr_tools_blender comme fondation, l'estimation est confortée voire réductible.

---

## 3. Auto-annotation bootstrap — alternative concrète pour le doc 14 §2.2

Le doc 14 proposait LocateAnything-3B ou SAM pour pré-annoter les photos réelles. **Mieux : il existe un
service spécialisé LEGO déjà opérationnel** — [Brickognize](https://brickognize.com) (API publique de
reconnaissance de pièces/sets/minifigs, non open source mais gratuite à ce jour). Écosystème GitHub :

| Repo | ⭐ | Licence | Usage |
|---|---|---|---|
| [cfrBernard/BulkCropper](https://github.com/cfrBernard/BulkCropper) | 1 | MIT | Segmentation/crop automatique de pièces individuelles depuis une photo d'étalement — utile pour préparer le realworld set (CH-1 jalon 1.6) |
| [NazarLysyi/brickscope](https://github.com/NazarLysyi/brickscope) | 8 | MIT | Serveur MCP pour l'API Brickognize — permet de piloter la pré-annotation directement depuis une session IA |
| [ryantheengineer/lego-sorting](https://github.com/ryantheengineer/lego-sorting) | 2 | GPL-3.0 | Exemple d'intégration Brickognize + Rebrickable |

**Usage prévu** : pendant le DÉVELOPPEMENT uniquement (pré-annotation du realworld test set, bootstrap
de données réelles) — aucune dépendance runtime, cohérent avec l'offline. ⚠️ Vérifier les CGU de l'API
Brickognize (usage des annotations pour entraîner un modèle commercial) en CH-0, même réflexe que Rebrickable.

---

## 4. Catalogue Rebrickable — accélère CH-7 jalon 7.1

| Repo | ⭐ | Licence | Rôle |
|---|---|---|---|
| [jncraton/rebrickable-sqlite](https://github.com/jncraton/rebrickable-sqlite) | 52 | **MIT** | Scripts CSV snapshot → SQLite local, **actif (2026-01), 0 issue ouverte**. C'est quasi exactement le jalon 7.1 — base de départ directe, il restera à ajouter nos filtres (scope classes, ≤ 1500 pièces) et notre schéma |
| [xxao/rebrick](https://github.com/xxao/rebrick) | 50 | MIT | Client Python API Rebrickable (utile CH-0/CH-1 pour vérifications) |
| [rienafairefr/pyrebrickable](https://github.com/rienafairefr/pyrebrickable) | 7 | MIT | Alternative client Python + CLI |
| [renTramontano/RebrickableSDK](https://github.com/renTramontano/RebrickableSDK) | 7 | MIT | Client Swift — **vieux (2022)** et inutile en V1 (l'app n'appelle pas l'API), noté pour mémoire |

---

## 5. Veille concurrentielle & projets frères

| Repo | ⭐ | Licence | Intérêt |
|---|---|---|---|
| [brickit-app/brickit-flutter-camera](https://github.com/brickit-app/brickit-flutter-camera) | 8 | Apache-2.0 | Org GitHub officielle de **Brickit** : fork du plugin caméra Flutter → **insight : Brickit est une app Flutter**. Conforte D01 (le natif iOS + CoreML est un avantage perf/latence possible face à eux) |
| [basicallysource/sorter](https://github.com/basicallysource/sorter) | 129 | ⚠️ aucune | Machine de tri LEGO active (2026-01) — à lire pour leur stack de reconnaissance |
| [blokbot-io/OpenBlok](https://github.com/blokbot-io/OpenBlok) | 29 | MIT | Système d'identification/tri IA de pièces — approche caméra fixe |
| [hubnedav/PrintABrick](https://github.com/hubnedav/PrintABrick) | 266 | GPL-2.0 | Catalogue web de pièces basé LDraw — référence utile pour le **mapping LDraw ↔ part ids Rebrickable** (piège connu : les numérotations divergent parfois) |
| [LegoSorter/LegoSorterServer](https://github.com/LegoSorter/LegoSorterServer) | 9 | ⚠️ aucune | Projet académique de tri (détection+classification) — inspiration |

---

## 6. Synthèse des enseignements (ce que cette veille change)

1. **D02 conforté et affiné** : YOLOX et RT-DETR confirmés Apache-2.0 ; RT-DETR favori à date (maintenance).
2. **Le risque n°1 (domain gap, D05) est mieux couvert que prévu** : la chaîne synthétique LDraw→Blender
   existe en MIT (`ldr_tools_blender`) et le pattern complet a déjà été démontré publiquement (jtheiner,
   mantyni). L'investissement doc 14 §2.1 démarre de ~40 % du chemin, pas de zéro.
3. **CH-7 jalon 7.1 accéléré** : `rebrickable-sqlite` (MIT) fait déjà le gros du travail CSV→SQLite.
4. **Brickognize remplace avantageusement LocateAnything-3B** comme outil de pré-annotation (spécialisé
   LEGO, API prête) — sous réserve de ses CGU, à vérifier en CH-0.
5. **Insight concurrentiel** : Brickit tourne sur Flutter — le choix natif iOS (D01) est un différenciateur
   potentiel de latence/qualité caméra, pas seulement une contrainte.
6. **Rien trouvé qui remette en cause l'architecture 2-stages** (DET mono-classe + CLS crop) — les projets
   de tri les plus aboutis utilisent des variantes du même schéma.

## Actions dérivées (à intégrer aux chantiers, pas de nouveau chantier)

- **CH-0 jalon 0.3** : ajouter à la revue de licences — CGU API Brickognize, licence bibliothèque LDraw (CC-BY ?), et trancher YOLOX vs RT-DETR sur l'état des repos à date.
- **CH-1 jalon 1.6** : évaluer BulkCropper pour préparer les crops du realworld set.
- **CH-2/doc 14** : partir de `ldr_tools_blender` (MIT) pour le pipeline synthétique ; lire jtheiner pour l'architecture du générateur (sans copier le code, pas de licence).
- **CH-7 jalon 7.1** : partir de `rebrickable-sqlite` (MIT) comme squelette du script `07_build_catalog.py`.
