import Foundation

struct SetMatchResult: Identifiable {
    let id: String
    let set: LegoSet
    let coverage: Double
    let missingParts: [InventoryItem]
}
