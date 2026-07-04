# AUDIT_DATASET.md — Jalon 2.0 : audit visuel gdansk_det (doc 14, Phase 1)

> Date : 2026-07-04. Auditeur : agent (inspection visuelle image par image).
> Dataset : `data/raw/gdansk_det/` — 2 933 photos réelles (`photos/`) + 2 908 rendus (`renders/`),
> annotations VOC colocalisées (classe unique `lego`).

---

## 1. Méthode

- **Échantillon reproductible** : `random.Random(42).sample()` sur la liste triée (`rglob` trié) des `.jpg`,
  conformément à la référence `data/scripts/04_audit_sample.py` → **40 photos réelles + 15 rendus**.
- **Sur-échantillon multi-pièces** : le dataset est structuré en sous-dossiers `photos/<nb_pièces>/` et
  **82 % des photos sont mono-pièce** (2 392/2 933 dans `photos/1/`). Un tirage uniforme teste donc mal
  les scènes multi-pièces → ajout de **10 photos multi-pièces** (seed 42 sur la liste triée hors `photos/1/`),
  comptées à part. Total inspecté : **65 images, 227 bboxes** (photos : 112 ; multi-extra : 50 ; rendus : 15).
- **Procédé** : pour chaque image, les bboxes du XML ont été **dessinées en rouge sur une copie réduite
  (max 900 px)** puis l'image a été inspectée visuellement (méthode plus forte que le simple comptage
  pièces-vs-bboxes initialement prévu). Tout écart suspect a été contre-vérifié par requête directe des
  coordonnées XML et/ou crop plein-résolution de la zone.
- **Limites honnêtes** :
  - traits rouges fins peu visibles sur petites pièces après réduction → **5 fausses alertes levées**
    uniquement grâce à la contre-vérification XML (sans elle, le taux d'erreur aurait été surestimé) ;
  - le caractère LEGO de petits objets ambigus n'est pas toujours tranchable (ex. contenu d'une boîte
    plastique translucide dans `photos/1/1_8NKD_original_1608913111552.jpg`) ;
  - la justesse fine des boîtes (IoU exact) n'est pas mesurable à l'œil sur copie réduite — seuls les
    décalages grossiers, boîtes fantômes et oublis sont détectables ;
  - n = 55 (+10 orienté) reste petit devant les 500 visées par le doc 14 ; les pourcentages ont une
    incertitude de l'ordre de ±5 pts. Les grilles HTML complètes (`ml/audit_grid_gdansk_photos.html`,
    `ml/audit_grid_gdansk_renders.html`) permettent d'étendre la revue.

---

## 2. Résultats chiffrés — qualité des annotations

| Constat | Photos (50 img / 162 bboxes) | Rendus (15 img / 15 bboxes) |
|---|---|---|
| Boîtes fantômes (bbox sans pièce) | **0** | **0** |
| Boîtes grossièrement décalées | **0** | **0** |
| Boîtes lâches (pièce couverte mais marge excessive) | 3–4 (~2 %) — toutes contiennent la pièce | 0 |
| Pièce **entière visible non annotée** | **0** | 0 |
| Pièce **coupée par le bord du cadre** non annotée | **1 nette + 2 slivers marginaux** | 0 |

Cas concrets (vérifiés en pleine résolution + XML) :
- `photos/18/IMG_20201127_003500.jpg` — **oubli net** : brique ronde noire ~50 % visible au bord bas,
  aucune bbox (18 bboxes pour 19 pièces au moins partiellement visibles).
