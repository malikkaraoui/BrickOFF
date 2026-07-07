import AVFoundation
import CoreMedia
import QuartzCore
import os

/// Accès opaque à l'`AVCaptureSession` pour la preview SwiftUI.
/// Les ViewModels manipulent ce type (défini dans Core/Vision), jamais AVFoundation
/// directement (conventions §2). `@unchecked Sendable` : la session est thread-safe
/// côté AVFoundation pour l'attachement à une preview layer.
struct CameraPreviewSource: @unchecked Sendable {
    let session: AVCaptureSession
}

/// Contrat caméra du flow de scan (jalon 5.1), mockable (tests, simulateur).
protocol ScanCameraControlling: Sendable {
    /// Session pour la preview — `nil` tant qu'aucune caméra réelle n'est configurée
    /// (mock, simulateur, permission refusée).
    var previewSource: CameraPreviewSource? { get }

    /// Configure la session (une seule fois) puis la démarre.
    /// - Throws: `VisionError.cameraUnavailable` si aucune caméra n'est exploitable.
    func start() async throws

    /// Stoppe la session (vue disparue / app en background) et libère
    /// immédiatement toute attente de frame en cours (résolue à `nil`).
    func stop() async

    /// Prochaine frame throttlée. Le contrat de throttling du jalon 5.1 est porté par
    /// le modèle "pull" : demander la frame suivante matérialise "la précédente est
    /// traitée", et `FrameThrottler` impose ≥ 400 ms entre deux frames remises.
    /// - Returns: `nil` si la session s'arrête pendant l'attente.
    func nextFrame() async -> CapturedFrame?
}

/// Implémentation système du jalon 5.1 : `AVCaptureSession` 1920×1080, sortie
/// `AVCaptureVideoDataOutput` (CVPixelBuffer), throttling par `FrameThrottler`,
/// frames intermédiaires jetées (`alwaysDiscardsLateVideoFrames` — profondeur 1).
///
/// Concurrence : la configuration et start/stop vivent sur `sessionQueue`
/// (recommandation Apple : `startRunning()` bloque) ; l'état partagé entre le
/// delegate vidéo et les appels async est protégé par `OSAllocatedUnfairLock`,
/// d'où le `@unchecked Sendable` justifié.
final class CameraService: NSObject, ScanCameraControlling, @unchecked Sendable {
    private static let logger = Logger(subsystem: "com.brickoff.app", category: "Camera")

    private let session = AVCaptureSession()
    private let sessionQueue = DispatchQueue(label: "com.brickoff.app.camera.session")
    private let videoQueue = DispatchQueue(label: "com.brickoff.app.camera.frames")

    private struct State {
        var throttler = FrameThrottler()
        var pendingRequest: CheckedContinuation<CapturedFrame?, Never>?
        var isConfigured = false
    }

    private let state = OSAllocatedUnfairLock(initialState: State())

    var previewSource: CameraPreviewSource? {
        state.withLock { $0.isConfigured } ? CameraPreviewSource(session: session) : nil
    }

    func start() async throws {
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            sessionQueue.async { [self] in
                do {
                    try configureIfNeeded()
                    if !session.isRunning {
                        session.startRunning()
                    }
                    continuation.resume()
                } catch {
                    continuation.resume(throwing: error)
                }
            }
        }
    }

    func stop() async {
        // Libère un éventuel consommateur en attente AVANT d'arrêter la session,
        // pour ne jamais laisser un scan suspendu.
        resolvePendingRequest(with: nil)
        await withCheckedContinuation { continuation in
            sessionQueue.async { [self] in
                if session.isRunning {
                    session.stopRunning()
                }
                continuation.resume()
            }
        }
    }

    func nextFrame() async -> CapturedFrame? {
        await withCheckedContinuation { continuation in
            let displaced: CheckedContinuation<CapturedFrame?, Never>? = state.withLock { state in
                // Le consommateur redemande une frame → la précédente est traitée.
                state.throttler.finishProcessing()
                let previous = state.pendingRequest
                state.pendingRequest = continuation
                return previous
            }
            // Un seul consommateur attendu ; si une attente traînait, on la libère.
            displaced?.resume(returning: nil)
        }
    }

    // MARK: - Privé

    /// À exécuter sur `sessionQueue` uniquement.
    private func configureIfNeeded() throws {
        guard !state.withLock({ $0.isConfigured }) else { return }

        guard
            let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
            let input = try? AVCaptureDeviceInput(device: device)
        else {
            Self.logger.error("Aucune caméra arrière exploitable (simulateur ?)")
            throw VisionError.cameraUnavailable
        }

        session.beginConfiguration()
        defer { session.commitConfiguration() }

        // Plan 5.1 : capture 1920×1080 (le downscale 640×640 pour DET sera fait par Vision, CH-3).
        session.sessionPreset = session.canSetSessionPreset(.hd1920x1080) ? .hd1920x1080 : .high

        guard session.canAddInput(input) else { throw VisionError.cameraUnavailable }
        session.addInput(input)

        let output = AVCaptureVideoDataOutput()
        output.alwaysDiscardsLateVideoFrames = true // profondeur 1 : aucune frame en file
        output.videoSettings = [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA
        ]
        output.setSampleBufferDelegate(self, queue: videoQueue)
        guard session.canAddOutput(output) else { throw VisionError.cameraUnavailable }
        session.addOutput(output)

        state.withLock { $0.isConfigured = true }
    }

    private func resolvePendingRequest(with frame: CapturedFrame?) {
        let pending: CheckedContinuation<CapturedFrame?, Never>? = state.withLock { state in
            let request = state.pendingRequest
            state.pendingRequest = nil
            return request
        }
        pending?.resume(returning: frame)
    }
}

// MARK: - Delegate vidéo (appelé sur `videoQueue`)

extension CameraService: AVCaptureVideoDataOutputSampleBufferDelegate {
    func captureOutput(
        _ output: AVCaptureOutput,
        didOutput sampleBuffer: CMSampleBuffer,
        from connection: AVCaptureConnection
    ) {
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }

        let now = CACurrentMediaTime()
        let request: CheckedContinuation<CapturedFrame?, Never>? = state.withLock { state in
            // Frame remise seulement si un consommateur attend ET que le throttle accepte
            // (≥ 400 ms depuis la précédente) ; toutes les autres frames sont jetées.
            guard state.pendingRequest != nil, state.throttler.shouldSubmitFrame(at: now) else {
                return nil
            }
            let pending = state.pendingRequest
            state.pendingRequest = nil
            return pending
        }
        request?.resume(returning: CapturedFrame(pixelBuffer: pixelBuffer))
    }
}
