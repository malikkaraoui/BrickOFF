# S.1-pré — Préflight technique CH-S : rapport de gate

**Date : 2026-07-05 — Machine : MacBook Pro M1, 16 Go — Blender 5.1.2 headless (Metal),
addon ldr_tools_blender 0.5.1, bibliothèque LDraw officielle (24 299 pièces).**

Tout a été **réellement exécuté** sur cette machine. Scripts et résultats bruts (JSON/JSONL,
rendus de contrôle) : `ml/synth/preflight/` (base de code prévue pour S.2).
Référence plan : `docs/plan/16_PIPELINE_SYNTHETIQUE.md` v1.1, jalon S.1-pré (constats 8-13
de `CHALLENGE_CH_S_REVUE.md`).

## Verdict global : **GO avec parades**

Les 5 points sont verts, dont le point 2 « avec parades » : la collision `MESH` sur corps
actifs est **non viable** dans Bullet/Blender (explosion mesurée et reproduite) ; la méthode
retenue est `CONVEX_HULL` aux paramètres par défaut — stable, rapide (bake 0,8 s / 20 pièces)
et visuellement plausible — avec ses biais chiffrés (cavités remplies, flottement ~1 mm) et
les parades prévues au plan (validation visuelle contre de vrais tas en S.2, parois de
confinement pendant le bake). Aucun point ne nécessite le fallback Cycles ni une
re-conception. **Décisions techniques finales pour S.2 en fin de document.**

| Point | Verdict | Chiffre clé |
|---|---|---|
| 1. Smoke-test 447 pièces | **VERT** | 99,6 % OK (critère ≥ 97 %), 87 s |
| 2. Physique concaves | **VERT avec parades** | HULL défaut : 0 sous-sol, posé ; MESH : 14/20 à travers le sol |
| 3. Échelle | **VERT** | 3001 = 31,92 × 15,92 mm (attendu 31,8 × 15,8 ; 1 unité = 40 mm) |
| 4. Cryptomatte-EEVEE | **VERT** | IoU 0,99987-0,99998 (critère ≥ 0,99), décodage 0,08 s |
| 5. Pièces fines | **VERT** | bruit masques < 0,1 % à 640 px ; pas de passe ×2 |

---

## Point 1 — Smoke-test des 447 part_ids cibles : **VERT**

Scope extrait des dossiers de classes de `data/raw/gdansk_cls/photos/` (447 part_ids).
Pour chaque pièce : résolution `.dat` (avec alias), import, rigid body `CONVEX_HULL`
+ 4 frames de simulation réelle (force la construction de la collision Bullet), rendu
vignette EEVEE 128 px, contrôle « pièce visible » (pixels alpha > 0).

