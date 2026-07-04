# CHANGELOG CH-1 — Dataset & préparation des données

> Journal du chantier (exigence Master Plan §3.6). Amendement structurant : le jalon 1.7
> (corpus réel d'entraînement) a été ajouté suite à la revue adversaire CH-0 (constat 3).

## 2026-07-04 — Ouverture, jalon 1.1 (acquisition) ✅ CLOS le jour même

### Jalon 1.1 — Acquisition

| Source | Statut | Preuve |
|---|---|---|
| gdansk_det (DOI 10.34808/anq4-rn44, CC BY 4.0) | ✅ acquis + intègre | 5 841 images (= 2 933 réelles + 2 908 rendus du papier, compte exact), 0 corrompue, 0 doublon — `data/manifests/dataset_stats.json` |
| gdansk_cls (DOI 10.34808/rcza-jy08, CC BY 4.0) | ✅ acquis + intègre | 620 078 images (= 52 597 photos + 567 481 rendus du papier, compte exact), 0 corrompue, 0 doublon, 448 classes (1 seule < 50 img) |
| legobricks_hf (Apache-2.0, 400k rendus) | ✅ acquis + intègre | 400 000 images / 1 000 classes exactement, échantillon de 2 550 décodé sans échec |

Scripts livrés : `data/scripts/01_download.py` (idempotent, provenance DOI+licence+sha256 tracée),
`data/scripts/02_integrity_check.py` (PIL.verify, doublons MD5, distribution par classe, exit 1 si corruption).

### Écarts au plan

- Le "dataset segmentation académique" supposé par le plan est en réalité un dataset de **détection**
  (bbox VOC) — c'est exactement ce dont on a besoin, terminologie corrigée (cf. `docs/research/DATASETS_SURVEY.md`).
- Ajout de gdansk_cls (447 classes réelles) non prévu au plan initial : c'est la réponse au constat
  adversaire n°3 (besoin de photos réelles pour le classifieur).
- Incident mineur : URL gdansk_cls initialement extrapolée au lieu d'être résolue via DOI — détectée
  par le garde-fou d'intégrité zip, corrigée (leçon : toujours résoudre les DOI, jamais deviner un slug).

## 2026-07-05 — Jalon 1.3 (partie DET) ✅

- Conversion gdansk_det VOC→YOLO mono-classe : 5 096 train / 566 val / 179 test, 7 688 bboxes.
- Critères prouvés : aller-retour numérique ≤ 1 px sur 100 % des boxes (échec bloquant sinon),
  inspection visuelle d'un échantillon reconverti (`ml/validation_yolo_sample.png`), aucune image
  dans deux splits (répartition par fichier), chaque split non vide.
- Recommandations d'audit appliquées : split -test d'origine préservé, 121 images à pièce au bord
  tracées au manifest (`data/manifests/splits_detection.json`), conservées à l'entraînement.
- La partie CLS du jalon 1.3 (ImageFolder unifié + mapping classes) attend le jalon 1.2 (scope),
  lui-même en attente des CSV Rebrickable (téléchargement manuel PO).

### Prochaines étapes (ordre)

1. Jalon 2.1 — baseline DET sur M1 (time-box 1 semaine, configs par défaut)
2. Pipeline de scènes synthétiques multi-pièces (Blender installé, ldr_tools_blender MIT en salle blanche)
3. Jalon 1.2 — scope classes (préalable : CSV Rebrickable en téléchargement MANUEL, cf. legal/)

Note d'audit : la fiche gdansk_cls annonce 447 classes, le papier 431, le disque en contient 448 —
écart mineur à élucider au jalon 1.2 (probable : dossiers de variantes/molds fusionnés différemment).
