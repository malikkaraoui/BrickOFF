# Analyse de liberté d'exploitation — Brevets « génération d'instructions de montage »

> **Statut : analyse préliminaire, non normatif.** Réalisée le **2026-07-04** (sources : Google Patents, Registre européen des brevets — register.epo.org, données consultées le jour même ; le registre EPO indiquait « Database last updated on 03.07.2026 »).
>
> ⚠️ **DISCLAIMER — analyse préliminaire par IA, ne remplace pas un conseil en propriété industrielle — relecture professionnelle recommandée avant l'engagement V1.5.** Cette analyse porte sur les revendications telles que délivrées, ne couvre pas la doctrine des équivalents, les demandes divisionnaires/continuations en cours d'examen, ni une recherche d'antériorité exhaustive. Deux des familles analysées portent un indicateur de **litige** (base Darts-ip) : LEGO fait valoir ses brevets en justice, la prudence s'impose.
>
> **Positionnement produit (rappel)** : démarche de *design-around* — on identifie ce que couvrent exactement les revendications pour concevoir autour, pas pour copier. Un brevet n'est contrefait que si **TOUS les éléments d'au moins une revendication** sont reproduits (règle dite « all elements rule », identique en substance en droit US et européen).

---

## 1. Tableau de synthèse

| Brevet | Titulaire | Statut (2026-07-04) | Expiration | Ce que couvre la revendication 1 (résumé) | Risque pour A1 (blueprints éditoriaux) | Risque pour V3 (génération) |
|---|---|---|---|---|---|---|
| **US8374829B2** | LEGO A/S | **Actif** (US) | **2028-05-18** (ajustée PTA) | Génération **automatique** d'instructions par **déconstruction algorithmique** d'un modèle 3D (processus itératif, sous-assemblages candidats, force de connexion) | **Nul** — aucun élément reproduit : les étapes sont écrites par un humain, rien n'est déconstruit | **Faible** — à risque seulement si V3 dérive les étapes par désassemblage du modèle ; expire de toute façon **avant/pendant V3** |
| ↳ EP2135222B1 (même famille) | LEGO A/S | **Actif, en vigueur en FRANCE** (annuité 19 payée le 2026-03-20) | **2028-03-14** | Identique en substance à US claim 1 | Nul (idem) | Faible (idem) — expire 03/2028 |
| **US9821242B2** | LEGO A/S | **Actif** (US) ; famille marquée **litige** (Darts-ip) | **2032-07-12** (ajustée PTA) | Guidage **en réalité augmentée** : caméra filme le **modèle physique partiel**, détection position/orientation, superposition de la pièce suivante sur l'image captée | **Nul si et seulement si** aucune superposition AR sur l'image caméra du modèle en cours — c'est le cas d'A1 (rendu 3D synthétique) | **Nul pour la génération elle-même** ; **élevé** si on ajoute un mode « guidage AR » avant 2032 |
| ↳ EP2714223B1 (même famille) | LEGO A/S | **Actif, en vigueur en FRANCE** (annuité 14 payée, opt-out JUB) | **2032-05-22** | Idem (revendication 1 EP = « toy construction system » avec caméra + superposition) | Nul (idem) | Idem — vaut aussi pour le marché français |
| **US11393153B2** | **Texas A&M University System** (⚠️ PAS LEGO) | **Actif** (US) | **2040-05-29** | Technique de rendu d'**occlusion en AR** : double fonction de rendu (fil de fer + masque occlusif transparent), bascule à la détection de fin d'étape | **Nul** — aucune AR dans A1 | **Nul en UE** (pas d'équivalent EP/FR) ; aux US, seulement si on implémente **cette technique précise** d'occlusion AR |

**Lecture d'ensemble** : les trois brevets couvrent trois choses différentes — (1) *calculer* des étapes depuis un modèle 3D arbitraire, (2) *guider* en AR sur l'image caméra du montage en cours, (3) une *technique de rendu* d'occlusion AR. **L'approche A1 ne fait aucune des trois.**

---

## 2. Analyse détaillée par brevet

### 2.1 US8374829B2 — « Automatic generation of building instructions for building element models »

**Données bibliographiques** (source : Google Patents, événements légaux)
- Titulaire : LEGO A/S. Déposé le **2009-09-15** (US 12/584,951), avec priorité revendiquée du **2007-03-16** (US 11/724,915, dont il est la continuation). Délivré le **2013-02-12**.
- Statut : **Active**. Expiration : **2028-05-18** — « Adjusted expiration » selon Google Patents, soit la base de 20 ans à compter du dépôt parent effectif (2027-03-16) **+ ajustement PTA** (~14 mois).
- Famille : **EP2135222B1** (dépôt PCT/EP2008/053124 du **2008-03-14**, délivré 2010-08-25), plus CN, KR, CA, JP, MX, BR, HK.
- **Statut France** : EP2135222B1 désignait FR ; le registre EPO ne montre de déchéance que dans les petits États (CY, CZ, EE, HR, HU, LT, LV, MT, PL, PT, RO, SI, SK, BG, NO, GR, IS, IE, LU, MC) ; les événements post-délivrance montrent le **paiement de l'annuité française année 19 le 2026-03-20** (code PLFP/PGFP) → **en vigueur en France jusqu'au 2028-03-14** (20 ans du dépôt EP, pas de PTA en droit européen). LEGO a enregistré un **opt-out de la Juridiction Unifiée du Brevet** (2023) et la famille porte un indicateur de **litige** (Darts-ip, famille 39473765) : ce brevet est activement géré et défendu.

**Revendications indépendantes** : claims 1 et 39 (les claims 35, 36, 38 — système / programme / signal — dépendent du procédé de la claim 1).

Claim 1 (verbatim, découpée par élément — TOUS doivent être reproduits pour contrefaire) :

> "1. A computer-implemented method of generating building instructions for a building element model, [...] the building instructions being indicative of a sequential order of construction steps [...]; the method comprising:
> **(a)** determining, from a digital representation of the building element model at least one sequence of **deconstruction steps** for at least partially deconstructing the building element model [...];
> **(b)** determining at least one construction step of the sequential order of construction steps **based on the at least one plurality of deconstruction steps**;
> **(c)** wherein determining the sequence of deconstruction steps comprises performing an **iterative process** [...]: obtaining a previous part-model resulting from a previous iteration; determining at least one building element to disconnect from the previous part-model [...];
> **(d)** determining a **set of candidate sub-assemblies** of the previous part-model [...] selecting the candidate sub-assemblies according to a second set of selection criteria; and wherein at least one of the second set of selection criteria includes determining a **connection strength** of the connection of one or more of the candidate sub-assemblies with the previous part-model;
> **(e)** selecting, according to a first set of predetermined selection criteria, either a single building element or one of the determined set of candidate sub-assemblies **to be disconnected** [...]."

Claim 39 (variante « sens construction ») — verbatim abrégé :

> "39. A computer-implemented method of generating building instructions [...] comprising performing an iterative process [...]: obtaining a sequential order of construction steps resulting from a previous iteration [...]; **determining a candidate construction step** [...]; determining, from a digital representation of the building element model, at least one sequence of deconstruction steps [...] **so as to determine whether the building element model is deconstructable** [...]; if [...] deconstructable [...], **appending the determined candidate subsequent construction step** [...]."

**Ce que ça couvre exactement** : un algorithme qui, partant d'un **modèle numérique fini**, **calcule** l'ordre des étapes — soit en le désassemblant itérativement (claim 1 : « peler l'oignon » algorithmique, avec sous-assemblages candidats notés par force de connexion), soit en construisant l'ordre pas à pas et en validant chaque étape candidate par un test de **déconstructibilité** (claim 39). L'objet breveté est le *calcul de la séquence*, pas les instructions elles-mêmes ni leur affichage.

**Analyse de contournement — A1, élément par élément** :

| Élément de la claim 1 | Présent dans A1 ? | Pourquoi |
|---|---|---|
| (a) déterminer des étapes de **déconstruction** depuis une représentation numérique | ❌ | A1 ne déconstruit rien : le champ `steps` du blueprint est **écrit par un auteur humain** dans l'outil éditorial (cf. `docs/plan/13_GENERATION_FIGURES.md` : « les steps sont dans le blueprint ») |
| (b) déduire les étapes de construction des étapes de déconstruction | ❌ | Aucune dérivation : les étapes existent avant toute exécution |
| (c) processus itératif sur des part-models | ❌ | Le solveur A1 itère sur des **slots d'inventaire** (choix d'alternatives de pièces), jamais sur des états partiels du modèle pour en retirer des pièces |
| (d) sous-assemblages candidats + critère de **force de connexion** | ❌ | Inexistant ; aucune notion de force de connexion dans A1 |
| (e) sélection d'un élément/sous-assemblage à déconnecter | ❌ | Inexistant |

**Conclusion US8374829/EP2135222 pour A1 : risque nul.** Aucun des cinq éléments n'est reproduit — et l'élément-cadre lui-même (« generating building instructions ») est discutable pour A1, puisque l'app ne *génère* pas d'instructions : elle **rend** des instructions préexistantes après substitution de pièces dans des slots. Même la validation éditoriale recommandée (connexité/stabilité de chaque préfixe, R3 de `docs/research/INSTRUCTIONS_FORMATS.md`) ne tombe pas sous la claim 39 : elle valide des étapes **déjà écrites par l'auteur** par des critères de connectivité/appui, elle ne *détermine* pas d'étapes candidates par test de déconstructibilité du modèle final. Par précaution, ne pas implémenter dans l'outil éditorial un bouton « générer les étapes automatiquement par désassemblage » avant mars 2028 (EP) / mai 2028 (US).

**Pour V3** : c'est le brevet le plus proche du sujet « génération d'instructions » — mais il **expire le 2028-03-14 (France) et le 2028-05-18 (US)**, très probablement avant ou pendant le développement de V3 (spike A3 conditionné, cf. doc 13). Si V3 démarrait avant : voir stratégie §4.

---

### 2.2 US9821242B2 — « Generation of building instructions for construction element models »

**Données bibliographiques**
- Titulaire : LEGO A/S. Priorité **2011-05-23** (DK PA 2011 70255), dépôt PCT **2012-05-22** (PCT/EP2012/059471 → US 14/119,534), délivré **2017-11-21**.
- Statut : **Active**. Expiration US : **2032-07-12** (« Adjusted expiration » = 2032-05-22 + PTA ~51 jours).
- ⚠️ Le titre est trompeur : malgré « Generation of building instructions », c'est un brevet de **guidage en réalité augmentée**, pas de calcul d'étapes.
- Famille : **EP2714223B1** (délivré 2015-07-01), CA (délivré), CN, JP (délivrés), KR, BR, MX, DK, ES, PL + divisionnaires de traduction. **Indicateur de litige** (Darts-ip, famille 46124379).
- **Statut France** : EP2714223B1 — déchéances uniquement dans les petits États (AL, BG, CY, CZ, EE, GR, HR, HU, IS, LT, LV, MC, MK, MT, PT, RO, RS, SI, SK, SM) ; **annuités françaises payées sans interruption (années 5, 6, 7… puis année 14 payée le 2025-05-28)**, maintenu aussi en DE, GB, ES, IT, NL, PL, DK, BE, AT, CH, FI, NO, SE, TR. Opt-out JUB (2023). → **En vigueur en France jusqu'au 2032-05-22.**

**Revendication indépendante US** : claim 1 (les claims 22, 24, 25 — système / programme / signal — y renvoient).

Claim 1 (verbatim, découpée par élément) :

> "1. A computer-implemented method for generating building instructions for constructing a **physical** toy construction model [...]; the method comprising:
> **(a)** **capturing, by a digital camera, an image of a partial physical toy construction model** constructed from a subset of the toy construction elements;
> **(b)** processing, by a digital processor, the captured image to **detect at least a position and an orientation of the partial toy construction model**;
> **(c)** determining a set of subsequent construction elements from a digital representation of the partial physical toy construction model and from a **stored data structure indicative of a plurality of sequences of optional construction steps**, each sequence resulting in one of a set of **alternative construction models** constructable from the set of toy construction elements;
> **(d)** displaying digital representations of the set of alternative construction elements in a user interface on a display;
> **(e)** identifying a **user selection** indicative of at least one of the set of alternative subsequent construction elements [...];
> **(f)** responsive to the detected position and orientation [...], displaying [...] one or more **composite images comprising the captured images of the partial physical toy construction model having superimposed thereon the digital representations** of [...] the selected subsequent construction elements connected thereto."

La revendication 1 de l'EP correspondante (EP2714223B1) est un peu plus large (revendication de *système* sans l'élément (c) de structure de données) mais garde le même cœur : « *capture an image of a partial toy construction model* », « *detect at least a position and an orientation of the partial toy construction model* », « *display [...] a composite image comprising the captured image having superimposed an image of at least the selected subsequent construction element* » (claims 1 et 11 EP, verbatim).

