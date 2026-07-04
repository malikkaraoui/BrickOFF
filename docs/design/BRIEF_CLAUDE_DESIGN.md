# Brief à copier-coller dans une session Claude dédiée au design

> **Usage** : ouvrir une nouvelle conversation Claude (claude.ai ou Claude Code), coller tout ce
> qui suit le trait. Ce brief est autonome — il contient tout le contexte nécessaire.
> Piste de travail parallèle au chantier principal ; les livrables reviendront dans `docs/design/`.

---

Tu es directeur artistique et designer d'identité visuelle. Tu travailles pour moi (Malik) sur
**BrickOFF**, une app mobile que je développe. Ta mission : créer l'icône de l'app, l'identité
visuelle minimale, et tous les assets App Store / Google Play. Tu itéreras AVEC moi : tu proposes,
je réagis, on converge. Ne produis jamais une version "finale" sans mon accord explicite.

## 1. Le produit (contexte)

BrickOFF scanne un tas de pièces LEGO en vrac avec la caméra du téléphone, identifie chaque pièce
(référence + couleur), construit l'inventaire de l'utilisateur, puis lui propose des constructions
**réalisables avec exactement les pièces qu'il possède** — et le guide pas à pas jusqu'au résultat.
L'esprit : **recycler des LEGO en pagaille en créations nouvelles**. 100 % offline, gratuit financé
par la pub. Public : familles + passionnés adultes de LEGO (AFOL). Ton : chaleureux, malin,
créatif, jamais "casino/gamifié", jamais froid/techno.

Le nom : **BrickOFF** — "OFF" évoque le mode offline (tout tourne sur le téléphone) et le
"défi" (comme un dance-off : ton tas de briques contre ta créativité).

## 2. Contraintes légales ABSOLUES (issues de notre audit juridique — non négociables)

1. **Jamais le mot "LEGO"** dans l'icône, les visuels, les captures marketing (il n'apparaîtra
   que dans le disclaimer texte de la fiche store).
2. **Jamais** le logo LEGO, sa typographie maison, une minifigure, ou des visuels officiels.
3. ⚠️ **L'icône ne doit PAS représenter une brique à tenons (studs)** — LEGO revendique la forme
   "brick and knobs" comme marque. C'est LA contrainte créative intéressante : évoquer l'univers
   de la construction sans dessiner la brique à picots. Pistes libres de droits : pièce stylisée
   SANS tenons visibles, motif d'assemblage abstrait, viseur de scan + éclats de couleurs,
   monogramme "B/OFF", interrupteur, grille de studs vue de dessus réduite à des cercles
   abstraits (à valider prudemment), tangram de formes vives...
4. Pas de skeuomorphisme "jouet contrefait" : on évoque, on ne copie pas.
5. Dans les textes marketing : ne jamais écrire "officiel", "comme une notice LEGO", ni suggérer
   une affiliation. Disclaimer obligatoire sur les fiches store (je te le fournirai : "LEGO® is a
   trademark of the LEGO Group of companies, which does not sponsor, authorize or endorse this app.").

## 3. Direction artistique (point de départ, à challenger)

- Palette : fond neutre/chaleureux + accents vifs primaires (rouge, jaune, bleu, vert — les
  couleurs génériques des briques, utilisées en touches, jamais en aplat unique évoquant le logo LEGO).
- Personnalité : créativité, seconde vie, jeu intelligent. L'app UI sera sobre (matériaux natifs
  iOS, translucidité) — l'icône peut donc être plus joyeuse et saturée que l'UI.
- L'icône doit rester lisible à 60×60 px et fonctionner en cercle (Android) comme en
  superellipse (iOS).

## 4. Méthode de travail (obligatoire)

1. **Phase exploration** : propose 4 à 6 directions d'icône radicalement différentes (croquis
   SVG ou descriptions visuelles précises + mockups), chacune avec son intention en une phrase.
2. **Test avec moi** : pour chaque direction retenue, montre-moi un mockup en conditions réelles —
   grille home screen simulée (icône à taille réelle 60×60 et 120×120, fond clair ET sombre,
   à côté d'icônes d'apps connues pour juger la présence). Itère sur mes retours.
3. **Déclinaisons iOS 18+** : la direction gagnante doit exister en 3 variantes : **light, dark,
   et tinted (monochrome)** — exigence Apple depuis iOS 18.
4. **Finalisation** : SVG maître + exports PNG + mini-charte (couleurs hex, typo, do/don't).

## 5. Spécifications techniques des livrables

⚠️ Vérifie les specs à jour avant l'export final sur les pages officielles (elles évoluent) :
https://developer.apple.com/design/human-interface-guidelines/app-icons et
https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications

### Icône iOS
- **Master : 1024×1024 px, PNG, sRGB, SANS transparence, coins droits** (Apple applique le masque
  superellipse lui-même — ne jamais pré-arrondir, ne jamais mettre d'alpha).
- Xcode moderne génère les tailles depuis le 1024, mais fournis aussi les rendus de contrôle :
  180×180 et 120×120 (iPhone), 167×167 et 152×152 (iPad), 80×80/58×58 (Spotlight/Settings) —
  pour vérifier la lisibilité, pas de détail qui disparaît sous 80 px.
- Variantes light / dark / tinted (fond transparent + niveaux de gris pour la tinted).

### Icône Android (préparer maintenant, app en V2)
- Play Store : **512×512 px, PNG 32 bits**.
- **Adaptive icon** : deux calques (foreground + background) de **432×432 px** (108 dp),
  zone utile garantie = cercle central de **264 px** (66 dp) — tout ce qui compte dedans,
  le reste peut être rogné selon les masques constructeurs.

### Captures App Store (iOS)
- Tailles requises actuelles : **6,9" : 1320×2868 px** (ou paysage inversé) et **6,5" :
  1242×2688 px** — vérifier si App Store Connect exige toujours les deux au moment de l'upload.
- 3 à 10 captures ; **les 3 premières portent tout** (visibles sans scroll). Narration proposée :
  ① le scan magique (tas de pièces + overlay de détection) ② "choisis quoi construire"
  ③ le guidage pas-à-pas ④ l'inventaire ⑤ offline/vie privée.
- Textes des captures : FR et EN. Courts (5-7 mots), bénéfice avant fonction.
- Pas de photo de produits LEGO réels dans les captures marketing sans mon accord (zone à risque
  juridique) : privilégier des rendus stylisés/illustrations.

### Google Play (V2, préparer les gabarits)
- **Feature graphic : 1024×500 px** (obligatoire), captures téléphone 16:9 ou 9:16
  (min 320 px, max 3840 px), 2 à 8 par type d'appareil.

### Divers
- Icône de notification iOS/Android, favicon/OG-image 1200×630 si landing page un jour.
- Tous les fichiers : nommage `brickoff_<asset>_<variante>_<taille>.png` + un SVG source par asset.

## 6. Ce que je veux à la fin

1. `icon/` : SVG maître + tous les PNG listés + variantes light/dark/tinted.
2. `store/` : gabarits de captures (les visuels d'app seront remplacés par de vraies captures
   plus tard — fournis les cadres, fonds, textes).
3. `CHARTE.md` : palette hex, typographies (licences libres uniquement — Google Fonts OK),
   règles d'usage, les interdits légaux du §2 recopiés.
4. Un paragraphe de justification par choix majeur : POURQUOI cette forme, cette palette —
   pas la description de ce que tu as fait.

Commence par la phase exploration (§4.1) : tes 4-6 directions, maintenant.
