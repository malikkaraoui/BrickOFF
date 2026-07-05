# SYNTH_DESIGN_INPUTS — État de l'art pour le pipeline de scènes synthétiques LEGO

> Date : 2026-07-05. Prépare la conception du pipeline (doc 14 §2.1, it.3 de EVAL_DET_V1).
> **Règle salle blanche** : les repos SANS licence (`LegoBrickClassification`, `brick-renderer`) et GPL
> (`ImportLDraw`) sont étudiés pour leurs IDÉES uniquement — aucun code n'en sera copié.
> `Multi-object-detection-lego` (MIT) et `ldr_tools_blender` (MIT, notre importeur installé) sont réutilisables.
> Contexte cible : **tas de pièces avec occlusions, photos smartphone en intérieur domestique** —
> le corpus réel (audit) est à 82 % mono-pièce et sans occlusion, le test det_v1 plafonne faute de scènes "tas".

---

## 1. Synthèse des approches existantes

### 1.1 brick-renderer (spencerhhubert, SANS licence — idées seulement)
Pipeline `blender -b -P render.py` pour une machine de tri. Ce qu'il fait :
- **Placement par physique** : chaque pièce est spawnée en l'air à position XY aléatoire (z=5), rotation
  euler uniforme sur les 3 axes, déclarée *rigid body*, puis la simulation est jouée 75 frames → les pièces
  **retombent et se stabilisent naturellement** sur le sol. Des murs invisibles (*passive rigid bodies*
  cachés au rendu) empêchent les pièces de sortir du cadre. 5 pièces par scène.
- **Fond** : une photo réelle importée comme plan (*image-to-plane*), **mise à l'échelle physiquement**
  (px/mm connu) pour que la taille relative pièce/fond soit correcte — idée précieuse contre le biais d'échelle.
- **Couleurs** : parsées depuis `LDConfig.ldr` officiel, en **excluant les finitions exotiques**
  (Chrome, Trans, Glitter, Glow, Metallic, Speckle, Rubber…) — liste d'exclusion directement réutilisable.
- **Annotations** : masques par pièce obtenus en re-rendant la scène N fois avec une seule pièce visible,
  puis empilés en un masque .npy (les chevauchements sont résolus arbitrairement).
- **Éclairage/caméra** : 1 point light énergie 1000 colocalisée caméra, monde noir, focale 35 mm, 50 samples Cycles.

**Bien** : la physique (poses de repos réalistes), l'échelle physique du fond, le filtre couleurs LDConfig.
**Manque pour nous** : pas de tas (5 pièces éparses), pas d'HDRI ni d'éclairage varié, matière = défauts
ImportLDraw sans imperfections, aucun post-process capteur, masques par re-rendu = coût ×(N+1) par scène
(en Blender moderne on utilisera plutôt une passe *object index / cryptomatte* en un seul rendu).

### 1.2 Multi-object-detection-lego (MIT)
Scène .blend + script (`blender/lego_rendering_scripts/blender_script.py`), YOLOv5/SSD entraînés sur le
synthétique et démontrés sur webcam réelle — preuve de concept syn→réel encourageante. Ce qu'il fait :
- **Composition** : 2–5 pièces par image (10 meshes de briques faits main), position XY uniforme ±1,5,
  rotation euler aléatoire 0–180° par axe, **pas de physique** (z fixé → pièces posées/flottantes).
- **Fonds** : 5 textures maison (carpet, marble, tiles, wood, wool_rug) activées aléatoirement +
  **images "fond seul" sans pièce** (négatifs purs, recommandé pour les détecteurs).
- **Caméra** : `camera_to_view_selected` (auto-cadrage sur les pièces) — cadre toujours bien rempli.
- **Bboxes VOC par projection des sommets du mesh dans l'espace caméra** (`camera_view_bounds_2d`),
  clampées à l'image — la méthode standard, réutilisable (MIT).
