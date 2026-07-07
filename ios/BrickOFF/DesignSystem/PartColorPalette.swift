import SwiftUI

/// Pastille couleur des pièces (D09 : fallback pictos + pastille, aucune image tierce).
///
/// v0 : mapping statique des `color_id` Rebrickable les plus fréquents vers leur RGB
/// officiel. La table complète des couleurs viendra avec `rebrickable.sqlite`
/// (CH-7/CH-10) ; un id inconnu ou `-1` ("unknown", conventions §1.1) rend un gris hachuré.
enum PartColorPalette {
    /// Couleur d'affichage pour un `color_id` Rebrickable. `nil` si l'id est inconnu.
    static func color(forColorId colorId: Int) -> Color? {
        known[colorId].map { Color(red: $0.r, green: $0.g, blue: $0.b) }
    }

    /// Ids proposés par le picker de correction de couleur (écran de revue, CH-5 jalon 5.6).
    /// v0 : les couleurs du mapping statique — la palette complète viendra du catalogue.
    static var knownColorIds: [Int] { known.keys.sorted() }

    /// RGB officiels Rebrickable (hex de la table colors) pour les ids courants du scope V1.
    private static let known: [Int: (r: Double, g: Double, b: Double)] = [
        0: rgb(0x05, 0x13, 0x1D),   // Black
        1: rgb(0x00, 0x55, 0xBF),   // Blue
        2: rgb(0x23, 0x78, 0x41),   // Green
        3: rgb(0x00, 0x8F, 0x9B),   // Dark Turquoise
        4: rgb(0xC9, 0x1A, 0x09),   // Red
        5: rgb(0xC8, 0x70, 0xA0),   // Dark Pink
        6: rgb(0x58, 0x39, 0x27),   // Brown
        7: rgb(0x9B, 0xA1, 0x9D),   // Light Gray
        8: rgb(0x6D, 0x6E, 0x5C),   // Dark Gray
        9: rgb(0xB4, 0xD2, 0xE3),   // Light Blue
        10: rgb(0x4B, 0x9F, 0x4A),  // Bright Green
        14: rgb(0xF2, 0xCD, 0x37),  // Yellow
        15: rgb(0xFF, 0xFF, 0xFF),  // White
        19: rgb(0xE4, 0xCD, 0x9E),  // Tan
        25: rgb(0xFE, 0x8A, 0x18),  // Orange
        27: rgb(0xBB, 0xE9, 0x0B),  // Lime
        28: rgb(0x95, 0x8A, 0x73),  // Dark Tan
        46: rgb(0xF5, 0xCD, 0x2F),  // Trans-Yellow
        70: rgb(0x58, 0x2A, 0x12),  // Reddish Brown
        71: rgb(0xA0, 0xA5, 0xA9),  // Light Bluish Gray
        72: rgb(0x6C, 0x6E, 0x68),  // Dark Bluish Gray
        84: rgb(0xCC, 0x70, 0x2A),  // Medium Nougat
        320: rgb(0x72, 0x0E, 0x0F), // Dark Red
    ]

    private static func rgb(_ r: Int, _ g: Int, _ b: Int) -> (r: Double, g: Double, b: Double) {
        (Double(r) / 255, Double(g) / 255, Double(b) / 255)
    }
}

/// Pastille ronde : couleur pleine si connue, gris + "?" sinon (dont color_id = -1).
struct PartColorSwatch: View {
    let colorId: Int
    var diameter: CGFloat = 14

    var body: some View {
        Circle()
            .fill(PartColorPalette.color(forColorId: colorId) ?? Color(.systemGray4))
            .overlay {
                if PartColorPalette.color(forColorId: colorId) == nil {
                    Text("?")
                        .font(.system(size: diameter * 0.6, weight: .bold))
                        .foregroundStyle(.secondary)
                }
            }
            .overlay(Circle().strokeBorder(.quaternary, lineWidth: 1))
            .frame(width: diameter, height: diameter)
            .accessibilityLabel("Couleur \(colorId)")
    }
}
