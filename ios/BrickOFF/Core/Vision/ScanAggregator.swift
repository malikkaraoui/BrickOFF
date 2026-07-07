import CoreGraphics
import Foundation

/// Jalon 5.5 — Consolidation multi-frames d'un scan déclenché.
///
/// Décision UX figée (plan 5.5) : le scan est une action déclenchée — l'utilisateur cadre,
/// appuie sur "Scanner", on capture N = 5 frames consécutives analysées (~2,5 s) puis on
/// consolide. Algorithme V1 :
///   1. appariement inter-frames : même pièce si IoU > 0.5 (glouton, IoU décroissant,
///      une détection ↔ un track par frame) ;
///   2. part_id et color_id = vote majoritaire pondéré par confidence ;
///   3. confidence finale = moyenne des votes gagnants ;
///   4. rejet des pièces vues sur < 3 frames sur 5 (faux positifs transitoires).
///
/// `actor` : thread-safety par construction (conventions §2 — agrégateur = actor).
actor ScanAggregator {
    struct Configuration: Sendable {
        /// Nombre de frames analysées par scan (plan 5.5 : N = 5).
        var frameCount = 5
        /// Seuil d'appariement inter-frames (plan 5.5 : IoU > 0.5).
        var iouThreshold = 0.5
        /// Nombre minimal de frames où une pièce doit être vue (plan 5.5 : 3/5).
        var minimumFrameAppearances = 3

        static let standard = Configuration()
    }

    /// Pièce en cours de consolidation : ses occurrences (≤ 1 par frame) et sa
    /// dernière bbox connue (référence d'appariement pour la frame suivante).
    private struct Track {
        var detections: [RawDetection]
        var lastBoundingBox: CGRect
    }

    let configuration: Configuration
    private var tracks: [Track] = []
    private(set) var framesAdded = 0

    init(configuration: Configuration = .standard) {
        self.configuration = configuration
    }

    /// Toutes les frames attendues ont-elles été ajoutées ?
    var isComplete: Bool { framesAdded >= configuration.frameCount }

    /// Ajoute les détections d'une frame analysée.
    ///
    /// Appariement glouton : les paires (track, détection) sont triées par IoU décroissant ;
    /// chaque track reçoit au plus une détection par frame, chaque détection rejoint au plus
    /// un track. Les détections non appariées ouvrent de nouveaux tracks.
    func add(frameDetections: [RawDetection]) {
        framesAdded += 1

        var candidates: [(trackIndex: Int, detectionIndex: Int, iou: Double)] = []
        for (trackIndex, track) in tracks.enumerated() {
            for (detectionIndex, detection) in frameDetections.enumerated() {
                let iou = Self.iou(track.lastBoundingBox, detection.boundingBox)
                if iou > configuration.iouThreshold {
                    candidates.append((trackIndex, detectionIndex, iou))
                }
            }
        }
        candidates.sort { $0.iou > $1.iou }

        var matchedTracks = Set<Int>()
        var matchedDetections = Set<Int>()
        for candidate in candidates
        where !matchedTracks.contains(candidate.trackIndex)
            && !matchedDetections.contains(candidate.detectionIndex) {
            matchedTracks.insert(candidate.trackIndex)
            matchedDetections.insert(candidate.detectionIndex)
            let detection = frameDetections[candidate.detectionIndex]
            tracks[candidate.trackIndex].detections.append(detection)
            tracks[candidate.trackIndex].lastBoundingBox = detection.boundingBox
        }

        for (detectionIndex, detection) in frameDetections.enumerated()
        where !matchedDetections.contains(detectionIndex) {
            tracks.append(Track(detections: [detection], lastBoundingBox: detection.boundingBox))
        }
    }

    /// Consolide les tracks en pièces détectées, en rejetant les transitoires
    /// (vues sur moins de `minimumFrameAppearances` frames).
    func aggregate() -> [DetectedPiece] {
        tracks
            .filter { $0.detections.count >= configuration.minimumFrameAppearances }
            .map { Self.consolidate($0.detections) }
    }

    /// Réinitialise l'agrégateur pour un nouveau scan.
    func reset() {
        tracks = []
        framesAdded = 0
    }

    // MARK: - Logique pure (statique, testable sans actor)

    /// Intersection-over-Union de deux rectangles (0 si disjoints ou dégénérés).
    static func iou(_ a: CGRect, _ b: CGRect) -> Double {
        let intersection = a.intersection(b)
        guard !intersection.isNull, !intersection.isEmpty else { return 0 }
        let intersectionArea = Double(intersection.width * intersection.height)
        let unionArea = Double(a.width * a.height + b.width * b.height) - intersectionArea
        guard unionArea > 0 else { return 0 }
        return intersectionArea / unionArea
    }

    /// Vote majoritaire pondéré par confidence.
    /// - Returns: la valeur dont la somme des confidences est maximale, et la moyenne
    ///   des confidences des votes gagnants (plan 5.5, étape 3).
    ///   Égalité départagée de façon déterministe par la valeur elle-même.
    static func weightedVote<Value: Hashable & Comparable>(
        _ votes: [(value: Value, confidence: Double)]
    ) -> (winner: Value, meanConfidence: Double)? {
        guard !votes.isEmpty else { return nil }

        var confidenceSums: [Value: Double] = [:]
        for vote in votes {
            confidenceSums[vote.value, default: 0] += vote.confidence
        }
        let winner = confidenceSums
            .sorted { lhs, rhs in
                lhs.value != rhs.value ? lhs.value > rhs.value : lhs.key < rhs.key
            }
            .first!
            .key

        let winningVotes = votes.filter { $0.value == winner }
        let mean = winningVotes.map(\.confidence).reduce(0, +) / Double(winningVotes.count)
        return (winner, mean)
    }

    /// Fusionne les occurrences d'un track en une pièce consolidée
    /// (votes pondérés + bbox moyenne).
    static func consolidate(_ detections: [RawDetection]) -> DetectedPiece {
        // `detections` n'est jamais vide (un track naît avec une détection).
        let part = weightedVote(detections.map { (value: $0.partId, confidence: $0.partConfidence) })!
        let color = weightedVote(detections.map { (value: $0.colorId, confidence: $0.colorConfidence) })!

        let count = CGFloat(detections.count)
        let boxes = detections.map(\.boundingBox)
        let meanBox = CGRect(
            x: boxes.map(\.origin.x).reduce(0, +) / count,
            y: boxes.map(\.origin.y).reduce(0, +) / count,
            width: boxes.map(\.width).reduce(0, +) / count,
            height: boxes.map(\.height).reduce(0, +) / count
        )

        return DetectedPiece(
            id: UUID(),
            partId: part.winner,
            colorId: color.winner,
            boundingBox: meanBox,
            partConfidence: part.meanConfidence,
            colorConfidence: color.meanConfidence
        )
    }
}
