import GRDB
import XCTest
@testable import BrickOFF

final class DatabaseManagerTests: XCTestCase {

    func test_migratorV1_freshDatabase_createsThreeTables() throws {
        let manager = try DatabaseManager.inMemory()

        let tables = try manager.userDatabase.read { db in
            try String.fetchAll(
                db,
                sql: "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name <> 'grdb_migrations' ORDER BY name"
            )
        }

        XCTAssertEqual(tables, ["app_meta", "inventory", "scan_history"])
    }

    func test_inventoryInsert_negativeQuantity_fails() throws {
        let manager = try DatabaseManager.inMemory()

        XCTAssertThrowsError(
            try manager.userDatabase.write { db in
                try db.execute(
                    sql: "INSERT INTO inventory (part_id, color_id, quantity, updated_at) VALUES (?, ?, ?, ?)",
                    arguments: ["3001", 4, -1, 1_750_000_000]
                )
            },
            "La contrainte CHECK (quantity >= 0) doit rejeter les quantités négatives"
        ) { error in
            guard let dbError = error as? GRDB.DatabaseError else {
                return XCTFail("Erreur inattendue : \(error)")
            }
            XCTAssertEqual(dbError.resultCode, .SQLITE_CONSTRAINT)
        }
    }

    func test_inventoryInsert_duplicatePrimaryKey_fails() throws {
        let manager = try DatabaseManager.inMemory()

        try manager.userDatabase.write { db in
            try db.execute(
                sql: "INSERT INTO inventory (part_id, color_id, quantity, updated_at) VALUES ('3001', 4, 1, 0)"
            )
        }

        XCTAssertThrowsError(
            try manager.userDatabase.write { db in
                try db.execute(
                    sql: "INSERT INTO inventory (part_id, color_id, quantity, updated_at) VALUES ('3001', 4, 2, 0)"
                )
            },
            "PRIMARY KEY (part_id, color_id) doit rejeter les doublons"
        )
    }

    func test_migratorV1_appliedTwice_isIdempotent() throws {
        let manager = try DatabaseManager.inMemory()

        // Re-migrer une base déjà à jour ne doit rien casser (DatabaseMigrator no-op).
        XCTAssertNoThrow(try DatabaseManager.migrator.migrate(manager.userDatabase))
    }
}