**Ce que ça couvre exactement** : la boucle AR « filme ton montage en cours → l'app le reconnaît et le localise → elle superpose la ou les pièces suivantes sur l'image caméra ». C'est le mode d'instruction « Instructions PLUS/AR » de LEGO.

**Analyse de contournement — A1, élément par élément** :

| Élément | Présent dans A1 ? | Pourquoi |
|---|---|---|
| (a) capture caméra du **modèle physique partiel** en cours de montage | ❌ | Dans BrickOFF, la caméra sert **une seule fois, en amont**, à scanner le **tas de pièces en vrac** pour l'inventaire (VISION.md). Pendant le guidage, aucune capture du montage en cours |
| (b) détection position/orientation du modèle partiel | ❌ | Inexistant |
| (c) structure de données de séquences d'étapes optionnelles → modèles alternatifs | ⚠️ partiellement analogue | Le blueprint avec slots/alternatives y ressemble de loin — mais cet élément seul ne suffit pas : la contrefaçon exige TOUS les éléments, dont (a), (b), (f) |
| (d)-(e) affichage d'alternatives + sélection utilisateur | ⚠️ partiel | L'utilisateur choisit un blueprint, pas des « éléments suivants alternatifs » pièce à pièce en cours de montage |
| (f) **image composite** : image captée + pièces superposées | ❌ | Le rendu V1.5 est un rendu 3D **entièrement synthétique** depuis les placements du blueprint (R6 de INSTRUCTIONS_FORMATS.md), jamais une superposition sur flux caméra |

