import XCTest
@testable import BrickOFF

final class InventoryItemTests: XCTestCase {

    func test_decode_contractSample_fieldsMatch() throws {
        let json = """
        {"part_id": "3001", "color_id": 4, "quantity": 12}
        """

        let item = try JSONDecoder().decode(InventoryItem.self, from: Data(json.utf8))

        XCTAssertEqual(item, InventoryItem(partId: "3001", colorId: 4, quantity: 12))
    }

    func test_encode_itemToJSON_keysAreSnakeCaseContract() throws {
        let item = InventoryItem(partId: "3001", colorId: 4, quantity: 12)

        let data = try JSONEncoder().encode(item)
        let object = try XCTUnwrap(
            JSONSerialization.jsonObject(with: data) as? [String: Any]
        )

        XCTAssertEqual(Set(object.keys), ["part_id", "color_id", "quantity"])
        XCTAssertEqual(object["part_id"] as? String, "3001")
        XCTAssertEqual(object["color_id"] as? Int, 4)
        XCTAssertEqual(object["quantity"] as? Int, 12)
    }

    func test_roundTrip_encodeDecode_equalValue() throws {
        let original = InventoryItem(partId: "3020", colorId: -1, quantity: 1)

        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(InventoryItem.self, from: data)

        XCTAssertEqual(decoded, original)
    }
}
