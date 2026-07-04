# DATASETS_SURVEY.md — Recensement des datasets LEGO exploitables (remédiation R1 + revue HF)

> **Date de vérification : 2026-07-04.** Réponse aux constats CRITIQUES n°1 et n°3 de
> `legal/CHALLENGE_CH0_REVUE_ADVERSAIRE.md`. Toutes les licences ci-dessous ont été vérifiées ce
> jour sur sources primaires. **Note de méthode** : les fiches Most Wiedzy (mostwiedzy.pl) et les
> pages Kaggle/Roboflow sont derrière des protections anti-bot (Anubis, reCAPTCHA, Cloudflare) qui
> bloquent la consultation automatisée directe ; les licences ont donc été vérifiées sur les
> **captures Wayback Machine** de ces pages (JSON-LD/HTML d'origine, dates de capture citées).
> Avant tout téléchargement effectif (CH-1 jalon 1.1), re-vérifier la fiche live à la main —
> coût : 10 minutes.

---

## Tableau récapitulatif

| Dataset | Source / URL | Type | Réel / synth. | Volume | Licence vérifiée (citation + date) | Commercial OK ? | Verdict pour BrickOFF |
|---|---|---|---|---|---|---|---|
| **Tagged images with LEGO bricks** (Boiński, Gdańsk Univ. of Technology) | Most Wiedzy, DOI [10.34808/anq4-rn44](https://doi.org/10.34808/anq4-rn44) | **DET** (bbox PASCAL VOC, annotées à la main via labelImg, **sans part ID**) | **2 933 photos réelles** (1–32 pièces/photo, fonds et éclairages variés : boîte, tapis, clavier…) + 2 908 rendus | **CC BY 4.0** — fiche Most Wiedzy : « License: CC BY Attribution », lien vers creativecommons.org/licenses/by/4.0 (capture Wayback du 2025-03-18, vérifiée 2026-07-04) | **OUI** (attribution) | ⭐ **C'est LE dataset R1.** Détection mono-classe exactement dans notre format cible. Volume faible (~6k images) → complément, pas socle |
| **Tagged images with LEGO bricks part 2** (Gdańsk) | Most Wiedzy, DOI [10.34808/7kk9-tn08](https://doi.org/10.34808/7kk9-tn08) | DET (bbox **auto-générées par YOLOv5, non nettoyées** — le papier le dit explicitement) + part ID par dossier | **15 608 photos réelles**, fond blanc mat (bureau) | **CC BY 4.0** — même mention sur fiche Most Wiedzy (capture Wayback 2025, vérifiée 2026-07-04) | **OUI** (attribution) | Utile en pré-entraînement DET après nettoyage (annotations bruitées + biais fond blanc). Audit Phase 1 (doc 14) obligatoire |
| **Images of LEGO bricks** (Gdańsk) | Most Wiedzy, DOI [10.34808/arsb-4268](https://doi.org/10.34808/arsb-4268) | CLS (crops 1 pièce/image, label = part ID officiel par dossier, catégories Rebrickable) | **77 535 photos réelles** (crops extraits de « part 2 », vérifiés manuellement) | **CC BY 4.0** — fiche Most Wiedzy (capture Wayback 2025, vérifiée 2026-07-04) | **OUI** (attribution) | ⭐ La plus grosse source de **photos réelles labellisées part ID**. Biais : fond blanc, pièces de la collection d'un seul auteur |
| **LEGO bricks for training classification network** (Gdańsk) | Most Wiedzy, DOI [10.34808/rcza-jy08](https://doi.org/10.34808/rcza-jy08) | CLS | **52 597 photos réelles + 567 481 rendus**, **447 classes** (fiche dataset ; le papier dit 431), fond blanc | **CC BY 4.0** — fiche Most Wiedzy (capture Wayback 2025, vérifiée 2026-07-04) | **OUI** (attribution) | Version curatée du précédent (photos triées + rendus mélangés). Bon set de fine-tuning réel du classifieur — mais 447 classes vs nos 1000 |
| **LDRAW-based renders… conveyor belt** (Gdańsk) | Most Wiedzy, DOI [10.34808/xfgk-6f77](https://doi.org/10.34808/xfgk-6f77) | CLS | Synthétique | **935 967 rendus** (LDraw + Blender/ImportLDraw) | **CC BY 4.0** — fiche Most Wiedzy (capture Wayback 2025, vérifiée 2026-07-04) | **OUI** (attribution, + attribution LDraw déjà prévue) | Redondant avec pvrancx + notre pipeline §2.1 ; à garder en réserve |
| **pvrancx/legobricks** | [Hugging Face](https://huggingface.co/datasets/pvrancx/legobricks) | CLS | Synthétique (rendus LDraw) | 400 000 images, **1 000 classes** (part IDs), 400 img/classe | **Apache-2.0** (champ `license` de la card, re-vérifié 2026-07-04 via l'API HF ; cf. `ML_LICENSES.md` §2 et ambiguïté A2) | **OUI** | ⭐ Socle classification déjà retenu au plan. 100 % synthétique (constat adversaire n°3) |
| **B200C LEGO Classification Dataset** (R. Pickell) | [Kaggle](https://www.kaggle.com/datasets/ronanpickell/b200c-lego-classification-dataset) | CLS | Synthétique (rendus) | 800 000 rendus, 200 classes | **CC BY-SA 4.0** — JSON-LD de la page Kaggle : `"license":{"name":"CC BY-SA 4.0"}` (capture Wayback 2025-09-16, vérifiée 2026-07-04) | ⚠️ Commercial permis **mais clause ShareAlike** : en lecture conservatrice, des poids entraînés dessus pourraient devoir être partagés sous BY-SA → contamination inacceptable pour une app fermée | À ÉVITER pour l'entraînement. Utilisable au plus en benchmark interne |
| **B200 LEGO Detection Dataset** (R. Pickell) | [Kaggle](https://www.kaggle.com/datasets/ronanpickell/b100-lego-detection-dataset) | DET (bbox) | Synthétique (rendus) | ~2 000 rendus, 200 classes | **CC BY-SA 4.0** — JSON-LD de la page (capture Wayback 2026-01-14, vérifiée 2026-07-04) | ⚠️ Même problème ShareAlike | À ÉVITER (et notre pipeline §2.1 produira mieux, sans SA) |
| **Images of LEGO Bricks** (J. Hazelzet) | [Kaggle](https://www.kaggle.com/datasets/joosthazelzet/lego-brick-images) | CLS | Synthétique (rendus Blender) | 40 000 images, 50 classes | **GPL 2** — JSON-LD de la page : `"license":{"name":"GPL 2"}` (capture Wayback 2025-12-07, vérifiée 2026-07-04) | **NON** en pratique (copyleft sur données : incompatible avec notre chaîne fermée, statut juridique confus) | Inutilisable. De toute façon redondant et petit |
| **Lego Brick Sorting – Image Recognition** (pacogarciam3) | [Kaggle](https://www.kaggle.com/datasets/pacogarciam3/lego-brick-sorting-image-recognition) | CLS | **Réel** | 4 580 photos, 20 classes (2 fonds, 3 caméras) | **CC BY-SA 3.0** — JSON-LD de la page (capture Wayback 2023-10-18, vérifiée 2026-07-04) | ⚠️ ShareAlike | À ÉVITER pour l'entraînement ; 20 classes seulement, intérêt marginal |
| **Lego Brick Recognition1 / 2** (Roboflow Universe) | [universe.roboflow.com/lego-brick-recognition/lego-brick-recognition1](https://universe.roboflow.com/lego-brick-recognition/lego-brick-recognition1) | DET | Réel (photos, à auditer) | 3 033 + 2 808 images | **CC BY 4.0** — page projet : lien licence creativecommons.org/licenses/by/4.0 (capture Wayback 2025-08-08, vérifiée 2026-07-04) | **OUI** (attribution) — ⚠️ provenance des images non documentée (contributeur anonyme) : risque résiduel sur la chaîne des droits | Complément DET possible après audit visuel + vérification live de la licence. Ne pas en faire une dépendance |
| **Autres Roboflow Universe** (LegoDataset 3 302 img ; lego-b0vt2 287 img ; LEGO EMMET B200 2 000 rendus [dérivé de B200C → hérite de BY-SA] ; Lego Blocks 47 img ; AutoDash 33 img…) | universe.roboflow.com | DET | Mixte | Petits (33–3 302) | **Licence non déterminée = inutilisable** (pages bloquées par Cloudflare le 2026-07-04, pas de capture Wayback exploitable par projet) | Non déterminable | Ignorer, sauf vérification manuelle au cas par cas si besoin |
| **Armaggheddon/lego_brick_captions** | [Hugging Face](https://huggingface.co/datasets/Armaggheddon/lego_brick_captions) | CLS/captioning | Images catalogue | 80 868 images + captions Gemini | Card : « MIT » — **mais la card dit que les images sont téléchargées depuis les `img_url` de `inventory_parts.csv` de Rebrickable** (vérifié 2026-07-04 sur le README). Le relicenciement MIT n'est pas valable, et la clause Rebrickable « No Rebrickable content may be used in the training of AI models » s'applique frontalement | **NON** | **INUTILISABLE** — exactement le cas visé par le constat adversaire n°2. Ne pas toucher |
| **TontonTremblay/RTMV_BRICKS** (NVIDIA RTMV, sous-ensemble bricks) | [Hugging Face](https://huggingface.co/datasets/TontonTremblay/RTMV_BRICKS) | NVS (multi-vues ray-tracées) | Synthétique | ~190 Go (tar multi-parts) | **Licence non déterminée = inutilisable** — aucune licence sur la card HF ni trouvée sur la page projet (vérifié 2026-07-04) | Non déterminable | Ignorer (conçu pour la synthèse de vues, pas pour DET/CLS de toute façon) |
| **LegoSorter** (github.com/LegoSorter) | GitHub | modèles + code | — | Pas de dataset publié ; releases de poids `detection_models.zip` / `classification_models.zip` | **Aucun fichier LICENSE sur aucun des 7 repos** (vérifié 2026-07-04 via l'API GitHub) → tous droits réservés par défaut | **NON** | Inutilisable (code et poids). Les données publiées de cette ligne de recherche polonaise sont précisément les datasets Gdańsk ci-dessus |
| **Daniel West (Universal LEGO Sorting Machine)** | [Medium 2019](https://medium.com/towards-data-science/how-i-created-over-100-000-labeled-lego-training-images-ec74191bb4ef) | CLS | Synthétique | >100 000 images décrites | **Jamais publié** — aucun lien de téléchargement public trouvé lors de cette revue | — | N'existe pas en tant que dataset téléchargeable |
| **RebrickNet / Brickognize** (services) | rebrickable.com / brickognize.com | — | Réel | Non téléchargeable | Données non distribuées ; Brickognize gelé par ToS (cf. `ML_LICENSES.md` §6), contenu Rebrickable sous clause anti-IA | **NON** | Pas des datasets. Pour mémoire |

Référence académique centrale : Boiński, T. M., « Photos and rendered images of LEGO bricks »,
*Scientific Data* 10, 811 (2023), DOI [10.1038/s41597-023-02682-2](https://doi.org/10.1038/s41597-023-02682-2)
(article CC BY 4.0, consulté via [PMC10657460](https://pmc.ncbi.nlm.nih.gov/articles/PMC10657460/) le 2026-07-04).
C'est ce papier qui décrit les 5 datasets Gdańsk et leur généalogie.

⚠️ **Double comptage à connaître** (généalogie décrite dans le papier) : *Images of LEGO bricks*
(77 535 crops) est **extrait** des photos de *part 2* (15 608), et les 52 597 photos du dataset
« classification network » sont **triées depuis** *Images of LEGO bricks*. Les « ~155 000 photos »
de l'abstract comptent donc plusieurs fois les mêmes prises de vue. Photos sources réellement
indépendantes : **≈ 18 500** (2 933 scènes variées + 15 608 fond blanc).

---

## Réponse R1 — le « dataset segmentation académique » du plan CH-1 existe-t-il ?

**Oui, à un détail de vocabulaire près : c'est un dataset de _détection_ (bboxes), pas de
segmentation.** Il s'agit de **« Tagged images with LEGO bricks »** (Gdańsk University of
Technology, Most Wiedzy, DOI 10.34808/anq4-rn44, **CC BY 4.0**) : 2 933 photos réelles contenant
de 1 à 32 pièces sur fonds domestiques variés + 2 908 rendus, annotés à la main en PASCAL VOC,
**sans part ID** — ce qui correspond exactement à notre détection mono-classe « lego_piece »
(jalon 1.3). Son extension *part 2* (15 608 photos, bboxes auto-générées non nettoyées, CC BY 4.0)
peut s'y ajouter après nettoyage.

**Mais le constat adversaire n°1 reste matériellement fondé sur le volume** : ~2 900 photos
réelles de scènes annotées à la main, c'est un ordre de grandeur en dessous de ce qu'exige un
détecteur robuste. Conséquences à propager dans le plan :

1. **CH-1 jalon 1.1 / `ML_LICENSES.md`** : remplacer la mention vague « dataset segmentation
   académique » par la référence exacte ci-dessus (nom, DOI, CC BY 4.0, attribution
   « Boiński, Gdańsk University of Technology » à ajouter aux mentions légales) et corriger
   « segmentation » → « détection ».
2. **La génération synthétique de scènes (doc 14 §2.1) devient la voie nominale pour le VOLUME
   d'entraînement DET** — non plus un plan B. Le dataset Gdańsk sert de : (a) set réel de
   fine-tuning/mélange (recette 70/30 du doc 14), (b) sanity check indépendant, (c) le seul
   ancrage réel non-maison disponible. Le circulaire pointé par l'adversaire (synthétique évalué
   sur synthétique) est cassé par le realworld set maison (jalon 1.6), qui reste le seul juge.
3. Aucun dataset public de **segmentation** de tas de pièces n'a été trouvé lors de cette revue
   (le papier Brickinspector, MDPI Sensors 2023, travaille en segmentation synthétique mais aucun
   dataset public associé n'a été identifié). Si la segmentation devient nécessaire, elle sortira
   de notre pipeline Blender (masques gratuits par construction).

---

## Images réelles annotées — ce qui existe, et l'écart restant

### Ce qui existe réellement (licence compatible, vérifiée)

Tout le stock réel exploitable vient de Gdańsk (CC BY 4.0), plus un appoint Roboflow :

| Usage | Source | Volume réel utilisable | Limites |
|---|---|---|---|
| DET scènes réalistes, bbox propres | Tagged images | **2 933 photos** (multi-pièces, fonds variés) | Volume faible |
| DET fond blanc, bbox bruitées | Tagged part 2 | 15 608 photos | Annotations YOLOv5 non nettoyées, biais studio fort |
| DET appoint | Roboflow Lego Brick Recognition1/2 | ~5 800 images | Provenance non documentée, audit obligatoire |
| CLS par part ID | Images of LEGO bricks (et sa version curatée 52 597) | **77 535 crops réels** | **447 classes sur nos 1000** (~45 % du scope), fond blanc, collection d'un seul auteur, couleurs non contrôlées |

### L'écart à combler par nos propres photos (constat n°3 : confirmé, partiellement atténué)

- **Classification** : ~553 de nos 1000 classes n'ont **aucune photo réelle publique**. Pour les
  447 couvertes, le critère CH-1 « ≥ 50 images/classe » est probablement atteint en volume brut,
  mais en conditions studio uniquement. Le classifieur reste donc entraîné à ~90 % sur du
  synthétique — le critère de bascule du doc 14 (« > 90 % studio → voie synthétique ») demeure
  satisfait par construction.
- **Détection** : ~2 900 vraies scènes « type utilisateur » au total. Rien ne ressemble à un tas
  dense sur tapis en éclairage chaud.
- **Conclusion opérationnelle** : la campagne photos maison doit être **élargie au-delà du seul
  test set** du jalon 1.6 (200 photos, interdites d'entraînement). Amendement recommandé pour
  CH-1/doc 14 : une seconde campagne « photos maison d'ENTRAÎNEMENT » (cible indicative
  1 000–2 000 photos multi-pièces, pré-annotées par notre propre détecteur synthétique puis
  corrigées — l'auto-annotation §2.2 sans Brickognize), distincte et sans fuite vers le test set.

---

## Top-3 pour BrickOFF (synthèse)

1. **Tagged images with LEGO bricks** (Gdańsk, CC BY 4.0) — répond à R1 : la seule source publique
   de détection réelle annotée à la main. À intégrer au jalon 1.1.
2. **Images of LEGO bricks / LEGO bricks for training classification network** (Gdańsk, CC BY 4.0)
   — 52–77k photos réelles labellisées part ID : le levier anti-« 100 % synthétique » du
   classifieur pour 447 de nos classes (fine-tuning ou mélange 70/30).
3. **pvrancx/legobricks** (HF, Apache-2.0) — confirmé comme socle classification 1000 classes
   (déjà au plan, licence re-vérifiée ce jour).

**Attributions à ajouter** à l'écran mentions légales si ces datasets sont utilisés : « Boiński,
Gdańsk University of Technology — LEGO bricks datasets (CC BY 4.0) » (+ LDraw et pvrancx déjà
prévus dans `ML_LICENSES.md`). Écarter tout ce qui est CC BY-SA (B200/B200C, pacogarciam3),
GPL (Hazelzet), sans licence (Roboflow non vérifiés, RTMV_BRICKS, LegoSorter) et tout contenu
dérivé de Rebrickable (lego_brick_captions).

---

*Sources primaires consultées le 2026-07-04 : API Hugging Face (`/api/datasets?search=lego|brick`,
cards `pvrancx/legobricks`, `Armaggheddon/lego_brick_captions`, `TontonTremblay/RTMV_BRICKS`) ;
papier Scientific Data 10:811 via PMC ; fiches Most Wiedzy des 5 DOI 10.34808/* (via captures
Wayback 2025, anti-bot Anubis sur le live) ; JSON-LD des pages Kaggle (captures Wayback
2023-10-18 → 2026-01-14) ; page Roboflow lego-brick-recognition1 (capture Wayback 2025-08-08) ;
API GitHub org LegoSorter ; liste [awesome-lego-machine-learning](https://github.com/360er0/awesome-lego-machine-learning).*
