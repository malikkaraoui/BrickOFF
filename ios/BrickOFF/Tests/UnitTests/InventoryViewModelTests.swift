import XCTest
@testable import BrickOFF

@MainActor
final class InventoryViewModelTests: XCTestCase {

    private func makeViewModel() throws -> InventoryViewModel {
        let repository = GRDBInventoryRepository(database: try DatabaseManager.inMemory())
        return InventoryViewModel(repository: repository)
    }

    /// Injecte directement l'état observé (les allers-retours repository sont testés
    /// dans InventoryRepositoryTests ; ici on teste la logique de présentation).
    private func makeViewModel(items: [InventoryItem]) throws -> InventoryViewModel {
        let viewModel = try makeViewModel()
        viewModel.setItemsForTesting(items)
        return viewModel
    }

    func test_sections_mixedCategories_groupedInFixedOrderAndSortedByQuantity() throws {
        let viewModel = try makeViewModel(items: [
            InventoryItem(partId: "3068", colorId: 0, quantity: 9),  // tile
            InventoryItem(partId: "3001", colorId: 4, quantity: 2),  // brick
            InventoryItem(partId: "3003", colorId: 1, quantity: 5),  // brick
            InventoryItem(partId: "99207", colorId: 71, quantity: 1), // other
        ])

        let sections = viewModel.sections

        XCTAssertEqual(sections.map(\.category), [.brick, .tile, .other])
        XCTAssertEqual(sections[0].items.map(\.partId), ["3003", "3001"], "tri par quantité décroissante")
    }

    func test_searchText_matchesPartIdAndDisplayName() throws {
        let viewModel = try makeViewModel(items: [
            InventoryItem(partId: "3001", colorId: 4, quantity: 2),  // "Brique 3001"
            InventoryItem(partId: "3020", colorId: 1, quantity: 3),  // "Plate 3020"
        ])

        viewModel.searchText = "3020"
        XCTAssertEqual(viewModel.sections.flatMap(\.items).map(\.partId), ["3020"])

        viewModel.searchText = "brique"
        XCTAssertEqual(viewModel.sections.flatMap(\.items).map(\.partId), ["3001"], "recherche par nom v0")

        viewModel.searchText = "introuvable"
        XCTAssertTrue(viewModel.sections.isEmpty)
    }

    func test_totalPieceCount_sumsQuantities() throws {
        let viewModel = try makeViewModel(items: [
            InventoryItem(partId: "3001", colorId: 4, quantity: 2),
            InventoryItem(partId: "3020", colorId: 1, quantity: 3),
        ])

        XCTAssertEqual(viewModel.totalPieceCount, 5)
        XCTAssertEqual(viewModel.distinctItemCount, 2)
    }

    func test_startObserving_afterRepositoryWrite_itemsUpdated() async throws {
        let repository = GRDBInventoryRepository(database: try DatabaseManager.inMemory())
        let viewModel = InventoryViewModel(repository: repository)

        let observing = Task { await viewModel.startObserving() }
        defer { observing.cancel() }

        try await repository.setQuantity(partId: "3001", colorId: 4, quantity: 3)

        // L'observation pousse la mise à jour de façon asynchrone : on attend (borné).
        for _ in 0..<200 where viewModel.items.isEmpty {
            try await Task.sleep(for: .milliseconds(10))
        }
        XCTAssertEqual(viewModel.items, [InventoryItem(partId: "3001", colorId: 4, quantity: 3)])
    }
}
