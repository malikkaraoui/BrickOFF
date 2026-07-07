import CoreGraphics

/// Détection brute produite par l'analyse d'UNE frame.
///
/// C'est la sortie consolidée par frame de la chaîne DET → CLS → COLOR
/// (jalons 5.2–5.4, bloqués sur CH-3) : bbox du détecteur, part_id du classifieur,
/// color_id du pipeline couleur. Écart documenté (CHANGELOG_CH5) : le plan 5.2 appelle
/// "RawDetection" la sortie du seul détecteur (bbox + score) ; ici le contrat est celui
/// du pipeline complet par frame, ce dont l'agrégateur 5.5 a besoin pour voter.
///
/// - `boundingBox` : normalisée 0–1, origine en haut à gauche (conventions §1.2).
/// - confidences ∈ [0, 1] ; `colorId == -1` = "unknown" (conventions §1.1).
struct RawDetection: Equatable, Sendable {
    let boundingBox: CGRect
    let partId: String
    let partConfidence: Double
    let colorId: Int
    let colorConfidence: Double
}

/// Contrat du pipeline d'analyse d'une frame.
///
/// Implémentations :
/// - `MockDetectionPipeline` (DEBUG) — détections plausibles et bruitées, sans modèle (CH-5) ;
/// - la vraie chaîne CoreML DET + CLS + COLOR arrive avec CH-3 (jalons 5.2–5.4).
protocol DetectionPipeline: Sendable {
    /// Analyse une frame (le CVPixelBuffer voyage dans `CapturedFrame`, propriété transférée).
    /// Inférence hors main thread à la charge de l'implémentation (conventions §2).
    func detections(in frame: CapturedFrame) async throws -> [RawDetection]
}
