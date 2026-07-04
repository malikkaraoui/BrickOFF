# CHANGELOG CH-4 — Fondations app iOS

> Compte-rendu d'exécution au format `12_CONVENTIONS_AI.md` §3.2.
> Périmètre de cette session : jalons 4.1 et 4.2 uniquement (4.3 et 4.4 à venir).

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

## Jalons 4.3 (AppState & navigation) et 4.4 (CI minimale)

- Statut : ⏸ non démarrés (hors périmètre de cette session, sur instruction du chef d'orchestre).

---

## Commande de validation (rejouable)

```bash
cd ios
xcodegen generate
xcodebuild build test -scheme BrickOFF -destination 'platform=iOS Simulator,name=iPhone 17'
```
