import CoreGraphics
import Foundation

struct DetectedPiece: Identifiable, Codable {
    let id: UUID
    let partId: String
    let colorId: Int
    let boundingBox: CGRect
    let partConfidence: Double
    let colorConfidence: Double
}

extension DetectedPiece {
    private enum CodingKeys: String, CodingKey {
        case partId = "part_id"
        case colorId = "color_id"
        case boundingBox = "bbox"
        case partConfidence = "part_confidence"
        case colorConfidence = "color_confidence"
    }

    private struct BoundingBox: Codable {
        let x: Double
        let y: Double
        let w: Double
        let h: Double
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.id = UUID()
        self.partId = try container.decode(String.self, forKey: .partId)
        self.colorId = try container.decode(Int.self, forKey: .colorId)
        let bbox = try container.decode(BoundingBox.self, forKey: .boundingBox)
        self.boundingBox = CGRect(x: bbox.x, y: bbox.y, width: bbox.w, height: bbox.h)
        self.partConfidence = try container.decode(Double.self, forKey: .partConfidence)
        self.colorConfidence = try container.decode(Double.self, forKey: .colorConfidence)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(partId, forKey: .partId)
        try container.encode(colorId, forKey: .colorId)
        let bbox = BoundingBox(
            x: boundingBox.origin.x,
            y: boundingBox.origin.y,
            w: boundingBox.width,
            h: boundingBox.height
        )
        try container.encode(bbox, forKey: .boundingBox)
        try container.encode(partConfidence, forKey: .partConfidence)
        try container.encode(colorConfidence, forKey: .colorConfidence)
    }
}
