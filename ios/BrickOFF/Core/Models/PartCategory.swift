import Foundation

/// Catégorie d'affichage d'une pièce (écran inventaire, CH-6 jalon 6.3).
///
/// ⚠️ CATÉGORISATION HEURISTIQUE v0 (écart documenté dans CHANGELOG_CH6) :
/// le mapping catégorie officiel viendra du catalogue `rebrickable.sqlite`
/// (table part_categories, CH-7/CH-10). En attendant, on classe par le numéro
/// de moule `part_id`, en s'appuyant sur les plages de numérotation LEGO
/// classiques — approximation assumée, uniquement cosmétique (regroupement UI).
enum PartCategory: String, CaseIterable, Sendable {
    case brick
    case plate
    case tile
    case other

    /// Heuristique v0 : plages/valeurs connues du numéro de moule.
    /// - briques : 3001–3019 (3001…3010 briques standard) + moules connus hors plage
    /// - plates  : 3020–3036 + moules connus hors plage (3460, 3623, 3666, 3710…)
    /// - tiles   : liste explicite (3068–3070, 2431, 6636…)
    /// - tout le reste : `other`
    static func heuristic(forPartId partId: String) -> PartCategory {
        // Numéro de moule = préfixe numérique du part_id ("3001", "3070b" → 3070, "99207"…).
        guard let mold = Int(partId.prefix(while: \.isNumber)) else { return .other }

        if knownTiles.contains(mold) { return .tile }
        if knownBricks.contains(mold) || (3001...3019).contains(mold) { return .brick }
        if knownPlates.contains(mold) || (3020...3036).contains(mold) { return .plate }
        return .other
    }

    // Moules fréquents hors plages (scope V1 ~1000 pièces) — v0, non exhaustif.
    private static let knownBricks: Set<Int> = [2357, 2456, 3062, 3065, 3622, 30145]
    private static let knownPlates: Set<Int> = [2420, 3460, 3623, 3666, 3710, 3795, 3832, 60479]
    private static let knownTiles: Set<Int> = [2431, 3068, 3069, 3070, 4162, 6636, 63864, 87079]

    // MARK: - Affichage (UI brute 6.3, habillage réel en CH-8)

    /// Titre de section dans la liste groupée.
    var sectionTitle: String {
        switch self {
        case .brick: "Briques"
        case .plate: "Plates"
        case .tile: "Tiles"
        case .other: "Autres pièces"
        }
    }

    /// Nom v0 d'une pièce (pas encore de catalogue de noms) : "Brique 3001".
    var pieceDisplayName: String {
        switch self {
        case .brick: "Brique"
        case .plate: "Plate"
        case .tile: "Tile"
        case .other: "Pièce"
        }
    }

    /// Picto SF Symbol générique par catégorie (fallback D09 : pas d'images tierces).
    var systemImage: String {
        switch self {
        case .brick: "cube.fill"
        case .plate: "square.stack.3d.up.fill"
        case .tile: "square.fill"
        case .other: "puzzlepiece.fill"
        }
    }
}
