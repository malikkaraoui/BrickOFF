# Annotation du set TAS (S.0) — mode d'emploi mercredi

> Outillage du jalon S.0 (`docs/plan/16_PIPELINE_SYNTHETIQUE.md`). Convention à respecter :
> `data/manifests/annotation_convention.md` (v1). Protocole photos :
> `docs/plan/PROTOCOLE_PHOTOS_TAS.md`. **Aucune image S.0 ne rejoint jamais l'entraînement.**

## Rappel convention (à avoir en tête en annotant)

- **≥ 25 % de la pièce visible → bbox "lego"** (sur la partie VISIBLE seulement, pas
  l'étendue supposée sous l'occlusion).
- **10-25 % visible → bbox + cocher la case `hard`** (sélectionner la région, cocher).
- **< 10 % → pas de bbox.**
- Une pièce coupée en fragments par l'occlusion = **une seule bbox** englobant les fragments.
- Distracteurs non-LEGO : **jamais annotés**.

## 0. Prérequis (FAIT le 06/07 — rien à installer mercredi)

- `.venv` du projet : `pillow-heif==1.4.0` installé (HEIC→JPEG) — cf. `ml/requirements.txt`.
- Label Studio **1.13.1** installé dans le **venv séparé** `.venv-labelstudio`
  (décision : LS embarque Django + ~150 dépendances qui entreraient en conflit avec
  l'env torch ; l'isolation garde les deux mondes stables). Démarrage vérifié le 06/07
  (le serveur répond après ~40 s au premier boot). Pour réinstaller au besoin :

```bash
cd /Users/malik/Documents/BrickOFF
python3 -m venv .venv-labelstudio
.venv-labelstudio/bin/pip install label-studio==1.13.1
```

## 1. Déposer les photos

```
data/raw/piles_malik/
├── session_01/  IMG_xxx.HEIC|jpg …
├── session_02/  …
└── holdout/     les ≥ 20 photos hors-domicile / 2e téléphone  🔒
```

HEIC, JPEG, PNG acceptés. Le dossier `holdout/` est obligatoire et reste séparé de bout
en bout (répertoires, tâches, exports, labels distincts).

## 2. Ingestion + pré-annotation (~2 min pour 100 photos)

```bash
.venv/bin/python ml/annotation/prepare_piles.py
```

Ce que ça fait : HEIC→JPEG + orientation EXIF → copie renommée vers
`data/processed/realworld_piles/{decision,holdout}/images/` → pré-annotation
`ml/runs/det_v3/best.pt` au **seuil 0.15** (convention S.0), device **cpu** par défaut
(~0,5 s/image mesuré sur M1, ne gêne pas un entraînement MPS en cours ; `--device mps`
si la machine est libre) → tâches Label Studio + config XML.

Sorties :

```
data/processed/realworld_piles/
├── decision/images/*.jpg
├── holdout/images/*.jpg
├── labelstudio/
│   ├── labelstudio_config.xml      # label "lego" + checkbox per-region "hard"
│   ├── tasks_decision.json         # tâches avec pré-annotations
│   └── tasks_holdout.json
└── manifest_ingest.json            # traçabilité source→cible, seuil, timing
```

⚠️ Mesuré sur photos de test (multi-pièces gdansk) : le seuil 0.15 produit **140-220
boxes/scène dont ~90 % sous 0.25 de score**. Si le pilote (§5) montre que le tri des
fausses boxes coûte plus cher qu'il ne rapporte :
`--score-threshold 0.25` (ou 0.35) et comparer sur les 5 mêmes scènes.

## 3. Lancer Label Studio

```bash
cd /Users/malik/Documents/BrickOFF
export LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
export LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT="$PWD/data/processed/realworld_piles"
.venv-labelstudio/bin/label-studio start
```

→ http://localhost:8080 (premier lancement : créer un compte local, n'importe quel email).
Les deux variables d'environnement sont **obligatoires** (elles servent les images
locales référencées par `/data/local-files/?d=…`) — relancer LS depuis un terminal qui
les a exportées.

## 4. Créer les projets (2 projets, jamais mélangés)

Pour **« TAS decision »** puis **« TAS holdout »** :

1. *Create Project* → nom → onglet **Labeling Setup** → *Custom template* → **coller le
   contenu** de `data/processed/realworld_piles/labelstudio/labelstudio_config.xml` → Save.
2. *Import* → glisser `tasks_decision.json` (resp. `tasks_holdout.json`) → laisser
   **« List of tasks »** → Import.
