import CoreGraphics
import Foundation
import Observation

/// ViewModel de l'écran de revue (jalon 5.6) : consolidation → corrections utilisateur
/// → ajout EXPLICITE à l'inventaire (aucun ajout silencieux, plan 5.6 critère 3).
///
/// Les pièces consolidées sont regroupées par (part_id, color_id) avec quantité.
/// Une pièce "incertaine" (couleur unknown ou confidence basse) part dans une section
/// dédiée, exclue par défaut de l'ajout — l'utilisateur doit l'inclure explicitement.
@MainActor
@Observable
final class ScanReviewViewModel {
    /// Seuil d'incertitude v0 — à recaler quand les vrais modèles (CH-3) donneront
    /// de vraies distributions de confidence.
    nonisolated static let uncertaintyThreshold = 0.6

    struct ReviewGroup: Identifiable {
        let id: UUID
        var partId: String
        var colorId: Int
        /// Moyennes des confidences des détections consolidées ; passées à 1.0
        /// quand l'utilisateur corrige (sa correction fait foi).
        var partConfidence: Double
        var colorConfidence: Double
        /// Inclure dans "Ajouter à l'inventaire" ? (Les incertaines démarrent à `false`.)
        var includeInInventory: Bool
        /// Détections consolidées sous-jacentes (bboxes conservées pour le payload §1.2).
        var detections: [DetectedPiece]

        var quantity: Int { detections.count }

        var isUncertain: Bool {
            colorId == -1
                || partConfidence < ScanReviewViewModel.uncertaintyThreshold
                || colorConfidence < ScanReviewViewModel.uncertaintyThreshold
        }
    }

    private(set) var groups: [ReviewGroup]
    /// Capture figée du scan (dernière frame analysée) — `nil` si la caméra n'a rien fourni.
    let capturedFrame: CapturedFrame?

    private(set) var isAdding = false
    private(set) var didAddToInventory = false
    var errorMessage: String?

    private let repository: any InventoryRepository

    init(
        pieces: [DetectedPiece],
        capturedFrame: CapturedFrame? = nil,
        repository: any InventoryRepository
    ) {
        self.capturedFrame = capturedFrame
        self.repository = repository
        self.groups = Self.makeGroups(from: pieces)
    }

    // MARK: - Lecture (sections de l'écran)

    var certainGroups: [ReviewGroup] { groups.filter { !$0.isUncertain } }
    var uncertainGroups: [ReviewGroup] { groups.filter(\.isUncertain) }

    /// Nombre de pièces qui seront réellement ajoutées.
    var includedPieceCount: Int {
        groups.filter(\.includeInInventory).map(\.quantity).reduce(0, +)
    }

    /// Bboxes consolidées pour l'overlay de la capture figée.
    var overlayBoxes: [(box: CGRect, isUncertain: Bool)] {
        groups.flatMap { group in
            group.detections.map { ($0.boundingBox, group.isUncertain) }
        }
    }

    // MARK: - Actions utilisateur (plan 5.6 : toutes les corrections)

    /// Supprime une détection consolidée (le groupe entier, avec sa quantité).
    func deleteGroup(_ id: UUID) {
        groups.removeAll { $0.id == id }
    }

    /// Corrige la couleur d'un groupe (picker palette v0). La correction fait foi
    /// (confidence → 1.0) ; les groupes devenus identiques sont fusionnés.
    func setColor(_ id: UUID, colorId: Int) {
        guard let index = groups.firstIndex(where: { $0.id == id }) else { return }
        groups[index].colorId = colorId
        groups[index].colorConfidence = 1.0
        includeIfNowCertain(at: index)
        mergeDuplicates()
    }

    /// Corrige le part_id d'un groupe (champ texte v0 — le top-5 du vrai classifieur
    /// viendra avec CH-3). Entrée vide ignorée.
    func setPartId(_ id: UUID, partId: String) {
        let trimmed = partId.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty, let index = groups.firstIndex(where: { $0.id == id }) else { return }
        groups[index].partId = trimmed
        groups[index].partConfidence = 1.0
        includeIfNowCertain(at: index)
        mergeDuplicates()
    }

    /// Inclusion explicite d'un groupe (seule voie d'ajout pour les incertaines).
    func setIncluded(_ id: UUID, _ included: Bool) {
        guard let index = groups.firstIndex(where: { $0.id == id }) else { return }
        groups[index].includeInInventory = included
    }

    /// Ajout à l'inventaire — le VRAI `InventoryRepository.addPieces` (CH-6),
    /// avec les corrections utilisateur appliquées au payload.
    /// - Returns: `true` si l'ajout a réussi.
    @discardableResult
    func addToInventory() async -> Bool {
        let included = groups.filter(\.includeInInventory)
        let pieces = included.flatMap { group in
            group.detections.map { detection in
                DetectedPiece(
                    id: UUID(),
                    partId: group.partId,
                    colorId: group.colorId,
                    boundingBox: detection.boundingBox,
                    partConfidence: group.partConfidence,
                    colorConfidence: group.colorConfidence
                )
            }
        }
        guard !pieces.isEmpty else { return false }

        isAdding = true
        defer { isAdding = false }
        do {
            try await repository.addPieces(pieces)
            didAddToInventory = true
            return true
        } catch {
            errorMessage = "L'ajout à l'inventaire a échoué. Réessayez."
            return false
        }
    }

    // MARK: - Privé

    private static func makeGroups(from pieces: [DetectedPiece]) -> [ReviewGroup] {
        struct Key: Hashable {
            let partId: String
            let colorId: Int
        }
        let byKey = Dictionary(grouping: pieces) { Key(partId: $0.partId, colorId: $0.colorId) }

        return byKey
            .map { key, members in
                let count = Double(members.count)
                let group = ReviewGroup(
                    id: UUID(),
                    partId: key.partId,
                    colorId: key.colorId,
                    partConfidence: members.map(\.partConfidence).reduce(0, +) / count,
                    colorConfidence: members.map(\.colorConfidence).reduce(0, +) / count,
                    includeInInventory: false,
                    detections: members
                )
                var configured = group
                configured.includeInInventory = !group.isUncertain
                return configured
            }
            // Ordre stable et lisible : quantité décroissante puis clé.
            .sorted {
                if $0.quantity != $1.quantity { return $0.quantity > $1.quantity }
                if $0.partId != $1.partId { return $0.partId < $1.partId }
                return $0.colorId < $1.colorId
            }
    }

    /// Un groupe corrigé qui n'est plus incertain devient inclus par défaut :
    /// l'utilisateur vient d'agir dessus explicitement, ce n'est pas un ajout silencieux.
    private func includeIfNowCertain(at index: Int) {
        if !groups[index].isUncertain {
            groups[index].includeInInventory = true
        }
    }

    /// Fusionne les groupes devenus identiques après correction (même part_id + color_id).
    private func mergeDuplicates() {
        var merged: [ReviewGroup] = []
        for group in groups {
            if let index = merged.firstIndex(where: {
                $0.partId == group.partId && $0.colorId == group.colorId
            }) {
                let total = Double(merged[index].quantity + group.quantity)
                merged[index].partConfidence =
                    (merged[index].partConfidence * Double(merged[index].quantity)
                        + group.partConfidence * Double(group.quantity)) / total
                merged[index].colorConfidence =
                    (merged[index].colorConfidence * Double(merged[index].quantity)
                        + group.colorConfidence * Double(group.quantity)) / total
                merged[index].detections += group.detections
                merged[index].includeInInventory =
                    merged[index].includeInInventory || group.includeInInventory
            } else {
                merged.append(group)
            }
        }
        groups = merged
    }
}
