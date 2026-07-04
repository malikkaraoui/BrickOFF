# Licence des données Rebrickable — vérification pour BrickOFF

> **Jalon 0.1 (CH-0).** Vérification effectuée le **4 juillet 2026** sur les pages en ligne de rebrickable.com. Toutes les citations ci-dessous sont reproduites verbatim (en anglais) depuis les pages consultées ce jour-là.

---

## Verdict

**AUTORISÉ AVEC CONDITIONS** — l'usage commercial des snapshots CSV est explicitement permis (« any purpose »), l'attribution est *recommandée mais non obligatoire* ; les conditions à respecter sont : (1) télécharger les snapshots via la page Downloads et non par scraping/automatisation, (2) exclure toute donnée ou image de MOC, (3) ne jamais utiliser de contenu Rebrickable pour entraîner un modèle d'IA, (4) traiter les images de sets/pièces comme de la propriété intellectuelle LEGO (régime distinct des CSV).

---

## Pages consultées (4 juillet 2026)

| Page | URL | Statut |
|---|---|---|
| Page API | https://rebrickable.com/api/ | Consultée — ne contient plus de section « Terms of Use » propre ; renvoie vers la page Downloads et vers les ToS générales |
| Page Downloads (snapshots CSV) | https://rebrickable.com/downloads/ | Consultée — contient la clause d'usage des fichiers |
| Terms of Service | https://rebrickable.com/terms/ | Consultée — sections 5 (Automation) et 6 (Legal Stuff) pertinentes |

Note : l'ancienne URL de ToS (`/help/terms-of-service/`) renvoie une 404 ; le document officiel est désormais à `https://rebrickable.com/terms/`.

---

## (a) Usage commercial des snapshots CSV : **AUTORISÉ**

**Citation** — https://rebrickable.com/downloads/ (consulté le 2026-07-04) :

> "The LEGO Parts/Sets/Colors and Inventories of every official LEGO set in the Rebrickable database is available for download as csv files here. These files are automatically updated daily."
>
> "**You can use these files for any purpose.** If you publish any articles please let us know and maybe we can help promote it."

**Citation** — https://rebrickable.com/terms/ , §5.1 « API Usage » (consulté le 2026-07-04) :

> "The Rebrickable API may be used for **any purpose, including commercial**. However, it would be highly appreciated if you provide a statement that the data is sourced from Rebrickable. The API is provided for ease of access to LEGO and Rebrickable catalog data. Alternatively, you can download the full catalog via the Downloads page."

**Interprétation.** La page Downloads accorde une permission sans réserve (« any purpose ») sur les fichiers CSV, sans exclusion de l'usage commercial. Les ToS confirment la logique : le §5.1 autorise explicitement l'usage commercial de l'API et présente les Downloads comme le canal *alternatif et équivalent* pour obtenir le catalogue complet (« Alternatively, you can download the full catalog via the Downloads page »). Il serait incohérent que le canal recommandé pour le volume soit plus restrictif que l'API. Une app commerciale financée par la publicité entre donc dans « any purpose ».

---

## (b) Attribution : **NON OBLIGATOIRE, mais recommandée — nous la ferons**

**Citation** — https://rebrickable.com/terms/ , §5.1 (consulté le 2026-07-04) :

> "However, it would be **highly appreciated** if you provide a statement that the data is sourced from Rebrickable."

**Citation** — https://rebrickable.com/downloads/ (consulté le 2026-07-04) :

> "If you publish any articles please let us know and maybe we can help promote it."

**Interprétation.** Le vocabulaire est celui de la demande de courtoisie (« highly appreciated », « please let us know »), pas de l'obligation contractuelle (« must », « required »). Aucune forme exacte d'attribution n'est imposée. Nous adoptons néanmoins l'attribution comme **engagement de bonne pratique** (voir Actions), car elle coûte peu, protège la relation avec Rebrickable et correspond à ce que la formulation suggère : *« a statement that the data is sourced from Rebrickable »*.

---

## (c) Redistribution — embarquer les données dans une app distribuée au public : **AUTORISÉ (par portée de « any purpose »), non nommé explicitement**

**Citations pertinentes** (2026-07-04) :

