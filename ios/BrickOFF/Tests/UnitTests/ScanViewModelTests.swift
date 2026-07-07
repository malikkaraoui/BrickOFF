import XCTest
@testable import BrickOFF

/// Flux de scan déclenché de bout en bout, sans caméra ni modèle réels :
/// source de frames mock (cadence nulle) + pipeline mock seedé → phase `.reviewing`.
@MainActor
final class ScanViewModelTests: XCTestCase {
    private func makeViewModel(pipeline: (any DetectionPipeline)?) throws -> ScanViewModel {
        ScanViewModel(
            repository: GRDBInventoryRepository(database: try .inMemory()),
            camera: MockScanFrameSource(frameDelay: .zero),
            pipeline: pipeline,
            useDefaultPipelineIfNil: false
        )
    }

    func test_startScan_mockPipeline_reachesReviewWithConsolidatedPieces() async throws {
        let viewModel = try makeViewModel(
            pipeline: MockDetectionPipeline(seed: 99, inferenceDelay: .zero)
        )

        viewModel.startScan()
        await viewModel.scanTask?.value

        XCTAssertEqual(viewModel.phase, .reviewing)
        let review = try XCTUnwrap(viewModel.reviewModel)
        XCTAssertFalse(review.groups.isEmpty, "la scène mock doit produire des pièces consolidées")
        XCTAssertNotNil(review.capturedFrame, "capture figée conservée pour l'écran de revue")
    }

    func test_startScan_withoutPipeline_failsExplicitly() async throws {
        let viewModel = try makeViewModel(pipeline: nil)

        viewModel.startScan()
        await viewModel.scanTask?.value

        guard case .failed = viewModel.phase else {
            return XCTFail("attendu .failed sans pipeline (CH-3 non livré), obtenu \(viewModel.phase)")
        }
    }

    func test_cancelScan_returnsToIdle() async throws {
        let viewModel = try makeViewModel(
            pipeline: MockDetectionPipeline(seed: 1, inferenceDelay: .milliseconds(50))
        )

        viewModel.startScan()
        viewModel.cancelScan()

        XCTAssertEqual(viewModel.phase, .idle)
        XCTAssertNil(viewModel.reviewModel)
    }
}
