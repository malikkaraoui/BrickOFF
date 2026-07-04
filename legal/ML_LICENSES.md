# ML_LICENSES.md — Licences des composants ML/data (CH-0, jalon 0.3)

> **Date de vérification : 2026-07-04.** Toutes les licences ci-dessous ont été vérifiées ce jour
> sur les sources primaires (fichiers LICENSE réels, dataset cards, ToS en ligne) — rien n'est
> affirmé de mémoire. Contexte : BrickOFF est une **app iOS commerciale fermée** ; les modèles
> sont **entraînés hors app** (pipeline interne) puis **embarqués** sous forme de poids CoreML.

---

## Tableau récapitulatif

| # | Composant | Licence vérifiée (source, 2026-07-04) | Usage prévu | Compatible app commerciale fermée ? | Conditions |
|---|---|---|---|---|---|
| 1 | **Bibliothèque de pièces LDraw** (ldraw.org, 16 873 formes au parts update 2026-06) | **CC BY 2.0** (pièces historiques) + **CC BY 4.0** (contributions depuis le CA de 2022) + option **CC0** (depuis 2024-06). Vérifié dans le `CAreadme.txt` distribué avec la bibliothèque et dans l'en-tête des fichiers de pièces eux-mêmes (ex. `3001.dat` : `0 !LICENSE Redistributable under CCAL version 2.0 : see CAreadme.txt`) ; nouveau Contributor Agreement : « *the Author agrees to release the Work under the Creative Commons Attribution License 4.0* » (forums.ldraw.org/thread-26086.html) | Rendu d'images synthétiques (Blender) pour entraîner détecteur + classifieur. Les fichiers .dat **ne sont pas embarqués** dans l'app | **OUI** | Attribution requise. Le CAreadme est explicite : « *You are free … to make commercial use of the CA approved LDraw Parts Library* » et « *The LDraw Steering Committee (SteerCo) also holds an attribution to 'The LDraw Parts Library' in such Derivative Works to be sufficient in lieu of a full list of authors* » → une mention « The LDraw Parts Library » suffit |
| 2 | **Dataset Hugging Face `pvrancx/legobricks`** (400 000 images, 1 000 classes = part IDs Rebrickable, 400 img/classe, images générées depuis LDraw) | **Apache-2.0** (champ `license` de la dataset card, https://huggingface.co/datasets/pvrancx/legobricks). La card précise : « *Images generated using ldraw. This dataset is not created or endorsed by LEGO.* » | Entraînement du classifieur (et pré-entraînement éventuel du détecteur) | **OUI** | Apache-2.0 : conserver la notice. ⚠️ Nuance : les images étant des rendus de la bibliothèque LDraw (CC BY), l'attribution « The LDraw Parts Library » couvre aussi ce dataset par prudence (voir Ambiguïté A2) |
| 3 | **YOLOX** (github.com/Megvii-BaseDetection/YOLOX) | **Apache License 2.0**, copyright Megvii Inc. 2021-2022 — vérifié sur le fichier `LICENSE` du repo (raw.githubusercontent.com/Megvii-BaseDetection/YOLOX/main/LICENSE) | Framework d'entraînement + architecture du détecteur (poids exportés CoreML embarqués) | **OUI** | Conserver notice + texte de licence dans les mentions légales ; indiquer les modifications si le code est redistribué (il ne l'est pas : seul le modèle exporté est embarqué) |
| 4 | **RT-DETR** (github.com/lyuwenyu/RT-DETR) | **Apache License 2.0** — vérifié sur le fichier `LICENSE` du repo (raw.githubusercontent.com/lyuwenyu/RT-DETR/main/LICENSE) | Candidat alternatif au détecteur (favori à date selon la veille, maintenance active) | **OUI** | Identiques à YOLOX (Apache-2.0) |
| 5 | **MobileNetV3 pré-entraîné ImageNet (torchvision)** | Code torchvision : **BSD 3-Clause**, copyright Soumith Chintala 2016 (raw.githubusercontent.com/pytorch/vision/main/LICENSE). Poids : la doc officielle avertit : « *The pre-trained models provided in this library may have their own licenses or terms and conditions derived from the dataset used for training. It is your responsibility to determine whether you have permission to use the models for your use case.* » (docs.pytorch.org/vision/stable/models.html). ImageNet lui-même : « *Researcher shall use the Database only for non-commercial research and educational purposes* » (image-net.org/download.php) | Initialisation (transfer learning) du classifieur, ensuite ré-entraîné sur nos données synthétiques | **OUI, avec réserve** (voir Ambiguïté A1) | BSD-3 : conserver la notice torchvision. Réserve documentée sur les poids ImageNet ci-dessous |
| 6 | **API Brickognize** (brickognize.com, api.brickognize.com) | Pas de licence — service en ligne régi par ses **ToS** (https://brickognize.com/terms-of-service/, référencés comme `termsOfService` dans l'OpenAPI de l'API). §2 : « *Permission is granted to temporarily download one copy of the materials on brickognize.com's Website for personal, non-commercial transitory viewing only* » et interdiction d'« *use the materials for any commercial purpose* ». Droit polonais (§10). Contact : piotr.rybak@brickognize.com | Outil de **développement uniquement** : pré-annotation du realworld test set (aucune dépendance runtime) | **NON en l'état** pour notre usage (voir Ambiguïté A3) — accord écrit requis avant toute pré-annotation | Ne pas utiliser sans réponse écrite du propriétaire. L'app elle-même n'appelle jamais l'API : le risque est circonscrit au pipeline de données |
| 7 | **coremltools** (github.com/apple/coremltools) | **BSD 3-Clause**, « Copyright © 2020-2023, Apple Inc. All rights reserved. » — vérifié sur `LICENSE.txt` du repo | Conversion PyTorch/ONNX → CoreML (outil de build, pas embarqué) | **OUI** | Aucune obligation dans l'app (outil interne, non distribué). Notice conservée dans le repo ML par hygiène |
| 8a | **ldr_tools_blender** (github.com/ScanMountGoat/ldr_tools_blender) | **MIT**, « Copyright (c) 2023 SMG » — vérifié sur `LICENSE` du repo | Import LDraw dans Blender pour le pipeline de rendu synthétique (outil interne) | **OUI** | MIT : conserver la notice si le code est redistribué (il ne l'est pas). Forkable librement si besoin |
| 8b | **ImportLDraw** (github.com/TobyLobster/ImportLDraw) | **GPL-2.0 or later** — vérifié : README « *Import Ldraw is licensed under the GPLv2 or any later version* » + badge GitHub GPL-2.0 | Alternative d'import LDraw (outil interne uniquement) | **OUI** (sans impact sur l'app — voir explication ci-dessous) | Aucune condition côté app. Si on modifie et **redistribue** le plugin, alors seulement le GPL s'applique (au plugin) |

---

## Pourquoi un plugin GPL utilisé en interne n'impose rien à l'app

Point souvent mal compris, documenté ici une fois pour toutes :

1. **Le GPL est déclenché par la distribution du programme ou d'œuvres dérivées du programme.**
   ImportLDraw (GPL-2.0+) tourne dans Blender, sur nos machines, pendant la génération du dataset.
   Le plugin n'est **jamais distribué** par nous : pas de déclencheur.
2. **Les sorties d'un programme GPL ne sont pas des œuvres dérivées du programme.** Les images PNG
   rendues sont dérivées des **données d'entrée** (les fichiers LDraw, CC BY) et de la scène, pas du
   code du plugin. Le GPL lui-même ne revendique les sorties que si elles incorporent des portions
   du programme (cas type : `bison` embarquant son squelette dans le parser généré) — rien de tel
   ici : aucun octet du plugin ne se retrouve dans une image, ni a fortiori dans des poids de
   modèle entraînés sur ces images. Blender (lui-même GPL) documente exactement la même position
   pour ses rendus : les artworks produits appartiennent à leur auteur.
3. **Chaîne complète** : plugin GPL → images (pas dérivées du plugin) → poids de modèle (pas dérivés
   des images du point de vue du GPL, et encore moins du plugin) → app. Aucun maillon ne transporte
   d'obligation GPL vers l'app.
4. Par symétrie de précaution, le pipeline privilégie quand même **ldr_tools_blender (MIT)** comme
   fondation (décision de la veille GitHub, doc 15) : si un jour on veut forker, patcher et
   redistribuer l'outil, le MIT ne pose aucune question.

Le même raisonnement vaut pour **Blender** lui-même (GPL) et pour tout outil GPL du pipeline de
données : outil interne, sorties non dérivées, rien n'atteint l'app.

---

## Détail des verdicts

### 1. LDraw — OUI
La bibliothèque est sous licences Creative Commons **Attribution** (mélange CC BY 2.0 pour le stock
historique — la ligne `!LICENSE` figure dans chaque fichier de pièce — et CC BY 4.0 pour les
contributions postérieures au Contributor Agreement du 2022-02-23, plus une option CC0 ajoutée le
2024-06-06). Les deux CC BY autorisent **explicitement** l'usage commercial et les œuvres dérivées ;
le CAreadme le dit mot pour mot (« *to make commercial use* », « *to make derivative works* »).
Rendre des images depuis les fichiers de pièces pour entraîner un modèle commercial est donc permis.
La seule obligation est l'**attribution**, et LDraw simplifie : la mention « The LDraw Parts
Library » suffit en lieu et place de la liste complète des auteurs. Comme les fichiers .dat ne sont
pas embarqués dans l'app et que seuls des poids de modèle en dérivent (très indirectement), une
attribution dans l'écran « Mentions légales » de l'app est une précaution peu coûteuse qui couvre
tous les cas (voir A2).

### 2. Dataset `pvrancx/legobricks` — OUI
C'est bien le dataset du plan (400k images / 1000 classes, part IDs Rebrickable, rendus LDraw).
Champ `license: apache-2.0` sur la dataset card. Apache-2.0 permet l'usage commercial sans
restriction ; entraîner un modèle propriétaire dessus est permis. Le verdict est OUI parce que la
licence déclarée est permissive **et** que la matière première sous-jacente (LDraw) est elle-même
compatible commercial — les deux étages de la chaîne sont sains (nuance en A2).

### 3–4. YOLOX et RT-DETR — OUI
Fichiers LICENSE vérifiés : Apache-2.0 dans les deux cas. Apache-2.0 n'a aucun effet viral : le code
d'entraînement reste interne, et les poids produits par nous ne sont pas soumis à copyleft. C'est
précisément la propriété qui motive l'arbitrage D02 (écarter Ultralytics AGPL-3.0). Les deux
candidats sont juridiquement équivalents ; le choix final YOLOX vs RT-DETR peut donc se faire sur
critères purement techniques (taille nano, export CoreML/ANE, maintenance — RT-DETR favori à date
selon la veille doc 15).

### 5. MobileNetV3 torchvision — OUI avec réserve
Le code torchvision est BSD-3 (permissif, aucun problème). Les **poids** pré-entraînés posent la
seule vraie question : torchvision décline explicitement la responsabilité (« *may have their own
licenses… derived from the dataset used for training* »), et les conditions d'accès d'ImageNet
sont non commerciales. Le verdict reste OUI parce que : (a) notre usage est du **transfer
learning** — les poids sont un point de départ entièrement ré-entraîné (fine-tuning complet) sur
nos données synthétiques, pas une redistribution des poids ImageNet ; (b) la position de l'industrie
entière (y compris les acteurs les plus prudents) est que les restrictions ImageNet portent sur le
**dataset** (les images), que nous ne téléchargeons ni n'utilisons jamais ; (c) aucune jurisprudence
n'a jamais qualifié des poids fine-tunés d'œuvre dérivée du dataset d'origine. Réserve documentée
en A1 avec plan B trivial.

### 6. Brickognize — NON en l'état, accord écrit requis
Les ToS (seul texte applicable : l'OpenAPI de l'API pointe explicitement vers cette page) accordent
une licence limitée au « *personal, non-commercial transitory viewing* » et interdisent tout
« *commercial purpose* ». Pré-annoter un dataset destiné à entraîner le modèle d'une app commerciale
est, sans ambiguïté d'objectif, une fin commerciale. Même si l'on plaidait que les *prédictions API*
ne sont pas les « materials » du site (argument possible, voir A3), s'appuyer dessus sans accord
serait exactement le genre de fragilité que CH-0 existe pour éliminer. Verdict : **ne pas utiliser
avant accord écrit** (email à piotr.rybak@brickognize.com décrivant l'usage : pré-annotation d'un
test set, volumétrie faible, pas d'usage runtime). Plan B si refus : annotation manuelle du
realworld set (volumétrie CH-1 prévue faible) ou outils open source (SAM et équivalents).

### 7. coremltools — OUI
BSD-3-Clause (Apple). Outil de conversion utilisé au build ; rien de coremltools n'est embarqué dans
l'app (le runtime CoreML fait partie d'iOS, sous licence Apple OS). Aucune obligation côté app.

### 8. Plugins Blender — OUI (les deux)
ldr_tools_blender est MIT : aucun sujet, y compris en cas de fork redistribué. ImportLDraw est
GPL-2.0+ mais utilisé exclusivement comme outil interne : voir la section dédiée ci-dessus — aucune
obligation ne remonte jusqu'à l'app. Le choix par défaut reste ldr_tools_blender (MIT) par confort.

---

## Verdict global

**La chaîne ML/data envisagée est compatible avec une app commerciale fermée, avec une seule
exclusion en l'état : l'API Brickognize.** Tous les composants structurants — bibliothèque LDraw
(CC BY 2.0/4.0, commercial explicitement permis), dataset `pvrancx/legobricks` (Apache-2.0), YOLOX
et RT-DETR (Apache-2.0 vérifié sur les fichiers LICENSE), torchvision/MobileNetV3 (BSD-3),
coremltools (BSD-3), plugins Blender (MIT / GPL sans effet sur l'app) — sont permissifs ou à simple
obligation d'attribution. Brickognize est interdit d'usage commercial par ses ToS : soit accord
écrit, soit abandon au profit de l'annotation manuelle — dans les deux cas sans impact sur
l'architecture (outil de développement optionnel, jamais dans l'app). La recommandation D02
(détecteur permissif au lieu d'Ultralytics AGPL) est confirmée par les vérifications du jour.

## Attributions à embarquer dans l'app (écran « Mentions légales »)

1. **« The LDraw Parts Library »** — mention exacte : *« Trained in part using renders of The LDraw
   Parts Library (ldraw.org), licensed under CC BY 2.0 / CC BY 4.0. LDraw™ is a trademark owned and
   licensed by the Estate of James Jessiman. »* (couvre CC BY 2.0 et 4.0 ; la formule courte
   « The LDraw Parts Library » est déclarée suffisante par le SteerCo).
2. **Notices Apache-2.0** du framework de détection retenu (YOLOX : « Copyright 2021-2022 Megvii
   Inc. » — ou RT-DETR) : notice + lien vers le texte Apache-2.0. Obligatoire si du code est
   redistribué ; recommandé même pour les seuls poids dérivés (coût nul, lève tout débat sur le
   statut des poids).
3. **Notice BSD-3 torchvision** (« Copyright (c) Soumith Chintala 2016 ») — même logique.
4. **Dataset `pvrancx/legobricks`** (Apache-2.0) — mention de courtoisie recommandée.
5. Déjà prévu ailleurs (jalons 0.1/0.2, rappel) : attribution Rebrickable et disclaimer LEGO
   (« LEGO® is a trademark of the LEGO Group, which does not sponsor, authorize or endorse this
   app »).

Les points 2–4 vont au-delà du strict minimum légal (les poids d'un modèle ne sont probablement pas
des « œuvres dérivées » du code d'entraînement), mais l'écran de mentions coûte zéro et ferme
définitivement la question.

## Points ambigus et hypothèses retenues

- **A1 — Poids ImageNet de MobileNetV3.** Les conditions ImageNet sont non commerciales, mais elles
  encadrent l'accès au *dataset* ; torchvision distribue les poids sans licence dédiée et renvoie la
  responsabilité à l'utilisateur. **Hypothèse retenue** : des poids intégralement fine-tunés sur nos
  données ne sont pas une redistribution d'ImageNet — position standard de l'industrie, risque
  résiduel jugé faible. **Plan B trivial si l'on veut un risque nul** : initialisation aléatoire ou
  poids pré-entraînés sur un dataset à licence claire ; sur 400k images synthétiques, le
  pré-entraînement ImageNet est un confort de convergence, pas une nécessité.
- **A2 — Relicenciement du dataset `pvrancx/legobricks` en Apache-2.0.** Les images sont des rendus
  de pièces LDraw (CC BY) ; l'auteur du dataset a peut-être relicencié plus largement qu'il ne le
  pouvait (un rendu d'une œuvre CC BY reste soumis à l'attribution CC BY). **Hypothèse retenue** :
  on traite le dataset comme s'il héritait de CC BY et on embarque l'attribution LDraw (point 1
  ci-dessus) — ce qui neutralise entièrement l'ambiguïté, quelle que soit la lecture juridique.
- **A3 — Périmètre exact des ToS Brickognize.** Les ToS visent les « materials » du *Website* ; on
  pourrait soutenir que les réponses JSON de l'API n'en font pas partie et qu'aucun texte n'interdit
  d'utiliser les prédictions. Mais l'OpenAPI de l'API désigne ces ToS comme siennes, et aucun autre
  texte n'existe. **Hypothèse retenue (conservatrice)** : les ToS s'appliquent à l'API → usage gelé
  tant qu'un accord écrit n'est pas obtenu. Action : email au contact déclaré
  (piotr.rybak@brickognize.com) avant CH-1 jalon 1.6 ; plan B = annotation manuelle.
- **A4 — LDraw, pièces récentes vs anciennes.** La bibliothèque mélange CC BY 2.0 et CC BY 4.0 (et
  du CC0) selon la date de contribution, sans qu'on ait à trier : les obligations (attribution) sont
  identiques pour notre usage et l'attribution unique « The LDraw Parts Library » couvre les deux.
  Aucune action requise.

---

*Sources primaires consultées le 2026-07-04 : CAreadme.txt de la distribution LDraw (miroir
gkjohnson/ldraw-parts-library + github.com/ctiller/ldraw) ; en-têtes `!LICENSE` des fichiers .dat ;
forums.ldraw.org/thread-26086.html (nouveau Contributor Agreement CC BY 4.0) ;
huggingface.co/datasets/pvrancx/legobricks ; fichiers LICENSE bruts des repos GitHub YOLOX, RT-DETR,
pytorch/vision, apple/coremltools, ScanMountGoat/ldr_tools_blender ; README de
TobyLobster/ImportLDraw ; docs.pytorch.org/vision/stable/models.html ; image-net.org/download.php ;
brickognize.com/terms-of-service (rendu complet via navigateur headless) + OpenAPI
api.brickognize.com/openapi.json.*
