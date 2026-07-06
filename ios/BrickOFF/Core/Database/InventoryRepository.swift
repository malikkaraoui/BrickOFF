import Foundation
import GRDB

/// Contrat du plan CH-6 jalon 6.2 (12_CONVENTIONS_AI.md §1 pour les identifiants).
///
/// Règles métier :
/// 1. `addPieces` regroupe par (part_id, color_id) et incrémente — transaction unique.
/// 2. Chaque scan ajouté crée une entrée `scan_history` (payload JSON `[DetectedPiece]`)
///    → permet ``undoLastScan()``.
/// 3. Toute écriture passe par le repository — aucune requête SQL hors de `Core/Database/`.
protocol InventoryRepository: Sendable {
    /// Incrémente les quantités (regroupement par pièce) et journalise le scan.
    func addPieces(_ pieces: [DetectedPiece]) async throws
    /// Fixe la quantité d'une pièce. `0` = suppression de la ligne. Négatif = `DatabaseError.invalidQuantity`.
    func setQuantity(partId: String, colorId: Int, quantity: Int) async throws
    func allItems() async throws -> [InventoryItem]
    func totalPieceCount() async throws -> Int
    /// Vide l'inventaire ET l'historique de scans (un undo après vidage n'aurait plus de sens).
    func clear() async throws
    /// Flux réactif pour l'UI (ValueObservation GRDB). Émet l'état courant à l'abonnement,
    /// puis à chaque modification de la table `inventory`.
    func observeItems() -> AsyncStream<[InventoryItem]>
    /// Annule le dernier scan : restaure exactement l'état antérieur de l'inventaire
    /// et supprime l'entrée `scan_history` correspondante. No-op si l'historique est vide.
    func undoLastScan() async throws
}

/// Implémentation GRDB sur `user.sqlite` (jalon 6.2).
final class GRDBInventoryRepository: InventoryRepository {
    private let databaseWriter: any DatabaseWriter

    init(database: DatabaseManager) {
        self.databaseWriter = database.userDatabase
    }

    // MARK: - Écritures

    func addPieces(_ pieces: [DetectedPiece]) async throws {
        guard !pieces.isEmpty else { return }

        let grouped = Self.grouped(pieces)
        let payload = try String(decoding: JSONEncoder().encode(pieces), as: UTF8.self)
        let scanId = UUID().uuidString
        let now = Self.epochNow()
        let pieceCount = pieces.count

        try await databaseWriter.write { db in
            for (key, count) in grouped {
                try db.execute(
                    sql: """
                        INSERT INTO inventory (part_id, color_id, quantity, updated_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT (part_id, color_id)
                        DO UPDATE SET quantity = quantity + excluded.quantity,
                                      updated_at = excluded.updated_at
                        """,
                    arguments: [key.partId, key.colorId, count, now]
                )
            }
            try db.execute(
                sql: "INSERT INTO scan_history (id, created_at, piece_count, payload) VALUES (?, ?, ?, ?)",
                arguments: [scanId, now, pieceCount, payload]
            )
        }
    }

    func setQuantity(partId: String, colorId: Int, quantity: Int) async throws {
        guard quantity >= 0 else { throw DatabaseError.invalidQuantity(quantity) }
        let now = Self.epochNow()

        try await databaseWriter.write { db in
            if quantity == 0 {
                try db.execute(
                    sql: "DELETE FROM inventory WHERE part_id = ? AND color_id = ?",
                    arguments: [partId, colorId]
                )
            } else {
                try db.execute(
                    sql: """
                        INSERT INTO inventory (part_id, color_id, quantity, updated_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT (part_id, color_id)
                        DO UPDATE SET quantity = excluded.quantity,
                                      updated_at = excluded.updated_at
                        """,
                    arguments: [partId, colorId, quantity, now]
                )
            }
        }
    }

    func clear() async throws {
        try await databaseWriter.write { db in
            try db.execute(sql: "DELETE FROM inventory")
            try db.execute(sql: "DELETE FROM scan_history")
        }
    }

    func undoLastScan() async throws {
        let now = Self.epochNow()

        try await databaseWriter.write { db in
            guard let scan = try Row.fetchOne(
                db,
                sql: "SELECT id, payload FROM scan_history ORDER BY created_at DESC, rowid DESC LIMIT 1"
            ) else {
                return // Historique vide : rien à annuler.
            }

            let payload: String = scan["payload"]
            let pieces = try JSONDecoder().decode([DetectedPiece].self, from: Data(payload.utf8))

            for (key, count) in Self.grouped(pieces) {
                let current = try Int.fetchOne(
                    db,
                    sql: "SELECT quantity FROM inventory WHERE part_id = ? AND color_id = ?",
                    arguments: [key.partId, key.colorId]
                ) ?? 0
                let restored = current - count
                if restored <= 0 {
                    // La pièce n'existait pas avant ce scan → la ligne disparaît.
                    try db.execute(
                        sql: "DELETE FROM inventory WHERE part_id = ? AND color_id = ?",
                        arguments: [key.partId, key.colorId]
                    )
                } else {
                    try db.execute(
                        sql: "UPDATE inventory SET quantity = ?, updated_at = ? WHERE part_id = ? AND color_id = ?",
                        arguments: [restored, now, key.partId, key.colorId]
                    )
                }
            }

            try db.execute(
                sql: "DELETE FROM scan_history WHERE id = ?",
                arguments: [scan["id"] as String]
            )
        }
    }

    // MARK: - Lectures

    func allItems() async throws -> [InventoryItem] {
        try await databaseWriter.read { db in
            try Self.fetchItems(db)
        }
    }

    func totalPieceCount() async throws -> Int {
        try await databaseWriter.read { db in
            try Int.fetchOne(db, sql: "SELECT COALESCE(SUM(quantity), 0) FROM inventory") ?? 0
        }
    }

    func observeItems() -> AsyncStream<[InventoryItem]> {
        let observation = ValueObservation.tracking { db in
            try Self.fetchItems(db)
        }
        let reader = databaseWriter

        return AsyncStream { continuation in
            let task = Task {
                do {
                    for try await items in observation.values(in: reader) {
                        continuation.yield(items)
                    }
                } catch {
                    // Observation interrompue (base fermée…) : on termine le flux proprement.
                }
                continuation.finish()
            }
            continuation.onTermination = { _ in task.cancel() }
        }
    }

    // MARK: - Privé

    private struct PieceKey: Hashable, Sendable {
        let partId: String
        let colorId: Int
    }

    /// Regroupe un scan par (part_id, color_id) → quantités.
    private static func grouped(_ pieces: [DetectedPiece]) -> [PieceKey: Int] {
        pieces.reduce(into: [:]) { counts, piece in
            counts[PieceKey(partId: piece.partId, colorId: piece.colorId), default: 0] += 1
        }
    }

    /// Tri par quantité décroissante (spécification de l'écran 6.3), puis clé stable.
    private static func fetchItems(_ db: Database) throws -> [InventoryItem] {
        try Row.fetchAll(
            db,
            sql: "SELECT part_id, color_id, quantity FROM inventory ORDER BY quantity DESC, part_id ASC, color_id ASC"
        ).map { row in
            InventoryItem(partId: row["part_id"], colorId: row["color_id"], quantity: row["quantity"])
        }
    }

    private static func epochNow() -> Int {
        Int(Date().timeIntervalSince1970)
    }
}
