import CoreGraphics
import XCTest
@testable import BrickOFF

/// Le pipeline mock doit être assez "vrai" pour développer 5.5/5.6 :
/// sorties reproductibles à seed fixé, bboxes valides, scène retrouvée par l'agrégateur.
final class MockDetectionPipelineTests: XCTestCase {
    private func makeFrame() throws -> CapturedFrame {
        try XCTUnwrap(CapturedFrame.blank(width: 64, height: 36))
    }

    func test_detections_sameSeed_isDeterministic() async throws {
        let frame = try makeFrame()
        let first = MockDetectionPipeline(seed: 42, inferenceDelay: .zero)
        let second = MockDetectionPipeline(seed: 42, inferenceDelay: .zero)

        for _ in 0..<5 {
            let a = try await first.detections(in: frame)
            let b = try await second.detections(in: frame)
            XCTAssertEqual(a, b)
        }
    }

    func test_detections_boundingBoxesAndConfidences_withinValidRanges() async throws {
        let frame = try makeFrame()
        let pipeline = MockDetectionPipeline(seed: 7, inferenceDelay: .zero)

        for _ in 0..<10 {
            for detection in try await pipeline.detections(in: frame) {
                let box = detection.boundingBox
                XCTAssertTrue(CGRect(x: 0, y: 0, width: 1.0001, height: 1.0001).contains(box.origin))
                XCTAssertGreaterThanOrEqual(box.width, 0)
                XCTAssertGreaterThanOrEqual(box.height, 0)
                XCTAssertTrue((0...1).contains(detection.partConfidence))
                XCTAssertTrue((0...1).contains(detection.colorConfidence))
                XCTAssertFalse(detection.partId.isEmpty)
            }
        }
    }

    func test_detections_fiveFramesAggregated_recoverScenePieces() async throws {
        // Bout-en-bout mock → agrégateur : la scène par défaut (6 pièces) doit être
        // très largement retrouvée, malgré le bruit (seed fixé → déterministe).
        let frame = try makeFrame()
        let pipeline = MockDetectionPipeline(seed: 123, inferenceDelay: .zero)
        let aggregator = ScanAggregator()

        for _ in 0..<5 {
            let detections = try await pipeline.detections(in: frame)
            await aggregator.add(frameDetections: detections)
        }
        let pieces = await aggregator.aggregate()

        let sceneCount = MockDetectionPipeline.defaultScene.count
        XCTAssertGreaterThanOrEqual(pieces.count, sceneCount - 1, "au plus une pièce de la scène perdue")
        XCTAssertLessThanOrEqual(pieces.count, sceneCount + 1, "au plus un faux positif survivant")
    }
}