- **Équilibrage** : table de comptage d'apparition de chaque pièce pour vérifier l'uniformité du tirage.
- **Ops** : rendu par batchs de ~400 (fuites mémoire Blender) — contrainte réelle à prévoir (relancer le process).

**Bien** : bboxes par projection, négatifs purs, comptage d'équilibrage, honnêteté sur les batchs mémoire.
**Manque** : 6 couleurs seulement, 300×300 px, pas d'occlusions (la bbox projette TOUS les sommets, y
compris cachés — sur un tas ça produirait des boîtes de pièces invisibles : il faudra un **seuil de
visibilité par masque**), pas d'HDRI, matériaux diffuse naïfs, pas de physique.

### 1.3 LegoBrickClassification (SANS licence — idées seulement)
Rendu mono-pièce pour la classification (ancêtre du problème Brickognize). Ce qu'il fait :
- **Caméra sur hémisphère supérieur** : positions échantillonnées sur une sphère (theta 0–360°, phi 0–90°),
  caméra contrainte *TRACK_TO* la pièce ; lumière ponctuelle tirée sur la même sphère.
- **Augmentations config JSON** : 38 couleurs LEGO officielles (hex), rotation x ∈ {0, 90, 180, 270},
  zoom 0,7–1,5, **normalisation de taille (plus grande dimension = constante)** — pertinent pour la
  classif de crops, mais à NE PAS reproduire en détection (détruit l'info d'échelle réelle).
- **Fonds** : images IndoorCVPR09 vs bruit procédural.
- **Analyse de similarité SSIM entre thumbnails** pour identifier pièces identiques / de forme identique →
  CSV `identical` / `shape_identical`. **Directement pertinent pour notre doc 14 §2.3** (fusion des molds
  confusables) : générer les thumbnails standardisés de nos 1000 classes et regrouper avant d'entraîner.
- **Leçon principale (assumée par les auteurs)** : résultats "non satisfaisants" sur leur test réel —
  domain gap trop grand, causes listées : taille, éclairage, résolution, fond, angle de vue. Ils rendaient
  en Blender Internal 2.79 (non-PBR, aucune imperfection) : c'est exactement le piège "plastique parfait".

### 1.4 Outils d'import : ImportLDraw (GPL — idées) vs ldr_tools_blender (MIT — notre outil, installé)
- **ImportLDraw** propose `useLogoStuds` (logo LEGO sur les tenons — micro-détail qui aide le réalisme),
  gaps entre pièces, bevels d'arêtes, et un système complet de matériaux par finition LDraw (voir §2).
- **ldr_tools_blender** (MIT, déjà installé chez nous) importe plus vite, applique des matériaux Principled
  BSDF modernes avec **rugosité procédurale, SSS et normales bruitées par défaut** (§2), et corrige les
  couleurs LDraw par des tables plus fidèles (`rgb_ldr_tools_by_code`, `rgb_peeron_by_code`). C'est notre base.

### 1.5 Littérature directement applicable (bonus)
- **Brickognize** (Sensors 2023 — on étudie le PAPIER, le gel licence ne concerne que le service) :
  BlenderProc, pièce(s) échantillonnées au-dessus du sol puis **posées par gravité**, salle carrée avec
  plafond émissif + point light aléatoire (position, intensité, couleur), **fonds = textures PBR variées**
  (nature, domestique, industriel), **20 caméras par scène sur une coquille sphérique** (amortit le coût de
  la simulation physique), 1 000 scènes × 20 = 20 000 images 512². Résultats : synthétique seul 83,3 AP50 ;
  **+ fine-tuning 20 photos réelles → 91,3 (test non contrôlé) / 98,7 (contrôlé) ; saturation au-delà de
  ~20 shots**. Source : https://pmc.ncbi.nlm.nih.gov/articles/PMC9967933/ (doi:10.3390/s23041898).
