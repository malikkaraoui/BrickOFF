import XCTest
@testable import BrickOFF

/// Jalon 5.1 — logique de throttle extraite, testée sans caméra réelle (horloge injectée).
final class FrameThrottlerTests: XCTestCase {
    func test_shouldSubmitFrame_firstFrame_accepted() {
        var throttler = FrameThrottler(minimumInterval: 0.4)
        XCTAssertTrue(throttler.shouldSubmitFrame(at: 10.0))
    }

    func test_shouldSubmitFrame_whileProcessing_rejected() {
        var throttler = FrameThrottler(minimumInterval: 0.4)
        XCTAssertTrue(throttler.shouldSubmitFrame(at: 10.0))
        // Frame suivante bien après l'intervalle, mais la précédente n'est pas traitée.
        XCTAssertFalse(throttler.shouldSubmitFrame(at: 11.0))
    }

    func test_shouldSubmitFrame_processedButBeforeInterval_rejected() {
        var throttler = FrameThrottler(minimumInterval: 0.4)
        XCTAssertTrue(throttler.shouldSubmitFrame(at: 10.0))
        throttler.finishProcessing()
        XCTAssertFalse(throttler.shouldSubmitFrame(at: 10.3))
    }

    func test_shouldSubmitFrame_processedAndIntervalElapsed_accepted() {
        var throttler = FrameThrottler(minimumInterval: 0.4)
        XCTAssertTrue(throttler.shouldSubmitFrame(at: 10.0))
        throttler.finishProcessing()
        XCTAssertTrue(throttler.shouldSubmitFrame(at: 10.5))
    }

    func test_shouldSubmitFrame_exactIntervalBoundary_accepted() {
        var throttler = FrameThrottler(minimumInterval: 0.4)
        XCTAssertTrue(throttler.shouldSubmitFrame(at: 10.0))
        throttler.finishProcessing()
        XCTAssertTrue(throttler.shouldSubmitFrame(at: 10.4))
    }

    func test_shouldSubmitFrame_burstAt30fps_acceptsOnlyThrottledFrames() {
        var throttler = FrameThrottler(minimumInterval: 0.4)
        var accepted = 0
        // 2 s de flux 30 fps, traitement instantané : ~1 frame / 400 ms max.
        for frameIndex in 0..<60 {
            let now = Double(frameIndex) / 30.0
            if throttler.shouldSubmitFrame(at: now) {
                accepted += 1
                throttler.finishProcessing()
            }
        }
        XCTAssertEqual(accepted, 5, "2 s à 400 ms d'intervalle = 5 frames (t=0, 0.4, 0.8, 1.2, 1.6)")
    }

    func test_finishProcessing_withoutSubmission_keepsRejectingBeforeInterval() {
        var throttler = FrameThrottler(minimumInterval: 0.4)
        XCTAssertTrue(throttler.shouldSubmitFrame(at: 10.0))
        throttler.finishProcessing()
        throttler.finishProcessing() // appel superflu : sans effet
        XCTAssertFalse(throttler.shouldSubmitFrame(at: 10.1))
    }
}
