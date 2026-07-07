import CoreGraphics
import XCTest
@testable import BrickOFF

/// Jalon 5.5 — appariement IoU, vote pondéré, rejet des transitoires.
/// Fixtures déterministes construites à la main (aucun aléa).
final class ScanAggregatorTests: XCTestCase {
    // MARK: - Fixtures

    /// Détection de référence : bbox (x, y, 0.1 × 0.1), part 3001 rouge, confidences 0.9.
    private func detection(
        x: Double,
        y: Double,
        width: Double = 0.1,
        height: Double = 0.1,
        partId: String = "3001",
        partConfidence: Double = 0.9,
        colorId: Int = 4,
        colorConfidence: Double = 0.9
    ) -> RawDetection {
        RawDetection(
            boundingBox: CGRect(x: x, y: y, width: width, height: height),
            partId: partId,
            partConfidence: partConfidence,
            colorId: colorId,
            colorConfidence: colorConfidence
        )
    }

    // MARK: - IoU

    func test_iou_identicalRects_isOne() {
        let rect = CGRect(x: 0.2, y: 0.2, width: 0.3, height: 0.3)
        XCTAssertEqual(ScanAggregator.iou(rect, rect), 1.0, accuracy: 1e-9)
    }

    func test_iou_disjointRects_isZero() {
        XCTAssertEqual(
            ScanAggregator.iou(
                CGRect(x: 0, y: 0, width: 0.1, height: 0.1),
                CGRect(x: 0.5, y: 0.5, width: 0.1, height: 0.1)
            ),
            0
        )
    }

    func test_iou_halfShiftedRects_isOneThird() {
        // Deux carrés unité décalés de moitié : inter = 0.5, union = 1.5 → IoU = 1/3.
        let iou = ScanAggregator.iou(
            CGRect(x: 0, y: 0, width: 1, height: 1),
            CGRect(x: 0.5, y: 0, width: 1, height: 1)
        )
        XCTAssertEqual(iou, 1.0 / 3.0, accuracy: 1e-9)
    }

    func test_iou_degenerateRect_isZero() {
        XCTAssertEqual(
            ScanAggregator.iou(
                CGRect(x: 0, y: 0, width: 0, height: 0),
                CGRect(x: 0, y: 0, width: 0.1, height: 0.1)
            ),
            0
        )
    }

    // MARK: - Vote pondéré

    func test_weightedVote_higherSummedConfidence_wins() {
        // 3 votes "3001" (somme 1.5) vs 2 votes "3020" (somme 1.8) → 3020 gagne.
        let result = ScanAggregator.weightedVote([
            ("3001", 0.5), ("3001", 0.5), ("3001", 0.5),
            ("3020", 0.9), ("3020", 0.9),
        ])
        XCTAssertEqual(result?.winner, "3020")
        XCTAssertEqual(result!.meanConfidence, 0.9, accuracy: 1e-9)
    }

    func test_weightedVote_meanConfidence_isMeanOfWinningVotesOnly() {
        let result = ScanAggregator.weightedVote([
            (4, 0.8), (4, 0.9), (1, 0.2),
        ])
        XCTAssertEqual(result?.winner, 4)
        XCTAssertEqual(result!.meanConfidence, 0.85, accuracy: 1e-9)
    }

    func test_weightedVote_tie_deterministicSmallestValue() {
        let result = ScanAggregator.weightedVote([("B", 0.5), ("A", 0.5)])
        XCTAssertEqual(result?.winner, "A")
    }

    func test_weightedVote_empty_returnsNil() {
        let noVotes: [(value: String, confidence: Double)] = []
        XCTAssertNil(ScanAggregator.weightedVote(noVotes))
    }

    // MARK: - Appariement inter-frames

    func test_add_samePieceJitteredAcrossFiveFrames_consolidatesToOnePiece() async {
        let aggregator = ScanAggregator()
        for frame in 0..<5 {
            let jitter = Double(frame) * 0.004 // léger dérive, IoU >> 0.5 entre frames
            await aggregator.add(frameDetections: [detection(x: 0.2 + jitter, y: 0.3)])
        }
        let pieces = await aggregator.aggregate()
        XCTAssertEqual(pieces.count, 1)
        XCTAssertEqual(pieces.first?.partId, "3001")
        XCTAssertEqual(pieces.first?.colorId, 4)
    }

    func test_add_twoDistantPieces_consolidateToTwoPieces() async {
        let aggregator = ScanAggregator()
        for _ in 0..<5 {
            await aggregator.add(frameDetections: [
                detection(x: 0.1, y: 0.1),
                detection(x: 0.7, y: 0.7, partId: "3020", colorId: 14),
            ])
        }
        let pieces = await aggregator.aggregate()
        XCTAssertEqual(pieces.count, 2)
        XCTAssertEqual(Set(pieces.map(\.partId)), ["3001", "3020"])
    }

    func test_add_twoOverlappingDetectionsSameFrame_onlyOneJoinsTrack() async {
        let aggregator = ScanAggregator()
        await aggregator.add(frameDetections: [detection(x: 0.2, y: 0.2)])
        // Frame 2 : deux détections identiques → une rejoint le track, l'autre ouvre le sien.
        await aggregator.add(frameDetections: [detection(x: 0.2, y: 0.2), detection(x: 0.2, y: 0.2)])
        await aggregator.add(frameDetections: [detection(x: 0.2, y: 0.2)])
        await aggregator.add(frameDetections: [detection(x: 0.2, y: 0.2)])
        await aggregator.add(frameDetections: [detection(x: 0.2, y: 0.2)])

        let pieces = await aggregator.aggregate()
        // Track principal : 5 occurrences (gardé). Track du doublon : 1 occurrence (rejeté).
        XCTAssertEqual(pieces.count, 1)
    }

