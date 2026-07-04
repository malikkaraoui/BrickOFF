# CHANGELOG CH-4 — Fondations app iOS

> Compte-rendu d'exécution au format `12_CONVENTIONS_AI.md` §3.2.
> Jalons 4.1/4.2 : session 1. Jalons 4.3/4.4 : session 2 (2026-07-05).

---

## Jalon 4.1 — Création projet & structure

- Statut : ✅ (validation sur device reportée au PO, voir écarts)
- Livrables produits :
  - `ios/project.yml` — définition XcodeGen du projet (versionnée)
  - `ios/.gitignore` — exclut `*.xcodeproj` (régénéré par `xcodegen generate`)
  - `ios/BrickOFF/` — structure complète conforme au schéma CH-4 :
    `App/`, `Features/{Scan,Inventory,Matching,Settings}/`, `Core/{Vision,Database,Matching,Models}/`,
    `Resources/{Models,Data,Assets.xcassets}/`, `DesignSystem/`, `Tests/UnitTests/`
    (dossiers vides tenus par des `.gitkeep`, exclus du build)
  - `ios/BrickOFF/App/BrickOFFApp.swift` — point d'entrée `@main` SwiftUI
  - `ios/BrickOFF/App/ContentView.swift` — TabView placeholder 3 onglets
    (Scan / Inventaire / Constructions ; navigation réelle au jalon 4.3)
- Critères d'acceptation :
  - [x] Build sans warning de compilation — preuve :
    ```
    ** BUILD SUCCEEDED **
    ```
    (xcodebuild build test, scheme BrickOFF, simulateur iPhone 17, Xcode 26.6.
    Seule sortie résiduelle : 2 notes de l'outil `appintentsmetadataprocessor`
    "No AppIntents.framework dependency found" — notice d'outillage Apple connue,
    pas un warning de code.)
  - [ ] Run sur les 2 devices de test — **reporté** : aucun device physique branché
    sur la machine d'exécution ; validé sur simulateur, le run device sera fait par le PO.
  - [x] Structure conforme au schéma — vérifiée par `find ios -type d`, identique au plan
    (`SnapshotTests/` non créé : marqué "optionnel V1" dans le plan).