- Downloads : > "You can use these files for **any purpose**."
- ToS §5.2 « Images » : > "Images of Sets, Parts and Minifigs may be used **on external websites or apps**. […] However, you may not use MOC images for any purpose."
- Page API (https://rebrickable.com/api/) : > "Rebrickable provides a number of API/Web Services to assist developers **build their own websites or apps** which use the Rebrickable database." et > "If you just want a copy of the entire LEGO catalog database, or need to extract high volumes of data please use the Downloads page instead."

**Interprétation.** Aucune clause ne restreint la redistribution des données CSV ; « any purpose » couvre littéralement l'inclusion d'un extrait de la base dans un binaire d'app. Deux indices contextuels renforcent cette lecture : (1) le §5.2 des ToS envisage explicitement l'usage du contenu Rebrickable « on external websites or apps » ; (2) la page API décrit l'écosystème attendu comme des développeurs qui « build their own websites or apps which use the Rebrickable database », et oriente les besoins de volume vers les Downloads. Le mot « redistribution » n'apparaît nulle part — ni pour l'autoriser ni pour l'interdire — d'où le classement « autorisé avec conditions » plutôt que « autorisé » sec, et l'email de confirmation ci-dessous (recommandé, non bloquant).

**Limites explicites qui s'appliquent à nous :**

1. **Données/Images MOC exclues.** ToS §5.2 : *"you may not use MOC images for any purpose."* et §6.1 : *"MOCs - these materials are owned by the original designer […] You may not use these images for your own purposes."* → Le snapshot embarqué ne doit contenir **que** le catalogue officiel (sets, parts, colors, inventories, minifigs) — c'est justement tout ce que contiennent les CSV de la page Downloads : *"This database stores only official LEGO items - Sets, Parts and Minifigs (no B-Models, Sub-Sets, MOCs)"* (Downloads, 2026-07-04).
2. **Interdiction d'entraînement IA.** ToS §5.3 : *"**No Rebrickable content may be used in the training of AI models.**"* → Les CSV/images Rebrickable ne doivent **jamais** alimenter l'entraînement de nos modèles de détection/classification (chantiers ML). Embarquer les données comme base de consultation dans l'app n'est pas de l'entraînement ; la frontière doit rester étanche et documentée.
3. **Images = PI LEGO, régime séparé.** ToS §6.1 : *"LEGO-owned IP - images such as Sets/Parts/Minifigs/Instructions are LEGO IP. You may use them, but their usage must adhere to the LEGO copyright rules."* → Si l'app embarque des images de pièces/sets, la conformité relève du jalon 0.2 (Fair Play LEGO), pas de la seule permission Rebrickable. Les CSV eux-mêmes ne contiennent pas d'images (seulement des URLs).

---

## (d) Limites de volume / fréquence

**Citations** (2026-07-04) :

- Downloads : > "These files are automatically updated daily. If you need more details, you can use the API which provides **real-time data, but has rate limits** that prevent bulk downloading of data."
- ToS §5.3 « Scrapers/Bots » : > "**Under no circumstances are you allowed to use automation tools to download data or to automate traffic**, doing so will get your IP and/or account banned."

**Interprétation.**

- **Snapshots CSV** : aucune limite de volume — c'est le canal *prévu* pour le volume. Régénérés quotidiennement côté Rebrickable (vérifié : les 12 fichiers étaient horodatés « July 4, 2026, 7:12 a.m. » le jour de la consultation).
- **API** : rate-limitée, explicitement inadaptée au bulk. Pour BrickOFF (snapshot embarqué), l'API ne sert au plus qu'à des vérifications ponctuelles.
- **Point de vigilance réel** : le §5.3 interdit les « automation tools to download data ». Un cron qui re-télécharge les CSV chaque nuit serait défendable (fichiers publiés pour le téléchargement en masse) mais s'expose à une lecture littérale de la clause. Notre besoin est faible (rafraîchir le snapshot à chaque release, soit quelques téléchargements par mois) : un téléchargement **manuel ou déclenché manuellement** à chaque mise à jour du snapshot nous place hors de toute zone grise.

---

## Point résiduel d'ambiguïté et email de confirmation (recommandé, non bloquant)

L'unique zone non nommée explicitement est la **redistribution embarquée** (les données vivent dans le binaire de l'app, hors ligne, chez des millions d'utilisateurs potentiels). Notre lecture (« any purpose » la couvre) est solide, mais une confirmation écrite de Rebrickable vaudrait preuve définitive. Contact : formulaire https://rebrickable.com/contact/ (lien « Contact Us » en pied de page).

**Brouillon d'email (anglais) :**

> Subject: Confirmation of permitted use — embedding Downloads CSV data in a commercial offline mobile app
>
> Hi Rebrickable team,
>
> We are building a mobile app for LEGO fans that identifies parts and suggests buildable sets. The app works fully offline: at build time we take a filtered extract of the CSV files from your Downloads page (sets, parts, colors, inventories — no MOC data), convert it into a local SQLite database, and ship that database inside the app binary. The app is free and ad-supported (commercial). We would refresh the embedded snapshot manually with each app release (a few downloads per month at most).
>
> Your Downloads page states "You can use these files for any purpose", and section 5.1 of your Terms of Service allows commercial use. We would like to confirm our reading on two points:
>
> 1. Does "any purpose" cover redistributing an extract of the catalog data embedded inside a commercial app distributed to the public?
> 2. Is manually downloading the CSV files a few times per month, tied to our release cycle, an acceptable usage pattern under section 5.3 (Scrapers/Bots)?
>
> We will of course display a clear attribution in the app ("Catalog data sourced from Rebrickable.com") with a link to your site, and we will never use any Rebrickable content for AI model training, per your Terms.
>
> Thank you for maintaining such a great resource.
>
> Best regards,
> [Nom] — BrickOFF

**Plans B si la réponse était négative (peu probable) :**

1. **Mode connecté à la première ouverture** : l'app télécharge elle-même le snapshot CSV public depuis rebrickable.com (ou notre proxy le renvoyant à l'identique) au premier lancement, au lieu de l'embarquer dans le binaire — la « redistribution » disparaît, l'usage redevient un simple téléchargement par l'utilisateur final. Perte : première ouverture non offline.
2. **Base maison réduite** : reconstruire une base minimale (numéros de sets, noms de pièces, couleurs) à partir de sources factuelles non protégées — les données factuelles brutes (un set contient X pièces de couleur Y) sont peu protégeables en soi ; coût élevé de constitution et de maintenance.
3. **Accord commercial / partenariat** : négocier une licence écrite dédiée avec Rebrickable Pty Ltd (éventuellement adossée à leur programme d'affiliation, lien « Affiliates » en pied de page), qui sécuriserait aussi les images.

---

## Actions concrètes pour BrickOFF

1. **Attribution dans l'app** (écran Settings/À propos) : « Catalog data sourced from Rebrickable.com » + lien vers https://rebrickable.com — répond à la demande du §5.1 des ToS.
2. **Pipeline de snapshot** : téléchargement des CSV **déclenché manuellement** à chaque release depuis https://rebrickable.com/downloads/ (pas de cron ni de scraping) ; consigner la date du snapshot et l'afficher dans l'app (« Données du catalogue : snapshot du JJ/MM/AAAA »).
3. **Périmètre des données embarquées** : uniquement les CSV du catalogue officiel (themes, colors, part_categories, parts, part_relationships, elements, sets, minifigs, inventories, inventory_parts, inventory_sets, inventory_minifigs). **Aucune donnée ni image de MOC.**
4. **Garde-fou ML (à propager vers le jalon 0.3 et les chantiers ML)** : interdiction absolue d'utiliser du contenu Rebrickable (CSV, images, textes) dans l'entraînement des modèles — ToS §5.3. Le dataset d'entraînement doit provenir d'autres sources (LEGOBricks/HF, photos maison).
5. **Images de pièces/sets** : si l'app en embarque, elles relèvent de la PI LEGO (ToS §6.1) → à instruire au jalon 0.2 (Fair Play), indépendamment de la permission Rebrickable. Les CSV seuls ne posent pas ce problème.
6. **Envoyer l'email de confirmation** ci-dessus via https://rebrickable.com/contact/ — recommandé pour verrouiller le point « redistribution embarquée » ; n'est pas bloquant pour démarrer les chantiers data.
7. **Re-vérifier les ToS avant la release publique** (elles peuvent changer ; la présente vérification date du 2026-07-04).