**Conclusion US9821242/EP2714223 pour A1 : risque nul**, à une condition d'architecture ferme : **le guidage pas-à-pas ne superpose jamais rien sur une image caméra du modèle en cours de construction**. Les éléments (a), (b) et (f) — le cœur de la revendication — sont absents d'A1. C'est le brevet le plus dangereux du lot pour la roadmap car il est **en vigueur en France ET aux US jusqu'en 2032** et sa famille a déjà été **litigée** : toute feature future type « pointe ta caméra sur ton montage et on te montre la pièce suivante en AR » (ghost mode AR, vérification de progression par caméra…) devrait être gelée jusqu'en mai 2032 ou passer par un avis de CPI.

**Pour V3** : la génération de structures (A3) elle-même ne touche aucun élément de ce brevet ; seul un éventuel mode de **guidage AR** serait concerné (mêmes conditions que ci-dessus).

---

### 2.3 US11393153B2 — « Systems and methods performing object occlusion in augmented reality-based assembly instructions »

**Données bibliographiques**
- Titulaire : **The Texas A&M University System** — ⚠️ **correction** : `docs/research/INSTRUCTIONS_FORMATS.md` § 1.1 l'attribue implicitement à LEGO ; c'est inexact (vérifié : « Application filed by Texas A&M University System », réassignation 2021 à Texas A&M). À corriger dans le doc de recherche.
- Déposé le **2020-05-29** (US 16/887,485, priorité même jour), délivré **2022-07-19**.
- Statut : **Active**. Expiration : **2040-05-29** (« Anticipated expiration » = dépôt + 20 ans, pas de PTA signalé par Google Patents).
- Famille : **aucun équivalent EP/FR** — dépôt US uniquement (aucune demande WO/EP dans la famille selon Google Patents). **Sans effet sur une distribution UE/France** ; ne concernerait que l'App Store US.