- Écarts au plan :
  1. **Nom projet : `BrickOFF`** (au lieu de l'exemple "BrickScan") — application de la
     décision [D08](ARBITRAGES/D08_NOM_APP.md). Bundle id : `com.brickoff.app`.
  2. **XcodeGen au lieu d'un .xcodeproj créé à la main** : le plan ne spécifiait pas
     l'outillage. Choix : projet décrit dans `ios/project.yml` (texte, diffable,
     reviewable en PR), `.xcodeproj` gitignoré et régénéré à la demande — élimine les
     conflits de merge sur le pbxproj binaire-verbeux et rend le projet reproductible
     par toute session IA/humaine (`cd ios && xcodegen generate`). XcodeGen 2.45.4.
  3. **Cible minimale iOS 17.0** (au lieu du "iOS 16.0 à confirmer" du plan) :
     le plan lui-même conditionne le choix (jalon 4.3 : "ObservableObject ou
     @Observable selon cible iOS"). `@Observable` (Observation framework) exige
     iOS 17 et simplifie nettement les ViewModels MVVM prévus ; en 2026, iOS 17+
     couvre très largement le parc, et tous les devices A14+ requis pour l'ANE
     (contrainte produit) supportent iOS 17. Aucun device visé par le produit
     n'est exclu par ce relèvement. À entériner par le PO.
  4. **GRDB épinglé `from: 7.11.1`** — dernière release stable vérifiée à date
     (2026-07-04) sur github.com/groue/GRDB.swift. Seule dépendance du projet,
     conformément au plan.
  5. `TARGETED_DEVICE_FAMILY = 1,2` (iPhone + iPad) : l'iPad M4 est device de test
     officiel (D10).
  6. `SWIFT_VERSION = 6.0` (mode langage Swift 6, toolchain Xcode 26.6) : "dernière
     version stable" demandée par le plan ; la concurrence stricte est donc active
     dès le départ.
- Blocages / questions : aucun bloquant. Le run sur devices physiques (critère 2)
  reste à faire par le PO.

---

## Jalon 4.2 — Modèles de données partagés (contrats)

- Statut : ✅
- Livrables produits :
  - `ios/BrickOFF/Core/Models/DetectedPiece.swift`
  - `ios/BrickOFF/Core/Models/InventoryItem.swift`
  - `ios/BrickOFF/Core/Models/LegoSet.swift`
  - `ios/BrickOFF/Core/Models/SetMatchResult.swift`
  - Tests : `ios/BrickOFF/Tests/UnitTests/{DetectedPiece,InventoryItem,LegoSet,SetMatchResult}Tests.swift`
- Critères d'acceptation :
  - [x] Structs compilent, tests d'encodage/décodage JSON passent — preuve :
    ```
    Test Suite 'BrickOFFTests.xctest' passed at 2026-07-04 21:16:23.414.
    Test Suite 'All tests' passed at 2026-07-04 21:16:23.415.
    ** TEST SUCCEEDED **
    ```
    11 tests, 0 échec. Couverts : décodage de l'échantillon exact du contrat §1.2,
    clés snake_case exactes à l'encodage (`part_id`, `color_id`, `bbox` = `{x,y,w,h}`,
    `part_confidence`, `color_confidence` ; `{part_id,color_id,quantity}` pour
    l'inventaire §1.3), aller-retour encode/décode sans perte, `color_id = -1`
    ("unknown", §1.1) accepté.
  - [x] Aucun écart avec les signatures de `12_CONVENTIONS_AI.md` / CH-4 jalon 4.2 :
    propriétés, types et conformances strictement identiques au contrat.
- Écarts au plan / décisions d'implémentation (le contrat ne fixait que les signatures
  Swift et le JSON ; le pont entre les deux est explicité ici) :
  1. **CodingKeys explicites** (pas de stratégie `convertToSnakeCase`) : le mapping
     est visible et verrouillé dans chaque struct, insensible aux renommages Swift,
     et indispensable de toute façon pour `bbox` (voir 2) et `set_num` (voir 4).
  2. **`boundingBox: CGRect` ↔ `"bbox": {x,y,w,h}`** : Codable manuel sur
     `DetectedPiece` via une struct interne `BoundingBox {x,y,w,h}` — l'encodage
     Codable par défaut de CGRect (tableaux imbriqués) ne respecte pas le contrat.
  3. **`id: UUID` de `DetectedPiece` est hors format d'échange** : le JSON §1.2 ne
     contient pas de champ `id` pour une pièce. Décision : l'UUID est une identité
     locale (SwiftUI/`Identifiable`), non encodée, régénérée au décodage. Le JSON
     émis contient exactement les 5 clés du contrat, rien de plus (testé).
  4. **Clés JSON de `LegoSet`** : non définies par les contrats §1 — alignées sur le
     nommage Rebrickable (`set_num`, `name`, `num_parts`, `year`, `theme_id`),
     cohérent avec §1.1 et avec le snapshot SQLite de CH-7. À reporter dans
     `12_CONVENTIONS_AI.md` si ce format devient un format d'échange.
  5. **`SetMatchResult` non Codable** (conforme à la signature du contrat, qui ne
     le déclare que `Identifiable`) : testé sur construction/exposition des champs,
     pas d'aller-retour JSON.
  6. Tests en **XCTest** (pas Swift Testing) : colle au nommage imposé par les
     conventions §2 (`test_<méthode>_<cas>_<attendu>()`).

---

## Jalon 4.3 — AppState & navigation

