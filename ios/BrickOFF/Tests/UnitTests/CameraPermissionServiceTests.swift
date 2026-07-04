import XCTest
@testable import BrickOFF

/// Provider mocké : simule l'autorisation système sans toucher AVCaptureDevice.
@MainActor
private final class MockCameraAuthorizationProvider: CameraAuthorizationProviding {
    var authorizationStatus: CameraPermissionStatus
    var grantsAccessOnRequest: Bool
    private(set) var requestAccessCallCount = 0

    init(status: CameraPermissionStatus, grantsAccessOnRequest: Bool = false) {
        self.authorizationStatus = status
        self.grantsAccessOnRequest = grantsAccessOnRequest
    }

    func requestAccess() async -> Bool {
        requestAccessCallCount += 1
        authorizationStatus = grantsAccessOnRequest ? .authorized : .denied
        return grantsAccessOnRequest
    }
}

@MainActor
final class CameraPermissionServiceTests: XCTestCase {

    // MARK: - État initial (les 3 cas)

    func test_init_neverRequested_statusIsNotDetermined() {
        let service = CameraPermissionService(
            provider: MockCameraAuthorizationProvider(status: .notDetermined)
        )
        XCTAssertEqual(service.status, .notDetermined)
    }

    func test_init_alreadyGranted_statusIsAuthorized() {
        let service = CameraPermissionService(
            provider: MockCameraAuthorizationProvider(status: .authorized)
        )
        XCTAssertEqual(service.status, .authorized)
    }

    func test_init_alreadyRefused_statusIsDenied() {
        let service = CameraPermissionService(
            provider: MockCameraAuthorizationProvider(status: .denied)
        )
        XCTAssertEqual(service.status, .denied)
    }

    // MARK: - requestAccess()

    func test_requestAccess_userGrants_statusBecomesAuthorized() async {
        let provider = MockCameraAuthorizationProvider(
            status: .notDetermined, grantsAccessOnRequest: true
        )
        let service = CameraPermissionService(provider: provider)

        await service.requestAccess()

        XCTAssertEqual(service.status, .authorized)
        XCTAssertEqual(provider.requestAccessCallCount, 1)
    }

    func test_requestAccess_userRefuses_statusBecomesDenied() async {
        let provider = MockCameraAuthorizationProvider(
            status: .notDetermined, grantsAccessOnRequest: false
        )
        let service = CameraPermissionService(provider: provider)

        await service.requestAccess()

        XCTAssertEqual(service.status, .denied)
        XCTAssertEqual(provider.requestAccessCallCount, 1)
    }

    func test_requestAccess_alreadyAuthorized_doesNotCallSystem() async {
        let provider = MockCameraAuthorizationProvider(status: .authorized)
        let service = CameraPermissionService(provider: provider)

        await service.requestAccess()

        XCTAssertEqual(service.status, .authorized)
        XCTAssertEqual(provider.requestAccessCallCount, 0)
    }

    func test_requestAccess_alreadyDenied_doesNotCallSystem() async {
        let provider = MockCameraAuthorizationProvider(status: .denied)
        let service = CameraPermissionService(provider: provider)

        await service.requestAccess()

        XCTAssertEqual(service.status, .denied)
        XCTAssertEqual(provider.requestAccessCallCount, 0)
    }

    // MARK: - refresh()

    func test_refresh_permissionChangedInSettings_statusUpdated() {
        let provider = MockCameraAuthorizationProvider(status: .denied)
        let service = CameraPermissionService(provider: provider)
        XCTAssertEqual(service.status, .denied)

        // L'utilisateur accorde la permission dans l'app Réglages puis revient.
        provider.authorizationStatus = .authorized
        service.refresh()

        XCTAssertEqual(service.status, .authorized)
    }
}
