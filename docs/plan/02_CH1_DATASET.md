# CH-1 — Dataset & préparation des données

> Durée : 2–3 semaines. Dépend de CH-0 (licences validées).
> C'est le chantier le plus déterminant pour la qualité finale. Ne pas le bâcler.

---

## Architecture data cible

```
data/
├── raw/                      # données brutes téléchargées (jamais modifiées)
│   ├── legobricks_hf/
│   └── segmentation_academic/
├── processed/
│   ├── detection/            # format YOLO : images/ + labels/ (txt)
│   │   ├── train/ val/ test/
│   └── classification/       # format ImageFolder : <class_id>/<img>.jpg
│       ├── train/ val/ test/
├── palettes/
│   └── lego_colors_lab.json  # palette officielle en LAB
├── manifests/
│   ├── classes_v1.json       # les 1000 classes retenues (part_id → index)
│   └── dataset_stats.json
└── scripts/                  # tous les scripts de préparation, versionnés
```

---

## Jalon 1.1 — Acquisition des données

### Tâches
1. Télécharger le dataset LEGOBricks depuis Hugging Face vers `data/raw/legobricks_hf/`
2. Télécharger le dataset segmentation académique vers `data/raw/segmentation_academic/`
3. Calculer et logger : nombre d'images, distribution par classe, formats, résolutions
4. **Vérifier l'intégrité** : images corrompues, doublons (hash MD5), labels manquants

### Livrable
- `data/manifests/dataset_stats.json` : stats complètes
- `data/scripts/01_download.py` + `data/scripts/02_integrity_check.py`

