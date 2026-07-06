import Observation
import os

/// État global minimal de l'application (CH-4 jalon 4.3, enrichi en CH-6).
@MainActor
@Observable
final class AppState {
    private static let logger = Logger(subsystem: "com.brickoff.app", category: "AppState")

    /// L'onboarding a-t-il été complété ? (Persistance et écran réels en CH-8.)
    var onboardingDone = false

    /// État de la permission caméra, partagé par tout le flow de scan.
    let cameraPermission: CameraPermissionService

    /// Inventaire persistant (CH-6) — unique point d'accès des ViewModels à la persistance.
    let inventoryRepository: any InventoryRepository

    init(
        cameraPermission: CameraPermissionService = CameraPermissionService(),
        inventoryRepository: (any InventoryRepository)? = nil
    ) {
        self.cameraPermission = cameraPermission
        self.inventoryRepository = inventoryRepository ?? Self.makeDefaultInventoryRepository()
    }

    /// Ouvre `user.sqlite` (Application Support). En cas d'échec — jamais observé en
    /// sandbox iOS —, fallback documenté sur une base en mémoire pour ne pas
    /// crasher au lancement (perte de persistance tracée en log).
    private static func makeDefaultInventoryRepository() -> any InventoryRepository {
        do {
            return GRDBInventoryRepository(database: try .openUserDatabase())
        } catch {
            logger.error("user.sqlite indisponible, fallback en mémoire : \(error)")
            do {
                return GRDBInventoryRepository(database: try .inMemory())
            } catch {
                // SQLite lui-même est hors service : rien de raisonnable à faire.
                fatalError("SQLite indisponible : \(error)")
            }
        }
    }
}
