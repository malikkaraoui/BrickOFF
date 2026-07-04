# CH-4 — Fondations app iOS

> Durée : 1 semaine. Dépend de CH-0 uniquement → peut démarrer en parallèle de CH-1/2/3.

---

## Jalon 4.1 — Création projet & structure

### Spécifications projet
| Paramètre | Valeur |
|---|---|
| Nom projet | (nom retenu en CH-0, ex: BrickScan) |
| Langage | Swift (dernière version stable) |
| UI | SwiftUI |
| Cible minimale | iOS 16.0 (à confirmer : couvre les devices A14+ requis pour l'ANE confortable) |
| Architecture | MVVM + couche Services |
| Concurrence | Swift Concurrency (async/await, actors) — pas de Combine sauf nécessité |

### Structure de dossiers (à respecter strictement)
```
ios/BrickScan/
├── App/                    # @main, AppState, configuration
├── Features/
│   ├── Scan/               # ScanView, ScanViewModel
│   ├── Inventory/          # InventoryView, InventoryViewModel
│   ├── Matching/           # MatchesView, SetDetailView, ViewModels
│   └── Settings/
├── Core/
│   ├── Vision/             # DetectionService, ClassificationService, ColorService
│   ├── Database/           # GRDB setup, repositories
│   ├── Matching/           # MatchingEngine
│   └── Models/             # structs partagées (DetectedPiece, InventoryItem, LegoSet...)
├── Resources/
│   ├── Models/             # .mlpackage (DET, CLS)
│   ├── Data/               # rebrickable.sqlite, lego_colors_lab.json
│   └── Assets.xcassets
├── DesignSystem/           # tokens, composants réutilisables (liquid glass)
└── Tests/
    ├── UnitTests/
    └── SnapshotTests/      # optionnel V1
```

### Dépendances (SPM uniquement, minimum vital)
| Package | Usage | Justification |
|---|---|---|
| GRDB | SQLite | Référence Swift pour SQLite, performant, migrations propres |
| (aucune autre en V1) | | CoreML, Vision, AVFoundation, SwiftUI = natifs |

⚠️ Règle : toute nouvelle dépendance doit être justifiée par écrit dans `CHANGELOG_CH4.md`. Par défaut : natif.

### Livrable
- Projet Xcode qui build et run sur device, structure en place, GRDB intégré

### Critères d'acceptation
- [ ] Build sans warning
- [ ] Run sur les 2 devices de test
- [ ] Structure conforme au schéma ci-dessus

---

## Jalon 4.2 — Modèles de données partagés (contrats)

> Implémenter les structs EXACTEMENT comme spécifiées dans `12_CONVENTIONS_AI.md` §Contrats. Résumé :

```swift
// Core/Models/ — signatures attendues (corps à implémenter)

struct DetectedPiece: Identifiable, Codable {
    let id: UUID
    let partId: String        // ex "3001" — référence catalogue
    let colorId: Int          // id couleur Rebrickable
    let boundingBox: CGRect   // coordonnées normalisées 0–1
    let partConfidence: Double
    let colorConfidence: Double
}

struct InventoryItem: Codable, Equatable {
    let partId: String
    let colorId: Int
    var quantity: Int
}

struct LegoSet: Identifiable, Codable {
    let id: String            // set_num Rebrickable, ex "31058-1"
    let name: String
    let numParts: Int
    let year: Int
    let themeId: Int
}

struct SetMatchResult: Identifiable {
    let id: String            // set id
    let set: LegoSet
    let coverage: Double      // 0–1 : pièces dispo / pièces requises
    let missingParts: [InventoryItem]
}
```

### Critères d'acceptation
- [ ] Structs compilent, tests d'encodage/décodage JSON passent
- [ ] Aucun écart avec `12_CONVENTIONS_AI.md` (sinon mettre à jour le contrat d'abord)

---

## Jalon 4.3 — AppState & navigation

### Tâches
1. `AppState` (ObservableObject ou @Observable selon cible iOS) : état global minimal (onboarding fait ?, inventaire courant chargé ?)
2. Navigation : TabView 3 onglets — Scan / Inventaire / Constructions — + Settings accessible
3. Écrans placeholder pour chaque onglet (UI réelle en CH-8)
4. Gestion permission caméra : flow de demande propre, écran d'explication si refusée

### Critères d'acceptation
- [ ] Navigation 3 onglets fonctionnelle
- [ ] Permission caméra : les 3 cas gérés (jamais demandée / accordée / refusée avec lien Réglages)

---

## Jalon 4.4 — CI minimale

### Tâches
1. Script `ios/scripts/build_test.sh` : `xcodebuild build test` sur simulateur
2. GitHub Actions (ou équivalent) : build + tests unitaires à chaque PR sur `ios/**`
3. SwiftLint en mode warning (config de base, pas de zèle)

### Critères d'acceptation
- [ ] Pipeline vert sur un commit de test
- [ ] Un test unitaire factice tourne en CI

---

## Sortie de chantier CH-4

- App squelette navigable sur device, contrats implémentés, CI verte
- `CHANGELOG_CH4.md`
