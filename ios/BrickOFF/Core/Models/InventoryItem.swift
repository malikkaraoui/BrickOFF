import Foundation

struct InventoryItem: Codable, Equatable {
    let partId: String
    let colorId: Int
    var quantity: Int

    private enum CodingKeys: String, CodingKey {
        case partId = "part_id"
        case colorId = "color_id"
        case quantity
    }
}
