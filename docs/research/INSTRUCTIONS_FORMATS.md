# Étude de référence — Formats d'instructions de montage LEGO

> **Statut : recherche, non normatif.** Étude réalisée le 2026-07-04 (recherche web réelle, sources citées en fin de section et en fin de document).
> **Objet :** alimenter la conception du champ `steps` des blueprints BrickOFF (V1.5, approche A1 de [13_GENERATION_FIGURES.md](../plan/13_GENERATION_FIGURES.md)), conformément au backlog de recherche annoncé dans [VISION.md](../VISION.md).
> **Méthode :** chaque affirmation est adossée à une source publique. Quand une information n'est pas vérifiable (formats internes LEGO notamment), c'est dit explicitement.

---

## 1. Les notices officielles LEGO et l'app LEGO Builder

### 1.1 Notices papier/PDF : le processus officiel

LEGO documente publiquement son processus de conception d'instructions ([lego.com — How we design our building instructions](https://www.lego.com/en-us/service/help-topics/article/how-we-design-our-building-instructions)) :

- Les instructions sont conçues **après** que le set a atteint sa forme finale, avec un **logiciel 3D interne développé sur mesure** (non commercialisé, format non public).
- Une équipe dédiée décide **manuellement** : le découpage en étapes, **le nombre de pièces à ajouter à chaque étape**, et **l'angle de vue** montré dans le livret.
- L'équipe **reconstruit physiquement le modèle plusieurs fois**, « en partant du sol, comme vous » (bottom-up), pour valider la séquence de montage.

**Point important et vérifié : LEGO ne publie aucun chiffre officiel de « pièces par étape ».** C'est une décision éditoriale au cas par cas (âge cible, complexité du set). L'observation courante des notices (peu de pièces par étape, souvent 1 à ~10) est un constat empirique, pas une règle documentée par LEGO.

Principes UX identifiés par l'analyse externe des notices ([UXmatters, 2020](https://www.uxmatters.com/mt/archives/2020/12/inspirations-from-a-lego-instructional-booklet.php)) :

1. **Vision aspirationnelle** : montrer le résultat final dès le départ (motivation).
2. **Découpage en étapes atteignables**, avec trois sous-principes :
   - **Vue d'ensemble avant de commencer** (sacs numérotés, sommaire) ;
   - **Préfiguration du résultat** à chaque stade (réduit l'anxiété : on voit où on va) ;
   - **Simplification de chaque étape** : uniquement l'essentiel, **zéro texte**, numérotation, flèches directionnelles.
3. Les mécanismes concrets bien connus des notices — **inventaire de pièces de l'étape** (vignette « 2× [pièce] » en haut de page), **mise en évidence des pièces nouvelles** (contraste/flèches sur fond du modèle déjà construit), **angle de vue stable** avec rotations signalées par une icône — relèvent du constat d'observation ; LEGO ne publie pas de guide de style formel à leur sujet.

À noter : LEGO détient des **brevets sur la génération automatique d'instructions** ([US8374829](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8374829) « Automatic generation of building instructions for building element models », [US9821242](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9821242), et — correction 2026-07-04, cf. `legal/PATENTS_ANALYSIS.md` — [US11393153](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11393153), brevet **Texas A&M** (pas LEGO) sur l'occlusion en instructions AR, sans famille EP/FR) — signe que le problème « décomposer un modèle en étapes » est traité industriellement comme un problème algorithmique, pas seulement éditorial.

### 1.2 L'app « LEGO Builder » (instructions 3D interactives)

