import AVFoundation
import Observation

/// État de la permission caméra, réduit aux trois cas gérés par l'app (CH-4 jalon 4.3).
enum CameraPermissionStatus: Equatable, Sendable {
    /// Jamais demandée — afficher l'écran d'explication avec bouton de demande.
    case notDetermined
    /// Accordée — le scan peut démarrer.
    case authorized
    /// Refusée (ou restreinte, ex. contrôle parental) — renvoyer vers Réglages.
    case denied
}

/// Abstraction du mécanisme d'autorisation système, injectable et mockable en tests.
@MainActor
protocol CameraAuthorizationProviding {
    /// État courant de l'autorisation caméra.
    var authorizationStatus: CameraPermissionStatus { get }
    /// Déclenche la demande système. Retourne `true` si l'accès est accordé.
    func requestAccess() async -> Bool
}

/// Implémentation réelle, adossée à `AVCaptureDevice`.
struct SystemCameraAuthorizationProvider: CameraAuthorizationProviding {
    var authorizationStatus: CameraPermissionStatus {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .notDetermined: .notDetermined
        case .authorized: .authorized
        case .denied, .restricted: .denied
        @unknown default: .denied
        }
    }

    func requestAccess() async -> Bool {
        await AVCaptureDevice.requestAccess(for: .video)
    }
}

/// Source de vérité observable de l'état de la permission caméra.
@MainActor
@Observable
final class CameraPermissionService {
    private let provider: any CameraAuthorizationProviding

    /// État courant, mis à jour par `requestAccess()` et `refresh()`.
    private(set) var status: CameraPermissionStatus

    init(provider: any CameraAuthorizationProviding = SystemCameraAuthorizationProvider()) {
        self.provider = provider
        self.status = provider.authorizationStatus
    }

    /// Relit l'état système — à appeler au retour au premier plan
    /// (l'utilisateur a pu changer la permission dans Réglages).
    func refresh() {
        status = provider.authorizationStatus
    }

    /// Demande l'autorisation système si elle n'a jamais été demandée.
    /// Sans effet si la permission est déjà accordée ou refusée.
    func requestAccess() async {
        guard status == .notDetermined else { return }
        status = await provider.requestAccess() ? .authorized : .denied
    }
}