3. *Settings → Annotation* → activer **« Use predictions to prelabel tasks »** et
   sélectionner la version de modèle `det_v3_t0.15` (sinon les pré-annotations restent
   affichées en lecture seule au lieu d'être éditables).

## 5. Pilote 5 scènes CHRONOMÉTRÉ (à faire AVANT d'enchaîner — plan S.0.3)

But : calibrer le budget d'annotation réel (le plan provisionne 4-13 h).

1. Annoter **5 scènes variées** (1 petite / 2 moyennes / 2 grosses piles) en partant des
   pré-annotations. Label Studio chronomètre chaque tâche (`lead_time`, repris dans le
   manifest à la conversion §8 : `mean_lead_time_s`).
2. Extrapoler : `temps moyen × ~100 scènes` → GO si compatible avec le budget, sinon
   tester `--score-threshold 0.25` sur les 5 mêmes scènes et re-chronométrer.
3. Noter le temps dans le CHANGELOG de l'itération.

### Annoter vite

- Ouvrir la tâche : les boxes pré-annotées sont éditables (§4.3).
- **Supprimer une fausse box** : la sélectionner (clic, ou via la liste des régions dans
  le panneau latéral) → `Backspace`. Le panneau latéral est plus rapide pour purger en
  série les boxes de score faible.
- **Ajouter une pièce manquée** : touche `1` (sélectionne "lego") puis cliquer-glisser.
- **Flag hard** (pièce 10-25 % visible) : sélectionner la région → cocher `hard` dans le
  panneau sous l'image.
- **Valider la scène** : `Ctrl+Entrée` (Submit) → tâche suivante automatique.
- Zoom : molette / boutons ; `Échap` désélectionne.

## 6. Passe AVEUGLE sur 15 scènes (plan S.0.3 — angles morts de la pré-annotation)

But : mesurer ce que la pré-annotation fait rater. **À faire après** avoir annoté les
scènes correspondantes en mode corrigé (§5 étendu).

1. Générer 15 tâches SANS pré-annotations (tirage reproductible seed 0) :

```bash
.venv/bin/python - <<'EOF'
import json, random
from pathlib import Path
d = Path("data/processed/realworld_piles/labelstudio")
tasks = json.loads((d / "tasks_decision.json").read_text())
random.seed(0)
blind = [{"data": t["data"]} for t in random.sample(tasks, 15)]
(d / "tasks_decision_blind15.json").write_text(json.dumps(blind, indent=1))
print("15 tâches aveugles →", d / "tasks_decision_blind15.json")
EOF
```

2. Créer un **3e projet** « TAS blind15 » (même config XML, SANS activer le prelabel),
   importer `tasks_decision_blind15.json`, annoter les 15 scènes **sans regarder** les
   annotations corrigées.
3. Exporter (§7) vers `export_blind15.json`, convertir vers un dossier séparé :

```bash
.venv/bin/python ml/annotation/labelstudio_to_yolo.py \
    --export export_blind15.json --out-dir /tmp/tas_blind15
```

4. Comparer `n_pos` par image entre `manifest_annotations_decision.json` (corrigé) et
   `/tmp/tas_blind15/manifest_annotations_decision.json` (aveugle).
   **Critère du plan : > 5 % de pièces manquantes dans les scènes corrigées →
   annotation from scratch de tout le set** (budget honnête 8-13 h).

## 7. Export depuis Label Studio

Projet → **Export** → format **JSON** (⚠️ PAS « JSON-MIN » : il perd la structure
annotations/predictions attendue par le convertisseur) → enregistrer sous :

- `data/processed/realworld_piles/export_decision.json`
- `data/processed/realworld_piles/export_holdout.json`

## 8. Conversion → YOLO + manifest

```bash
.venv/bin/python ml/annotation/labelstudio_to_yolo.py \
    --export data/processed/realworld_piles/export_decision.json
.venv/bin/python ml/annotation/labelstudio_to_yolo.py \
    --export data/processed/realworld_piles/export_holdout.json
```

Sorties (format identique au synthétique, lu par `ml/det/dataset.py`) :

```
data/processed/realworld_piles/
├── decision/labels/<stem>.txt      # "0 cx cy w h" + lignes "# hard 0 cx cy w h"
├── holdout/labels/<stem>.txt
├── manifest_annotations_decision.json   # n_pos/n_hard par image, lead_time moyen
└── manifest_annotations_holdout.json
```

Vérifier dans la sortie : `images_without_labels` vide, pas de tâches skippées.

## 9. Baseline (étape suivante, plan S.0.4)

```bash
.venv/bin/python ml/det/eval.py --weights ml/runs/det_v1/best.pt \
    --split-dir data/processed/realworld_piles/decision --device cpu
```

⚠️ `eval.py` ignore les lignes `# hard` (elles ne comptent pas en faux négatifs) mais ne
neutralise pas encore les détections SUR les pièces hard côté mAP (elles compteraient en
faux positifs) — un éval dédié TAS sera fait au moment de la baseline. Le **holdout ne
sert jamais** aux décisions d'itération : seule la fin d'It.3 y touche.

## Points à valider mercredi

1. **HEIC réel iPhone** : la conversion a été validée sur un HEIC généré par pillow-heif
   (lecture + orientation OK) ; à confirmer sur un vrai fichier iPhone (Live Photos ne
   posent pas de problème : seul le .heic est lu, les .mov/.aae sont ignorés).
2. **Seuil 0.15** : bruyant sur les photos de test (~90 % des boxes < 0.25) — trancher
   au pilote chronométré (§5) entre 0.15 / 0.25 / 0.35.
3. **Device** : cpu par défaut (0,5 s/img) ; passer `--device mps` seulement si aucun
   entraînement ne tourne.
