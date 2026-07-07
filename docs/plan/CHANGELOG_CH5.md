# CHANGELOG CH-5 — Pipeline scan (partie indépendante des modèles)

> Compte-rendu d'exécution au format `12_CONVENTIONS_AI.md` §3.2.
> Session du 2026-07-07 : jalons 5.1, 5.5, 5.6 avec pipeline de détection MOCK.
> **Jalons 5.2 / 5.3 / 5.4 : ⏸ bloqués sur CH-3** (mlpackages DET/CLS + algo couleur validé CH-2) — voir section dédiée en fin de fichier.

Décision d'architecture transverse : tout le pipeline vision (caméra comprise) vit dans
`Core/Vision/` — c'est le dossier prévu par le schéma CH-4 pour cette couche, et la caméra
est le point d'entrée du diagramme d'architecture du plan CH-5 ; aucun dossier `Core/Camera/`
créé (pas de nouveau dossier top-level, conforme §3.4).

---

## Jalon 5.1 — Capture caméra

- Statut : ✅ (logique prouvée par tests ; critères "à l'œil sur device" reportés au PO, voir blocages)
- Livrables produits :
  - `ios/BrickOFF/Core/Vision/CameraService.swift` —
    - protocole `ScanCameraControlling` (mockable) : `start()/stop()/nextFrame()` +
      `previewSource` ;
    - `CameraService` (implémentation système) : `AVCaptureSession` préset **1920×1080**
      (fallback `.high` si refusé), sortie `AVCaptureVideoDataOutput` en CVPixelBuffer BGRA,
      `alwaysDiscardsLateVideoFrames = true` (profondeur 1 : aucune frame en file),
      configuration/start/stop sur queue de session dédiée (recommandation Apple),
      état partagé delegate ↔ async protégé par `OSAllocatedUnfairLock` ;
    - `CameraPreviewSource` : boîte opaque autour de l'`AVCaptureSession` pour que les
      ViewModels ne touchent jamais AVFoundation (conventions §2).
  - `ios/BrickOFF/Core/Vision/FrameThrottler.swift` — logique de throttle **extraite et pure**
    (horloge injectée) : frame soumise seulement si la précédente est traitée ET ≥ 400 ms.
  - `ios/BrickOFF/Core/Vision/CapturedFrame.swift` — wrapper Sendable du CVPixelBuffer
    (propriété transférée, profondeur 1), fabrique `.blank()` (tests/simulateur), rendu
    `uiImage()` pour la capture figée de 5.6.
  - `ios/BrickOFF/Core/Vision/CameraPreviewView.swift` — `AVCaptureVideoPreviewLayer`
    wrappée SwiftUI (`UIViewRepresentable`, `videoGravity = .resizeAspectFill`).
  - `ios/BrickOFF/Core/Vision/VisionError.swift` — erreurs typées du domaine (conventions §2).
  - Lifecycle : `ScanViewModel.handleAppear/handleDisappear/handleScenePhase` +
    `ScanView.onChange(of: scenePhase)` — session stoppée en background et à la
    disparition de la vue, relancée au retour ; toute attente de frame en cours est
    libérée (`nil`) à l'arrêt pour ne jamais laisser un scan suspendu.
  - Tests : `Tests/UnitTests/FrameThrottlerTests.swift` (7 tests, sans caméra) — premier
    accept immédiat, rejet pendant traitement, rejet < 400 ms, accept à exactement 400 ms,
    burst 30 fps sur 2 s → exactement 5 frames acceptées.
- Critères d'acceptation :
  - [x] Throttling conforme (≥ 400 ms + précédente traitée, profondeur 1) — prouvé par
    les 7 tests unitaires de `FrameThrottlerTests` (sortie : 92 tests verts, voir bas de page).
  - [~] Preview fluide 30+ fps indépendamment de l'inférence — par construction : la preview
    layer est branchée sur la session, le throttle ne s'applique qu'à la sortie vidéo ;
    **à vérifier à l'œil sur device par le PO** (pas de caméra au simulateur).
  - [~] Mémoire stable 5 min / session background-foreground réels — même report device.
    Aucune frame ne peut s'accumuler par construction (`alwaysDiscardsLateVideoFrames` +
    remise directe au consommateur sans file).