| Mesure | Valeur |
|---|---|
| Pièces OK | **445 / 447 = 99,6 %** (critère ≥ 97 %) |
| Échecs | 2 : `20896`, `98560` — absents de la bibliothèque LDraw officielle (aucune variante) |
| Temps total | **87 s** (0,195 s/pièce en moyenne : import 0,017 s + rendu 0,168 s) |
| Crashs process | 0 (le harnais de reprise `run_smoke.sh` n'a pas servi) |
| Alias résolus | `30237b→30237`, `30361c→30361`, `3245→3245a`, `35336_4176→4176`, `57909b→57909` |

Décision : les 2 pièces manquantes sont **exclues proprement du scope v1** (à tracer dans le
manifest S.2) ; s'il faut les récupérer, chercher dans le dépôt *unofficial* LDraw (non testé).
Fichiers : `out/smoke_summary.json`, `out/smoke_results.jsonl`, vignettes `out/smoke/*.png`.

## Point 2 — Physique des pièces concaves : **VERT avec parades** (méthode : CONVEX_HULL défaut)

Drop de 20 pièces concaves/complexes du scope, mêmes positions/rotations initiales (seed 42)
pour toutes les variantes : 6 arches (`3659`, `4490`, `6182`, `88292`, `92950`, `15254`),
2 brackets (`44728`, `99207`), barrière ajourée `3185`, 5 Technic à trous (`3700`, `3701`,
`32000`, `32316`, `6541`), clip `61252`, barre `30374`, plaques fines `3023`/`3623`,
cheese slope `54200`, antenne `3957`. Sol passif BOX, 150 frames, masse 0,01, friction 0,7.

| Variante | Bake | Sous le sol | Éjectées | Posé à f150 ? | Hauteur tas |
|---|---|---|---|---|---|
| **`CONVEX_HULL`, marge défaut (0,04 u), 20 substeps** | **0,80 s** | **0** | 2* | **oui** (Δ 0,008 u) | 20,2 mm |
| `CONVEX_HULL`, marge 0,002 u | 0,59 s | 1 | 6 | non (Δ 36 u) | — |
| `CONVEX_HULL`, marge 0,01 u | 0,66 s | 2 | 8 | non (Δ 38 u) | — |
| `CONVEX_HULL`, géométrie ×5, marge défaut | 0,83-2,6 s | 5 | 8 | non (même à 400 frames) | — |
| `MESH` (base), marge 0,002, **60 substeps** | 82,2 s | **14** | 16 | non (Δ 57 u) | explosion |
| Hybride (MESH concaves / HULL reste), 60 substeps | 55,0 s | 12 | 15 | non (Δ 43 u) | explosion |

\* 2 arches (`92950`, `15254`) glissent hors de la zone de tas (15-24 cm équiv.) mais restent
posées sur le sol — dû au rebond + hulls arrondis par la marge.

Constats :
- **`MESH` sur corps actifs est non viable** : même avec marge réduite et 60 substeps
  (bake ×100), tunneling massif — 14/20 pièces traversent le sol et finissent à des
  centaines d'unités ; pénétrations pièce-pièce visibles au rendu sur les survivantes
  (`out/physics/pile_mesh_m002_s60.png`). C'est une limitation connue de Bullet (tri-mesh
  actifs via GImpact). L'hybride hérite du problème pour ses 15 pièces MESH.
- **Toute déviation des défauts déstabilise le hull** : marges réduites (0,002/0,01 u) et
  géométrie ×5 provoquent jitter, passages sous le sol et éjections. Les défauts
  Blender/Bullet sont accordés à ces ordres de grandeur — on ne les touche pas.
- Biais du hull retenu, chiffrés : (1) cavités remplies — arches/brackets/Technic ne
  s'imbriquent pas, tas légèrement « gonflé » ; (2) **flottement ~1,0 mm** au-dessus du sol
  (effet de la marge 0,04 u = 1,6 mm), sub-pixel au cadrage tas 640 px ; (3) pièces
  arrondies → 2/20 roulent/glissent hors zone.
- Rendu comparatif : `pile_hull_default.png` = tas plausible, contacts et empilements
  corrects, aucune pénétration visible.

**Recommandation : `CONVEX_HULL` pour TOUTES les pièces, paramètres Bullet par défaut**
(pas d'hybride). Parades S.2 : parois invisibles pendant le bake (contient les rebonds,
supprime les éjections), hauteurs de chute modérées, et validation visuelle du biais
« tas gonflé » contre 5 photos de vrais tas (déjà au plan v1.1). Si cette validation échoue
sur les arches, l'option restante est la décomposition convexe hors-Blender (V-HACD) en
shapes `COMPOUND` — non nécessaire à ce stade.
Fichiers : `out/physics/physics_results.json`, `pile_*.png`.

## Point 3 — Assertion d'échelle (bloquant) : **VERT**

Brique `3001` (2×4) importée, dimensions mesurées sur les sommets en coordonnées monde.
Facteur d'échelle documenté : l'addon pose `scene_scale = 0,01` sur l'objet racine et les
mailles sont en LDU (1 LDU = 0,4 mm) → **1 unité scène = 100 LDU = 40 mm**.

| Config | L × l × h mesurées (mm) | Attendu |
|---|---|---|
| `add_gap_between_parts=True` (défaut) | **31,92 × 15,92 × 11,12** | 31,8 × 15,8 (réel) |
| `add_gap_between_parts=False` | 32,00 × 16,00 × 11,20 | 32 × 16 (nominal LDraw) |