**Revendications indépendantes** : claims 1 (méthode occlusion par objet physique), 7 (méthode occlusion/saisie par une main), 9 (système). Cœur commun, verbatim (claim 1) :

> "1. A method for performing object occlusion in augmented reality-based step-by-step instructions [...]: capturing an image of a physical item; determining a location and an orientation of a first virtual item in the image with an **augmented reality registration function**; generating an augmented reality image [...] a rendering of the first virtual item [...] using only a **first rendering function** [...] and a rendering of a second virtual item [...] using only a **second rendering function**, wherein the first rendering function is a **wireframe rendering function** [...] and the second rendering function is an **occlusive and transparent rendering function** [...] transparent for showing the physical item and occlusive for hiding the first virtual item; displaying the augmented reality image [...]; **detecting completion of the next step** [...]; and in response [...], **switching** from rendering the first virtual item [...] using only the first rendering function to [...] the second rendering function."

**Ce que ça couvre exactement** : une **technique de rendu précise** pour l'AR d'assemblage — la pièce « à poser » est rendue en fil de fer, un double virtuel de l'objet physique sert de masque d'occlusion transparent, et le rendu bascule quand la fin de l'étape est détectée. Revendications très étroites (chaque claim exige la combinaison wireframe + masque occlusif-transparent + détection de complétion + bascule).

