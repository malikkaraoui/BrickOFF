# CHANGELOG CH-S — Pipeline de scènes synthétiques

> Comptes-rendus de jalons au format §3.2 de `12_CONVENTIONS_AI.md`.
> Jalons antérieurs documentés dans leurs rapports dédiés : S.1-pré →
> `docs/research/SYNTH_PREFLIGHT.md` (gate GO), S.1 → `docs/research/SYNTH_ASSETS_REPORT.md`.

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
