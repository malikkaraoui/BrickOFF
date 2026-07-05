# CH-S — Pipeline de scènes synthétiques réalistes (It.3 et socle produit) — v1.1

> **Statut : NORMATIF v1.1 (2026-07-05)** — plan initial passé en revue adversaire (24 constats,
> `CHALLENGE_CH_S_REVUE.md`) et révisé en réponse. Analyses amont : `docs/research/SYNTH_FEASIBILITY.md`
> (mesures sur machine) et `docs/research/SYNTH_DESIGN_INPUTS.md` (conception, assets, littérature).
> Objectif : apprendre au détecteur le cas produit — des TAS de pièces avec occlusions, en
> conditions domestiques variées — que le corpus réel (82 % mono-pièce) ne contient pas.

## Décisions structurantes actées en v1.1 (issues de la revue)

| Sujet | Décision |
|---|---|
| Annotations & occlusion | **Cryptomatte sur le rendu EEVEE lui-même** (vérifié présent en EEVEE) : masques par pièce extraits du MÊME rendu que le beauty → alignement garanti par construction + taux d'occlusion sans passes multiples. Fallback si échec au préflight : passe IDs Cycles avec regroupement des pièces sans chevauchement écran (3-5 rendus/scène) |
| Profondeur de champ | **Jamais dans le rendu** : DoF + flou de bougé en post-process APRÈS extraction des labels (constat 13) |
| Convention de visibilité | **Écrite avant toute annotation, unique pour les 3 mondes** (synthétique, set TAS, futur 1.7) : bbox émise si ≥ 25 % de la pièce visible ; zone 10-25 % → flag `hard` (ni entraîné positif ni compté faux positif à l'éval) |
| Ratio réel/synth (recette A) | **70 réel / 30 synthétique par epoch** (doctrine doc 14 rétablie — le plan v1.0 l'avait inversée par erreur, constat 19) |
| Premier tir de génération | **10 k images** (pas 20 k) ; on ne monte que si S.5 le justifie ; itérations intermédiaires sur 5 k |
| Fréquences de tirage pièces/couleurs | Fallback v0 : **fréquences empiriques des ~450 part_ids gdansk** (sur disque) ; bascule vers fréquences Rebrickable quand les CSV arrivent (action PO) |
| Shader | **Un seul node-tree partagé, paramétré par attributs objet** (roughness/HSV/usure par pièce sans recompilation — constat 16) |
| Versioning | Seed maître → seeds par scène ; hash git du générateur + `dataset_id` (`synth_v1.0`…) dans chaque manifest ; scène (params+bake) conservée séparément du rendu → re-rendu sans re-simulation |

## Faisabilité prouvée / restant à prouver

Prouvé sur machine (M1, Blender 5.1.2 — SYNTH_FEASIBILITY.md) : import LDraw scripté (0,05 s/pièce,
24 299 pièces dispo), tas rigid body 20 pièces (bake 1,06 s), EEVEE headless 640² (1,2-4 s),
lecture EXR par OpenImageIO, pièges API 5.x documentés.

**La revue a montré que ces tests couvraient un cas dégénéré.** D'où le jalon préflight :

### S.1-pré — Préflight technique (½ à 1 jour) — GATE avant tout engagement
1. **Smoke-test des ~450 part_ids cibles** : import + hull/collision + rendu EEVEE de chaque pièce ;
   rapport des échecs (critère : ≥ 97 % OK, échecs listés et exclus proprement).
2. **Physique sur pièces concaves** : 20 pièces représentatives (arches, brackets, plaques fines,
   Technic) — comparer CONVEX_HULL vs MESH vs décomposition convexe ; mesurer stabilité/temps ;
   choisir et documenter (le biais "tas gonflés" du convex hull, s'il est retenu, est validé
   visuellement contre 5 photos de vrais tas).
3. **Assertion d'échelle** : brique 2×4 importée = 31,8 × 15,8 mm en unités scène (bloquant).
4. **Cryptomatte-EEVEE headless** : extraction des masques par pièce + coverage sur une scène de
   test ; vérifier l'alignement silhouette (IoU masque vs alpha ≥ 0,99 sur 20 scènes).
5. **Pièces fines** : masques stables sur barres/cheese slopes à 640 px (sinon passe masques à
   résolution ×2 — coût mesuré au préflight).
- **Sortie de gate : les 5 points verts (ou parades chiffrées) — sinon STOP et re-conception.**

## Jalons

### S.0 — Set réel "TAS" (le juge) — en parallèle du préflight, PRÉALABLE à S.5
1. **Convention d'annotation écrite d'abord** (voir décision ci-dessus), versionnée dans
   `data/manifests/annotation_convention.md`.
2. **Action PO (Malik)** : ~**100 scènes** de tas réels (10-40 pièces) — 3 éclairages (dont chaud),
   3+ fonds, hauteurs/angles variés, **dont ≥ 20 scènes hors du domicile principal et/ou avec un
   2e téléphone → HOLDOUT jamais utilisé pour les décisions d'itération** (constat 4).
   Protocole fourni ; ~3-4 h de prises de vue.
3. **Pilote d'annotation chronométré (5 scènes)** pour calibrer le budget réel (constat 7), puis :
   pré-annotation modèle v1 seuil 0.15 + correction, ET **passe totalement aveugle sur 15 scènes**
   pour mesurer les angles morts hérités de la pré-annotation (constat 1) ; si > 5 % de pièces
   manquantes dans les scènes corrigées → annotation from scratch (budget honnête : 8-13 h).
4. **Mesure baseline det_v1 sur le set TAS AVANT S.4/S.5** → le critère de succès It.3 est
   recalibré sur cette baseline (constat 5), exprimé en **réduction relative des faux négatifs**
   avec test apparié par instance (McNemar) + IC bootstrap PAR SCÈNE (constat 2).
- Statut vs jalon 1.6 : S.0 est un **set d'évaluation DET distinct** (bbox seulement) ; le 1.6
  complet (part_id + couleur) reste dû — l'écart est tracé au CHANGELOG_CH1 (constat 6).
  Aucune image S.0 ne rejoint jamais l'entraînement.

### S.1 — Assets à licence propre (½ j)
- **40-60 HDRI** CC0 Poly Haven (≥ 50 % chauds — jugés sur température estimée par échantillonnage
  des pixels, méthode documentée, pas sur les tags) ; ~15 textures PBR sols/tables CC0 (ambientCG) ;
  **~10 objets distracteurs non-LEGO CC0** (stylo, pièce de monnaie, câble, dé…) — constat 20 ;
  LDraw ✅ (CC BY 2.0, attribution ajoutée aux crédits app).
- Critères : manifest `synth_assets.json` (asset, source, licence, sha256) ; zéro asset hors CC0/CC-BY.

### S.2 — Générateur de scènes v0 (1,5-2 j)
`ml/synth/generate_scenes.py` (config YAML, batchs de ~400 avec relance process — fuites Blender) :
1. Sol texturé + HDRI randomisés ; caméra plongée 60 % [60-90°] / 40 % [30-60°], focale 24-28 mm éq.,
   tilt ±10°, cadrage tas 30-80 %.
2. Pièces : 3 régimes de N — 20 % [1-3] / 40 % [4-15] / 40 % [16-40] ; tirage pondéré (70 %
   fréquences empiriques gdansk / 30 % uniforme) ; couleurs palette LEGO réelle ; drop séquentiel
   rigid body (méthode choisie au préflight).
3. **30 % des scènes : 0-3 distracteurs non-LEGO ; 3-5 % d'images fond seul (négatifs purs)** (constat 20).
4. Annotations : Cryptomatte → bbox visibles + coverage ; seuil 25 % + flag `hard` 10-25 %.
5. Sortie : beauty PNG + labels YOLO + manifest/scène (seed, params, hash générateur, dataset_id).
- Critères : 100 scènes de validation ; grille visuelle ; 20 scènes vérifiées à la main (bboxes,
  occlusions, zéro fantôme) ; throughput mesuré et projeté honnêtement.

### S.3 — Réalisme matière & capteur (½-1 j)
- Shader partagé paramétré (roughness bruitée [0,05-0,35], SSS, micro-normales, rayures/poussière
  légères, jitter HSV/pièce) ; transparents exclus v1 si artefacts (flag).
- Post-process Python APRÈS labels : bruit ISO, flou bougé ≤ 1,5 px, DoF simulé, AWB ±800 K,
  vignettage, JPEG q70-95.
- Critères **falsifiables** : re-mesure du throughput post-S.3 (constat 16) ; revue par grille
  mélangée 20 synth + 10 réelles gdansk — un relecteur (agent vision) doit se tromper ≥ 4 fois
  sur l'origine (test "spot-the-fake" documenté, remplace le "réaliste au premier regard").

### S.4 — Génération v1 : **10 000 images** (~1 j machine, 6-15 Go)
- Stats de diversité versionnées (histogrammes params/occlusion). Critère : distribution conforme config.

### S.5 — It.3 : entraînement comparatif (2-4 j machine, mesuré avant promesse)
| Recette | Détail |
|---|---|
| A — Mélange 70 réel / 30 synth | un entraînement |
| B — Pré-entraînement synth → fine-tuning réel | converge vite en fine-tuning |
| **C — Synth seul (court)** | **sanity check** : si C est nul sur le set TAS, le rendu a un problème — distingue "synthétique mauvais" de "recette mauvaise" (constat 20) |
- **1 epoch chronométrée sur le mélange AVANT de promettre un calendrier** (constat 15) ; early
  stopping sur val mono-pièce = catch-22 assumé et documenté (constat 22) ; le choix A vs B
  consomme le set TAS de décision (les scènes HOLDOUT restent vierges pour le verdict final).
- **Critère It.3 (recalibré post-S.0)** : réduction relative des faux négatifs sur le set TAS
  significative au bootstrap par scène, sans régression > 1 pt mAP@50 mono-pièce.

### S.6 — Bilan & décision d'échelle
- Succès → scale-up chiffré (20-50 k, nouvelles classes, vignettes D09, guidage V1.5 — même outillage).
- Échec → taxonomie doc 14 Phase 3 sur le set TAS avant tout nouveau tir. **Budget itérations
  après It.3 : 3 restantes** (constat 21d).

## Budget honnête (constats 14-17, 24)

| Poste | Machine | Humain (PO) | Dev (IA) |
|---|---|---|---|
| S.1-pré préflight | 2-4 h | — | ½-1 j |
| S.0 set TAS | — | **3-4 h photos + 4-13 h annotation** (pilote chronométré d'abord) | ½ j outillage |
| S.1 assets | 1-2 h DL | — | ¼ j |
| S.2 générateur | — | — | 1,5-2 j |
| S.3 réalisme | re-mesure | revue spot-the-fake 15 min | ½-1 j |
| S.4 tir 10 k | ~1 j | — | — |
| S.5 A+B+C | **2-4 j** (mesuré à la 1re epoch) | — | ¼ j |
| **Total calendaire réaliste** | | | **~8-12 jours** (S.0 et S.4/S.5 parallélisables avec le dev) |

## Risques & parades (complétés)

| Risque | Parade |
|---|---|
| Convex hull → tas irréalistes | testé au préflight sur pièces concaves ; validation visuelle vs vrais tas |
| Masques instables pièces fines | préflight ; résolution masques ×2 si besoin |
| EEVEE ombres/GI limitées | lot Cycles 2 k comparatif si S.5 déçoit |
| Fuites mémoire Blender | batchs 400 + relance process |
| Juge S.0 biaisé/sous-puissant | convention écrite, passe aveugle, ~100 scènes, holdout tiers, stats appariées |
| Coût re-génération | scènes bakées conservées ; itérations sur 5 k |
| Sur-ajustement méthodologique au set TAS | holdout intouchable pour le verdict final |