    // MARK: - Rejet des transitoires (< 3 frames sur 5)

    func test_aggregate_pieceSeenTwoFrames_rejected() async {
        let aggregator = ScanAggregator()
        await aggregator.add(frameDetections: [detection(x: 0.2, y: 0.2)])
        await aggregator.add(frameDetections: [detection(x: 0.2, y: 0.2)])
        await aggregator.add(frameDetections: [])
        await aggregator.add(frameDetections: [])
        await aggregator.add(frameDetections: [])
        let pieces = await aggregator.aggregate()
        XCTAssertTrue(pieces.isEmpty)
    }

    func test_aggregate_pieceSeenThreeFrames_kept() async {
        let aggregator = ScanAggregator()
        await aggregator.add(frameDetections: [detection(x: 0.2, y: 0.2)])
        await aggregator.add(frameDetections: [detection(x: 0.2, y: 0.2)])
        await aggregator.add(frameDetections: [detection(x: 0.2, y: 0.2)])
        await aggregator.add(frameDetections: [])
        await aggregator.add(frameDetections: [])
        let pieces = await aggregator.aggregate()
        XCTAssertEqual(pieces.count, 1)
    }

    func test_aggregate_movingFalsePositive_rejected() async {
        let aggregator = ScanAggregator()
        // Un faux positif qui saute à un endroit différent (disjoint) à chaque frame :
        // aucun appariement possible → 5 tracks d'une occurrence → tous rejetés.
        let positions = [(0.0, 0.0), (0.4, 0.0), (0.8, 0.0), (0.0, 0.5), (0.4, 0.5)]
        for (x, y) in positions {
            await aggregator.add(frameDetections: [detection(x: x, y: y)])
        }
        let pieces = await aggregator.aggregate()
        XCTAssertTrue(pieces.isEmpty)
    }

    // MARK: - Votes sur un track consolidé

    func test_aggregate_partIdVote_weightedByConfidence() async {
        let aggregator = ScanAggregator()
        // Même bbox sur 5 frames : 3× "3001" à 0.4 (somme 1.2) vs 2× "3002" à 0.9 (somme 1.8).
        let parts: [(String, Double)] = [("3001", 0.4), ("3002", 0.9), ("3001", 0.4), ("3002", 0.9), ("3001", 0.4)]
        for (partId, confidence) in parts {
            await aggregator.add(frameDetections: [
                detection(x: 0.2, y: 0.2, partId: partId, partConfidence: confidence)
            ])
        }
        let pieces = await aggregator.aggregate()
        XCTAssertEqual(pieces.count, 1)
        XCTAssertEqual(pieces.first?.partId, "3002")
        XCTAssertEqual(pieces.first!.partConfidence, 0.9, accuracy: 1e-9)
    }

    func test_aggregate_colorIdVote_weightedByConfidence() async {
        let aggregator = ScanAggregator()
        let colors: [(Int, Double)] = [(4, 0.9), (4, 0.8), (1, 0.3), (4, 0.7), (1, 0.2)]
        for (colorId, confidence) in colors {
            await aggregator.add(frameDetections: [
                detection(x: 0.2, y: 0.2, colorId: colorId, colorConfidence: confidence)
            ])
        }
        let pieces = await aggregator.aggregate()
        XCTAssertEqual(pieces.first?.colorId, 4)
        XCTAssertEqual(pieces.first!.colorConfidence, 0.8, accuracy: 1e-9) // moyenne de 0.9, 0.8, 0.7
    }

    func test_aggregate_boundingBox_isMeanOfMembers() async {
        let aggregator = ScanAggregator()
        await aggregator.add(frameDetections: [detection(x: 0.20, y: 0.30)])
        await aggregator.add(frameDetections: [detection(x: 0.22, y: 0.30)])
        await aggregator.add(frameDetections: [detection(x: 0.24, y: 0.30)])
        let pieces = await aggregator.aggregate()
        XCTAssertEqual(Double(pieces.first!.boundingBox.origin.x), 0.22, accuracy: 1e-9)
        XCTAssertEqual(Double(pieces.first!.boundingBox.origin.y), 0.30, accuracy: 1e-9)
    }

    // MARK: - Cycle de vie

    func test_isComplete_afterConfiguredFrameCount_true() async {
        let aggregator = ScanAggregator()
        for _ in 0..<5 {
            let complete = await aggregator.isComplete
            XCTAssertFalse(complete)
            await aggregator.add(frameDetections: [])
        }
        let complete = await aggregator.isComplete
        XCTAssertTrue(complete)
    }

    func test_reset_clearsTracksAndFrameCount() async {
        let aggregator = ScanAggregator()
        for _ in 0..<5 {
            await aggregator.add(frameDetections: [detection(x: 0.2, y: 0.2)])
        }
        await aggregator.reset()
        let framesAdded = await aggregator.framesAdded
        let pieces = await aggregator.aggregate()
        XCTAssertEqual(framesAdded, 0)
        XCTAssertTrue(pieces.isEmpty)
    }
}