Écart avec le gap par défaut : **+0,12 mm (0,4 %)** sur chaque axe — LDraw modélise au
nominal 32 mm et le « gap » de l'addon retire 0,08 mm/axe. Dans la tolérance (±0,5 mm),
aucun facteur correctif nécessaire. Hauteur avec tenons : 11,2 mm nominal (mesuré 11,12).
Fichier : `out/scale_results.json`.

## Point 4 — Cryptomatte-EEVEE headless : **VERT**

3 scènes (seeds 101-103) de 15 pièces qui se chevauchent (tas simulé, transforms figées,
sol caché au rendu). **Un seul rendu EEVEE 640²** écrit beauty + `CryptoObject00-02`
(EXR multilayer, film transparent). Décodage par script avec l'OpenImageIO embarqué :
manifest lu dans le header EXR (`cryptomatte/…/manifest`), ids float par pièce, masque =
somme des paires (id, coverage) sur les 6 rangs → bbox visible + coverage par pièce.

| Seed | IoU union masques vs alpha beauty | Rendu | Décodage | Pièces visibles |
|---|---|---|---|---|
| 101 | **0,99993** | 0,48 s | 0,09 s | 12/15 |
| 102 | **0,99998** | 0,36 s | 0,08 s | 13/15 |
| 103 | **0,99987** | 0,33 s | 0,08 s | 11/15 |

Critère IoU ≥ 0,99 : **passé sur les 3 scènes** (alignement par construction confirmé :
les résidus < 10⁻⁴ sont l'anti-aliasing du seuil 0,5). EXR : 0,3-0,5 Mo/scène (à supprimer
après extraction). Le fallback « passe IDs Cycles 1 spp » n'est **pas nécessaire**.

Deux pièges de décodage rencontrés et résolus (documentés dans `common.py`, à réutiliser en S.2) :
1. **OpenImageIO 3.x** : `read_image` doit recevoir explicitement `(subimage, miplevel,
   chbegin, chend, format)` — les variantes « subimage courant » relisent silencieusement le
   subimage 0 (on obtient le beauty à la place des couches crypto, coverage ≡ 0).
2. **Manifest vs pixels** : le manifest EXR stocke le hash mmh3 **brut** ; le float écrit
   dans les pixels applique la correction d'exposant de la spec Cryptomatte (bit 23 flippé si
   exposant 0/255). Sans cette conversion, ~1 pièce sur 15 a un masque vide (vu sur seed 102,
   IoU tombé à 0,928). Implémentation vérifiée aussi en recalcul direct mmh3 des noms d'objets.

Note S.2 : 2 à 4 pièces par scène ont rebondi hors cadre pendant la simulation (rebond des
hulls) → prévoir parois invisibles pendant le bake ou rejet des pièces sorties de zone.
Fichiers : `out/crypto/crypto_results.json`, `align_*.png` (contrôle visuel), `beauty_*.png`.

## Point 5 — Pièces fines à 640 px : **VERT**

Scène statique : barre `30374` couchée, cheese slope `54200` de chant, antenne `3957`
debout, plaque 1×1 `3024`, tuile 1×1 `3070b`. 3 poses caméra proches (jitter gaussien
~1 % de la distance + visée recalculée), masques Cryptomatte extraits comme au point 4.
Deux cadrages : gros plan (margin 1,2) et **cadrage type tas** (margin 3,2, pièces ~7×
plus petites en aire — la barre fait ~5 px de large).

| Config | Pire dispersion relative du coverage (3 rendus) | Plus petite pièce | Rendu moyen |
|---|---|---|---|
| 640 px, gros plan | 7,0 % | 1 720 px | 0,39 s |
| 1280 px, gros plan | 7,0 % | 6 886 px | 0,57 s |
| **640 px, cadrage tas** | **6,5 %** | **248 px** | 0,34 s |
| 1280 px, cadrage tas | 6,8 % | 990 px | 0,53 s |

Lecture : la dispersion 5-7 % est **identique à 640 et à 1280 px** et se retrouve seed à
seed (ex. 2 189 px à 640 vs 2 188,8 px-équivalents à 1280) → elle vient du changement réel
de taille projetée dû au jitter caméra, **pas du bruit de quantification des masques**
(< 0,1 %). Aucune pièce ne disparaît ni ne franchit erratiquement un seuil de visibilité.

