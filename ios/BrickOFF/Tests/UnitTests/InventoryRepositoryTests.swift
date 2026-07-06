import GRDB
import XCTest
@testable import BrickOFF

final class InventoryRepositoryTests: XCTestCase {

    private var manager: DatabaseManager!
    private var repository: GRDBInventoryRepository!

    override func setUpWithError() throws {
        try super.setUpWithError()
        manager = try DatabaseManager.inMemory()
        repository = GRDBInventoryRepository(database: manager)
    }

    override func tearDown() {
        repository = nil
        manager = nil
        super.tearDown()
    }

    /// Fabrique une pièce détectée de test (bbox/confidences sans importance ici).
    private func piece(_ partId: String, _ colorId: Int) -> DetectedPiece {
        DetectedPiece(
            id: UUID(),
            partId: partId,
            colorId: colorId,
            boundingBox: CGRect(x: 0.1, y: 0.2, width: 0.05, height: 0.05),
            partConfidence: 0.9,
            colorConfidence: 0.8
        )
    }

    // MARK: - addPieces

    func test_addPieces_newPieces_groupsByPartAndColor() async throws {
        try await repository.addPieces([
            piece("3001", 4), piece("3001", 4), piece("3001", 15), piece("3020", 4),
        ])

        let items = try await repository.allItems()
        XCTAssertEqual(items.count, 3)
        XCTAssertEqual(quantity(of: "3001", 4, in: items), 2)
        XCTAssertEqual(quantity(of: "3001", 15, in: items), 1)
        XCTAssertEqual(quantity(of: "3020", 4, in: items), 1)
    }

    func test_addPieces_existingPiece_incrementsQuantity() async throws {
        try await repository.addPieces([piece("3001", 4), piece("3001", 4)])
        try await repository.addPieces([piece("3001", 4), piece("3001", 4), piece("3001", 4)])

        let items = try await repository.allItems()
        XCTAssertEqual(items, [InventoryItem(partId: "3001", colorId: 4, quantity: 5)])
    }

    func test_addPieces_scan_writesScanHistoryWithContractPayload() async throws {
        try await repository.addPieces([piece("3001", 4), piece("3020", 1)])

        struct ScanRow: Sendable {
            let id: String
            let pieceCount: Int
            let payload: String
        }
        let rows: [ScanRow] = try await manager.userDatabase.read { db in
            try Row.fetchAll(db, sql: "SELECT id, created_at, piece_count, payload FROM scan_history")
                .map { ScanRow(id: $0["id"], pieceCount: $0["piece_count"], payload: $0["payload"]) }
        }
        XCTAssertEqual(rows.count, 1)
        XCTAssertEqual(rows[0].pieceCount, 2)
        XCTAssertNotNil(UUID(uuidString: rows[0].id))

        // Le payload est un JSON [DetectedPiece] conforme au contrat §1.2 (clés snake_case).
        let payload = rows[0].payload
        let decoded = try JSONDecoder().decode([DetectedPiece].self, from: Data(payload.utf8))
        XCTAssertEqual(decoded.map(\.partId), ["3001", "3020"])
        XCTAssertEqual(decoded.map(\.colorId), [4, 1])
    }

    func test_addPieces_emptyScan_writesNothing() async throws {
        try await repository.addPieces([])

        let items = try await repository.allItems()
        let scans = try await manager.userDatabase.read { db in
            try Int.fetchOne(db, sql: "SELECT COUNT(*) FROM scan_history") ?? 0
        }
        XCTAssertTrue(items.isEmpty)
        XCTAssertEqual(scans, 0)
    }

    // MARK: - setQuantity

    func test_setQuantity_positiveValue_overwritesQuantity() async throws {
        try await repository.addPieces([piece("3001", 4)])

        try await repository.setQuantity(partId: "3001", colorId: 4, quantity: 12)

        let items = try await repository.allItems()
        XCTAssertEqual(items, [InventoryItem(partId: "3001", colorId: 4, quantity: 12)])
    }

    func test_setQuantity_zero_deletesRow() async throws {
        try await repository.addPieces([piece("3001", 4), piece("3020", 1)])

        try await repository.setQuantity(partId: "3001", colorId: 4, quantity: 0)

        let items = try await repository.allItems()
        XCTAssertEqual(items, [InventoryItem(partId: "3020", colorId: 1, quantity: 1)])
    }