- **Dataset gdansk** (notre corpus) : Boiński et al., *Photos and rendered images of LEGO bricks*,
  Scientific Data 2023, https://www.nature.com/articles/s41597-023-02682-2 — photos sur bureau blanc/papier
  mat, bboxes générées par YOLOv5 (explique les boîtes lâches vues à l'audit) ; leurs rendus sont studio.
- **Tremblay et al. 2018** (domain randomization, détection) : https://arxiv.org/abs/1804.06516 —
  randomisation volontairement NON réaliste (couleurs/textures/lumières extrêmes) + **fine-tuning réel >
  réel seul** ; les "distracteurs" (objets parasites) dans les scènes améliorent la robustesse.

**Ce qu'aucun des repos ne couvre et que NOUS devons apporter** : (a) les **tas** (empilements avec
occlusions mutuelles et bboxes filtrées par visibilité), (b) le **photoréalisme domestique** (HDRI chauds,
fonds PBR, imperfections matière), (c) le **post-process capteur smartphone**, (d) la distribution de
fréquence réelle des pièces/couleurs (notre `rebrickable-sqlite` local le permet).

---

## 2. Réalisme matière : le plastique ABS sans le piège du "plastique parfait"

Constat partagé (LegoBrickClassification §1.3, audit des rendus gdansk) : un ABS idéal — couleur unie,
rugosité constante, aucune poussière — crée à lui seul un domain gap. Les pièces réelles ont des rayures,
traces de doigts, poussière, micro-ondulations de moulage qui cassent les reflets.

### 2.1 Paramètres observés dans les outils étudiés

**ldr_tools_blender (MIT — défauts appliqués par notre importeur)**, `ldr_tools_blender/material.py` :
| Paramètre | Valeur | Note |
|---|---|---|
| Roughness ABS opaque | **bruit procédural (Noise Scale 4, Detail 2) remappé sur [0,075 ; 0,2]** | commentaire "smudges" : simule traces de doigts/graisse |
| Subsurface | Weight 1,0, méthode Burley, Radius = couleur de base, Scale = 2,5 × échelle objet | le SSS est essentiel pour les couleurs claires/vives |
| IOR | 1,5 (transparent : 1,55, transmission 1, roughness [0,01 ; 0,15]) | |
| Normales | bruit très basse fréquence (Scale 0,01) + Bump + **Bevel des arêtes** — "les faces ne sont jamais parfaitement planes", casse les reflets spéculaires | |
| Faces obliques (slopes) | normales granuleuses dédiées (Noise Scale 2,5, Bump Strength 0,5) | les pentes LEGO sont réellement grenues |
| Finitions | Chrome roughness [0,075;0,1], Metal [0,15;0,3], Pearlescent metallic 0,35 roughness [0,3;0,5], Speckle, Rubber | |

**ImportLDraw (GPL — chiffres notés comme référence, pas de code)** : ABS = Principled avec
subsurface ∝ 5×échelle, subsurface radius 0,05, metallic 0, **roughness 0,1**, IOR 1,45 ; transparents
roughness 0,05, IOR 1,585, transmission 1 ; rubber roughness 0,4–0,5 + bump Voronoï ; bump procédural
générique (distance 0,02–0,08).

**Communauté Blender/LEGO** (recherche web) :
- *ABS Plastic Materials 3.0* (addon commercial, superhivemarket.com/products/abs-plastic-materials/docs) :
  curseurs dédiés **fingerprints & dust**, bruit de rugosité, "waviness" (displacement d'ondulation de
  moulage), SSS réglable — la liste de ses curseurs EST la check-list des imperfections à implémenter.
- *BlendBricks v2* (blenderartists.org/t/…/1454429) : fingerprints, **scratches**, graisse, variations
  d'IOR et de rugosité, SSS, *dirt generator* (usure d'arêtes).
- Stefan Müller, *Exploring LEGO Material* (stefanmuller.com/exploring-lego-material-part-2/) : glossy
  roughness ≈ 0,05 + **Fresnel IOR 1,46–1,60** ; fingerprints = 2e lobe de réflexion pondéré par une
  texture d'empreintes.

