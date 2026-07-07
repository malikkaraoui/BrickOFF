import CoreGraphics
import XCTest
@testable import BrickOFF

/// Jalon 5.6 — regroupement, corrections, section "incertaines", ajout explicite
/// via le vrai `InventoryRepository` (GRDB en mémoire).
@MainActor
final class ScanReviewViewModelTests: XCTestCase {
    private var repository: GRDBInventoryRepository!

    override func setUp() async throws {
        repository = GRDBInventoryRepository(database: try .inMemory())
    }

    private func piece(
        partId: String = "3001",
        colorId: Int = 4,
        partConfidence: Double = 0.9,
        colorConfidence: Double = 0.9
    ) -> DetectedPiece {
        DetectedPiece(
            id: UUID(),
            partId: partId,
            colorId: colorId,
            boundingBox: CGRect(x: 0.1, y: 0.1, width: 0.1, height: 0.1),
            partConfidence: partConfidence,
            colorConfidence: colorConfidence
        )
    }

    private func makeModel(_ pieces: [DetectedPiece]) -> ScanReviewViewModel {
        ScanReviewViewModel(pieces: pieces, repository: repository)
    }

    // MARK: - Regroupement

    func test_init_samePartAndColor_groupedWithQuantity() {
        let model = makeModel([piece(), piece(), piece(partId: "3020", colorId: 14)])
        XCTAssertEqual(model.groups.count, 2)
        let group3001 = model.groups.first { $0.partId == "3001" }
        XCTAssertEqual(group3001?.quantity, 2)
    }

    func test_init_confidences_areGroupMeans() {
        let model = makeModel([
            piece(partConfidence: 0.8, colorConfidence: 0.7),
            piece(partConfidence: 1.0, colorConfidence: 0.9),
        ])
        XCTAssertEqual(model.groups.first!.partConfidence, 0.9, accuracy: 1e-9)
        XCTAssertEqual(model.groups.first!.colorConfidence, 0.8, accuracy: 1e-9)
    }

    // MARK: - Incertaines

    func test_init_lowColorConfidence_isUncertainAndExcludedByDefault() {
        let model = makeModel([piece(colorConfidence: 0.4), piece(partId: "3020", colorId: 14)])
        let uncertain = model.uncertainGroups
        XCTAssertEqual(uncertain.count, 1)
        XCTAssertEqual(uncertain.first?.partId, "3001")
        XCTAssertFalse(uncertain.first!.includeInInventory)
        XCTAssertEqual(model.includedPieceCount, 1) // seule la pièce certaine compte
    }

    func test_init_unknownColor_isUncertain() {
        let model = makeModel([piece(colorId: -1, colorConfidence: 0.9)])
        XCTAssertEqual(model.uncertainGroups.count, 1)
        XCTAssertTrue(model.certainGroups.isEmpty)
    }

    // MARK: - Corrections

    func test_deleteGroup_removesGroup() {
        let model = makeModel([piece(), piece(partId: "3020", colorId: 14)])
        let id = model.groups.first!.id
        model.deleteGroup(id)
        XCTAssertEqual(model.groups.count, 1)
        XCTAssertNil(model.groups.first { $0.id == id })
    }

    func test_setColor_uncertainGroup_becomesCertainIncludedAndMerged() {
        // Un groupe certain 3001/4 et un incertain 3001/-1 : corriger le second en rouge
        // doit le rendre certain, l'inclure, et le FUSIONNER avec le premier.
        let model = makeModel([piece(), piece(colorId: -1, colorConfidence: 0.3)])
        let uncertainId = model.uncertainGroups.first!.id

        model.setColor(uncertainId, colorId: 4)

        XCTAssertEqual(model.groups.count, 1)
        XCTAssertTrue(model.uncertainGroups.isEmpty)
        XCTAssertEqual(model.groups.first?.quantity, 2)
        XCTAssertTrue(model.groups.first!.includeInInventory)
        XCTAssertEqual(model.includedPieceCount, 2)
    }

    func test_setPartId_updatesGroupAndConfidence() {
        let model = makeModel([piece()])
        let id = model.groups.first!.id
        model.setPartId(id, partId: "3003")
        XCTAssertEqual(model.groups.first?.partId, "3003")
        XCTAssertEqual(model.groups.first?.partConfidence, 1.0)
    }

    func test_setPartId_emptyInput_ignored() {
        let model = makeModel([piece()])
        let id = model.groups.first!.id
        model.setPartId(id, partId: "   ")
        XCTAssertEqual(model.groups.first?.partId, "3001")
    }

    // MARK: - Ajout à l'inventaire (jamais silencieux)

    func test_addToInventory_addsOnlyIncludedGroups() async throws {
        let model = makeModel([
            piece(), piece(), // certaines → incluses
            piece(partId: "3062", colorId: 2, colorConfidence: 0.4), // incertaine → exclue
        ])

        let success = await model.addToInventory()

        XCTAssertTrue(success)
        XCTAssertTrue(model.didAddToInventory)
        let items = try await repository.allItems()
        XCTAssertEqual(items.count, 1)
        XCTAssertEqual(items.first, InventoryItem(partId: "3001", colorId: 4, quantity: 2))
    }

    func test_addToInventory_explicitlyIncludedUncertain_isAdded() async throws {
        let model = makeModel([piece(colorConfidence: 0.4)])
        let id = model.uncertainGroups.first!.id
        model.setIncluded(id, true)

        let success = await model.addToInventory()

        XCTAssertTrue(success)
        let items = try await repository.allItems()
        XCTAssertEqual(items, [InventoryItem(partId: "3001", colorId: 4, quantity: 1)])
    }

    func test_addToInventory_correctionsAppliedToPayload() async throws {
        let model = makeModel([piece()])
        let id = model.groups.first!.id
        model.setColor(id, colorId: 15)
        model.setPartId(id, partId: "3004")

        _ = await model.addToInventory()

        let items = try await repository.allItems()
        XCTAssertEqual(items, [InventoryItem(partId: "3004", colorId: 15, quantity: 1)])
    }

    func test_addToInventory_nothingIncluded_failsWithoutWriting() async throws {
        let model = makeModel([piece(colorConfidence: 0.4)]) // uniquement une incertaine

        let success = await model.addToInventory()

        XCTAssertFalse(success)
        XCTAssertFalse(model.didAddToInventory)
        let count = try await repository.totalPieceCount()
        XCTAssertEqual(count, 0)
    }
}