    func test_setQuantity_negativeValue_throwsInvalidQuantity() async throws {
        do {
            try await repository.setQuantity(partId: "3001", colorId: 4, quantity: -3)
            XCTFail("Une quantité négative doit être rejetée")
        } catch let error as BrickOFF.DatabaseError {
            XCTAssertEqual(error, .invalidQuantity(-3))
        }
    }

    // MARK: - totalPieceCount / clear

    func test_totalPieceCount_multipleItems_sumsQuantities() async throws {
        try await repository.addPieces([piece("3001", 4), piece("3001", 4), piece("3020", 1)])
        try await repository.setQuantity(partId: "3068", colorId: 0, quantity: 7)

        let total = try await repository.totalPieceCount()
        XCTAssertEqual(total, 10)
    }

    func test_totalPieceCount_emptyInventory_isZero() async throws {
        let total = try await repository.totalPieceCount()
        XCTAssertEqual(total, 0)
    }

    func test_clear_populatedInventory_emptiesInventoryAndHistory() async throws {
        try await repository.addPieces([piece("3001", 4), piece("3020", 1)])

        try await repository.clear()

        let items = try await repository.allItems()
        let total = try await repository.totalPieceCount()
        let scans = try await manager.userDatabase.read { db in
            try Int.fetchOne(db, sql: "SELECT COUNT(*) FROM scan_history") ?? 0
        }
        XCTAssertTrue(items.isEmpty)
        XCTAssertEqual(total, 0)
        XCTAssertEqual(scans, 0, "clear() vide aussi scan_history (un undo après vidage serait incohérent)")
    }

    // MARK: - undoLastScan

    func test_undoLastScan_crossedQuantities_restoresExactPriorState() async throws {
        // État antérieur : deux scans avec quantités croisées sur les mêmes pièces.
        try await repository.addPieces([piece("3001", 4), piece("3001", 4), piece("3020", 1)])
        try await repository.addPieces([piece("3020", 1), piece("3020", 1), piece("3001", 4)])
        let priorState = try await repository.allItems()
        XCTAssertEqual(quantity(of: "3001", 4, in: priorState), 3)
        XCTAssertEqual(quantity(of: "3020", 1, in: priorState), 3)

        // Dernier scan : incréments croisés + une pièce nouvelle.
        try await repository.addPieces([
            piece("3001", 4), piece("3001", 4), piece("3001", 4),
            piece("3020", 1),
            piece("3068", 0),
        ])

        try await repository.undoLastScan()

        let restored = try await repository.allItems()
        // allItems est trié de façon déterministe → comparaison directe des deux états.
        XCTAssertEqual(
            restored, priorState,
            "L'annulation doit restaurer exactement l'état antérieur (la pièce nouvelle disparaît)"
        )
        XCTAssertNil(restored.first { $0.partId == "3068" })
    }

    func test_undoLastScan_twiceInARow_unwindsScansInReverseOrder() async throws {
        try await repository.addPieces([piece("3001", 4)])
        try await repository.addPieces([piece("3020", 1)])

        try await repository.undoLastScan()
        try await repository.undoLastScan()

        let items = try await repository.allItems()
        XCTAssertTrue(items.isEmpty)
    }

    func test_undoLastScan_emptyHistory_isNoOp() async throws {
        try await repository.setQuantity(partId: "3001", colorId: 4, quantity: 2)

        try await repository.undoLastScan() // aucun scan journalisé : no-op

        let items = try await repository.allItems()
        XCTAssertEqual(items, [InventoryItem(partId: "3001", colorId: 4, quantity: 2)])
    }

    // MARK: - observeItems

    func test_observeItems_afterWrite_emitsInitialThenUpdatedList() async throws {
        var iterator = repository.observeItems().makeAsyncIterator()

        // 1re émission : état courant à l'abonnement (inventaire vide).
        let initial = await iterator.next()
        XCTAssertEqual(initial, [])

        try await repository.addPieces([piece("3001", 4), piece("3001", 4)])

        // Émission suivante : l'état après écriture.
        let updated = await iterator.next()
        XCTAssertEqual(updated, [InventoryItem(partId: "3001", colorId: 4, quantity: 2)])
    }

    // MARK: - Helpers

    private func quantity(of partId: String, _ colorId: Int, in items: [InventoryItem]) -> Int? {
        items.first { $0.partId == partId && $0.colorId == colorId }?.quantity
    }
}