**Conclusion pour A1 : risque nul** (pas d'AR du tout dans A1). **Pour V3/AR : risque nul en France/UE** (brevet US sans famille européenne — il ne peut pas bloquer la distribution française/UE ; seule la distribution sur l'App Store **US** serait exposée), et même aux US le contournement est aisé : ne pas utiliser ce couple précis de fonctions de rendu (p. ex. occlusion par depth-map ARKit/ARCore standard, rendu plein plutôt que wireframe). À garder en tête seulement si un mode AR voit le jour.

---

## 3. Autres brevets pertinents identifiés (recherche « assignee:LEGO + building/assembly instructions / brick model generation »)

Recherche Google Patents du 2026-07-04. Aucun autre brevet LEGO ne vise directement la **génération d'instructions** ; les résultats connexes :

| Brevet | Objet | Pertinence BrickOFF |
|---|---|---|
| KR101470665B1, CN103764237B, EP2135222B1, HK1138092B… | Famille de US8374829 | Couverte au § 2.1 |
| **US10600240B2** « Toy scanner » (LEGO, priorité 2016, actif) | **Station de scan** matérielle (support d'objet + capteur multi-points de vue) pour numériser un modèle construit | Claim 1 exige une *scanning station* physique avec *object support* — le scan smartphone d'un tas en vrac ne reproduit pas ces éléments. Risque faible, à faire vérifier lors de la revue CPI du pipeline de scan (hors périmètre instructions) |
| **US11779846B2** « Method for creating a virtual object » (LEGO, priorité 2016, actif) | Créer un objet virtuel depuis des images d'un objet réel, avec attributs locaux et **image d'une configuration mise à jour** de l'objet, contexte jeu vidéo | Vise la boucle « re-photographie ton modèle modifié → l'objet virtuel évolue ». BrickOFF ne crée pas de double virtuel jouable d'un modèle photographié. À surveiller si un jour on scanne des **modèles construits** (et pas des tas) |
| US11583774B2 « Toy system » (LEGO) | Codes de déblocage de contenus virtuels liés à des modèles physiques | Sans rapport |
| US10427065B2 « Building blocks with lights for guided assembly » (LEGO) | Briques matérielles à LED pour guider le montage | Matériel, sans rapport |
| WO2010000774A1 « Product development support system » (LEGO) | Outil interne de développement produit | Sans rapport |

**Point notable** : aucune famille LEGO trouvée couvrant « photographier un tas de pièces en vrac → inventaire » (le cœur de V1) ni « adapter un modèle paramétrique à un inventaire » (le cœur d'A1). Le comparable direct Brickit opère publiquement depuis 2021 sur ce créneau sans qu'un blocage brevet LEGO soit documenté — indice de liberté d'exploitation, pas une preuve. La recherche exhaustive (y compris demandes non encore publiées, continuations US en cours) relève du CPI.

---

## 4. Stratégie de contournement recommandée

### Pour V1.5 / A1 (engagement immédiat) — 4 règles d'architecture qui verrouillent la non-contrefaçon

1. **Les étapes sont une donnée d'auteur, jamais un calcul.** Le champ `steps` est écrit par un humain dans l'outil éditorial et embarqué dans le blueprint. L'app (et l'outil éditorial) ne doit contenir **aucun code qui dérive un ordre d'étapes en désassemblant un modèle numérique** (≠ US8374829 claims 1/39, EP2135222). La validation éditoriale R3 (connexité, appui, stabilité de chaque préfixe) est un *contrôle* d'étapes écrites, pas une *détermination* d'étapes — la distinction doit rester nette dans le code : pas de mode « proposer des étapes automatiquement » avant l'expiration (mars/mai 2028).
2. **Le solveur ne touche qu'aux slots, pas à la séquence.** Le backtracking d'A1 choisit des alternatives de pièces pour des slots ; l'ordre des étapes reste celui du blueprint. Cette séparation (résolution d'inventaire ⊥ séquencement) est exactement ce qui distingue A1 des revendications de génération.
3. **Jamais de superposition sur flux caméra pendant le guidage.** Le rendu pas-à-pas est 100 % synthétique (placements du blueprint, R6). La caméra ne sert qu'au scan du tas. Tout mode « ghost AR sur le montage réel », « vérifie ma construction avec la caméra », « montre la pièce suivante posée sur mon vrai modèle » est **interdit jusqu'à mai 2032** (US9821242/EP2714223, en vigueur FR+US, famille litigée) sauf avis CPI contraire. Le « ghost mode » façon LEGO Builder appliqué au **modèle 3D synthétique** (estomper les étapes < N) ne pose aucun problème : aucune image captée n'entre dans la composition.
4. **Documenter la provenance humaine des étapes.** Conserver la trace d'auteur des blueprints (qui a conçu les steps, quand) : en cas de contestation, c'est la preuve directe que les instructions ne sont pas générées par le procédé breveté.

