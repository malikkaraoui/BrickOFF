import Foundation

struct LegoSet: Identifiable, Codable {
    let id: String
    let name: String
    let numParts: Int
    let year: Int
    let themeId: Int

    private enum CodingKeys: String, CodingKey {
        case id = "set_num"
        case name
        case numParts = "num_parts"
        case year
        case themeId = "theme_id"
    }
}