- Écarts au plan :
  1. **Modèle "pull"** pour la remise de frames (`nextFrame() async`) plutôt qu'un delegate
     push : "la frame précédente est traitée" est matérialisé par le retour de l'appel —
     le contrat de throttle du plan est structurellement impossible à violer.
  2. `CameraService` est `@unchecked Sendable` avec état sous lock (justifié en doc de code) :
     nécessaire pour un delegate AVFoundation sous Swift 6 strict.
- Blocages / questions : validation visuelle device (preview fps, background/foreground,
  mémoire 5 min) à faire par le PO — aucune caméra réelle sur simulateur.

---

## (Hors plan) Contrat `DetectionPipeline` + mock — demandé par l'ordre de mission

- Statut : ✅
- Livrables produits :
  - `ios/BrickOFF/Core/Vision/DetectionPipeline.swift` — `RawDetection` (bbox normalisée
    0–1 origine haut-gauche, part_id, color_id, confidences — §1.1/§1.2) + protocole
    `DetectionPipeline` (`CapturedFrame` async → `[RawDetection]`).
  - `ios/BrickOFF/Core/Vision/MockDetectionPipeline.swift` (**`#if DEBUG` uniquement**) —
    `actor` seedable (`SplitMix64`) : scène fixe de 6 pièces plausibles du scope V1
    (dont 2× la même plate jaune pour tester le regroupement de quantités, et 1 pièce à
    colorConfidence ~0.42 pour exercer la section "incertaines" de 5.6), bruit réaliste :
    jitter bbox/confidences entre frames, ~5 % de détections manquées, ~5 % part_id faux,
    ~8 % color_id faux, faux positif transitoire ~1 frame sur 5, latence simulée 80 ms.
    Également : `MockScanFrameSource` (frames unies cadencées à 400 ms) pour dérouler le
    flux complet au simulateur.
  - Tests : `MockDetectionPipelineTests.swift` (3 tests) — déterminisme à seed fixé,
    bornes bbox/confidences, bout-en-bout mock → agrégateur (scène retrouvée à ±1 pièce).
- Écarts au plan :
  1. **`RawDetection` est ici la sortie du pipeline COMPLET par frame** (DET + CLS + COLOR),
     pas celle du seul détecteur comme dans le texte du jalon 5.2 (bbox + score). C'est le
     niveau dont l'agrégateur 5.5 a besoin pour voter part_id/color_id. Quand CH-3 livrera
     les modèles, l'implémentation réelle de `DetectionPipeline` chaînera
     DetectionService → Classification → Color en interne et sortira ce même type ;
     le type "bbox+score" interne au futur DetectionService pourra prendre un autre nom.
     À reporter dans `12_CONVENTIONS_AI.md` si ce contrat devient inter-modules.

---

## Jalon 5.5 — ScanAggregator (multi-frames)

- Statut : ✅
- Livrables produits :
  - `ios/BrickOFF/Core/Vision/ScanAggregator.swift` — **actor** (thread-safety par
    construction, conventions §2), `Configuration` (N = 5 frames, IoU > 0.5, minimum
    3/5 apparitions) :
    - appariement inter-frames glouton par IoU décroissant (1 détection ↔ 1 track par
      frame), référence d'appariement = dernière bbox du track ;
    - `part_id` et `color_id` = vote majoritaire pondéré par confidence, égalités
      départagées de façon déterministe ;
    - confidence finale = moyenne des votes gagnants ; bbox finale = moyenne des membres ;
    - rejet des tracks vus sur < 3 frames ; sortie `[DetectedPiece]` (contrat §1.2) ;
    - logique pure (`iou`, `weightedVote`, `consolidate`) en statique, testable sans actor.
  - Tests : `Tests/UnitTests/ScanAggregatorTests.swift` (**19 tests**, fixtures
    déterministes, zéro aléa) — IoU (identique/disjoint/décalé/dégénéré), vote pondéré
    (somme de confidences > effectif, moyenne des seuls votes gagnants, égalité
    déterministe, vide), appariement (même pièce jitterée sur 5 frames → 1 pièce ;
    2 pièces distantes → 2 ; doublon même frame → 1 seule rejoint le track), rejet des
    transitoires (2/5 rejeté, 3/5 gardé, faux positif mobile rejeté), moyennes bbox,
    `isComplete`, `reset`.