- Statut : ✅
- Livrables produits :
  - `ios/BrickOFF/App/AppState.swift` — `@Observable @MainActor`, état global minimal :
    `onboardingDone` (persistance réelle en CH-8) + `cameraPermission` (service injecté).
  - `ios/BrickOFF/Core/Permissions/CameraPermissionService.swift` —
    `CameraPermissionStatus` (3 cas : `notDetermined`/`authorized`/`denied`),
    protocole `CameraAuthorizationProviding` (mockable), implémentation réelle
    `SystemCameraAuthorizationProvider` (AVCaptureDevice), service `@Observable`
    avec `requestAccess()` et `refresh()`.
  - `ios/BrickOFF/App/ContentView.swift` — TabView 3 onglets (Scan / Inventaire /
    Constructions), chaque onglet dans un `NavigationStack` avec bouton Réglages
    en toolbar ; Réglages présentés en sheet.
  - `ios/BrickOFF/App/BrickOFFApp.swift` — injection `AppState` via
    `.environment()`, `refresh()` de la permission au retour au premier plan
    (`scenePhase == .active`, l'utilisateur a pu changer la permission dans Réglages).
  - `ios/BrickOFF/Features/Scan/ScanView.swift` — flow permission complet :
    jamais demandée → écran d'explication + bouton "Autoriser la caméra" ;
    accordée → placeholder "prêt à scanner" ; refusée → écran + bouton
    "Ouvrir les Réglages" (`UIApplication.openSettingsURLString`).
  - `ios/BrickOFF/Features/Inventory/InventoryView.swift`,
    `ios/BrickOFF/Features/Matching/MatchesView.swift`,
    `ios/BrickOFF/Features/Settings/SettingsView.swift` — placeholders propres
    (`ContentUnavailableView` / `Form`), UI réelle en CH-8.
  - `ios/project.yml` — ajout `INFOPLIST_KEY_NSCameraUsageDescription` (texte FR
    sobre : "BrickOFF utilise la caméra pour reconnaître vos pièces LEGO et
    remplir votre inventaire.").
  - Tests : `ios/BrickOFF/Tests/UnitTests/CameraPermissionServiceTests.swift`
    (8 tests, provider mocké), `ios/BrickOFF/Tests/UnitTests/AppStateTests.swift` (3 tests).
- Critères d'acceptation :
  - [x] Navigation 3 onglets fonctionnelle — build vert, TabView + NavigationStack
    par onglet, Réglages accessibles depuis chaque onglet.
  - [x] Permission caméra : les 3 cas gérés — les 3 branches d'UI existent dans
    `ScanView`, et la logique d'état est prouvée par tests unitaires sur provider
    mocké (le simulateur ne permet pas de tester la caméra réelle) :
    ```
    Test Suite 'CameraPermissionServiceTests' passed
      Executed 8 tests, with 0 failures
    Test Suite 'All tests' passed at 2026-07-05 01:36:45.670.
      Executed 22 tests, with 0 failures (0 unexpected)
    ** TEST SUCCEEDED **
    ```
- Écarts au plan / décisions d'implémentation :
  1. **Settings en bouton toolbar + sheet** (et non 4e onglet) : le plan fixe la
     TabView à exactement 3 onglets (les 3 flows cœur du produit) et demande
     seulement que Settings soit "accessible". Un engrenage en barre de navigation
     de chaque onglet, ouvrant une sheet, est le pattern iOS standard pour un
     écran secondaire et laisse la tab bar disponible si un 4e flow cœur arrive.
  2. **Emplacement du service : `Core/Permissions/`** (nouveau sous-dossier de
     `Core/`) : c'est un service système réutilisable (couche Services du MVVM),
     pas de la configuration d'app — sa place est dans `Core/`. Aucun dossier du
     schéma CH-4 n'est renommé/déplacé (conforme §3.4) ; `Permissions/` est un
     ajout, au même titre que les fichiers.
  3. **Protocole `CameraAuthorizationProviding` `@MainActor`** : le service est
     `@MainActor` (état observé par l'UI) ; isoler le protocole au même acteur
     rend les mocks triviaux (pas de `Sendable` forcé) sous Swift 6 strict.
  4. `denied` regroupe `.denied` et `.restricted` (contrôle parental) : même UX
     de sortie (Réglages), distinction inutile au jalon.
  5. `onboardingDone` non persisté (pas d'AppStorage) : le plan ne demande que
     l'état global minimal ; la persistance viendra avec l'onboarding réel (CH-8).
- Blocages / questions : aucun. Le test des 3 cas réels sur device (demande
  système effective, refus, retour Réglages) reste à faire par le PO au run device.

---

## Jalon 4.4 — CI minimale

- Statut : ✅
- Livrables produits :
  - `ios/scripts/build_test.sh` — exécutable, rejouable depuis n'importe quel cwd :
    `xcodegen generate` puis `xcodebuild build test` sur simulateur.
    Destination par défaut `platform=iOS Simulator,name=iPhone 17`
    (surchargable via `BRICKOFF_SIM_DEVICE`) ; **fallback documenté** : si ce
    simulateur n'existe pas, premier iPhone disponible d'après
    `xcrun simctl list devices available` (fallback testé : renvoie "iPhone Air"
    en local quand on demande un device inexistant).
  - `.github/workflows/ios.yml` — déclencheurs : PR et push sur `main` quand
    `ios/**` (ou le workflow lui-même) change ; étapes : checkout,
    `brew install xcodegen`, `ios/scripts/build_test.sh` ; timeout 30 min.
- Critères d'acceptation :
  - [x] `ios/scripts/build_test.sh` passe en local — exécuté réellement :
    ```
    Test Suite 'All tests' passed at 2026-07-05 01:36:45.670.
      Executed 22 tests, with 0 failures (0 unexpected)
    ** TEST SUCCEEDED **
    ```
    Build sans warning de compilation (vérifié par grep sur la sortie xcodebuild ;
    seules restent les 2 notes `appintentsmetadataprocessor` déjà documentées en 4.1).
  - [ ] Pipeline vert sur un commit de test — **reporté** : rien n'est commité/poussé
    dans cette session (instruction explicite) ; à valider au premier push touchant
    `ios/**`. Le workflow exécute exactement le script prouvé vert en local et sa
    syntaxe YAML est validée.
  - [x] Un test unitaire (22 en réalité) tournera en CI via `build test` du script.
- Écarts au plan / décisions d'implémentation :
  1. **Runner `macos-26`** (et non macos-15) — vérifié le 2026-07-05 :
     macos-26 est GA sur GitHub Actions depuis février 2026, Xcode par défaut
     26.4.1 (donc simulateurs iPhone 17 disponibles), et `macos-latest` bascule
     sur macos-26 depuis juin 2026. macos-15 plafonne à Xcode 16.4 (pas de
     simulateur iPhone 17 — le fallback du script couvrirait ce cas, mais autant
     coller à l'environnement local Xcode 26). Label épinglé (pas `macos-latest`)
     pour éviter les bascules silencieuses d'image.
     Sources : github.blog/changelog (macos-26 GA 2026-02-26 ; macos-latest → macos-26,
     issue actions/runner-images#14167), readme runner-images macos-26.
  2. **SwiftLint reporté** (le plan le listait "en mode warning") : conformément à
     l'arbitrage du chef d'orchestre ("pas de SwiftLint si ça complique"), on garde
     la CI minimale — pas de config `.swiftlint.yml` ni d'install brew supplémentaire
     tant qu'il n'y a pas d'UI réelle. À introduire au plus tard en CH-8.
- Blocages / questions : aucun. Premier run CI à observer au premier push `ios/**`.

---

## Commande de validation (rejouable)

```bash
ios/scripts/build_test.sh
# équivalent à :
#   cd ios && xcodegen generate
#   xcodebuild build test -scheme BrickOFF -destination 'platform=iOS Simulator,name=iPhone 17'
```