### 2.2 Recette retenue pour le pipeline (paramètres de départ, à randomiser §3)
1. Base = matériaux `ldr_tools_blender` (déjà bons) ; vérifier que le **Bevel** et le bruit de normales
   restent actifs à notre échelle de scène.
2. Ajouter par-dessus, par pièce (shader unique paramétré) :
   - **Rayures** : texture procédurale anisotrope (scratches) mélangée dans la roughness, intensité 0–0,15 ;
   - **Empreintes/graisse** : élargir la plage de roughness de [0,075;0,2] à **[0,05 ; 0,35]** tirée par pièce ;
   - **Poussière** : couche diffuse gris clair pondérée par un masque bruité + orientation "up" (la poussière
     se dépose dessus), facteur 0–0,1 ;
   - **Usure d'arêtes** : éclaircissement léger piloté par le Bevel/pointiness, 0–0,05 ;
   - **Variation de teinte par pièce** : jitter HSV (±2° teinte, ±3 % sat/val) — deux briques rouges réelles
     ne sont jamais identiques (lots de production, UV).
3. Garder le SSS activé (couleurs claires) ; exclure en V1 les finitions exotiques (liste no_go de
   brick-renderer §1.1) qui sont hors scope classes.

---

## 3. Domain randomization : LA liste des paramètres (plages de départ)

Principes : plages larges (Tremblay), mais **biaisées vers notre usage réel** (audit : plongée dominante,
éclairage chaud/tamisé ~55–60 %, fonds domestiques). Chaque paramètre loggé dans un JSON par image
(reproductibilité + diagnostic doc 14 Phase 3).

