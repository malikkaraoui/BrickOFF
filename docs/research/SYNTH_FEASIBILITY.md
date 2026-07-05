# Faisabilité du pipeline de génération synthétique (Blender headless)

**Date : 2026-07-05 — Machine : MacBook Pro M1, 16 Go — Blender 5.1.2 (arm64, Metal)**

Tout ce qui suit a été **réellement exécuté** sur cette machine (pas d'estimation sur papier,
sauf la section budget qui extrapole des temps mesurés). Les scripts de test sont dans le
scratchpad de session ; les commandes exactes sont reproduites ici.

**Verdict : FAISABLE.** Chaîne complète validée de bout en bout : import LDraw scripté →
tas physique de 20 pièces → rendu 640×640 (Cycles GPU Metal **et** EEVEE) → extraction
par script des bbox visibles et du taux d'occlusion par pièce. Aucun blocage dur.

---

## 1. Blender headless

```
/Applications/Blender.app/Contents/MacOS/Blender --version
# Blender 5.1.2 (build 2026-05-19, branche blender-v5.1-release, arm64)
/Applications/Blender.app/Contents/MacOS/Blender --background --python-expr "import bpy; print(bpy.app.version_string)"
# 5.1.2 — Python embarqué : 3.13.9
```

Fonctionne. **Attention : Blender 5.x a cassé plusieurs API par rapport à la doc 4.x
qu'on trouve en ligne** (détail en §7 — pièges déjà résolus pendant ces tests).

Modules Python embarqués utiles : `numpy` ✅, **`OpenImageIO` ✅** (lecteur EXR intégré,
décisif pour les annotations). `OpenEXR`, `cv2`, `imageio` absents (pas nécessaires).

## 2. Moteurs de rendu en headless (mesuré, scène par défaut 640×640)

| Test | Temps mesuré |
|---|---|
| Cycles GPU Metal, 64 spp, **1er lancement** | **66,8 s** (compilation des kernels Metal, une seule fois par version de Blender — cache ensuite) |
| Cycles GPU Metal, 64 spp, cache chaud | **2,2 s** |
| EEVEE, 64 samples, 1er lancement | **5,3 s** (compilation shaders) |
| EEVEE, 64 samples, à chaud | **0,79 s** |

- **Cycles + Metal GPU : fonctionne en headless.** Les deux devices sont vus
  (`Apple M1 CPU` + `Apple M1 (GPU - 8 cores) METAL`), `scene.cycles.device='GPU'` OK.
