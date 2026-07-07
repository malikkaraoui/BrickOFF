import Foundation

/// Erreurs du domaine vision (conventions §2 : enum d'erreur typée par domaine).
/// Les messages utilisateur localisés vivent dans l'UI, pas ici.
enum VisionError: Error, Equatable {
    /// Aucune caméra exploitable (simulateur, device sans caméra arrière).
    case cameraUnavailable
    /// Aucun pipeline de détection disponible (les modèles CoreML arrivent avec CH-3).
    case pipelineUnavailable
    /// La caméra n'a pas fourni de frame (session stoppée pendant le scan).
    case frameCaptureInterrupted
}