| Groupe | Paramètre | Plage de départ | Justification |
|---|---|---|---|
| **Scène** | Nb pièces | 3 régimes tirés à 20/40/40 % : 1–3 (éparses), 4–12 (éparses), **13–40 (TAS empilé)** | le corpus réel couvre déjà le mono-pièce ; le manque = tas (audit §3) |
| | Génération du tas | drop physique séquentiel dans un rayon resserré (entonnoir invisible), 60–100 frames de simulation | poses de repos + occlusions réelles (brick-renderer, Brickognize) |
| | Visibilité min pour annoter | bbox émise si **≥ 20–30 % de pixels visibles** (masque par index de passe), flag `truncated` sinon | cohérent avec la convention gdansk (pièces coupées non annotées) |
| | Distracteurs | 0–3 objets non-LEGO (pièce de monnaie, câble, stylo, jouet) dans 30 % des scènes, non annotés | audit : monnaie/câbles présents dans le réel ; Tremblay : distracteurs ↑ robustesse |
| **Pièces** | Distribution des classes | mélange **70 % biaisé fréquence réelle** (table parts × sets de `rebrickable-sqlite`) / **30 % uniforme** | fréquence réaliste sans affamer les classes rares |
| | Couleurs | palette `LDConfig.ldr` filtrée (no_go §1.1), **70 % pondéré par fréquence Rebrickable part+couleur / 30 % uniforme** | les tas réels sont dominés par ~20 couleurs |
| | Échelle | jamais de normalisation de taille — échelle physique LDraw stricte | leçon inverse de LegoBrickClassification |
| **Fonds** | Texture sol/table | pool de 15–20 PBR CC0 (§4) : bois ×5, stratifié ×2, moquette/tapis ×4, tissu ×3, carrelage ×2, béton ×1, blanc uni ×1 | audit : bois/textile/divers dominants ; garder du studio blanc (28 % du réel) |
| | UV | échelle ×0,5–2, rotation 0–360°, léger displacement | variété gratuite par texture |
| | Scènes fond seul | 3–5 % d'images sans pièce (négatifs) | Multi-object-detection-lego §1.2 |
| **Éclairage** | HDRI | pool ~40–60 Poly Haven indoor/artificial light (§4), rotation Z 0–360°, force **0,3–2,0** | |
| | Biais CHAUD | ≥ 50 % du pool à dominante chaude ; + lampe ponctuelle/aire additionnelle dans 50 % des scènes : **température 2700–6500 K tirée avec 60 % dans [2700 ; 4000 K]**, énergie ±1 ordre de grandeur | audit + doc 14 : sous-perf attendue en éclairage chaud |
| | Extrêmes | 5 % de scènes sombres (force HDRI 0,05–0,3) et 5 % surexposées | cas "très sombre et flou" observés dans le réel |
| **Caméra** | Hauteur | 15–60 cm au-dessus du sol | smartphone tenu main au-dessus d'un tas |
| | Angle (pitch) | 90° (plongée verticale) à 20° ; **60 % dans [60° ; 90°]**, 40 % dans [20° ; 60°] | audit : plongée dominante mais compenser le biais |
| | Roll (tilt smartphone) | ±10° | personne ne tient un téléphone droit |
| | Focale | équivalent 24–28 mm (grand angle smartphone), sensor 36 mm → lens 24–28 ; ±10 % | pas de 35–50 mm "studio" |
| | Visée | point visé = centre du tas + jitter XY ±20 % du cadre ; distance telle que le tas occupe 30–90 % du cadre | aires bbox résultantes ~0,1–10 % (médiane réelle : 1,3 %) |
| | Profondeur de champ | f/1,8–f/2,8 simulé, focus sur le tas ±2 cm | flou d'arrière-plan réaliste smartphone |
| **Post-process** | Bruit capteur | gaussien+poisson, σ 0,5–2 % (↑ dans les scènes sombres) | |
| | Flou de bougé | 0–3 px directionnel sur 30 % des images | audit : flou fréquent |
| | Vignettage | 0–30 % | |
| | Balance des blancs | décalage ±800 K après rendu (en plus de la température lumière) | simule l'AWB smartphone qui se trompe |
| | Exposition | ±1 EV | |
| | Compression | JPEG qualité 70–95 | le corpus réel est du JPEG téléphone |
| **Rendu** | Résolution | 960–1280 px côté long (rendu Cycles ~64–128 samples + denoise) | ≥ résolution d'entrée du détecteur, sans payer du 4K |