- **EEVEE en background : fonctionne sur cette version** (le piège historique "EEVEE
  sans display" ne s'applique plus — Blender 5.1 rend EEVEE headless sans erreur,
  vérifié image écrite et correcte visuellement). L'identifiant moteur est
  `BLENDER_EEVEE` (il n'y a plus de `BLENDER_EEVEE_NEXT` en 5.x).

## 3. ldr_tools_blender : installé et validé en headless

- **Releases binaires** : oui — `ldr_tools_blender_macos_apple_silicon.zip` (0,9 Mo),
  release **0.5.1** (2026-04-11) :
  `https://github.com/ScanMountGoat/ldr_tools_blender/releases/download/0.5.1/ldr_tools_blender_macos_apple_silicon.zip`
  Le zip contient l'addon Python + **`ldr_tools_py.so` précompilé (Mach-O arm64)** —
  aucun build Rust nécessaire. Compatible Python 3.13 de Blender 5.1 (vérifié à l'exécution).
- **Installation faite** (scriptée, en headless) :
  `bpy.ops.preferences.addon_install(filepath=zip)` + `addon_enable(module='ldr_tools_blender')`
  → installé dans `~/Library/Application Support/Blender/5.1/scripts/addons/`.
- **API scriptable** : `bpy.ops.import_scene.importldr(filepath=..., ldraw_path=..., instance_type='LinkedDuplicates'|'GeometryNodes')`.
  Sous le capot l'addon appelle `ldr_tools_py.load_file()` (bindings PyO3) — utilisable
  aussi en direct pour un contrôle fin (table de couleurs via `ldr_tools_py.load_color_table(ldraw_path)`).
- **Bibliothèque LDraw téléchargée** : `https://library.ldraw.org/library/updates/complete.zip`
  → **142,7 Mo** (zip), **601 Mo** décompressé, **24 299 fichiers** dans `parts/`.
  Installée dans `/Users/malik/Documents/BrickOFF/data/raw/ldraw/ldraw/`.
- **Import testé** : `3001.dat` (brique 2×4) importé en headless en **0,05 s**
  (21 288 sommets, logos de tenons inclus). Import de 5 pièces différentes : **0,06 s**.
- Licence MIT : réutilisation du code du clone `research/ldr_tools_blender` possible
  avec attribution.

## 4. Simulation physique scriptée (mécanisme des tas) — validé

Test 1 — plan passif + 10 cubes actifs, bake 100 frames par
`bpy.ops.ptcache.bake_all(bake=True)`, lecture des positions finales via
`evaluated_depsgraph_get()` : **bake 0,03 s**, positions finales correctes
(tous posés à z=0,25, dispersés — la sim a bien tourné).

Test 2 — **conditions réelles** : 20 pièces LDraw (5 types : 3001, 3020, 3004, 3062b,
54200), duplicats liés, rigid body `CONVEX_HULL` (masse 0,01), chute sur un plan,
120 frames : **bake 1,06 s**. Le rendu confirme visuellement un tas plausible,
pièces posées et empilées avec contacts et occlusions.

Note : `bpy.ops.rigidbody.object_add()` fonctionne en background sans bidouille de contexte.

## 5. Annotations avec occlusions — méthode exacte validée

**Méthode retenue (testée, fonctionne)** — pass Object Index en Cycles :

1. `obj.pass_index = i` (entier unique par pièce) ; `view_layer.use_pass_object_index = True`.
2. Sortie **EXR multilayer** — API Blender 5.x :
   `image_settings.media_type = 'MULTI_LAYER_IMAGE'` **puis**
   `image_settings.file_format = 'OPEN_EXR_MULTILAYER'`, `color_depth = '32'`.
   (Un seul rendu écrit beauty + IndexOB dans le même fichier.)
3. Relecture **dans le même process Blender** avec l'`OpenImageIO` embarqué :
   la couche s'appelle **`ViewLayer.Object Index.X`** (pas "IndexOB") dans un
   subimage séparé. `np.round(...).astype(int)` → masque d'IDs par pixel.
4. bbox visible = min/max des pixels du masque ; aire visible = comptage de pixels.
5. **Taux d'occlusion** : second rendu IndexOB avec les pièces occultantes masquées
   (`hide_render`) → aire non-occluse ; occlusion = 1 − visible/non-occlus.

Test 2 cubes qui se chevauchent : bbox des deux objets extraites, occlusion du cube
arrière mesurée à **72,9 %** (11 579 px visibles / 42 778 px hors occlusion). Sur le tas
de 20 pièces : 10 pièces visibles à la caméra, bbox par pièce extraites correctement.

Points importants mesurés :
- **Un rendu Cycles "IDs seuls" à 1 spp coûte 0,38–0,40 s** (scène de 20 pièces). C'est
  la brique de base pour les masques amodaux (occlusion exacte par pièce) et pour le
  **mode hybride** ci-dessous.
- **EEVEE n'écrit PAS le pass Object Index** (la propriété s'active mais la couche est
  absente de l'EXR — vérifié). En EEVEE, l'alternative testée est **Cryptomatte**
  (`use_pass_cryptomatte_object = True` → couches `CryptoObject00-02` bien présentes
  dans l'EXR, rendu 0,87 s). Le décodage Cryptomatte (hash mmh3 des noms d'objets)
  est faisable mais plus lourd ; **plus simple : hybride EEVEE (beauty) + Cycles 1 spp
  (IDs)**, +0,4 s par image, IDs parfaits et alignés pixel à pixel (même caméra/scène).

## 6. Temps mesurés sur la scène réaliste et budget projeté

Scène de référence : tas de 20 pièces LDraw + plan + area light, 640×640, headless, M1 16 Go.

| Étape | Temps mesuré |
|---|---|
| Import 5 types de pièces LDraw | 0,06 s |
| Instanciation 20 pièces + rigid bodies | 0,02 s |
| Bake physique 120 frames | 1,06 s |
| **Cycles GPU 128 spp + denoise (EXR multilayer beauty+IDs)** | **39,2 s** (1er rendu de la scène) / **18,8 s** à chaud |
| **Cycles GPU 64 spp + denoise** | **12,5 s** / **11,1 s** à chaud |
| **Cycles 1 spp, IDs seuls** | **0,38 s** |
| **EEVEE 64 samples (EXR)** | **4,0 s** (1er) / **1,2 s** à chaud |

### Coût par image (génération en boucle dans un seul process Blender, temps amortis)

- **Option A — Cycles 64 spp** (photoréalisme max, annotations gratuites dans le même
  rendu) : ~1,5 s de scène + ~12 s de rendu ≈ **13,5 s/image**.
- **Option B — hybride EEVEE + Cycles-IDs** (recommandée) : ~1,5 s de scène +
  ~1,5–4 s EEVEE + 0,4 s IDs ≈ **3,5–6 s/image** (fourchette selon recompilation
  shaders quand les matériaux changent ; ~3,5 s si matériaux stables).

### Projection (machine allumée, job séquentiel)

| Volume | Option A (Cycles 64 spp) | Option B (hybride EEVEE) |
|---|---|---|
| 20 000 images | ~75 h (~3 j) | **~19–33 h (~1 j)** |
| 50 000 images | ~188 h (~8 j) | **~49–83 h (~2–3,5 j)** |

### Espace disque (mesuré sur les sorties de test 640×640)

- PNG beauty : 0,47 Mo (Cycles) à 1,09 Mo (EEVEE, plus de grain) → **~10–22 Go pour 20 k**, ~25–55 Go pour 50 k.
- EXR IDs 1 spp 32 bits : 2,5 Mo — **à ne pas conserver** : extraire bbox/masques à la
  volée puis supprimer. Labels (JSON/TXT YOLO) : négligeable. Masques PNG 16 bits
  optionnels : ~0,05–0,1 Mo/image.
- Fixe : bibliothèque LDraw 601 Mo + zip 143 Mo.
- **Total dataset : ~12–25 Go (20 k) / ~30–60 Go (50 k)** — OK pour le disque local.

## 7. Pièges Blender 5.x rencontrés (et résolus — à connaître pour le chantier)

1. `file_format='OPEN_EXR_MULTILAYER'` échoue si on ne met pas **d'abord**
   `image_settings.media_type = 'MULTI_LAYER_IMAGE'` (nouvel enum 5.x).
2. `scene.node_tree` n'existe plus : le compositeur est un node group assigné via
   `scene.compositing_node_group` ; le node File Output a une API `file_output_items`
   remaniée. **Non nécessaire** avec la méthode EXR multilayer retenue.
3. La couche EXR s'appelle `ViewLayer.Object Index.X`, pas `IndexOB`.
4. Le moteur EEVEE s'appelle `BLENDER_EEVEE` (plus de suffixe `_NEXT`).
5. Premier lancement Cycles/Metal : ~65 s de compilation de kernels (une fois par
   version de Blender, ensuite en cache utilisateur).

## 8. Chaîne technique recommandée

1. **Import** : addon `ldr_tools_blender` 0.5.1 (binaire arm64 officiel) +
   bibliothèque LDraw locale ; import scripté par `bpy.ops.import_scene.importldr`,
   1 import par type de pièce puis **duplicats liés** (mémoire quasi nulle par instance).
2. **Tas** : pluie de pièces avec rotations aléatoires + rigid body `CONVEX_HULL`,
   bake 120 frames (~1 s pour 20 pièces), lecture des transforms au dernier frame.
3. **Rendu** : **Option B hybride** pour le gros du volume — beauty EEVEE 64 samples +
   passe IDs Cycles 1 spp (mêmes caméra/objets → alignement parfait). Garder l'Option A
   (Cycles 64 spp) pour un sous-ensemble de validation qualité (~5–10 %) et comparer
   l'impact sur le détecteur.
4. **Annotations** : masque d'IDs par pixel → bbox visibles ; occlusion par rendus
   IDs additionnels à 1 spp (0,4 s chacun) ou décodage Cryptomatte si besoin d'amodal
   systématique.
5. **Orchestration** : un process Blender par lot (des centaines d'images par process),
   scènes régénérées en Python, sorties PNG + labels, EXR intermédiaires supprimés.

## 9. Risques restants

- **Qualité EEVEE vs Cycles** : ombres douces plus bruitées en EEVEE (visible sur le
  test) ; à régler (samples d'ombres, denoiser compositeur) et à valider par un A/B sur
  les métriques du détecteur. Repli assumé : tout Cycles à 64 spp (~13,5 s/img, 3 j pour 20 k).
- **Matériaux** : les matériaux procéduraux de l'addon sont pensés pour Cycles ; rendu
  EEVEE correct sur le test mais à contrôler pour les couleurs transparentes/brillantes.
  La randomisation des couleurs (via `LDConfig.ldr` / `load_color_table`) reste à écrire.
- **Occlusion amodale à grande échelle** : N rendus solo × 0,4 s pèsent sur un tas de 40
  pièces (~16 s) ; si l'amodal est requis partout, préférer le décodage Cryptomatte
  (1 rendu) — implémentation à écrire (~1 j).
- **Cadrage caméra** : sur le test, la moitié des pièces sortent du champ ; il faudra
  asservir la caméra à la bbox 3D du tas (facile, non testé ici).
- **Thermique/veille macOS** : jobs de plusieurs heures → prévoir `caffeinate -i` et
  surveiller le throttling ; les temps projetés supposent des perfs soutenues.
- **RAM** : aucun souci constaté à 20 pièces instanciées ; 16 Go largement suffisants
  à cette échelle (l'addon instancie par nom de pièce + couleur).

---
*Aucun commit effectué. Fichiers ajoutés : ce document + `data/raw/ldraw/` (bibliothèque
LDraw, ~750 Mo). Addon installé dans le profil utilisateur Blender 5.1.*
