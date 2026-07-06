import Foundation
import GRDB
import os

/// Erreurs du domaine base de données (conventions §2 : enum d'erreur typée par domaine,
/// messages utilisateur localisés gérés séparément côté UI).
enum DatabaseError: Error, Equatable {
    /// Quantité négative refusée par le contrat (`CHECK (quantity >= 0)`).
    case invalidQuantity(Int)
    /// Le répertoire Application Support est introuvable (ne devrait jamais arriver en sandbox iOS).
    case applicationSupportUnavailable
}

/// Point d'accès unique aux bases SQLite du plan CH-6 (jalon 6.1).
///
/// Deux bases distinctes (décision d'architecture du plan) :
/// 1. `user.sqlite` — données utilisateur, lecture/écriture, dans Application Support
///    (sauvegardée, iCloud backup OK). Migrée par ``migrator``.
/// 2. `rebrickable.sqlite` — catalogue en LECTURE SEULE, embarqué dans le bundle et
///    remplaçable par OTA (CH-10). À ce chantier, seul le hook d'ouverture existe :
///    ``openCatalogDatabase(at:)`` / ``catalogDatabaseInBundle()``.
///
/// Règle métier CH-6 : toute requête SQL vit dans `Core/Database/` — rien n'accède
/// aux bases en dehors de ce dossier.
final class DatabaseManager: Sendable {
    private static let logger = Logger(subsystem: "com.brickoff.app", category: "Database")

    /// Base utilisateur (`user.sqlite`, ou en mémoire pour les tests), migrations appliquées.
    let userDatabase: any DatabaseWriter

    private init(userDatabase: any DatabaseWriter) throws {
        try Self.migrator.migrate(userDatabase)
        self.userDatabase = userDatabase
    }

    // MARK: - Ouverture

    /// Ouvre (ou crée) `user.sqlite` dans Application Support et applique les migrations.
    static func openUserDatabase(fileManager: FileManager = .default) throws -> DatabaseManager {
        guard let supportURL = fileManager.urls(
            for: .applicationSupportDirectory, in: .userDomainMask
        ).first else {
            throw DatabaseError.applicationSupportUnavailable
        }
        try fileManager.createDirectory(at: supportURL, withIntermediateDirectories: true)
        let databaseURL = supportURL.appendingPathComponent("user.sqlite")
        logger.info("Ouverture de user.sqlite")
        return try DatabaseManager(userDatabase: DatabaseQueue(path: databaseURL.path))
    }

    /// Base utilisateur en mémoire — tests unitaires, previews, fallback.
    static func inMemory() throws -> DatabaseManager {
        try DatabaseManager(userDatabase: DatabaseQueue())
    }

    // MARK: - Hook catalogue (rebrickable.sqlite, CH-10)

    /// Ouvre un catalogue Rebrickable en LECTURE SEULE. Hook pour CH-7/CH-10 :
    /// la base n'est pas encore livrée à ce chantier.
    static func openCatalogDatabase(at url: URL) throws -> DatabaseQueue {
        var configuration = Configuration()
        configuration.readonly = true
        return try DatabaseQueue(path: url.path, configuration: configuration)
    }

    /// Catalogue embarqué dans le bundle, s'il est présent (CH-10). `nil` sinon.
    static func catalogDatabaseInBundle(_ bundle: Bundle = .main) throws -> DatabaseQueue? {
        guard let url = bundle.url(forResource: "rebrickable", withExtension: "sqlite") else {
            return nil
        }
        return try openCatalogDatabase(at: url)
    }

    // MARK: - Migrations

    /// Migrations de `user.sqlite`. Le schéma "v1" est NORMATIF (plan CH-6 jalon 6.1) :
    /// SQL brut, à l'identique du plan.
    static var migrator: DatabaseMigrator {
        var migrator = DatabaseMigrator()

        migrator.registerMigration("v1") { db in
            try db.execute(sql: """
                CREATE TABLE inventory (
                    part_id   TEXT NOT NULL,
                    color_id  INTEGER NOT NULL,
                    quantity  INTEGER NOT NULL CHECK (quantity >= 0),
                    updated_at INTEGER NOT NULL,          -- epoch seconds
                    PRIMARY KEY (part_id, color_id)
                );

                CREATE TABLE scan_history (
                    id         TEXT PRIMARY KEY,           -- UUID
                    created_at INTEGER NOT NULL,
                    piece_count INTEGER NOT NULL,
                    payload    TEXT NOT NULL               -- JSON [DetectedPiece] pour audit/annulation
                );

                CREATE TABLE app_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL                    -- versions de schéma, du catalogue, etc.
                );
                """)
        }

        return migrator
    }
}
