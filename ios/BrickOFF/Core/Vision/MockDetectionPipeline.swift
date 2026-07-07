#if DEBUG
import CoreGraphics
import Foundation

/// Générateur pseudo-aléatoire seedable (SplitMix64) — scènes mock reproductibles.
struct SplitMix64: RandomNumberGenerator, Sendable {
    private var state: UInt64

    init(seed: UInt64) {
        self.state = seed
    }

    mutating func next() -> UInt64 {
        state &+= 0x9E3779B97F4A7C15
        var z = state
        z = (z ^ (z >> 30)) &* 0xBF58476D1CE4E5B9
        z = (z ^ (z >> 27)) &* 0x94D049BB133111EB
        return z ^ (z >> 31)
    }
}

/// Pipeline de détection FACTICE (CH-5, en attendant les modèles CoreML de CH-3).
///
/// Simule une scène fixe de pièces vue sur plusieurs frames, avec le bruit attendu
/// du vrai pipeline : jitter de bbox et de confidence entre frames, détections
/// manquées, part_id/color_id occasionnellement erronés, faux positifs transitoires.
/// Sert à développer et tester l'agrégation (5.5) et l'écran de revue (5.6).
///
/// `actor` : l'état du RNG mute à chaque frame — thread-safety par construction.
actor MockDetectionPipeline: DetectionPipeline {
    struct ScenePiece: Sendable {
        let partId: String
        let colorId: Int
        let boundingBox: CGRect
        let partConfidence: Double
        let colorConfidence: Double
        /// Probabilité d'être détectée sur une frame donnée (détections manquées).
        let visibility: Double
    }

    /// Scène par défaut : 6 pièces plausibles du scope V1, dont une volontairement
    /// incertaine (colorConfidence basse) pour exercer la section "incertaines" de 5.6.
    static let defaultScene: [ScenePiece] = [
        ScenePiece(partId: "3001", colorId: 4, boundingBox: CGRect(x: 0.08, y: 0.12, width: 0.16, height: 0.11),
                   partConfidence: 0.93, colorConfidence: 0.90, visibility: 0.95),
        ScenePiece(partId: "3004", colorId: 1, boundingBox: CGRect(x: 0.55, y: 0.10, width: 0.12, height: 0.09),
                   partConfidence: 0.88, colorConfidence: 0.92, visibility: 0.95),
        ScenePiece(partId: "3020", colorId: 14, boundingBox: CGRect(x: 0.15, y: 0.45, width: 0.18, height: 0.08),
                   partConfidence: 0.85, colorConfidence: 0.87, visibility: 0.90),
        ScenePiece(partId: "3020", colorId: 14, boundingBox: CGRect(x: 0.60, y: 0.50, width: 0.18, height: 0.08),
                   partConfidence: 0.83, colorConfidence: 0.89, visibility: 0.90),
        ScenePiece(partId: "3070", colorId: 0, boundingBox: CGRect(x: 0.40, y: 0.75, width: 0.08, height: 0.07),
                   partConfidence: 0.78, colorConfidence: 0.85, visibility: 0.85),
        // Pièce incertaine : la couleur hésite → doit finir en section "incertaines".
        ScenePiece(partId: "3062", colorId: 2, boundingBox: CGRect(x: 0.75, y: 0.78, width: 0.07, height: 0.07),
                   partConfidence: 0.72, colorConfidence: 0.42, visibility: 0.90),
    ]

    /// Couleurs vers lesquelles une détection peut "glisser" (bruit du pipeline couleur).
    private static let noiseColorIds = [0, 1, 2, 4, 14, 15, 19, 71, 72]
    /// part_ids parasites pour les faux positifs.
    private static let noisePartIds = ["3001", "3003", "3022", "3069", "2431", "3710"]

    private let scene: [ScenePiece]
    private let inferenceDelay: Duration
    private var rng: SplitMix64

    init(
        scene: [ScenePiece] = MockDetectionPipeline.defaultScene,
        seed: UInt64 = UInt64.random(in: .min ... .max),
        inferenceDelay: Duration = .milliseconds(80)
    ) {
        self.scene = scene
        self.inferenceDelay = inferenceDelay
        self.rng = SplitMix64(seed: seed)
    }

    func detections(in frame: CapturedFrame) async throws -> [RawDetection] {
        if inferenceDelay > .zero {
            try? await Task.sleep(for: inferenceDelay) // simule la latence d'inférence
        }

        var detections: [RawDetection] = []

        for piece in scene {
            // Détection manquée occasionnelle.
            guard random() < piece.visibility else { continue }

            // Jitter de bbox (device tenu "stable" mais pas parfaitement).
            let box = CGRect(
                x: clamp(piece.boundingBox.origin.x + jitter(0.012)),
                y: clamp(piece.boundingBox.origin.y + jitter(0.012)),
                width: clamp(piece.boundingBox.width + jitter(0.006)),
                height: clamp(piece.boundingBox.height + jitter(0.006))
            )

            // Bruit de classification / couleur occasionnel.
            var partId = piece.partId
            if random() < 0.05 {
                partId = Self.noisePartIds.randomElement(using: &rng)!
            }
            var colorId = piece.colorId
            if random() < 0.08 {
                colorId = Self.noiseColorIds.randomElement(using: &rng)!
            }

            detections.append(RawDetection(
                boundingBox: box,
                partId: partId,
                partConfidence: jitteredConfidence(piece.partConfidence),
                colorId: colorId,
                colorConfidence: jitteredConfidence(piece.colorConfidence)
            ))
        }

        // Faux positif transitoire (~1 frame sur 5, position aléatoire → non apparié
        // entre frames → doit être rejeté par le filtre 3/5 de l'agrégateur).
        if random() < 0.2 {
            detections.append(RawDetection(
                boundingBox: CGRect(
                    x: CGFloat(Double.random(in: 0...0.9, using: &rng)),
                    y: CGFloat(Double.random(in: 0...0.9, using: &rng)),
                    width: 0.05,
                    height: 0.05
                ),
                partId: Self.noisePartIds.randomElement(using: &rng)!,
                partConfidence: Double.random(in: 0.36...0.55, using: &rng),
                colorId: Self.noiseColorIds.randomElement(using: &rng)!,
                colorConfidence: Double.random(in: 0.3...0.6, using: &rng)
            ))
        }

        return detections
    }

    // MARK: - Bruit

    private func random() -> Double {
        Double.random(in: 0..<1, using: &rng)
    }

    private func jitter(_ amplitude: Double) -> CGFloat {
        CGFloat(Double.random(in: -amplitude...amplitude, using: &rng))
    }

    private func jitteredConfidence(_ base: Double) -> Double {
        min(0.99, max(0.05, base + Double.random(in: -0.06...0.06, using: &rng)))
    }

    private func clamp(_ value: CGFloat) -> CGFloat {
        min(1, max(0, value))
    }
}

/// Source de frames factice pour le simulateur (pas de caméra réelle) :
/// cadence ~400 ms, frames unies — `MockDetectionPipeline` ignore les pixels,
/// le flux scan → agrégation → revue reste donc testable de bout en bout.
final class MockScanFrameSource: ScanCameraControlling {
    private let frameDelay: Duration

    /// - Parameter frameDelay: cadence des frames (défaut : 400 ms, comme le throttle réel ;
    ///   `.zero` en tests pour ne pas ralentir la suite).
    init(frameDelay: Duration = .milliseconds(400)) {
        self.frameDelay = frameDelay
    }

    var previewSource: CameraPreviewSource? { nil }

    func start() async throws {}

    func stop() async {}

    func nextFrame() async -> CapturedFrame? {
        if frameDelay > .zero {
            try? await Task.sleep(for: frameDelay)
        }
        return .blank()
    }
}
#endif
