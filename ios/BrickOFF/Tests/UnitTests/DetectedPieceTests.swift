import XCTest
@testable import BrickOFF

final class DetectedPieceTests: XCTestCase {

    private let contractJSON = """
    {
      "part_id": "3001",
      "color_id": 4,
      "bbox": {"x": 0.12, "y": 0.30, "w": 0.08, "h": 0.06},
      "part_confidence": 0.91,
      "color_confidence": 0.84
    }
    """

    func test_decode_contractSample_fieldsMatch() throws {
        let piece = try JSONDecoder().decode(DetectedPiece.self, from: Data(contractJSON.utf8))

        XCTAssertEqual(piece.partId, "3001")
        XCTAssertEqual(piece.colorId, 4)
        XCTAssertEqual(piece.boundingBox.origin.x, 0.12, accuracy: 1e-9)
        XCTAssertEqual(piece.boundingBox.origin.y, 0.30, accuracy: 1e-9)
        XCTAssertEqual(piece.boundingBox.width, 0.08, accuracy: 1e-9)
        XCTAssertEqual(piece.boundingBox.height, 0.06, accuracy: 1e-9)
        XCTAssertEqual(piece.partConfidence, 0.91, accuracy: 1e-9)
        XCTAssertEqual(piece.colorConfidence, 0.84, accuracy: 1e-9)
    }

    func test_encode_pieceToJSON_keysAreSnakeCaseContract() throws {
        let piece = DetectedPiece(
            id: UUID(),
            partId: "3001",
            colorId: 4,
            boundingBox: CGRect(x: 0.12, y: 0.30, width: 0.08, height: 0.06),
            partConfidence: 0.91,
            colorConfidence: 0.84
        )

        let data = try JSONEncoder().encode(piece)
        let object = try XCTUnwrap(
            JSONSerialization.jsonObject(with: data) as? [String: Any]
        )

        XCTAssertEqual(
            Set(object.keys),
            ["part_id", "color_id", "bbox", "part_confidence", "color_confidence"]
        )
        let bbox = try XCTUnwrap(object["bbox"] as? [String: Any])
        XCTAssertEqual(Set(bbox.keys), ["x", "y", "w", "h"])
        XCTAssertEqual(object["part_id"] as? String, "3001")
        XCTAssertEqual(object["color_id"] as? Int, 4)
    }

    func test_roundTrip_encodeDecode_valuesPreserved() throws {
        let original = DetectedPiece(
            id: UUID(),
            partId: "3020",
            colorId: -1,
            boundingBox: CGRect(x: 0.5, y: 0.25, width: 0.1, height: 0.2),
            partConfidence: 0.5,
            colorConfidence: 0.0
        )

        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(DetectedPiece.self, from: data)

        XCTAssertEqual(decoded.partId, original.partId)
        XCTAssertEqual(decoded.colorId, original.colorId)
        XCTAssertEqual(decoded.boundingBox, original.boundingBox)
        XCTAssertEqual(decoded.partConfidence, original.partConfidence)
        XCTAssertEqual(decoded.colorConfidence, original.colorConfidence)
    }

    func test_decode_twice_generatesDistinctLocalIds() throws {
        let decoder = JSONDecoder()
        let data = Data(contractJSON.utf8)

        let first = try decoder.decode(DetectedPiece.self, from: data)
        let second = try decoder.decode(DetectedPiece.self, from: data)

        XCTAssertNotEqual(first.id, second.id)
    }
}