- Critères d'acceptation :
  - [x] Implémenté en actor — data races impossibles à l'API (isolation d'acteur vérifiée
    par le compilateur, projet en Swift 6 strict qui fait de tout data race une erreur de
    compilation ; run Thread Sanitizer sur device possible en plus par le PO).
  - [x] Appariement, votes, rejet 3/5 prouvés par tests (19/19 verts).
  - [~] "Scène test de 20 pièces : ≥ 18 consolidées, ≤ 1 faux positif" — ce critère mesure
    la chaîne complète avec les VRAIS modèles : re-mesurable seulement après CH-3.
    L'équivalent mock est couvert (`test_detections_fiveFramesAggregated_recoverScenePieces`).
- Écarts au plan : aucun sur l'algorithme (V1 implémenté à la lettre). Décisions
  d'implémentation documentées dans le code : appariement glouton (suffisant pour V1),
  bbox de référence = dernière bbox appariée du track.
- Blocages / questions : aucun.

---

## Jalon 5.6 — Écran de revue scan

- Statut : ✅ (avec les v0 assumées ci-dessous — le top-5 réel exige le classifieur CH-3)
- Livrables produits :
  - `ios/BrickOFF/Features/Scan/ScanViewModel.swift` — orchestration du scan déclenché
    (décision UX 5.5 figée : bouton "Scanner" → 5 frames analysées → agrégation → revue,
    jamais d'ajout en live) ; phases `idle/scanning/reviewing/failed`, annulation propre
    (disparition de vue, background), composition par défaut : simulateur → mock frames,
    device → `CameraService` ; DEBUG → `MockDetectionPipeline`, Release → pas de pipeline
    (bouton désactivé + message "CH-3") ; sans import AVFoundation/GRDB (conventions §2).
  - `ios/BrickOFF/Features/Scan/ScanReviewViewModel.swift` — regroupement des
    `[DetectedPiece]` consolidés par (part_id, color_id) avec quantité ; corrections :
    suppression, couleur (la correction fait foi → confidence 1.0, fusion des groupes
    devenus identiques), part_id (champ texte v0) ; **section "incertaines"**
    (color_id = -1 ou confidence < 0.6) **exclue par défaut de l'ajout** — inclusion
    uniquement par geste explicite (toggle, ou correction qui rend la pièce certaine) ;
    `addToInventory()` → **le vrai `InventoryRepository.addPieces`** (CH-6), corrections
    appliquées au payload, bboxes §1.2 conservées.
  - `ios/BrickOFF/Features/Scan/ScanReviewView.swift` — capture figée (dernière frame,
    rendue via `CapturedFrame.uiImage()`) + overlay des bboxes consolidées (vert/orange),
    liste : picto catégorie (vignette v0), nom v0 + part_id, confidences, pastille couleur
    CH-6 (`PartColorSwatch`), quantité ; swipe-suppression ; tap → feuille de correction
    (champ part_id + grille de pastilles couleur + suppression) ; bouton
    "Ajouter à l'inventaire (N)" désactivé à 0 ; footer explicite sur les incertaines.
  - `ios/BrickOFF/Features/Scan/ScanView.swift` — le flow permission CH-4 est conservé ;
    l'état "autorisé" devient la session de scan : preview caméra (ou placeholder
    simulateur), **bouton "Scanner" central**, progression "image i/5 — tenez l'appareil
    stable", revue en `fullScreenCover`, alerte d'échec.
  - `ios/BrickOFF/DesignSystem/PartColorPalette.swift` — ajout `knownColorIds` (options
    du picker de correction, v0 = mapping statique CH-6).
  - Tests : `ScanReviewViewModelTests.swift` (**12 tests**, repository GRDB en mémoire —
    regroupement/quantités, moyennes de confidence, incertaines (seuil et color_id = -1)
    exclues par défaut, suppression, correction couleur → certain + inclus + fusionné,
    correction part_id (+ entrée vide ignorée), ajout : seuls les groupes inclus écrits,
    incertaine incluse explicitement écrite, corrections répercutées dans l'inventaire,
    sélection vide = aucune écriture) ; `ScanViewModelTests.swift` (3 tests — flux complet
    mock : scan → `.reviewing` avec pièces consolidées et capture conservée ; échec
    explicite sans pipeline ; annulation → `.idle`).
