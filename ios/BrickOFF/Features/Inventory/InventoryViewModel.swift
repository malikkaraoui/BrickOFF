import CoreGraphics
import Foundation
import Observation

/// Identité et affichage v0 des lignes d'inventaire (pas encore de catalogue de noms).
extension InventoryItem: Identifiable {
    var id: String { "\(partId)#\(colorId)" }

    /// Catégorie heuristique v0 (voir `PartCategory.heuristic`).
    var category: PartCategory { PartCategory.heuristic(forPartId: partId) }

    /// Nom v0 : "Brique 3001" — sera remplacé par le nom catalogue (CH-7/CH-10).
    var displayName: String { "\(category.pieceDisplayName) \(partId)" }
}

/// ViewModel de l'écran inventaire (CH-6 jalon 6.3, UI brute — habillage en CH-8).
/// Conventions §2 : pas d'import GRDB ici, tout passe par `InventoryRepository`.
@MainActor
@Observable
final class InventoryViewModel {
    /// Section de la liste groupée : une catégorie, ses pièces triées par quantité décroissante.
    struct Section: Identifiable {
        let category: PartCategory
        let items: [InventoryItem]
        var id: PartCategory { category }
    }

    private let repository: any InventoryRepository

    /// Inventaire courant, poussé par `observeItems()` (déjà trié par quantité décroissante).
    private(set) var items: [InventoryItem] = []
    /// Recherche par part_id ou nom v0.
    var searchText = ""
    /// Message d'erreur technique à présenter (UI brute : alerte simple).
    var errorMessage: String?

    init(repository: any InventoryRepository) {
        self.repository = repository
    }

    // MARK: - Lecture

    /// Compteur global de pièces (header).
    var totalPieceCount: Int {
        items.reduce(0) { $0 + $1.quantity }
    }

    /// Nombre de références (couples part_id/color_id) distinctes.
    var distinctItemCount: Int { items.count }

    /// Liste groupée par catégorie (ordre fixe brique/plate/tile/autre),
    /// filtrée par la recherche, triée par quantité décroissante dans chaque section.
    var sections: [Section] {
        let grouped = Dictionary(grouping: filteredItems, by: \.category)
        return PartCategory.allCases.compactMap { category in
            guard let sectionItems = grouped[category], !sectionItems.isEmpty else { return nil }
            // Tri par quantité décroissante (spec 6.3), clé stable en cas d'égalité.
            let sorted = sectionItems.sorted {
                ($0.quantity, $1.partId, $1.colorId) > ($1.quantity, $0.partId, $0.colorId)
            }
            return Section(category: category, items: sorted)
        }
    }

    private var filteredItems: [InventoryItem] {
        let query = searchText.trimmingCharacters(in: .whitespaces)
        guard !query.isEmpty else { return items }
        return items.filter {
            $0.partId.localizedCaseInsensitiveContains(query)
                || $0.displayName.localizedCaseInsensitiveContains(query)
        }
    }

    // MARK: - Observation

    /// À lancer depuis `.task` de la vue : suit le flux réactif du repository.
    func startObserving() async {
        for await newItems in repository.observeItems() {
            items = newItems
        }
    }

    // MARK: - Actions CRUD

    func increment(_ item: InventoryItem) {
        setQuantity(item, to: item.quantity + 1)
    }

    func decrement(_ item: InventoryItem) {
        setQuantity(item, to: max(0, item.quantity - 1)) // 0 = suppression (contrat 6.2)
    }

    func delete(_ item: InventoryItem) {
        setQuantity(item, to: 0)
    }

    func setQuantity(_ item: InventoryItem, to quantity: Int) {
        perform { repository in
            try await repository.setQuantity(
                partId: item.partId, colorId: item.colorId, quantity: quantity
            )
        }
    }

    func undoLastScan() {
        perform { repository in
            try await repository.undoLastScan()
        }
    }

    /// Vide tout l'inventaire — la confirmation est demandée par la vue.
    func clearAll() {
        perform { repository in
            try await repository.clear()
        }
    }

    /// Exécute une écriture repository en tâche de fond, remonte l'erreur à l'UI.
    private func perform(
        _ operation: @escaping @Sendable (any InventoryRepository) async throws -> Void
    ) {
        let repository = self.repository
        Task {
            do {
                try await operation(repository)
            } catch {
                errorMessage = "Opération impossible : \(error.localizedDescription)"
            }
        }
    }

    // MARK: - Debug

    #if DEBUG
    /// Hook de test : injecte l'état observé sans passer par la base
    /// (la logique repository est couverte par InventoryRepositoryTests).
    func setItemsForTesting(_ items: [InventoryItem]) {
        self.items = items
    }

    /// Injecte un scan factice aléatoire (3 à 8 pièces du scope) pour tester l'écran à l'œil.
    /// DEBUG uniquement — jamais présent en release.
    func addFakeScan() {
        let partIds = [
            "3001", "3003", "3004", "3010", "3020", "3023", "3024", "3062",
            "3068", "3069", "3070", "2431", "3710", "3666", "54200", "99207", "4162",
        ]
        let colorIds = [0, 1, 2, 4, 14, 15, 19, 25, 71, 72, -1]
        let pieces = (0..<Int.random(in: 3...8)).map { _ in
            DetectedPiece(
                id: UUID(),
                partId: partIds.randomElement()!,
                colorId: colorIds.randomElement()!,
                boundingBox: CGRect(
                    x: .random(in: 0...0.9), y: .random(in: 0...0.9), width: 0.1, height: 0.1
                ),
                partConfidence: .random(in: 0.5...1),
                colorConfidence: .random(in: 0.5...1)
            )
        }
        perform { repository in
            try await repository.addPieces(pieces)
        }
    }
    #endif
}