### Critères d'acceptation
- [ ] 100% des images ouvrables (PIL.verify)
- [ ] Doublons identifiés et listés
- [ ] Distribution par classe documentée (min/max/médiane d'images par classe)

### ⚠️ Point d'attention
Si une classe a < 50 images → la flagger. Ces classes seront soit exclues du scope V1, soit augmentées (jalon 1.4).

---

## Jalon 1.2 — Définition du scope classes V1

### Tâches
1. Croiser les ~1000 classes du dataset avec la fréquence d'apparition réelle des pièces dans les sets Rebrickable (snapshot CSV : table `inventory_parts`)
2. Trier les classes par : (a) fréquence dans les sets populaires, (b) volume d'images dispo
3. Sélectionner les **1000 classes définitives** : priorité aux pièces qui maximisent le nombre de sets matchables
4. Geler la liste : `classes_v1.json` avec mapping `{part_id: class_index}` — **ce fichier devient un contrat, il ne bouge plus en V1**

### Livrable
- `data/manifests/classes_v1.json`
- `docs/CLASSES_RATIONALE.md` : pourquoi ces 1000 classes, % de sets Rebrickable couverts à ≥80% de leurs pièces

### Critères d'acceptation
- [ ] 1000 classes exactement, chacune avec ≥ 50 images
- [ ] Métrique calculée : "% de sets officiels constructibles à ≥80% avec ce scope" — objectif ≥ 30% des sets < 500 pièces

---

## Jalon 1.3 — Conversion aux formats d'entraînement

### Détection (YOLO format)
1. Convertir les annotations du dataset segmentation en bounding boxes YOLO (un `.txt` par image : `class x_center y_center w h`, normalisé 0–1)
2. **Pour la détection, une seule classe suffit : "lego_piece"** (la classification fine est faite par le stage 2). Cela simplifie énormément l'entraînement détection et améliore le rappel.
3. Split : 80% train / 10% val / 10% test — split par IMAGE SOURCE (pas par crop) pour éviter la fuite de données

### Classification (ImageFolder format)
1. Cropper chaque pièce annotée → image individuelle
2. Ranger par classe : `processed/classification/train/<part_id>/img_001.jpg`
3. Resize : 224×224 (entrée MobileNetV3 standard)
4. Même split 80/10/10, stratifié par classe

### Livrable
- `data/processed/` peuplé
- `data/scripts/03_convert_detection.py`, `04_convert_classification.py`
- `data/manifests/splits.json` : listes exactes des fichiers par split (reproductibilité)

### Critères d'acceptation
- [ ] Validation format YOLO : 20 images tirées au hasard, bboxes affichées, vérifiées visuellement correctes
- [ ] Aucune image présente dans 2 splits
- [ ] Chaque classe présente dans les 3 splits

---

## Jalon 1.4 — Augmentation & équilibrage

### Tâches
1. Définir le pipeline d'augmentation (albumentations) :
   - **Toujours** : flips, rotations 90°, variations luminosité/contraste légères
   - **Détection uniquement** : mosaic, scale jitter
   - **INTERDIT pour la classification** : hue shift fort (détruirait l'info couleur... sauf que le classifier ne juge PAS la couleur — voir note) 
   
   **Note importante** : le classifier identifie la FORME (part_id), la couleur est traitée par le pipeline LAB séparé. Donc : hue shift agressif AUTORISÉ et même RECOMMANDÉ pour le classifier → force le modèle à ignorer la couleur et généraliser sur la forme.
2. Sur-échantillonner les classes < 200 images jusqu'à ~200 effectifs via augmentation
3. Générer un set de validation NON augmenté (toujours évaluer sur du réel)

### Livrable
- `data/scripts/05_augmentation_config.py` : config albumentations versionnée
- Stats post-augmentation dans `dataset_stats.json`

### Critères d'acceptation
- [ ] Ratio max/min d'images par classe ≤ 5:1 après équilibrage
- [ ] Val/test 100% non augmentés

---

## Jalon 1.5 — Palette couleur officielle LEGO

### Tâches
1. Extraire la table `colors.csv` du snapshot Rebrickable (id, name, rgb)
2. Convertir chaque couleur RGB → LAB (D65, via colormath ou skimage)
3. Filtrer : exclure les couleurs "transparent" dans une liste séparée (traitement spécifique : la transparence ne se détecte pas par couleur dominante simple — hors scope V1, flaggées "non identifiable")
4. Produire `lego_colors_lab.json` :
```json
{
  "colors": [
    {"id": 4, "name": "Red", "rgb": "C91A09", "lab": [45.2, 67.1, 53.8], "transparent": false}
  ],
  "version": "rebrickable-snapshot-YYYY-MM-DD"
}
```

### Livrable
- `data/palettes/lego_colors_lab.json`
- `data/scripts/06_build_palette.py`

### Critères d'acceptation
- [ ] Toutes les couleurs opaques du snapshot présentes
- [ ] Valeurs LAB vérifiées sur 5 couleurs par calcul indépendant (sanity check)

---

## Jalon 1.6 — Set de test "réalité terrain"

> Crucial : les datasets publics ≠ conditions réelles utilisateur.

### Tâches
1. Photographier soi-même **200+ photos** de pièces LEGO réelles étalées :
   - 3 éclairages : lumière du jour, LED intérieure, lampe chaude
   - 3 fonds : table bois, sol clair, tapis
   - Smartphones différents si possible
2. Annoter manuellement (outil : Label Studio ou CVAT, les deux open source) : bbox + part_id + color_id
3. Ce set ne sert JAMAIS à l'entraînement → uniquement évaluation finale

### Livrable
- `data/processed/realworld_test/` : images + annotations
- `docs/REALWORLD_PROTOCOL.md` : protocole de prise de vue documenté

### Critères d'acceptation
- [ ] ≥ 200 photos, ≥ 2000 pièces annotées au total
- [ ] Les 3 conditions d'éclairage représentées à parts comparables
- [ ] Double vérification des annotations (2 passes ou 2 annotateurs)

---

## Sortie de chantier CH-1

- Tous les jalons ✅
- `CHANGELOG_CH1.md` rédigé
- Handoff vers CH-2 : chemins des datasets processed + `classes_v1.json` + stats