### Pour V3 (génération de structures) — architectures qui échappent aux revendications

- **Générer dans l'ordre de pose (autorégressif), pas par désassemblage.** Si le générateur produit la structure **brique par brique dans l'ordre de construction** (approche LegoGPT, cf. INSTRUCTIONS_FORMATS.md § 5.3), la séquence d'assemblage EST la sortie de génération : il n'existe aucune étape « déterminer des deconstruction steps depuis la représentation numérique du modèle fini » (élément (a) de US8374829 claim 1) ni « déduire les construction steps des deconstruction steps » (élément (b)). Claim 39 est également évitée si la validation de chaque pose candidate se fait par **connectivité/stabilité physique du modèle partiel** (rollback physique) et non par un **test de déconstructibilité du modèle final** — c'est déjà l'approche recommandée par la littérature retenue au doc de recherche.
- **Le calendrier joue pour nous.** US8374829 expire le **2028-05-18** et EP2135222 (France) le **2028-03-14**. V3 étant conditionnée à un spike Go/No-Go postérieur à V2, il est plausible que ce brevet soit expiré au moment de l'engagement ; **à re-vérifier à la date du spike** (et vérifier alors l'absence de continuation US encore vivante dans la famille).
- **Regrouper les pièces en « groupes conceptuels » à l'écriture, pas au calcul.** Si V3 a besoin de découper la séquence générée en étapes lisibles (1–5 pièces), le faire par des règles éditoriales simples sur la séquence de pose (fenêtrage, regroupement par proximité) — sans processus itératif de déconnexion de sous-assemblages notés par force de connexion (élément (d) de claim 1).
- **AR : s'abstenir jusqu'en 2032, puis design-around.** Après expiration d'EP2714223/US9821242 (mai–juillet 2032), un guidage AR redevient envisageable ; d'ici là, l'alternative sans risque est l'affichage **côte à côte** (flux caméra d'un côté, rendu synthétique de l'autre) sans détection de position/orientation du modèle partiel ni image composite — mais la valeur UX étant discutable, le plus simple est de s'en tenir au rendu synthétique. Si AR un jour aux US : éviter la combinaison wireframe + masque occlusif-transparent de US11393153 (valable jusqu'en 2040, US uniquement).

