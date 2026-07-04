import Observation

/// État global minimal de l'application (CH-4 jalon 4.3).
/// S'enrichira au fil des chantiers (inventaire courant, préférences…).
@MainActor
@Observable
final class AppState {
    /// L'onboarding a-t-il été complété ? (Persistance et écran réels en CH-8.)
    var onboardingDone = false

    /// État de la permission caméra, partagé par tout le flow de scan.
    let cameraPermission: CameraPermissionService

    init(cameraPermission: CameraPermissionService = CameraPermissionService()) {
        self.cameraPermission = cameraPermission
    }
}
