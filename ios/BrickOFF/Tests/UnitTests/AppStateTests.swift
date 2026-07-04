import XCTest
@testable import BrickOFF

/// Provider mocké minimal pour injecter un état caméra dans AppState.
@MainActor
private struct StubCameraAuthorizationProvider: CameraAuthorizationProviding {
    let authorizationStatus: CameraPermissionStatus
    func requestAccess() async -> Bool { false }
}

@MainActor
final class AppStateTests: XCTestCase {

    func test_init_default_onboardingNotDone() {
        let state = AppState(cameraPermission: CameraPermissionService(
            provider: StubCameraAuthorizationProvider(authorizationStatus: .notDetermined)
        ))
        XCTAssertFalse(state.onboardingDone)
    }

    func test_init_injectedPermissionService_exposedAsIs() {
        let service = CameraPermissionService(
            provider: StubCameraAuthorizationProvider(authorizationStatus: .authorized)
        )
        let state = AppState(cameraPermission: service)

        XCTAssertIdentical(state.cameraPermission, service)
        XCTAssertEqual(state.cameraPermission.status, .authorized)
    }

    func test_onboardingDone_setTrue_valuePersistsInState() {
        let state = AppState(cameraPermission: CameraPermissionService(
            provider: StubCameraAuthorizationProvider(authorizationStatus: .notDetermined)
        ))
        state.onboardingDone = true
        XCTAssertTrue(state.onboardingDone)
    }
}