### Marchés
- **France/UE (marché principal)** : seuls **EP2135222B1** (→ 2028-03-14) et **EP2714223B1** (→ 2032-05-22) y sont en vigueur. A1 ne reproduit aucune de leurs revendications → pas d'obstacle identifié à la distribution UE de V1.5.
- **US (App Store US)** : US8374829 (→ 2028-05-18), US9821242 (→ 2032-07-12), US11393153 (→ 2040-05-29). Mêmes conclusions : A1 n'en reproduit aucun.
- Les familles CN/JP/KR/CA/BR/MX existent (surtout pour US9821242) : à vérifier si ces marchés entrent un jour dans la roadmap.

---

## 5. Limites de cette analyse (pourquoi la relecture CPI est nécessaire)

1. **Statuts nationaux** : le maintien en vigueur en France est déduit des événements de paiement d'annuités remontés à l'EPO (codes PLFP/PGFP, derniers constatés : 2026-03-20 pour EP2135222, 2025-05-28 pour EP2714223) ; une confirmation au registre INPI fait foi.
2. **Demandes en cours** : les familles peuvent contenir des continuations/divisionnaires non délivrées ou non publiées qui élargiraient la couverture ; une veille (au minimum avant V3 et avant toute feature AR) est recommandée.
3. **Doctrine des équivalents** : l'analyse « élément par élément » ci-dessus raisonne en contrefaçon littérale ; un CPI doit confirmer l'écart pour les équivalents (notamment l'élément (c) de US9821242, structurellement proche du blueprint à alternatives).
4. **Litiges** : les deux familles LEGO portent un indicateur Darts-ip « First worldwide family litigation filed » ; le détail (parties, juridictions, issues) est derrière un paywall et n'a pas pu être vérifié — un CPI y a accès.
5. **Recherche non exhaustive** : la recherche « autres brevets » (§ 3) couvre les portefeuilles LEGO visibles sur Google Patents avec les requêtes citées ; elle ne remplace pas une recherche FTO professionnelle (classes CPC complètes, tiers autres que LEGO, demandes récentes non publiées).

> **Rappel final : analyse préliminaire par IA, ne remplace pas un conseil en propriété industrielle — relecture professionnelle recommandée avant l'engagement V1.5.**