- `photos/2/IMG_20201129_030329.jpg` — sliver orange ~5 % visible au bord haut, non annoté (marginal).
- `photos/9/IMG_20201127_234032.jpg` — sliver sombre au bord haut, non annoté (marginal, nature incertaine).
- Boîtes lâches mais correctes : `photos/1/0_4Xix_original_1608913073549.jpg` (arche blanche sur robot
  ménager blanc — boîte ~2× l'aire de la pièce), `photos/1/IMG_20201209_004749.jpg`, `photos/1/54383_flash_03.jpg`.

**Taux d'annotations douteuses** :
- au niveau image : 3/50 photos avec au moins une pièce (même partielle) non annotée = **6 %** ;
  en ne comptant que l'oubli net : **2 %**.
- au niveau pièce : ~4 pièces manquantes / ~166 visibles = **≈ 2,5 %** (borne haute incluant les slivers).
- La convention implicite du dataset semble être « ne pas annoter les pièces trop coupées par le cadre » —
  cohérente mais à connaître pour l'entraînement (voir §5).

---

## 3. Résultats chiffrés — fonds, éclairages, angles (photos réelles)

Sur les 50 photos inspectées :

| Type de fond | Part | Exemples |
|---|---|---|
| **Uniforme « studio »** (papier blanc / surface unie, rien d'autre) | **≈ 28 %** (14/50) | `photos/1/54384_flash_06.jpg`, `photos/2/2_MIQA_original-test_1609981051090.jpg` |
| **Support neutre dans scène réelle** (feuille/carton/essuie-tout posé, bords, mains, objets périphériques) | ≈ 26 % (13/50) | `photos/27/IMG_20201127_192145.jpg` (cahier), `photos/18/IMG_20201127_003500.jpg` (carton) |
| **Domestique riche** (bois, verre, écrans, textiles, sol, monnaie, prise murale…) | **≈ 46 %** (23/50) | `photos/1/IMG_20201211_164801.jpg` (écran de tablette !), `photos/1/IMG_20201209_020613.jpg` (prise électrique), `photos/3/IMG_20201129_030439.jpg` (chaussettes), `photos/1/IMG_20201206_234053.jpg` (pièces de monnaie) |

- **Éclairage** : intérieur chaud/tamisé dominant (~55–60 %), flash direct ~20 % (séries `*_flash_*`),
  lumière neutre/jour ~15 %, cas extrêmes ~5 % (`photos/1/IMG_20201127_235327.jpg` : très sombre ET flou).
- **Angles** : plongée quasi verticale majoritaire (~60 %), oblique 30–45° fréquent, quelques prises à
  hauteur de pièce (`photos/1/IMG_20201209_004349.jpg`). Diversité réelle mais biais plongée.
- **Échelle des pièces** : très étalée — aire bbox de **0,06 % à 52 % de l'image** (médiane 1,3 %).
  Beaucoup de petites cibles : pertinent (et exigeant) pour le scan de tas.
- **Distracteurs réalistes** présents : monnaie, coins de meubles, câbles, mains, objets blancs sur fond
  blanc (camouflage) — excellent pour la robustesse.
- **⚠️ Structure du corpus** : 82 % mono-pièce ; les scènes ≥ 4 pièces ne représentent que ~7 % des photos
  (max observé : 32 pièces). Le « scan de tas » n'est PAS représenté par ce dataset réel — confirmé
  visuellement : les scènes multi-pièces sont des pièces éparpillées sans occlusion mutuelle, jamais de tas.

## 4. Rendus (`renders/`) — verdict bref

- **100 % studio** : fond gris uniforme, éclairage doux unique, 1 pièce/image, petite (aire médiane 2 %,
  souvent excentrée voire coupée au bord : `renders/1/3007_Brick-Yellow_0_1608818074.jpg`).
- Annotations : 15/15 correctes et serrées (attendu : générées par construction).
- Qualité de rendu correcte (ombres portées douces) mais **réalisme faible** : aucun fond varié, aucun
  bruit capteur, balance des blancs parfaite ; certains rendus 400×400 sont flous
  (`renders/1/54383_Aqua_4_1587374968.jpg`).
- **Utilité** : diversité géométrique/couleur pour le pré-entraînement DET (localiser « une pièce »), mais
  ils n'apportent rien contre le domain gap fond/éclairage — c'est précisément ce que le pipeline
  synthétique maison (doc 14 §2.1 : fonds texturés, HDRI, bruit) devra corriger.

---

## 5. Verdict vs critères de bascule (doc 14 Phase 1)

1. **> 10 % d'annotations fausses → nettoyage prioritaire : NON DÉCLENCHÉ.**
   Taux mesuré ≈ 2 % (oublis nets) à 6 % (borne haute avec pièces coupées au bord), 0 boîte fantôme,
   0 décalage grossier. Qualité d'annotation **bonne**. Pas de campagne de nettoyage avant entraînement.
2. **> 90 % studio → voie synthétique immédiate : NON DÉCLENCHÉ pour les photos** (~28 % de studio strict,
   fonds domestiques variés confirmés — le biais attendu « fonds domestiques » est bien réel).
   Pour les rendus : 100 % studio, critère satisfait par construction — sans objet puisque la voie
   synthétique (§2.1) et le jalon 1.7 sont déjà actifs d'office (amendement CH-0).
3. **Risque résiduel identifié hors critères** : le corpus réel est massivement **mono-pièce et sans
   occlusion** — la valeur « scènes multi-pièces réelles annotées » est plus rare que ne le laissait penser
   la fiche du dataset. Le scan de tas reposera donc sur le synthétique multi-pièces (§2.1) + corpus réel 1.7.

## 6. Recommandations pour les jalons 1.3 / 1.4

- **1.3 Conversion VOC→YOLO** :
  - conserver la structure `photos/<k>/` comme métadonnée (nb de pièces/scène) pour stratifier les splits ;
  - **respecter le marquage `-test` présent dans certains noms de fichiers** (`*original-test*`) : c'est
    vraisemblablement le split du papier — ne pas le mélanger au train sans décision explicite ;
  - clipper les bboxes aux dimensions image et vérifier xmin<xmax (garde-fou standard) ; prévoir un flag
    « pièce au bord » (bbox touchant le cadre) pour pouvoir exclure/ignorer ces cas ambigus à l'entraînement,
    puisque le dataset n'annote pas systématiquement les pièces très coupées.
- **1.4 Augmentation** (priorités issues des manques observés) :
  - **fonds** : le mélange réel couvre déjà bois/textile/écrans — l'augmentation doit surtout servir les
    rendus (copier-coller de pièces rendues sur fonds réels type BlenderProc/copy-paste) ;
  - **éclairage** : accentuer chaud/tamisé et sous-exposition (dominants en usage réel), flou de bougé ;
  - **angles** : compenser le biais plongée par des perspectives basses ;
  - **petites cibles** : mosaïque/scale jitter — la médiane d'aire bbox à 1,3 % l'exige ;
  - **multi-pièces/occlusions** : à générer synthétiquement, le réel n'en contient quasiment pas.
- **Suivi** : re-passer cet audit (mêmes seeds) après conversion 1.3 pour vérifier qu'aucune bbox n'est
  corrompue par la conversion ; étendre à n=500 via les grilles HTML si un doute apparaît en baseline.
