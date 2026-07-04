import XCTest
@testable import BrickOFF

final class LegoSetTests: XCTestCase {

    func test_decode_rebrickableStyleJSON_fieldsMatch() throws {
        let json = """
        {"set_num": "31058-1", "name": "Mighty Dinosaurs", "num_parts": 174, "year": 2017, "theme_id": 671}
        """

        let set = try JSONDecoder().decode(LegoSet.self, from: Data(json.utf8))

        XCTAssertEqual(set.id, "31058-1")
        XCTAssertEqual(set.name, "Mighty Dinosaurs")
        XCTAssertEqual(set.numParts, 174)
        XCTAssertEqual(set.year, 2017)
        XCTAssertEqual(set.themeId, 671)
    }

    func test_encode_setToJSON_keysAreSnakeCase() throws {
        let set = LegoSet(id: "31058-1", name: "Mighty Dinosaurs", numParts: 174, year: 2017, themeId: 671)

        let data = try JSONEncoder().encode(set)
        let object = try XCTUnwrap(
            JSONSerialization.jsonObject(with: data) as? [String: Any]
        )

        XCTAssertEqual(Set(object.keys), ["set_num", "name", "num_parts", "year", "theme_id"])
        XCTAssertEqual(object["set_num"] as? String, "31058-1")
    }

    func test_roundTrip_encodeDecode_valuesPreserved() throws {
        let original = LegoSet(id: "10696-1", name: "Medium Creative Brick Box", numParts: 484, year: 2015, themeId: 513)

        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(LegoSet.self, from: data)

        XCTAssertEqual(decoded.id, original.id)
        XCTAssertEqual(decoded.name, original.name)
        XCTAssertEqual(decoded.numParts, original.numParts)
        XCTAssertEqual(decoded.year, original.year)
        XCTAssertEqual(decoded.themeId, original.themeId)
    }
}