Volume cible doc 14 : 50 000–200 000 images. Démarrage proposé : **20 000 images** (validation du pipeline
+ première mesure d'impact, cf. §5), puis montée en volume si la courbe le justifie.

---

## 4. Assets à licence propre

### 4.1 Bibliothèque de pièces — LDraw (licence CC BY, redistribution OK)
- **URL exacte** : https://library.ldraw.org/library/updates/complete.zip
- **Taille vérifiée le 2026-07-05** : 142 693 798 octets (~143 Mo), dernière mise à jour 2026-06-28.
- **Licence** : CC BY 2.0 (« Redistributable under CCAL version 2.0 » dans l'en-tête de chaque .dat) ;
  contributions récentes en CC BY 4.0 ou CC0. Attribution "LDraw.org" requise dans nos crédits.
  Sources : https://www.ldraw.org/legal-info · https://www.ldraw.org/pt-policies.html
- Couleurs officielles : `LDConfig.ldr` inclus dans l'archive.
- Import : `ldr_tools_blender` (MIT), déjà installé et validé.

### 4.2 HDRI — Poly Haven (CC0)
- **Licence** : CC0 (https://polyhaven.com/license) — aucun risque, usage commercial libre.
- **API vérifiée le 2026-07-05** (https://api.polyhaven.com) :
  - liste : `GET /assets?type=hdris&categories=indoor` → **297 HDRI indoor** ; `artificial light` → 225 ;
    **indoor + artificial light → 196** ; `studio` → 96 (sur 977 au total) ;
  - fichiers : `GET /files/<id>` → URLs directes CDN par résolution (1k…19k, formats .hdr/.exr).
    **Téléchargement en masse trivial** : itérer la liste et prendre le `.hdr` 2k (suffisant pour
    l'éclairage ; ~5–15 Mo pièce, soit < 1 Go pour 60 HDRI).
- **Pré-sélection (12, vérifiés existants via l'API, dominante intérieure/chaude)** : `cabin`,
  `bathroom`, `art_studio`, `aft_lounge`, `anniversary_lounge`, `ballroom`, `billiard_hall`,
  `blender_institute`, `brown_photostudio_01`, `brown_photostudio_02`, `christmas_photo_studio_01`
  (nuit chaude), `boiler_room` — à compléter à ~50 en filtrant la catégorie indoor+artificial light.

### 4.3 Textures sols/tables — Poly Haven + ambientCG (CC0 les deux)
- **ambientCG** : licence **CC0 1.0 vérifiée** (https://docs.ambientcg.com/license/ — « copy, modify,
  distribute… even for commercial purposes »). API v2 : `https://ambientcg.com/api/v2/full_json?type=Material&q=…&include=downloadData`
  → liens ZIP directs (PBR 2K PNG suffisant). Vérifié : 101 matériaux "wood", 103 "fabric", 25 "carpet".
- **Liste concrète recommandée (16)** :
  - Poly Haven (vérifiés via API) : `wood_table_001`, `wood_table_worn`, `laminate_floor_02`,
    `laminate_floor_03`, `wood_floor_worn`, `old_wood_floor`, `dirty_carpet`, `denim_fabric`.
  - ambientCG (vérifiés via API) : `Carpet001`, `Carpet011`, `Carpet012`, `Carpet015`, `Carpet016`,
    `Fabric023`, `Fabric026`, `Fabric028` (+ catégories Wood/Tiles au choix pour compléter carrelage/parquet).
- Budget disque total assets ≈ 1,5–2 Go. Tous CC0 sauf LDraw (CC BY → ajouter l'attribution au fichier
  CREDITS du projet).

### 4.4 Fréquences réelles pièces/couleurs
- `research/rebrickable-sqlite` (déjà cloné) : tables parts/colors/inventories → pondérations §3.
  Données Rebrickable : vérifier les conditions d'usage des dumps CDN au moment de l'implémentation
  (usage interne pour pondérer un tirage = pas de redistribution).

---

## 5. Stratégie d'entraînement avec le synthétique

### 5.1 Ce que dit la littérature
- **Pré-entraînement synthétique → fine-tuning réel > réel seul** (Tremblay et al.,
  https://arxiv.org/abs/1804.06516) — schéma de référence.
- **Brickognize** : le fine-tuning avec très peu de réel (≈ 20 images par configuration) suffit à passer de
  83 → 91–99 AP50, et **sature vite** — notre corpus réel (2 933 photos + jalon 1.7) est largement au-dessus
  de ce régime : l'enjeu n'est pas la quantité de réel mais sa **diversité** (tas, éclairages).
- Études industrielles récentes (ex. https://arxiv.org/html/2506.07539v1) : le **mélange** synthétique +
  ~40 % des annotations réelles atteint la baseline 100 % réel — le mélange est une alternative valable au
  pré-entraînement séquentiel, surtout quand le réel est petit.

### 5.2 Plan pour BrickOFF (aligné doc 14 §2.1, it.3)
1. **Voie nominale : mélange direct 70 réel / 30 synthétique** (ratio de départ du doc 14) sur la recette
   det_v1, en conservant early stopping sur la **val photos réelles uniquement**. Le synthétique n'entre
   JAMAIS dans val/test.
2. **Variante à comparer : pré-entraînement 100 % synthétique (20k) puis fine-tuning 100 % réel** (LR réduit
   ×0,1, 10–20 epochs). La littérature ne tranche pas entre les deux à notre échelle → on mesure.
3. Ratios à balayer ensuite seulement si signal positif : 50/50, 30/70 (réel/synth), et montée en volume
   synthétique (20k → 50k → 100k) — **un changement par itération** (doc 14 Phase 4), chaque run dans
   `ml/EXPERIMENTS.md`.
4. Plus tard (jalon classification) : réutiliser les mêmes rendus pour les crops CLS ; l'idée SSIM de
   LegoBrickClassification servira à construire les groupes de classes confusables AVANT l'entraînement CLS.

### 5.3 Protocole d'évaluation : comment prouver que le synthétique aide
- **Juges** : (a) le test réel actuel (179 photos, baseline det_v1 : mAP50 0,773, rappel max 0,985,
  rappel@0,25 = 0,766) — il ne doit PAS régresser ; (b) **un mini-set "tas" réel à créer d'urgence**
  (~50 photos de tas maison, 10–40 pièces, éclairages variés dont chaud, annotées bbox-seulement,
  ~2–4 h de travail) — c'est LE juge de l'it.3, car le test actuel est mono-pièce et ne peut pas
  mesurer ce que le synthétique doit apporter.
- **Runs de l'ablation minimale** (mêmes seeds/config) : A = réel seul (det_v1, existant) ;
  B = synth seul (sanity check du pipeline : si B est nul sur le réel, le rendu a un problème) ;
  C = mélange 70/30 ; D = pré-train synth → FT réel.
- **Métriques** : mAP@50 et rappel/précision à seuil 0,20–0,25 (point de fonctionnement produit CH-5),
  **découpées par tranche** : mono-pièce vs multi vs tas, taille de bbox (petites < 1 % d'aire),
  éclairage chaud vs neutre (tag manuel du mini-set). Verdict "le synthétique aide" si :
  rappel@0,25 sur le set TAS ↑ de ≥ 5 pts ET mAP50 du test mono-pièce ↓ de < 1 pt.
- **Diagnostic en cas d'échec** : grille visuelle des faux négatifs du set tas (occlusion ? couleur ?
  taille ?) + comparer les distributions (aires bbox, luminosité) synth vs réel avant de toucher aux
  paramètres §3 — corriger la plage la plus divergente d'abord, une à la fois.
- **Comptabilité doc 14** : ceci consomme l'itération 3 (sur 6). La création du mini-set tas n'est pas
  une itération, c'est de l'infrastructure d'évaluation (et il resservira à toutes les itérations suivantes).

---

## Sources
- Repos locaux : `research/brick-renderer` (sans licence), `research/Multi-object-detection-lego` (MIT),
  `research/LegoBrickClassification` (sans licence), `research/ImportLDraw` (GPL 2.0),
  `research/ldr_tools_blender` (MIT), `research/rebrickable-sqlite`.
- Brickognize (paper) : https://pmc.ncbi.nlm.nih.gov/articles/PMC9967933/ · https://www.mdpi.com/1424-8220/23/4/1898
- Dataset gdansk : https://www.nature.com/articles/s41597-023-02682-2
- Domain randomization : https://arxiv.org/abs/1804.06516 · https://arxiv.org/html/2506.07539v1
- LDraw : https://library.ldraw.org/library/updates/complete.zip · https://www.ldraw.org/legal-info · https://www.ldraw.org/pt-policies.html
- Poly Haven : https://polyhaven.com/license · https://api.polyhaven.com (vérifié 2026-07-05)
- ambientCG : https://docs.ambientcg.com/license/ · https://ambientcg.com/api/v2/full_json
- Matériaux ABS communauté : https://superhivemarket.com/products/abs-plastic-materials/docs ·
  https://blenderartists.org/t/blendbricks-v2-photorealistic-abs-plastic-lego-material-for-blender-cycles-free-dirt-generator/1454429 ·
  https://stefanmuller.com/exploring-lego-material-part-2/
- Curated list utile pour la suite : https://github.com/360er0/awesome-lego-machine-learning
