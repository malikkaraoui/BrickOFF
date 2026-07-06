# CHANGELOG CH-6 — Inventaire local (persistance)

> Compte-rendu d'exécution au format `12_CONVENTIONS_AI.md` §3.2.
> Jalons 6.1/6.2/6.3 : session du 2026-07-06.

---

## Jalon 6.1 — Schéma base de données (GRDB)

- Statut : ✅
- Livrables produits :
  - `ios/BrickOFF/Core/Database/DatabaseManager.swift` — point d'accès unique aux bases :
    - `user.sqlite` ouvert/créé dans Application Support (`openUserDatabase()`),
      variante `inMemory()` pour tests/previews/fallback ;
    - hook catalogue lecture seule pour `rebrickable.sqlite`
      (`openCatalogDatabase(at:)` + `catalogDatabaseInBundle()` qui rend `nil`
      tant que la base n'est pas livrée — CH-7/CH-10) ;
    - `DatabaseMigrator` avec migration **"v1"** : les 3 tables du plan
      (`inventory`, `scan_history`, `app_meta`) créées en **SQL brut strictement
      identique au schéma normatif** du plan (CHECK quantity ≥ 0,
      PK composite (part_id, color_id), commentaires compris) ;
    - `DatabaseError` (enum d'erreur typée par domaine, conventions §2) ;
    - logs `os.Logger` subsystem `com.brickoff.app`, catégorie `Database`.
  - Tests : `ios/BrickOFF/Tests/UnitTests/DatabaseManagerTests.swift` (4 tests).
- Critères d'acceptation :
  - [x] Migrations GRDB en place (DatabaseMigrator, migration "v1") — prouvé par
    `test_migratorV1_freshDatabase_createsThreeTables` (les 3 tables exactes) et
    `test_migratorV1_appliedTwice_isIdempotent`.
  - [x] Contrainte quantity ≥ 0 testée — `test_inventoryInsert_negativeQuantity_fails`
    vérifie l'échec avec `SQLITE_CONSTRAINT` ; bonus : PK composite testée
    (`test_inventoryInsert_duplicatePrimaryKey_fails`).
- Écarts au plan :
  1. `DatabaseQueue` (et non `DatabasePool`) : suffisant pour une base utilisateur
     mono-process, et c'est la seule option compatible bases en mémoire pour les tests.
  2. `user.sqlite` posé directement à la racine d'Application Support (sandbox déjà
     propre à l'app) — le plan ne fixait pas de sous-dossier.
- Blocages / questions : aucun.

## Jalon 6.2 — InventoryRepository

- Statut : ✅
- Livrables produits :
  - `ios/BrickOFF/Core/Database/InventoryRepository.swift` — protocole
    `InventoryRepository` (signatures du plan à l'identique) + implémentation
    `GRDBInventoryRepository` :
    - `addPieces` : regroupement par (part_id, color_id), UPSERT incrémental et
      écriture `scan_history` (payload JSON `[DetectedPiece]` conforme §1.2) dans
      **une transaction unique** (`write { }`) ;
    - `setQuantity` : 0 = suppression de la ligne ; négatif =
      `DatabaseError.invalidQuantity` (avant même la contrainte SQL) ;
    - `allItems` (tri quantité décroissante puis clé stable), `totalPieceCount`
      (SUM SQL), `clear` ;
    - `observeItems()` : `ValueObservation` GRDB → `AsyncStream<[InventoryItem]>`
      (émission de l'état courant à l'abonnement puis à chaque écriture) ;
    - `undoLastScan()` : décrémente les quantités du dernier scan (payload décodé),
      supprime les lignes retombées à 0, efface l'entrée `scan_history` — le tout
      en transaction unique.
    - Tout le SQL du projet vit dans `Core/Database/` (règle métier 3 respectée).
  - Tests : `ios/BrickOFF/Tests/UnitTests/InventoryRepositoryTests.swift` (14 tests,
    base en mémoire) — ajout/regroupement, incrément, écriture scan_history + payload
    contractuel, scan vide, setQuantity (écrasement / zéro / négatif),
    totalPieceCount (somme + vide), clear, **annulation avec quantités croisées**
    (état antérieur restauré à l'identique, pièce nouvelle disparue), double undo,
    undo sur historique vide, observation réactive.
- Critères d'acceptation :
  - [x] Tests verts — voir sortie build (48 tests, 0 échec).
  - [x] Annulation de scan restaure exactement l'état antérieur —
    `test_undoLastScan_crossedQuantities_restoresExactPriorState`.
- Écarts au plan :
  1. **`undoLastScan()` ajouté au protocole** (demandé par l'ordre de mission ; le plan
     l'impliquait via la règle métier 2 et l'action "annuler le dernier scan" de 6.3,
     sans le lister dans le snippet). Sémantique : no-op si l'historique est vide ;
     si l'inventaire a été édité entre-temps, la quantité est plancherée à 0
     (suppression) plutôt que négative.
  2. **Protocole marqué `Sendable`** : requis par Swift 6 strict pour circuler entre
     `AppState`/ViewModels `@MainActor` et les écritures hors main thread.
  3. **`clear()` vide aussi `scan_history`** : un "annuler le dernier scan" après
     vidage recréerait des données fantômes ; décision documentée dans le doc du
     protocole (et testée).
  4. `addPieces([])` est un no-op : pas d'entrée `scan_history` vide.
- Blocages / questions : aucun.

## Jalon 6.3 — Écran inventaire (fonctionnel, UI brute)

- Statut : ✅ (habillage visuel = CH-8 ; critères de fluidité à l'œil re-vérifiés à ce moment-là)
- Livrables produits :
  - `ios/BrickOFF/Core/Models/PartCategory.swift` — catégorisation **heuristique v0**
    (voir écart 1) + titres de sections, noms v0, pictos SF Symbols par catégorie.
  - `ios/BrickOFF/DesignSystem/PartColorPalette.swift` — pastille couleur
    (`PartColorSwatch`) : mapping statique v0 des `color_id` Rebrickable fréquents
    vers leur RGB officiel, gris + "?" pour id inconnu / `-1` (D09 fallback).
  - `ios/BrickOFF/Features/Inventory/InventoryViewModel.swift` — `@Observable
    @MainActor`, sans import GRDB (conventions §2) : sections groupées par catégorie
    (ordre fixe briques/plates/tiles/autres) triées par quantité décroissante,
    recherche part_id/nom, compteurs, actions (stepper ±, suppression, undo, vider),
    abonnement à `observeItems()` ; bouton debug `addFakeScan()` (`#if DEBUG`).
  - `ios/BrickOFF/Features/Inventory/InventoryView.swift` — remplace le placeholder
    CH-4 : compteur global en header (`safeAreaInset`), `.searchable`, `List` en
    sections avec picto catégorie + pastille couleur + stepper, swipe-suppression,
    menu d'actions (annuler le dernier scan / vider avec `confirmationDialog` /
    "+ scan factice" en DEBUG), état vide, alerte d'erreur, préview sur base mémoire.
  - `ios/BrickOFF/App/AppState.swift` — expose `inventoryRepository` (ouverture de
    `user.sqlite` au lancement ; fallback documenté sur base en mémoire si échec,
    tracé en log, plutôt qu'un crash).
  - `ios/BrickOFF/App/ContentView.swift` — l'onglet Inventaire reçoit le repository.
  - Tests : `PartCategoryTests.swift` (4 tests, heuristique),
    `InventoryViewModelTests.swift` (4 tests : groupement/tri, recherche part_id + nom,
    compteurs, mise à jour réactive de bout en bout via le vrai repository).
- Critères d'acceptation :
  - [x] Toutes les actions CRUD opérationnelles avec UI réactive (`observeItems`) —
    logique prouvée par tests ; vérification à l'œil possible via le bouton debug
    "+ scan factice".
  - [~] Inventaire de 1000 lignes fluide : `List` SwiftUI (rendu lazy natif) ;
    non mesuré sur device dans cette session (pas de device branché) — à valider
    au run device / CH-8.
  - [~] Recherche réactive < 100 ms : filtre en mémoire sur ~1000 éléments
    (deux `contains` par élément), largement sous le seuil par construction ;
    non chronométré sur device.
- Écarts au plan :
  1. **Catégorisation heuristique v0 par part_id** (écart principal, assumé) : le plan
     prévoit le mapping catégorie "depuis le catalogue", mais `rebrickable.sqlite`
     n'arrive qu'en CH-7/CH-10. v0 documentée dans `PartCategory.swift` : numéro de
     moule = préfixe numérique du part_id ; plages 3001–3019 → brique, 3020–3036 →
     plate, listes explicites de moules connus (tiles 3068–3070, 2431, 6636… ;
     extras briques/plates), sinon "autre". Purement cosmétique (regroupement UI),
     remplacée par le catalogue dès qu'il est livré.
  2. **Noms de pièces v0** : "Brique 3001" (catégorie + part_id) faute de catalogue de
     noms ; la recherche "par nom" porte sur ce nom v0.
  3. **Visuels** : pictos SF Symbols par catégorie + pastille couleur — option
     fallback de D09 (les vignettes LDraw maison viendront du pipeline CH-1).
     Le mapping couleur v0 est statique (couleurs Rebrickable courantes) en attendant
     la table `colors` du catalogue.
  4. `List` (lazy par nature) plutôt que le `LazyVStack` cité par le plan : standard
     iOS pour sections + swipe actions + `.searchable`, même caractère lazy.
  5. Bouton "+ scan factice" (`#if DEBUG` uniquement) : ajout demandé par l'ordre de
     mission pour tester l'écran à l'œil, absent des builds release.
- Blocages / questions : aucun.

---

## Commande de validation (rejouable)

```bash
ios/scripts/build_test.sh
```

Sortie du 2026-07-06 (Xcode 26.6, simulateur iPhone 17) :

```
Test Suite 'All tests' passed at 2026-07-06 20:14:35.470.
	 Executed 48 tests, with 0 failures (0 unexpected) in 0.156 (0.328) seconds
** TEST SUCCEEDED **
```

48 tests (22 hérités de CH-4 + 26 nouveaux : 4 DatabaseManager, 14 InventoryRepository,
4 PartCategory, 4 InventoryViewModel), 0 échec, aucun warning de compilation
(hors les 2 notes `appintentsmetadataprocessor` documentées en CH-4).
