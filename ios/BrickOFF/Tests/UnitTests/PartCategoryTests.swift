import XCTest
@testable import BrickOFF

final class PartCategoryTests: XCTestCase {

    func test_heuristic_standardBrickRange_isBrick() {
        XCTAssertEqual(PartCategory.heuristic(forPartId: "3001"), .brick)
        XCTAssertEqual(PartCategory.heuristic(forPartId: "3010"), .brick)
        XCTAssertEqual(PartCategory.heuristic(forPartId: "2456"), .brick)
    }

    func test_heuristic_standardPlateRange_isPlate() {
        XCTAssertEqual(PartCategory.heuristic(forPartId: "3020"), .plate)
        XCTAssertEqual(PartCategory.heuristic(forPartId: "3024"), .plate)
        XCTAssertEqual(PartCategory.heuristic(forPartId: "3710"), .plate)
    }

    func test_heuristic_knownTiles_isTile() {
        XCTAssertEqual(PartCategory.heuristic(forPartId: "3068"), .tile)
        XCTAssertEqual(PartCategory.heuristic(forPartId: "2431"), .tile)
        // Variante de moule avec suffixe lettré : le préfixe numérique fait foi.
        XCTAssertEqual(PartCategory.heuristic(forPartId: "3070b"), .tile)
    }

    func test_heuristic_unknownOrNonNumeric_isOther() {
        XCTAssertEqual(PartCategory.heuristic(forPartId: "99207"), .other)
        XCTAssertEqual(PartCategory.heuristic(forPartId: "54200"), .other)
        XCTAssertEqual(PartCategory.heuristic(forPartId: "x127"), .other)
        XCTAssertEqual(PartCategory.heuristic(forPartId: ""), .other)
    }
}