Sources : [App Store](https://apps.apple.com/us/app/lego-builder-3d-instructions/id1486159728), [Google Play](https://play.google.com/store/apps/details?id=com.lego.legobuildinginstructions), [page officielle](https://www.lego.com/en-us/builder-app), [aide officielle](https://www.lego.com/en-us/service/help-topics/article/lego-builder-app-3d-building-instructions).

Ce qu'elle fait (vérifié) :

- **Instructions 3D interactives** (« Instructions PLUS ») pour les sets sortis à partir de **2019** ; PDF des notices pour les sets à partir de **2015**.
- Par étape : **zoom, rotation libre de la vue, retournement** des sections pour comprendre le placement.
- **« Ghost mode »** : superpose en transparence la section en cours sur le modèle final — l'utilisateur voit sa progression par rapport au tout ([thebrickblogger](https://thebrickblogger.com/2019/06/lego-life-app-instructions-plus-more/)).
- **Choix du sous-modèle** : si le set comporte plusieurs sections indépendantes, on choisit laquelle construire d'abord.
- Mode « Build Together » (construction sociale à plusieurs) et suivi de progression.

**Format de fichier : non public.** Aucune documentation officielle du format des instructions 3D de LEGO Builder n'a été trouvée ; il dérive vraisemblablement des données 3D internes de LEGO (cf. § 1.1), mais **ce n'est pas vérifiable**.

Ce qui **est** documenté : **LXFML** (LEGO eXchange Format Markup Language), le format de l'ancien LEGO Digital Designer (LDD, abandonné). C'est du **XML lisible** décrivant briques, couleurs, positions, connexions et caméra ; **LXF** en est la version compressée (ZIP contenant `IMAGE100.LXFML` + une vignette PNG) ([fileinfo.com](https://fileinfo.com/extension/lxf), [wiki.ldraw.org/LXF](https://wiki.ldraw.org/wiki/LXF), [guide Rebrickable LDD](https://rebrickable.com/help/guide-to-lego-digital-designer/)). LXFML décrit un **modèle**, pas des **étapes** : LDD générait ses instructions automatiquement (avec des résultats médiocres, raison souvent citée de l'existence d'outils tiers). Rien ne prouve que LEGO Builder utilise LXFML — à considérer comme un format hérité, encore utile comme format d'échange (Studio l'importe/exporte).

**Enseignements pour BrickOFF** : la référence UX c'est (a) peu d'informations par étape, décidées par un humain, (b) inventaire de pièces par étape, (c) vue 3D stable + ghost mode pour situer la progression, (d) sous-modèles choisissables. Aucun format officiel n'est réutilisable : il faut un format à nous.

---

## 2. LDraw (.ldr / .mpd) et la métacommande `0 STEP`

Sources : [spécification officielle du format](https://ldraw.org/article/218.html), [Wikipedia — LDraw](https://en.wikipedia.org/wiki/LDraw), [wiki LDraw — MPD](https://wiki.ldraw.org/wiki/MPD), [métacommandes non officielles](https://wiki.ldraw.org/index.php?title=List_of_Known_Unofficial_META_Commands).

LDraw est **le standard ouvert de facto** de la CAO LEGO (créé par James Jessiman en 1995, maintenu par LDraw.org, bibliothèque de pièces sous licence libre).

### Structure du format

- **Texte brut, une commande par ligne**, le premier nombre étant le « line type » :
  - `0` = commentaire **ou métacommande** ;
  - `1` = **inclusion d'un sous-fichier** (une pièce `.dat` ou un sous-modèle) avec couleur + matrice de transformation 4×3 (position + rotation) ;
  - `2`–`5` = géométrie brute (lignes, triangles, quads, lignes conditionnelles).
- Extensions : `.dat` (pièces/primitives), `.ldr` (modèle), `.mpd` (**Multi-Part Document** : plusieurs `.ldr` concaténés, séparés par `0 FILE nom` / `0 NOFILE` — c'est le mécanisme des **sous-modèles**).
- Unité : **1 LDU ≈ 0,4 mm** ; conventions de grille : 1 tenon = 20 LDU horizontalement, 1 plate = 8 LDU de haut, 1 brique = 24 LDU.

### Encodage des étapes

- **`0 STEP`** : métacommande officielle qui **découpe le fichier en étapes de montage**. Toutes les lignes de type 1 situées entre deux `0 STEP` constituent une étape. Historiquement, elle faisait marquer une pause au programme LDraw original ([spec](https://ldraw.org/article/218.html)).
- **L'ordre des lignes dans le fichier EST l'ordre de montage** : le format ne stocke pas d'étape « objet » avec métadonnées, il sérialise la séquence. C'est à la fois simple et limitant (pas d'attributs d'étape : ni caméra riche, ni texte, ni inventaire — tout est dérivé).
- Extensions **non officielles** mais universellement supportées (MLCad, LPub3D) ([wiki](https://wiki.ldraw.org/index.php?title=List_of_Known_Unofficial_META_Commands)) :
  - **`0 ROTSTEP x y z [REL|ABS|ADD]`** : étape avec **rotation de la vue** — l'équivalent machine de l'icône « tournez le modèle » des notices papier ;
  - **`0 BUFEXCHG A STORE|RETRIEVE`** : « buffer exchange », pour dessiner une pièce hors du modèle avec une flèche vers sa position finale (pièce éclatée) ;
  - Les métacommandes **`0 !LPUB ...`** de [LPub3D](https://trevorsandy.github.io/lpub3d/) ([référence](https://trevorsandy.github.io/lpub3d/assets/docs/lpub3d/metacommands.html)) pilotent la mise en page d'instructions : **callouts** (encarts de sous-assemblage), listes de pièces par étape (PLI, « Part List Image »), multi-étapes par page, etc.

### Exploitable pour générer des instructions ?

**Oui, c'est exactement son usage historique** : la chaîne LDraw → LPub3D produit des notices « style LEGO » (une image par étape + inventaire de l'étape, rendu via LDView/POV-Ray). Points clés pour nous :

- L'**inventaire de l'étape est dérivé** (diff des pièces entre deux `0 STEP`), jamais stocké : preuve qu'un format d'étapes minimal (liste ordonnée de placements + séparateurs) suffit à générer tout l'affichage.
- La **rotation de vue est une donnée d'étape** (ROTSTEP) : quand le concepteur juge le nouvel angle nécessaire, il l'encode. À reprendre.
- Écosystème riche et pérenne (30 ans) : bibliothèque de géométries de pièces, viewers open source ([LeoCAD](https://www.leocad.org/), LDView), importeurs Blender. **Rester convertible vers LDraw donne accès gratuitement à tout cet outillage** (rendu des images d'étapes pour notre pipeline éditorial, par exemple).

---

## 3. BrickLink Studio (.io)

Sources : [Studio Help — Exporting Instructions](https://studiohelp.bricklink.com/hc/en-us/articles/5628123432215-Exporting-Instructions), [Exporting to other formats](https://studiohelp.bricklink.com/hc/en-us/articles/6502197862679-Exporting-to-other-formats), [Import formats](https://studiohelp.bricklink.com/hc/en-us/articles/6502277722647-Import-formats), [Step List](https://studiohelp.bricklink.com/hc/en-us/articles/5626298196247-Step-List), [Step Editor](https://studiohelp.bricklink.com/hc/en-us/articles/5626973531287-Step-Editor), [Divide into steps](https://studiohelp.bricklink.com/hc/en-us/articles/7123910550039-Automatic-instructions-Divide-into-steps), [Submodels in Step Editor](https://studiohelp.bricklink.com/hc/en-us/articles/7123933495959-Submodels-in-Step-Editor).

Studio (BrickLink, propriété du groupe LEGO depuis 2019) est **l'outil dominant de la communauté MOC** pour concevoir des modèles ET produire des notices.

- **`.io`** : format natif projet (modèle + étapes + mise en page des instructions + rendus). **Propriétaire et non documenté publiquement** — inutilisable comme format cible pour un tiers.
- **Interopérabilité réelle** : Studio importe/exporte **`.ldr`/`.mpd` (LDraw)** et **`.lxfml`/`.lxf` (LDD)** ; il écrit un `.mpd` si le modèle a des sous-modèles. LDraw est donc bien la lingua franca de l'écosystème.
- **Les étapes sont éditées à la main** dans un « Step Editor » : liste d'étapes numérotées (nommables), déplacement de pièces d'une étape à l'autre, **sous-modèles ayant leurs propres étapes**, **liste de pièces par étape** affichée, callouts.
- Il existe un **« Divide into steps » automatique**, mais l'aide officielle elle-même prévient : « si Divide into steps ne fonctionne pas bien, essayez les sous-modèles ou appliquez-le plusieurs fois sur des sélections judicieuses ». La technique manuelle recommandée par la communauté est le **« peeling the onion »** : dé-construire le modèle en retirant les pièces de surface, étape par étape, en sens inverse ([guide Open L-Gauge](https://open-l-gauge.eu/making-building-instructions-in-studio/)). **Confirmation indépendante que le découpage automatique de qualité est un problème non résolu grand public.**
- **Export des notices : PDF (prêt à imprimer) ou séquence PNG (une image par page)**, avec facteur de zoom. Pas d'export d'un format d'instructions *structuré* (pas de JSON/XML d'étapes) : la notice exportée est figée en images.

**Enseignement** : même l'outil le plus avancé de l'écosystème traite l'étape comme une **donnée d'auteur** (éditée à la main) et la notice comme un **rendu** (PDF/PNG). Le seul échange structuré passe par LDraw et ses `0 STEP`.

---

## 4. Rebrickable et la distribution des instructions MOC

Sources : [Buying Premium MOCs](https://rebrickable.com/help/buying-premium-mocs/), [Selling Premium MOCs](https://rebrickable.com/help/selling-premium-mocs/), [MOC Building Instruction File Types](https://rebrickable.com/help/types-of-moc-building-instructions/), [Designer Features](https://rebrickable.com/help/plans-designer/), [BrickNerd — Mastering Rebrickable](https://bricknerd.com/home/mastering-rebrickable-a-guide-to-sharing-mocs-and-instructions-1-10-25).

- Rebrickable héberge des MOCs **gratuits et payants (« Premium »)**. Pour un Premium, **on achète uniquement les instructions** (fichiers), jamais les pièces.
- **Le PDF est le format roi** : les fichiers Studio/LDD/LDraw peuvent être joints mais **doivent accompagner un PDF** pour les Premium ; les MOCs gratuits ou anciens peuvent n'avoir qu'un fichier `.io`, LDraw ou LDD.
- Distribution sécurisée : fichiers sur **S3 privé**, liens signés **expirant après 60 minutes**, liés au compte acheteur ; option de **watermarking PDF** (tatouage semi-transparent identifiant l'acheteur) contre le piratage. Taille max 100 Mo en direct (1 Go via URL externe).
- Le designer fixe le prix, Rebrickable gère paiement/téléchargement/reporting (avec commission — [Premium MOC Fees](https://rebrickable.com/help/mocs-fees/)).

**Enseignement** : l'écosystème MOC distribue des instructions **figées et non machine-lisibles** (PDF rendu depuis Studio). Personne ne distribue d'étapes structurées consommables par une app — c'est précisément l'espace que le format blueprint BrickOFF occupe. (Rappel produit : Brickit, le comparable direct de BrickOFF, fournit ses propres instructions pas-à-pas intégrées à l'app pour un catalogue interne d'idées — [brickit.app](https://brickit.app/) ; son format interne n'est pas public.)

---

## 5. Génération automatique d'instructions : travaux open source et académiques

### 5.1 Le fondement : Agrawala et al., SIGGRAPH 2003

[« Designing Effective Step-By-Step Assembly Instructions »](https://graphics.stanford.edu/papers/assembly_instructions/assembly.pdf) (Agrawala, Phan, Heiser, Haymaker, Klingner, Hanrahan, Tversky — [ACM](https://dl.acm.org/doi/10.1145/1201775.882352)) : LE papier de référence, issu d'études de psychologie cognitive sur la manière dont les gens conçoivent et comprennent un assemblage. Principes établis expérimentalement :

- **La planification (ordre des opérations) et la présentation (que montrer) doivent être résolues ENSEMBLE**, pas séquentiellement ;
- Décomposer en **étapes correspondant aux groupes conceptuels** de l'objet (les gens pensent par sous-assemblages : « les pattes », « le toit ») ;
- Chaque nouvelle pièce doit être **visible et non occluse** dans la vue choisie ;
- Montrer **l'action** (flèches, pièces en position éclatée), pas seulement les états avant/après ;
- **Diagrammes structurels séquentiels** > vue éclatée unique, pour des novices.

### 5.2 « Legolization » d'un modèle 3D + stabilité

- **Ono, Andre et al., « LEGO Builder: Automatic Generation of LEGO Assembly Manual from 3D Polygon Model »** ([ResearchGate](https://www.researchgate.net/publication/285670439_Paper_LEGO_Builder_Automatic_Generation_of_LEGO_Assembly_Manual_from_3D_Polygon_Model)) : pipeline 3D → voxels par couches → briques + manuel de montage **couche par couche**. Formule la décomposition en étapes comme **optimisation combinatoire sous contrainte de stabilité**.
- **« Automatic generation of LEGO building instructions from multiple photographic images of real objects »** (Computer-Aided Design, 2015 — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0010448515001037)) : photos → modèle → briques, avec une structure de graphe (« legograph ») gérant **les connexions entre briques** pour garantir des modèles physiquement sains.
- **Luo et al., « Legolization: Optimizing LEGO Designs », SIGGRAPH Asia 2015** ([page projet](http://www.cmlab.csie.ntu.edu.tw/~forestking/research/SIGA15-Legolization/), [ACM TOG](https://dl.acm.org/doi/abs/10.1145/2816795.2818091)) : **analyse de stabilité par calcul de forces** (et non par heuristiques) donnant à la fois un ordre de solidité et un **seuil de stabilité** ; raffinement itératif du layout autour des zones faibles. Validé physiquement sur des assemblages de milliers de briques.
- **StableLego** (arXiv 2024, [PDF](https://arxiv.org/pdf/2402.10711)) : dataset + méthode d'**analyse de stabilité d'assemblages de briques**, pensé pour l'assemblage robotisé (donc pour la **constructibilité séquentielle**, pas seulement l'état final).

### 5.3 État de l'art génératif : LegoGPT (CMU, 2025)

[« Generating Physically Stable and Buildable LEGO Designs from Text »](https://arxiv.org/html/2505.05469v1) ([page projet + code publics](https://avalovelace1.github.io/LegoGPT/), [InfoQ](https://www.infoq.com/news/2025/05/legogpt-text-prompts/)) :

- LLM générant des structures LEGO **brique par brique, dans l'ordre de pose** — la sortie EST une séquence d'assemblage ;
- Dataset **StableText2Lego** : 47 000+ structures, chacune **validée en simulation physique** (NVIDIA PhysX 5) ;
- Résultat clé pour nous : pendant la génération, un **contrôle de validité (collision + connectivité) puis un rollback physique** en cas d'instabilité donnent **98,8 % de structures stables, contre 24 % sans rollback**. Autrement dit : **la validation physique incrémentale (à chaque pose) est ce qui rend une séquence de montage fiable — elle ne peut pas être un post-traitement.**

### 5.4 Ce qu'on retient de la littérature

1. La décomposition en étapes de qualité "notice LEGO" reste **partiellement manuelle partout** (LEGO : équipe dédiée ; Studio : Step Editor ; recherche : automatique seulement pour des sculptures par couches).
2. Quand elle est automatisée, elle est formulée comme **optimisation sous contraintes** : connectivité (chaque pièce posée s'attache à l'existant), **stabilité de chaque état intermédiaire**, accessibilité/visibilité de la pièce posée.
3. Les approches robustes valident **préfixe par préfixe** (chaque étape laisse un modèle partiel stable), pas seulement le modèle final.

---

## 6. Tableau comparatif

| | Notices LEGO (papier/PDF) | LEGO Builder (app) | LDraw `.ldr`/`.mpd` | Studio `.io` | Rebrickable (distribution) |
|---|---|---|---|---|---|
| **Nature** | Document rendu (images) | Instructions 3D interactives | Format texte ouvert (modèle + étapes) | Projet propriétaire (modèle + étapes + mise en page) | Plateforme (fichiers uploadés) |
| **Spécification publique** | Non | Non | **Oui** ([spec](https://ldraw.org/article/218.html)) | Non | n/a |
| **Encodage des étapes** | Implicite (pages) | Interne, non public | **`0 STEP`** (+ `ROTSTEP`, `BUFEXCHG` non officiels) | Step Editor interne, export figé | PDF figé (+ fichiers CAO en annexe) |
| **Inventaire par étape** | Oui (vignette) | Oui | **Dérivé** (diff entre STEPs), rendu par LPub3D | Oui (Parts list per step) | Dans le PDF |
| **Rotation de vue par étape** | Oui (icône) | Libre (l'utilisateur tourne) | `0 ROTSTEP x y z` | Oui (éditeur) | Dans le PDF |
| **Sous-modèles** | Oui (encarts) | Oui (sections au choix) | **MPD (`0 FILE`)** + callouts LPub | Oui (étapes propres) | n/a |
| **Qui décide des étapes ?** | Équipe humaine dédiée | (idem, données LEGO) | L'auteur du fichier | L'auteur (auto « Divide into steps » médiocre, reconnu) | Le designer du MOC |
| **Machine-lisible par un tiers** | Non | Non | **Oui** | Non (sauf via export LDraw) | Non |
| **Pertinence BrickOFF** | Référence UX | Référence UX (ghost mode) | **Référence format + outillage éditorial** | Outil auteur possible (export .mpd) | Preuve qu'aucun format structuré n'existe côté MOC |

---

## 7. Implications pour le format blueprint BrickOFF (champ `steps`)

Le contexte A1 impose une contrainte qu'aucun format existant ne traite : **nos étapes référencent des *slots* paramétriques** (remplis par le solveur avec les pièces réelles de l'utilisateur), pas des pièces fixes. D'où les recommandations suivantes.

### R1 — Une étape = liste ordonnée de placements référencés par slot, pas par pièce

```json
"steps": [
  {
    "id": 1,
    "placements": [
      {"slot_id": "body", "pos": [0, 0, 0], "rot": 0}
    ],
    "caption_key": null
  }
]
```

**Pourquoi** : (a) c'est le modèle LDraw prouvé depuis 30 ans — une séquence ordonnée de placements + séparateurs d'étapes suffit à générer TOUT l'affichage (l'inventaire de l'étape est un simple diff, cf. § 2) ; (b) référencer `slot_id` (et non `part_id`) fait que **les mêmes steps restent valides quelle que soit l'alternative choisie par le solveur** — l'inventaire d'étape affiché est calculé après résolution. Ne jamais stocker l'inventaire d'étape en dur : il serait faux dès la première substitution.
**Conséquence de conception** : si une alternative remplace 1 brique 2×4 par 2 briques 2×2, le slot doit définir les positions relatives de chaque pièce de l'alternative (le placement de l'étape positionne le slot, l'alternative positionne ses pièces dans le slot). Sinon le rendu pas-à-pas est impossible.

### R2 — Granularité : 1 à 5 pièces nouvelles par étape, modulée par `difficulty`

**Pourquoi** : LEGO ne publie pas de chiffre mais confie ce choix à des humains et reconstruit physiquement pour le valider (§ 1.1) ; la psychologie cognitive (Agrawala 2003, § 5.1) montre que des étapes simples alignées sur les groupes conceptuels réduisent la charge mentale ; UXmatters identifie « simplifier chaque étape » comme principe central. Pour nos modèles V1.5 (< 100 pièces, cible familles/enfants), une borne basse stricte est le bon défaut ; `difficulty: 1` → 1–2 pièces/étape, `difficulty: 3` → jusqu'à ~5. **C'est une décision d'auteur encodée dans le blueprint** (comme chez LEGO et Studio), pas un post-traitement : c'est exactement pourquoi le champ `steps` vit dans le JSON dès la conception (exigence VISION.md).

### R3 — Contrainte de validité : chaque préfixe d'étapes doit être connexe et stable, validé par l'outillage éditorial

Règles à imposer à tout blueprint (vérifiables automatiquement dans l'outil de saisie, PAS à l'exécution mobile) :
1. **Connectivité** : toute pièce posée à l'étape N s'attache à une pièce posée aux étapes ≤ N (pas de pièce flottante) ;
2. **Bottom-up par défaut** : pas de pose « en dessous » de l'existant (les notices LEGO se construisent du sol vers le haut, § 1.1) ;
3. **Stabilité du modèle partiel** : après chaque étape, le modèle posé sur la table tient seul.

**Pourquoi** : c'est LA leçon convergente de la littérature (§ 5.4) — LegoGPT passe de 24 % à 98,8 % de structures viables en validant *pendant* la séquence et non à la fin ; Legolization fournit la méthode d'analyse par forces ; StableLego confirme sur l'assemblage séquentiel. Pour BrickOFF/A1 la simulation lourde est inutile en production : les blueprints sont **conçus à l'avance**, donc la validation (même simple : connectivité + règle d'appui) se fait une fois, côté éditorial. Le mobile fait confiance au blueprint — cohérent avec « résultat garanti par design » du doc 13. **Point de vigilance A1** : la validation doit passer pour **toutes les combinaisons d'alternatives** de slots (ou au minimum pour chaque alternative localement, si les alternatives sont géométriquement équivalentes par construction — à garantir dans les règles d'édition).

### R4 — Caméra par étape : héritée par défaut, changée explicitement (équivalent ROTSTEP)

Champ optionnel par étape, p. ex. `"camera": {"yaw": 30, "pitch": 20}` — absent = on garde l'angle précédent.

**Pourquoi** : les notices officielles gardent un angle **stable** et signalent explicitement les rotations (repère spatial de l'utilisateur, § 1.1) ; LDraw a le même modèle (`0 ROTSTEP`, § 2) ; et Agrawala exige que la nouvelle pièce soit **visible, non occluse** — c'est le seul motif légitime de changer d'angle. Même si l'UI V1.5 offre la rotation libre (comme LEGO Builder), l'angle *par défaut* de chaque étape doit être une donnée d'auteur : c'est lui qui garantit la lisibilité sans manipulation.

### R5 — Prévoir les sous-modèles dès le schéma, même si V1.5 ne les exploite pas

Champ optionnel `submodel_id` sur les étapes (ou `steps` groupés par sous-modèle), à la manière des `0 FILE` de MPD et des submodels Studio.

**Pourquoi** : tous les formats matures ont convergé vers cette notion (MPD, Studio, encarts des notices, sections choisissables de LEGO Builder) parce qu'elle correspond aux groupes conceptuels des utilisateurs (Agrawala). Nos modèles V1.5 < 100 pièces peuvent s'en passer, mais l'ajouter après coup casserait le schéma des blueprints déjà publiés (contrainte OTA de V2) ; un champ optionnel aujourd'hui coûte zéro.

### R6 — L'UI dérive tout le reste : inventaire d'étape, mise en évidence, ghost mode

Ne PAS stocker dans `steps` : l'inventaire de l'étape (diff des placements, résolu), la mise en évidence des pièces nouvelles (ce sont les placements de l'étape courante ; le rendu grise/estompe les étapes < N — le « ghost mode » de LEGO Builder est le même principe appliqué au modèle final), les images pré-rendues (le rendu est fait par l'app depuis les placements, sinon le blueprint n'est plus paramétrique).

**Pourquoi** : toute donnée dérivée stockée devient fausse à la première substitution de pièce ou de couleur par le solveur — or la substitution est le cœur d'A1. LDraw/LPub3D prouve que la dérivation suffit (§ 2).

### R7 — Grille compatible LDraw pour les positions

Exprimer `pos` en unités de grille studs (x, z) et en plates (y), conversion triviale vers LDU (1 stud = 20 LDU, 1 plate = 8 LDU, 1 brique = 3 plates — conventions LDraw, § 2).

**Pourquoi** : ça rend chaque blueprint **exportable en `.ldr` mécaniquement**, ce qui ouvre gratuitement l'outillage LDraw pour la chaîne éditoriale (visualisation dans LeoCAD, rendu de contrôle via LPub3D, import des créations d'un designer travaillant dans Studio via export `.mpd` → conversion en blueprint). Le coût est nul (c'est juste une convention d'unités) et ça évite d'inventer un système de coordonnées incompatible avec 30 ans d'écosystème.

---

## Sources principales

- LEGO — [How we design our building instructions](https://www.lego.com/en-us/service/help-topics/article/how-we-design-our-building-instructions) ; [LEGO Builder app](https://www.lego.com/en-us/builder-app) ; [aide Builder 3D](https://www.lego.com/en-us/service/help-topics/article/lego-builder-app-3d-building-instructions) ; brevets [US8374829](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8374829) et [US9821242](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9821242) (LEGO), [US11393153](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11393153) (Texas A&M) — analyse complète : `legal/PATENTS_ANALYSIS.md`
- UX — [UXmatters : Inspirations from a LEGO Instructional Booklet](https://www.uxmatters.com/mt/archives/2020/12/inspirations-from-a-lego-instructional-booklet.php)
- LDraw — [File Format Specification](https://ldraw.org/article/218.html) ; [Wikipedia](https://en.wikipedia.org/wiki/LDraw) ; [wiki MPD](https://wiki.ldraw.org/wiki/MPD) ; [métacommandes non officielles](https://wiki.ldraw.org/index.php?title=List_of_Known_Unofficial_META_Commands) ; [LPub3D](https://trevorsandy.github.io/lpub3d/) ([métacommandes](https://trevorsandy.github.io/lpub3d/assets/docs/lpub3d/metacommands.html))
- LXF/LXFML — [fileinfo.com](https://fileinfo.com/extension/lxf) ; [wiki.ldraw.org/LXF](https://wiki.ldraw.org/wiki/LXF) ; [Rebrickable : Guide to LDD](https://rebrickable.com/help/guide-to-lego-digital-designer/)
- Studio — [Exporting Instructions](https://studiohelp.bricklink.com/hc/en-us/articles/5628123432215-Exporting-Instructions) ; [Exporting to other formats](https://studiohelp.bricklink.com/hc/en-us/articles/6502197862679-Exporting-to-other-formats) ; [Step List](https://studiohelp.bricklink.com/hc/en-us/articles/5626298196247-Step-List) ; [Step Editor](https://studiohelp.bricklink.com/hc/en-us/articles/5626973531287-Step-Editor) ; [Divide into steps](https://studiohelp.bricklink.com/hc/en-us/articles/7123910550039-Automatic-instructions-Divide-into-steps) ; [guide Open L-Gauge](https://open-l-gauge.eu/making-building-instructions-in-studio/)
- Rebrickable — [Buying Premium MOCs](https://rebrickable.com/help/buying-premium-mocs/) ; [Selling Premium MOCs](https://rebrickable.com/help/selling-premium-mocs/) ; [File Types](https://rebrickable.com/help/types-of-moc-building-instructions/) ; [Fees](https://rebrickable.com/help/mocs-fees/)
- Recherche — [Agrawala et al., SIGGRAPH 2003](https://graphics.stanford.edu/papers/assembly_instructions/assembly.pdf) ; [Ono et al., LEGO Builder (manuel auto)](https://www.researchgate.net/publication/285670439_Paper_LEGO_Builder_Automatic_Generation_of_LEGO_Assembly_Manual_from_3D_Polygon_Model) ; [CAD 2015, photos → instructions (legograph)](https://www.sciencedirect.com/science/article/abs/pii/S0010448515001037) ; [Legolization, SIGGRAPH Asia 2015](http://www.cmlab.csie.ntu.edu.tw/~forestking/research/SIGA15-Legolization/) ; [StableLego (arXiv 2402.10711)](https://arxiv.org/pdf/2402.10711) ; [LegoGPT (arXiv 2505.05469)](https://arxiv.org/html/2505.05469v1) + [page projet](https://avalovelace1.github.io/LegoGPT/)
- Comparable produit — [Brickit](https://brickit.app/)
