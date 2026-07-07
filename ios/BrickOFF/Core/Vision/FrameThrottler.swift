import Foundation

/// Logique de throttling du jalon 5.1, extraite de `CameraService` pour être
/// testable unitairement sans caméra réelle.
///
/// Règle du plan (5.1, spécification 3) : une frame n'est soumise à l'inférence que si
///   1. la frame précédente est entièrement traitée (file de profondeur 1 — les frames
///      intermédiaires sont jetées, jamais mises en file d'attente), ET
///   2. au moins `minimumInterval` s'est écoulé depuis la dernière frame soumise.
///
/// L'horloge est injectée (paramètre `now`, horloge monotone attendue, ex. `CACurrentMediaTime()`)
/// pour rendre la logique déterministe en tests.
struct FrameThrottler: Sendable {
    /// Intervalle minimal entre deux soumissions (plan 5.1 : 400 ms).
    let minimumInterval: TimeInterval

    /// Une frame soumise est-elle encore en cours de traitement ?
    private(set) var isProcessingFrame = false
    private var lastSubmissionTime: TimeInterval?

    init(minimumInterval: TimeInterval = 0.4) {
        self.minimumInterval = minimumInterval
    }

    /// À appeler pour CHAQUE frame capturée.
    /// - Returns: `true` → soumettre cette frame à l'inférence (l'appelant devra signaler
    ///   la fin du traitement via `finishProcessing()`) ; `false` → jeter la frame.
    mutating func shouldSubmitFrame(at now: TimeInterval) -> Bool {
        guard !isProcessingFrame else { return false }
        if let last = lastSubmissionTime, now - last < minimumInterval { return false }
        isProcessingFrame = true
        lastSubmissionTime = now
        return true
    }

    /// À appeler quand le traitement de la dernière frame soumise est terminé.
    mutating func finishProcessing() {
        isProcessingFrame = false
    }
}