- Critères d'acceptation :
  - [x] Toutes les corrections fonctionnelles — prouvées par tests (12/12).
  - [x] Aucun ajout à l'inventaire sans action explicite — bouton unique + incertaines
    exclues par défaut, prouvé par `test_addToInventory_addsOnlyIncludedGroups` et
    `test_addToInventory_nothingIncluded_failsWithoutWriting`.
  - [ ] Top-5 proposé à la correction de pièce — **impossible sans le classifieur réel** :
    v0 = champ texte libre part_id (écart assumé, à compléter en 5.3/CH-3).
  - [x] Flux navigable au simulateur : app lancée sur simulateur iPhone 17 (screenshot
    archivable : écran Scan avec placeholder "Preview caméra indisponible (simulateur)" +
    bouton Scanner actif). **Limite simulateur documentée** : pas de caméra réelle →
    `MockScanFrameSource` fournit des frames factices en DEBUG, le pipeline mock permet
    quand même de tester scan → revue → inventaire de bout en bout (et ce flux est aussi
    prouvé par `ScanViewModelTests` + `ScanReviewViewModelTests` sans UI).
- Écarts au plan :
  1. **Vignette = picto de catégorie** (pas le crop de la bbox) : les crops réels seront
     branchés quand le pipeline produira de vraies images (CH-3) ; la capture figée avec
     overlay donne déjà le contexte visuel.
  2. **Correction pièce = champ texte v0** (pas de recherche dans les 1000 classes
     pré-filtrée top-5) — dépend de `classes_v1.json` + classifieur (CH-3).
  3. **Seuil d'incertitude 0.6 (v0)** : le plan ne fixe pas de seuil ; à recaler avec les
     distributions de confidence des vrais modèles.
  4. "Supprimer une détection" opère sur le groupe consolidé (part_id, color_id) — c'est
     l'unité affichée ("quantité regroupée") ; la granularité à la détection individuelle
     n'a pas de sens à l'écran tant que les vignettes-crops n'existent pas.
- Blocages / questions : aucun bloquant.

---

## Jalons restants du chantier (état)

| Jalon | Statut | Bloqué par |
|---|---|---|
| 5.1 Capture caméra | ✅ (validation device par PO) | — |
| 5.2 DetectionService | ⏸ bloqué | CH-3 : `DetModel.mlpackage` + décision NMS |
| 5.3 ClassificationService | ⏸ bloqué | CH-3 : `ClsModel.mlpackage` + `classes_v1.json` |
| 5.4 ColorService | ⏸ bloqué | CH-2 jalon 2.3 (algo Python de référence) + `lego_colors_lab.json` / `color_config.json` |
| 5.5 ScanAggregator | ✅ | — (re-mesurer le critère "20 pièces réelles" après CH-3) |
| 5.6 Écran de revue | ✅ (v0 top-5/vignettes) | top-5 et crops réels : CH-3 |

Quand CH-3 livre : implémenter `DetectionPipeline` réel (5.2 + 5.3 + 5.4 chaînés),
le brancher à la place du mock dans `ScanViewModel.makeDefaultPipeline()` — l'agrégateur,
l'écran de revue et l'inventaire sont déjà prêts et testés contre ce contrat.

---

## Commande de validation (rejouable)

```bash
ios/scripts/build_test.sh
```

Sortie du 2026-07-07 (Xcode 26.6, simulateur iPhone 17) :

```
Test Suite 'All tests' passed at 2026-07-07 10:55:30.307.
	 Executed 92 tests, with 0 failures (0 unexpected) in 0.773 (1.228) seconds
** TEST SUCCEEDED **
```

92 tests (48 hérités CH-4/CH-6 + **44 nouveaux** : 7 FrameThrottler, 19 ScanAggregator,
3 MockDetectionPipeline, 12 ScanReviewViewModel, 3 ScanViewModel), 0 échec, aucun warning
de compilation (hors les 2 notes `appintentsmetadataprocessor` documentées en CH-4).

Vérification simulateur : `xcrun simctl install/launch com.brickoff.app` sur iPhone 17 —
écran Scan opérationnel (placeholder caméra + bouton Scanner), permission caméra accordée
via `simctl privacy grant camera`.