Décision : **masques à la résolution du rendu (640 px), pas de passe ×2**. Surcoût mesuré
si besoin ultérieur : rendu 1280 px = +55 % de temps (0,34 → 0,53 s). Fichier :
`out/thin/thin_results.json`.

---

## Décisions techniques finales pour S.2

| Sujet | Décision | Justification chiffrée |
|---|---|---|
| **Méthode collision** | `CONVEX_HULL` pour toutes les pièces, paramètres Bullet par défaut (marge 0,04 u, 20 substeps, 20 itérations), masse 0,01, friction 0,7 | seule config stable (0 sous-sol, posé en 150 frames, bake 0,8 s/20 pièces) ; MESH actif explose quoi qu'on fasse |
| **Confinement sim** | parois invisibles pendant le bake, retirées avant rendu ; rejet des pièces finissant hors zone | 2-4 pièces/scène rebondissent hors cadre sinon (mesuré aux points 2 et 4) |
| **Méthode masques** | Cryptomatte-EEVEE sur le rendu beauty lui-même (`use_pass_cryptomatte_object`, 6 niveaux, EXR multilayer, film transparent) ; décodage OIIO embarqué : manifest du header + correction d'exposant spec (bit 23) ; fallback Cycles 1 spp **abandonné** | IoU 0,9999 sur 3 scènes ; rendu 0,33-0,48 s + décodage 0,08 s ; EXR 0,3-0,5 Mo supprimé après extraction |
| **Résolutions** | rendu ET masques à 640×640 ; pas de passe masques ×2 | bruit de quantification < 0,1 % ; pièce fine la plus petite = 248 px au cadrage tas ; ×2 coûterait +55 % |
| **Facteur d'échelle** | `scene_scale = 0,01` (défaut addon), `add_gap_between_parts = True` → **1 unité = 40 mm** ; aucun correctif | 3001 mesurée 31,92 × 15,92 mm vs 31,8 × 15,8 réel (+0,4 %) |
| **Scope pièces v1** | 445 part_ids (447 − `20896`, `98560` absents de LDraw officiel) ; table d'alias du smoke-test reprise dans le générateur | 99,6 % d'import/collision/rendu OK |
| **Sol du bake** | boîte passive `BOX` (pas un plan sans épaisseur) | zéro traversée sur la config retenue |
| **Pipeline scène → rendu** | figer les transforms simulées (`apply_visual_transforms`), supprimer le rigid body world, puis rendre — découple bake et rendu (re-rendu sans re-simulation, conforme plan v1.1) | validé aux points 2, 4, 5 |

Budget indicatif confirmé au préflight (scène 15-20 pièces, config retenue, M1) : ~0,8 s de
bake (150 frames) + 0,3-0,5 s de rendu EEVEE 640² + 0,1 s de décodage — cohérent avec
l'option B de `SYNTH_FEASIBILITY.md` (~3,5-6 s/image tout compris, imports/setup et
matériaux S.3 inclus, à re-mesurer après S.3).

## Pièges nouveaux documentés (à connaître pour S.2, en plus de SYNTH_FEASIBILITY §7)

1. **OIIO 3.x `read_image`** : toujours passer `(subimage, miplevel, chbegin, chend, format)`
   explicitement — sinon lecture silencieuse du subimage 0.
2. **Manifest Cryptomatte** : hash brut dans le header, float corrigé (bit 23) dans les
   pixels — conversion dans `common.hex_to_float`.
3. **Bullet** : ne pas « améliorer » les défauts (marge, échelle de scène) — chaque
   déviation testée a dégradé la stabilité ; `MESH` actif interdit.
4. **`read_factory_settings(use_empty=True)`** désactive les addons non-défaut → réactiver
   `ldr_tools_blender` après chaque reset de scène.
5. Import d'un `.dat` : hiérarchie root(échelle 0,01)+mesh → aplatir la transform dans les
   données et recentrer l'origine sur le centre bbox avant rigid body (COM cohérent).

---
*Aucun commit effectué. Fichiers produits : ce rapport + `ml/synth/preflight/` (scripts et
résultats). Durée machine totale du préflight : ~15 min.*
