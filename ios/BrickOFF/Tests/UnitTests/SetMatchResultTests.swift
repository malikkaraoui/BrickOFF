import XCTest
@testable import BrickOFF

final class SetMatchResultTests: XCTestCase {

    func test_init_withSetAndMissingParts_fieldsExposed() {
        let set = LegoSet(id: "31058-1", name: "Mighty Dinosaurs", numParts: 174, year: 2017, themeId: 671)
        let missing = [InventoryItem(partId: "3001", colorId: 4, quantity: 2)]

        let result = SetMatchResult(id: set.id, set: set, coverage: 0.85, missingParts: missing)

        XCTAssertEqual(result.id, "31058-1")
        XCTAssertEqual(result.set.name, "Mighty Dinosaurs")
        XCTAssertEqual(result.coverage, 0.85, accuracy: 1e-9)
        XCTAssertEqual(result.missingParts, missing)
    }
}
