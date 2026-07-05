# SYNTH_ASSETS_REPORT — Jalon S.1 : assets à licence propre (CH-S)

> Date : 2026-07-05. Exécution du jalon S.1 du plan `docs/plan/16_PIPELINE_SYNTHETIQUE.md`.
> Manifest : `data/manifests/synth_assets.json` (85 assets, chaque entrée : id, type, source,
> URL de téléchargement, licence, sha256, taille ; + classe thermique pour les HDRI).
> Assets sur disque : `data/raw/synth_assets/{hdri,textures,distractors}/`.

## Compteurs finaux

| Poste | Cible S.1 | Obtenu |
|---|---|---|
| HDRI Poly Haven 2k (CC0) | 40-60, ≥ 50 % chauds | **60** — chauds 33 (**55 %**), neutres 13, froids 14 |
| Textures PBR ambientCG 2K-JPG (CC0 1.0) | ~15 | **15** — bois ×5, tissu/moquette ×4, carrelage ×3, béton ×3 |
| Distracteurs non-LEGO (CC0) | ~10 | **10** modèles Poly Haven (.blend + textures 1k) |
| Taille totale téléchargée | < 2 Go | **744 Mo** (zips) / ~1,06 Go sur disque (zips textures + extraits) |

Zéro asset hors CC0/CC0 1.0 : tout provient de Poly Haven (CC0, https://polyhaven.com/license)
et d'ambientCG (CC0 1.0, https://docs.ambientcg.com/license/), licences vérifiées le 2026-07-05.
Aucune attribution requise (le CC BY 2.0 de LDraw, hors périmètre S.1, reste dû aux crédits app).

## 1. HDRI (60 × 2k .hdr, Poly Haven)

- Source : API `https://api.polyhaven.com/assets?type=hdris&categories=indoor,artificial light`
  (196 candidats) → 87 téléchargés en 2 vagues, classés par température, **élagage à 60** pour
  atteindre le quota chaud (les 27 supprimés étaient majoritairement froids/redondants — séries
  studio quasi identiques, dominantes très bleues).
- **Méthode de classement thermique (par pixels, pas par tags)** — script
  `ml/synth/classify_hdri_temperature.py` :
  1. lecture du .hdr en RGB linéaire (OpenCV), réduction 256×128 ;
  2. moyenne RGB **pondérée par la luminance Rec.709** (clippée au percentile 99,5 pour qu'un
     pixel de lampe/soleil isolé ne domine pas seul) → couleur moyenne de la lumière émise ;
  3. ratio R/B + CCT estimée (sRGB linéaire → XYZ → xy → McCamy 1992) ;
  4. classes : **chaud** = CCT < 4500 K ou R/B > 1,35 ; **froid** = CCT > 5800 K et R/B < 1,05 ;
     **neutre** sinon. CCT hors [1000 ; 25000] K (McCamy hors domaine, 1 cas) → R/B seul.
- Étendue obtenue : de `warm_bar` (R/B 7,7, ~2800 K) à `bathroom` (R/B 0,56, ~9600 K) — les
  extrêmes froids type lumière du jour bleutée sont volontairement conservés en minorité (14/60)
  pour la robustesse, conformément au §3 de SYNTH_DESIGN_INPUTS (extrêmes ~10 %).
- Les 33 chauds incluent les ambiances domestiques visées : `fireplace`, `cabin`, `hotel_room`,
  `warm_bar`, `warm_restaurant_night`, `warm_reception_dinner`, `wooden_lounge`, `lythwood_lounge`,
  `en_suite`, `theater_01/02`, `pretville_cinema`, etc.

## 2. Textures PBR (15 × zip 2K-JPG, ambientCG)

Sélection via l'API v2 (`/api/v2/full_json?type=Material&include=downloadData`), zips vérifiés
(taille annoncée) puis extraits sur place (`textures/<Id>/` : diffuse, normal GL/DX, roughness,
displacement, AO…).

| Catégorie | Assets |
|---|---|
| Bois (5) | Wood026, Wood051 (plateaux), WoodFloor007, WoodFloor039, WoodFloor043 (parquets/stratifié) |
| Tissu/moquette (4) | Carpet001, Carpet011, Fabric023, Fabric026 |
| Carrelage (3) | Tiles036, Tiles074, Tiles101 |
| Béton/pierre (3) | Concrete016, Concrete019, Concrete034 |

Le fond « blanc uni » du §3 (28 % du réel) ne nécessite pas de texture (shader uni en S.2).

## 3. Distracteurs non-LEGO (10 modèles CC0, Poly Haven)

Poly Haven est la seule source vérifiable en CC0 réel parmi les candidats examinés ; les 521
modèles du site ont été passés en revue par mots-clés. **Trouvé en CC0 et à l'échelle table/sol** :

`stationery_supplies` (set stylo/crayon/gomme — couvre 3 items de la liste cible), `rubber_duck_toy`
(jouet), `gamepad` (manette), `digital_wrist_watch` (montre), `alarm_clock_01` (réveil),
`round_spectacles` (lunettes), `vintage_lighter` (briquet), `measuring_tape_01` (mètre ruban),
`screwdriver` (tournevis), `wooden_spoon` (cuillère). Format : `.blend` avec textures 1k incluses
(23 Mo au total), importables directement dans le générateur S.2.

**Manque / plan B** : pas de pièces de monnaie, clés, dés, câble ni bouchon en CC0 vérifié sur
Poly Haven (rien de fiable trouvé ailleurs sans doute de licence → exclus, conformément à la
contrainte). Plan B acté pour S.2 : ces 4-5 objets sont géométriquement triviaux et seront générés
en **primitives procédurales Blender** (cylindre aplati métallique = pièce ; cube biseauté à pips =
dé ; courbe extrudée = câble ; cylindre liège = bouchon), sans dépendance d'asset. Les distracteurs
ne sont jamais annotés — leur fidélité visuelle est secondaire (Tremblay 2018).

## 4. Écarts et notes

- **Aucun écart sur les critères S.1** : 60 HDRI (max de la fourchette), 55 % chauds (> 50 %),
  15 textures, 10 distracteurs, manifest complet, zéro asset hors CC0/CC-BY.
- Le classement chaud/neutre/froid est global par HDRI (une ambiance mixte fenêtre froide + lampe
  chaude est classée sur la lumière dominante) — suffisant pour piloter le tirage S.2 ; la lampe
  additionnelle 2700-4000 K du §3 renforcera le biais chaud indépendamment.
- Reproductibilité : chaque entrée du manifest contient l'URL directe de téléchargement + sha256 ;
  re-télécharger = rejouer les URLs et vérifier les hashes.
- Rien n'a été commité (consigne).
