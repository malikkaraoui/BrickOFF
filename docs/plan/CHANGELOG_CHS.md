# CHANGELOG CH-S — Pipeline de scènes synthétiques

> Comptes-rendus de jalons au format §3.2 de `12_CONVENTIONS_AI.md`.
> Jalons antérieurs documentés dans leurs rapports dédiés : S.1-pré →
> `docs/research/SYNTH_PREFLIGHT.md` (gate GO), S.1 → `docs/research/SYNTH_ASSETS_REPORT.md`.

## Jalon S.3 — Réalisme matière & capteur

- Statut : ⚠️ (2026-07-05) — code et pipeline livrés, throughput conforme, MAIS le
  critère falsifiable spot-the-fake ÉCHOUE (0 erreur/30 sur deux grilles, détail
  ci-dessous). Les causes identifiées sont surtout HORS matière (fonds, ombres,
  étalonnage, composition) — liste des « tells » consignée pour l'itération.
- Livrables produits :
  - `ml/synth/blender_scene.py` — shader partagé durci (toujours UN node-tree,
    nouveaux attributs objet) : roughness par pièce élargie à [0,05 ; 0,35]
    (tirage par pièce + noise spatiale + offset UV par pièce `bo_texoff` qui
    décorrèle deux pièces identiques) ; rayures procédurales (voronoï anisotrope
    seuillé → stries fines, `bo_scratch` ∈ [0 ; 0,12], mixées dans roughness ET
    normale) ; poussière (noise contrasté pondéré par l'orientation « up »,
    `bo_dust` ∈ [0 ; 0,10], roughness) ; jitter HSV par pièce (±3 % teinte,
    ±8 % sat/val, appliqué côté Python sur `obj.color`, tracé au manifest) ;
    SSS conservé ; transmission `bo_trans` câblée pour le test transparents.
  - `ml/synth/postprocess.py` — post-process capteur PIL/numpy APRÈS labels :
    bruit ISO (gaussien lecture + poisson photons, en linéaire), flou de bougé
    directionnel ≤ 1,5 px (moyenne de décalages sub-pixel bilinéaires), DoF
    simulé simple (mix net/flou radial hors zone centrale), dérive AWB ±800 K
    (gains RGB linéaires normalisés au vert), vignettage léger, JPEG q70-95
    (l'image finale devient .jpg, le .png est supprimé). Paramètres tirés PAR
    IMAGE (seed scène + 1000003) et tracés au manifest (clé `postprocess`).
    Idempotent, intégré à `generate_scenes.py` (étape post-batch,
    `--no-postprocess` pour debug), CLI autonome disponible.
  - `ml/synth/config_v1.yaml` — sections `piece_material` (imperfections, jitter
    HSV, bevel) et `postprocess` ; flag transparents `colors.p_transparent`.
  - `data/processed/synth_v11_val/` — 60 scènes de validation
    (`--dataset-id synth_v1.1_val`), 60/60 OK, 0 erreur d'auto-contrôle, 5,8 Mo
    (JPEG vs 63 Mo PNG pour 100 scènes S.2). Grille : `ml/synth_v11_val_grid.html`.
  - `ml/spot_the_fake/` — grille v1 (20 synth + 10 réelles gdansk_det recadrées
    640², noms neutres `spot_XX.jpg`, `key.json`) et `v2/` (version corrigée des
    biais du protocole, voir ci-dessous).
- Critères d'acceptation :
  - [x] **Throughput re-mesuré** (constat 16) : **2,54 s/image rendu + 0,07 s/image
        post = 2,62 s/image total** (60 scènes, 1 batch, 0 relance) — identique aux
        2,6 s/image de S.2 (le durcissement shader est gratuit : mêmes nœuds
        évalués, EEVEE 32 samples inchangé) ; **projection 10 k ≈ 7,3 h machine**.
  - [x] **Labels calés après post-process** : 8 images .jpg vérifiées avec bboxes
        dessinées (dont les 5 aux flou de bougé/DoF max : 1,49 px / σ 2,1) —
        boîtes au pixel sur la silhouette visible, distracteurs jamais annotés.
        Le flou ≤ 1,5 px déplace les bords < 1 px : convention 25 % non affectée.
  - [ ] **Spot-the-fake ÉCHOUÉ** : relecteur (agent vision, cette session) —
        **0 erreur / 30** sur la grille v1, puis **0 erreur / 30** sur une grille
        v2 assainie (synth jamais vues pendant le dev, réelles stratifiées sur
        les dossiers multi-pièces 4-32 de gdansk_det). Critère plan : ≥ 4 erreurs.
        Verdicts notés avant lecture de la clé (key.json) dans les deux cas.
- **Ce qui trahit encore le synthétique** (par ordre d'importance constatée) :
  1. **Fonds** : les ~15 textures PBR se reconnaissent en quelques images (même
     tapis moucheté, même denim, même plâtre, même damier) ; grain uniforme sans
     usure locale, ni miettes/poussière/objets de contexte. Le réel gdansk =
     papier/bureau avec fouillis authentique (câbles, fruits, jouets).
  2. **Ombres EEVEE** : ombre portée unique, longue et dure (ou halos rectangulaires
     doux « fantômes ») ; le réel a des ombres de contact riches et multi-sources.
  3. **Étalonnage** : la dérive AWB + vignettage produit un voile pastel désaturé
     uniforme (« scènes lavées ») qu'aucune vraie photo n'a — un vrai pipeline
     smartphone resature/contraste après l'AWB. Ajouter une courbe de contraste
     saturation post-AWB serait le correctif le plus rentable.
  4. **Composition** : tas = amas balistique circulaire centré à mi-distance sur
     fond nu ; les photos réelles sont cadrées près, pièces éparses posées main.
     (Ce point est en partie voulu — le cas produit EST le tas — mais un régime
     « éparses proches » type photos réelles réduirait le tell.)
  5. **Distracteurs procéduraux** (bouchon-cylindre, monnaie-disque) repérables
     comme primitives ; les modèles Poly Haven passent mieux.
  6. **Matière** : à 640², la matière n'est PAS le tell dominant — les rayures/
     poussière sont sous le pixel ; ce qui manque visuellement : logo des tenons,
     reflets spéculaires brisés en gros plan. Le durcissement S.3 reste utile
     (anti-« plastique parfait ») mais ne suffit pas seul.
  - NB méthodologique : le relecteur est aussi l'auteur du générateur (il connaît
    les assets) — un relecteur humain naïf (PO, 15 min prévues au plan) pourrait
    scorer différemment ; recommandé avant toute re-conception lourde.
- **Transparents (verdict, décision plan)** : EXCLUS v1, flag
  `colors.p_transparent: 0.0`. Test : 3 scènes 10-18 pièces avec ~50 % trans-*
  (23 pièces trans visibles) + 1 rendu brique isolée. Brique 2×4 Trans_Red en
  gros plan : rendu correct (translucidité crédible, raytracing EEVEE activé,
  `use_raytrace_refraction`). En tas à 640² : les pièces trans rendent
  **opaques et ternes** (aucune réfraction visible à cette taille) et les teintes
  claires sont viciées (ex. Trans_Bright_Light_Orange → brun-gris) — artefact
  de domaine pire que l'absence. Le câblage `bo_trans` reste en place pour un
  re-test Cycles ou EEVEE plus tard.
- Écarts au plan :
  1. **Micro-bevel non activé** (`bevel_width: 0.0`) : le node Bevel est
     Cycles-only (no-op EEVEE) → pas de chemin « coût nul » ; un modifier Bevel
     par pièce coûte de la géométrie pour un effet sub-pixel à 640²
     (0,25 mm ≈ 0,3 px). Réévaluer si passage à Cycles ou résolution ×2.
  2. **Jitter teinte ±3 %** interprété comme fraction du cercle chromatique
     (±10,8°) — tiré uniformément, tracé par pièce (`hsv_jitter` au manifest).
  3. **Grille spot-the-fake v1 biaisée** (constaté et corrigé) : le tirage
     aléatoire des réelles est tombé 10/10 sur `photos/1` (mono-pièce) et 4-5
     scènes synth avaient été vues pendant le dev → grille v2 assainie
     (`ml/spot_the_fake/v2/`). Les DEUX scorent 0 erreur : l'échec du critère
     n'est pas un artefact de protocole.
  4. Le dataset final est en **.jpg** (post-process) : `build_grid` et les
     manifests (`image`) suivent ; les labels YOLO et leur nommage sont inchangés.
- Blocages / questions : l'échec du spot-the-fake ne bloque PAS mécaniquement
  S.4/S.5 (le juge réel de l'utilité est S.5/recette C sur le set TAS), mais le
  plan exige la décision PO : itérer sur les tells 1-3 (fonds réels photographiés
  à l'échelle, contact shadows, courbe post-AWB) avant le tir 10 k, ou assumer
  le gap et laisser S.5 trancher.

### Throughput S.3 (mesure du 2026-07-05, M1 16 Go, 60 scènes)
| Mesure | S.2 | S.3 |
|---|---|---|
| s/image rendu (mur) | 2,6 | 2,54 |
| s/image post-process | — | 0,072 |
| **s/image total** | **2,6** | **2,62** |
| Projection 10 k | ≈ 7,2 h | **≈ 7,3 h** |

Reproduction : `.venv/bin/python ml/synth/generate_scenes.py --n 60
--dataset-id synth_v1.1_val --out data/processed/synth_v11_val`.

## Jalon S.2 — Générateur de scènes v0

- Statut : ✅ (2026-07-05)
- Livrables produits :
  - `ml/synth/generate_scenes.py` — orchestrateur (venv) : batchs ~400 avec relance du
    process Blender, reprise sur scènes manquantes (3 tentatives), auto-contrôles,
    stats, grille HTML.
  - `ml/synth/blender_scene.py` — script scène exécuté par Blender headless (communication
    par job/résultats JSON) ; réutilise `ml/synth/preflight/common.py` (import LDraw,
    HULL, Cryptomatte/OIIO).
  - `ml/synth/config_v1.yaml` — TOUS les paramètres de randomisation, versionnés.
  - `ml/synth/part_freqs_gdansk.json` — cache des fréquences empiriques (447 classes,
    comptage des photos gdansk_cls).
  - `data/processed/synth_v1_val/` — 100 scènes de validation (images/, labels/,
    manifests/, run/summary.json) — 63 Mo.
  - `ml/synth_val_grid.html` — grille d'inspection 100 vignettes avec bboxes (positifs
    rouges, hard orange).
- Critères d'acceptation :
  - [x] **100 scènes générées** : 100/100 OK en **260 s (4 min 20)**, 1 seul batch, aucune
        relance nécessaire (`run/summary.json`).
  - [x] **Auto-contrôles dans le code** (tous verts, 0 erreur) : nb labels = nb pièces
        éligibles (vérifié label ↔ manifest par scène) ; coverage ∈ [0,1] ; aucune bbox
        hors image (asserts dans `blender_scene.py` + revalidation orchestrateur) ;
        **assertion d'échelle au démarrage de chaque batch** (3001 = 32,0 × 16,0 × 11,2 mm,
        tolérance ±0,5 mm — bloquant).
  - [x] **Grille visuelle** produite (esprit `04_audit_sample.py`) : `ml/synth_val_grid.html`.
  - [x] **Vérification visuelle** : 12 rendus inspectés avec bboxes (N=1 à 40, plongée
        30-90°, fonds bois/carrelage/béton/tissu/uni, HDRI chauds/froids, distracteurs,
        fond seul) : tas plausibles (contacts corrects, zéro pénétration visible, zéro
        pièce fantôme), bboxes calées au pixel sur la partie visible, statuts hard
        cohérents sur pièces partiellement masquées, distracteurs jamais annotés
        (dont un cas montre-bracelet visuellement proche d'une plaque Technic — négatif
        difficile assumé, jamais labellisé).
  - [x] **Throughput mesuré honnêtement** : **2,6 s/image** mur (bake+rendu+décodage+
        raycast coverage+I/O, relances incluses) → **projection 10 k ≈ 7,2 h machine**
        (M1 16 Go, EEVEE 640², 32 samples). Marge vs budget plan (~1 j machine) : OK,
        à re-mesurer après S.3 (constat 16).
  - Conformité distributions (100 scènes) : régimes N = 20/39/38 (+3 fond seul) vs
    20/40/40 ; fond seul 3 % (cible 3-5) ; distracteurs 33 % (cible 30) ; sol uni 17 %
    (cible 20) ; HDRI chauds 44 % (pondération 50/25/25 correcte, écart binomial) ;
    1 589 pièces, 1 365 labels positifs, 91 hard ; 63 % des pièces visibles sont
    partiellement occluses (coverage moyen 0,74) — le cas produit visé.
- Écarts au plan :
  1. **Spawn des pièces** : l'empilement à pas vertical fixe (style préflight) créait des
     interpénétrations au spawn → impulsions de dépénétration Bullet explosives (mesuré :
     vitesses ~20 u/s dès la frame 2, tas éjecté). Remplacé par un spawn **sans
     interpénétration** par sphères englobantes (jeu 0,12 u ≥ 2× marge hull) — 1 seule
     pièce rejetée hors zone sur 1 589.
  2. **Nouveau piège Blender 5.1 documenté** : `transform_apply(scale)` sur les
     boîtes-parois corrompt la shape Bullet (impulsions fantômes à distance sur les corps
     actifs, reproduit et isolé par ablation). Parade : échelle laissée sur l'objet
     (jamais appliquée) pour les parois. Le sol (géométrie appliquée, méthode préflight)
     est sain.
  3. **Distracteurs posés au sol autour du tas APRÈS la simulation** (dans le champ
     caméra, test de non-chevauchement, 12 essais max) au lieu d'être lâchés dans le
     drop : évite les hulls dégénérés (câble) et les pénétrations tas/objet. 60 %
     modèles .blend / 40 % primitives procédurales (monnaie, dé, câble, bouchon —
     plan B S.1) ; 1-3 par scène concernée (le plan disait « 0-3 » ; 0 = les 70 % de
     scènes sans distracteur).
  4. **Coverage (dénominateur)** : aire de la silhouette non-occluse estimée par lancer
     de rayons sur la pièce seule (BVH monde, ≤ 2 500 rayons, grille adaptative) —
     précision ~2-3 %, suffisante pour les seuils 10/25 % ; l'aire visible (numérateur)
     reste exacte (Cryptomatte). Convention : dénominateur clippé au cadre (règle 5).
  5. **Garde-fou labels** : masque visible < 16 px → pas de label même si coverage ≥ 25 %
     (fragment sub-détectable, ex. pointe de pièce au bord d'occlusion). Paramètre
     `labels.min_visible_px` de la config, tracé par pièce dans le manifest
     (`dropped_low_px`).
  6. **Couleurs** : 75 % tirage pondéré sur 38 couleurs LEGO courantes + 25 % uniforme
     sur les 102 couleurs solides de LDConfig (codes ≤ 511 ; encres d'impression,
     Modulex, trans/chrome/pearl/metal exclus). Transparents exclus v0 (flag S.3).
  7. **Shader pièces** : un seul node-tree partagé conforme à la décision plan
     (paramétré par `obj.color` + attributs objet `bo_rough_min/max`, `bo_sss`,
     `bo_bump`) — reconstruit dans l'esprit du matériau ABS de ldr_tools_blender
     (roughness bruitée, SSS léger, micro-normales) plutôt que réutilisé tel quel :
     les matériaux de l'addon sont un node-tree PAR couleur (contraire à la décision
     « pas de node-tree par pièce »). Hooks S.3 en place.
  8. **Échelle** : 32,0 mm mesuré (nominal LDraw — le gap addon ne s'applique pas via ce
     chemin d'import) vs 31,92 mm au préflight ; écart 0,08 mm ≪ tolérance ±0,5 mm,
     aucun correctif (cohérent préflight point 3).
  9. **Beauty PNG extrait du MÊME rendu** que le Cryptomatte (`save_render` du Render
     Result, view transform scène appliqué) — pas de 2e rendu ; EXR supprimé après
     extraction. PAS de DoF ni flou (post-process S.3, après labels, conforme plan).
- Blocages / questions : aucun.

### Reproductibilité / versioning (décision plan)
Seed maître (config : 20260705) → seeds par scène indépendants du découpage en batchs ;
chaque manifest embarque : seed, tous les params tirés, coverage par pièce,
`dataset_id`, hash git du dépôt (+ flag dirty) et sha256 code+config du générateur.
Re-génération à l'identique : `.venv/bin/python ml/synth/generate_scenes.py --n 100
--dataset-id synth_v1_val`.

### Throughput (mesure du 2026-07-05, M1 16 Go)
| Mesure | Valeur |
|---|---|
| 100 scènes (1 batch, 0 relance) | 260 s mur |
| s/image (mur) | **2,6 s** |
| Répartition indicative (scène 26 pièces) | bake 1,6 s · rendu EEVEE 0,9 s · PNG 0,04 s · décodage+coverage 0,7 s |
| **Projection 10 k (S.4)** | **≈ 7,2 h machine** (+ marge relances/batchs : prévoir ~8 h) |
| À re-mesurer | après S.3 (matériaux durcis + post-process) — constat 16 |

## 2026-07-06 — Jalon S.5 ✅ : les trois recettes évaluées — le synthétique gagne

**Test = 179 photos réelles jamais vues (mono-pièce majoritaire — le verdict TAS attend S.0).**

| Modèle | Recette | mAP@50 test | Rappel max | Rappel @0.35 |
|---|---|---|---|---|
| det_v1 (champion précédent) | réel seul | 0.773 | 0.985 | 0.650 |
| det_v2C | synthétique SEUL | 0.666 | 0.982 | **0.686** |
| det_v2B | pré-entraînement synth → fine-tuning réel | 0.809 | **1.000** | 0.631 |
| **det_v2A** ⭐ | **mélange 70 réel / 30 synth** | **0.820 (+4,7 pts)** | 0.996 | 0.650 |

Lectures :
1. **Sanity check C : VALIDÉ haut la main.** Un modèle n'ayant jamais vu une photo réelle atteint
   0.666 de mAP et le MEILLEUR rappel opérationnel du tableau — le pipeline de rendu (S.2-S.3)
   transfère. L'échec du spot-the-fake n'était pas prédictif de l'utilité d'entraînement,
   comme la littérature domain-randomization le suggérait.
2. **La voie nominale doc 14 (mélange 70/30) l'emporte** sur le séquentiel (B), de peu (+1,1 pt).
   Les deux battent nettement le champion réel-seul.
3. Le rappel @0.35 ne bouge pas (~0.65) : la sous-confiance sur le réel demeure — cohérent avec
   la recommandation d'opérer à 0.20-0.25 + vote multi-frames (EVAL_DET_V1).
4. **Limite assumée : ce test ne contient PAS de tas.** Le gain attendu du synthétique porte sur
   les occlusions/tas — invisible ici. Verdict réel à la livraison du set TAS (S.0, photos PO),
   sur le critère recalibré (réduction relative des FN, stats appariées par scène).

Chaîne exécutée en démon détaché (2 interruptions de session survenues — script versionné
`ml/runs/run_s5_chain.sh`). Durées : C 19 ep., B 26 ep., A 34 ep. (~9 h de M1 au total).
**Champion courant : `ml/runs/det_v2A/best.pt` (dataset_id synth_v1.2 au manifest).**

## 2026-07-06 soir — It.4 ✅ : l'augmentation élargie (idées PO) reprend la tête

| Modèle | mAP@50 test | Rappel @0.35 | Rappel max |
|---|---|---|---|
| det_v2A (champion S.5) | 0.820 | 0.650 | 0.996 |
| **det_v3 (It.4 : tilt ±45° + crop-zoom)** ⭐ | **0.826** | **0.686 (+3,6 pts)** | 0.989 |

Le gain de mAP est marginal (+0,6 pt) mais le **rappel opérationnel au seuil produit bondit de
3,6 points** — le crop-zoom a surtout appris au modèle à avoir confiance sur les cadrages
variés. C'est le meilleur rappel@0.35 jamais mesuré à mAP quasi égal. Champion courant :
`ml/runs/det_v3/best.pt`. Budget d'itérations : 3/6 consommées, 3 restantes — réservées au
verdict TAS (set S.0 attendu mercredi).

## 2026-07-09 — It.5 (det_v4) : ne bat pas le mesurable, mais révèle un juge trompeur

Détail : `ml/runs/det_v4/EVAL_IT5.md`.
- Juge SPARSE (batch1 corrigé) : det_v3 mAP 0.656 → det_v4 **0.576** (léger recul, décalage vers le dense).
- Mono-pièce : 0.826 → 0.802 (légère régression).
- **Juge DENSE (9 tas batch2 de 50)** : det_v3 (juste) rappel@0.20 = **0.203** — le champion ne
  trouve que 20 % des pièces d'un vrai tas ! det_v4 (biaisé/mémorisé) monte à 0.566.
- **Leçon** : batch1 (éparpillé) mesurait le mauvais cas ; le dense progresse mais non prouvable
  (fuite train/test). **Champion conservé : det_v3.** Bloquant It.6 : un JUGE DENSE holdout propre
  (photos PO dédiées jamais entraînées OU décomptes monochromes).

## 2026-07-10 — It.5b (det_v4b) ✅ : le travail dense PROUVÉ (juge holdout équitable)

Détail : `ml/runs/det_v4b/EVAL_IT5b.md`. Juge dense HOLDOUT propre (4 tas jamais entraînés) :
- **Rappel@0.20 : det_v3 0.181 → det_v4b 0.513** (×2,8, PROUVÉ, pas de mémorisation).
- mAP dense 0.064 → 0.088 (le modèle trouve les pièces ; localisation dense = prochain chantier).
- Sparse : mAP 0.656 → 0.607 (léger recul) mais rappel@0.20 0.568 → 0.595 (hausse).
- Mono-pièce : 0.826 → 0.822 (aucune régression).
**Nouveau champion produit : det_v4b.** Prochain : juge dense définitif (50 photos PO à venir),
puis It.6 sur la précision/localisation en dense.
