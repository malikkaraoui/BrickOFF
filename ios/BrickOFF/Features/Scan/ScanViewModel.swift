import Foundation
import Observation
import os

/// Orchestration du scan déclenché (décision UX figée du plan 5.5) :
/// "Scanner" → N = 5 frames analysées → agrégation → écran de revue.
/// L'ajout à l'inventaire ne passe QUE par l'écran de revue, jamais en live.
///
/// Conventions §2 : pas d'import AVFoundation ici — la caméra est derrière
/// `ScanCameraControlling`, le pipeline derrière `DetectionPipeline` (mock en CH-5).
@MainActor
@Observable
final class ScanViewModel {
    enum Phase: Equatable {
        case idle
        case scanning(framesAnalyzed: Int, frameCount: Int)
        case reviewing
        case failed(message: String)
    }

    private static let logger = Logger(subsystem: "com.brickoff.app", category: "Scan")

    private(set) var phase: Phase = .idle
    /// Modèle de l'écran de revue, non-nil en phase `.reviewing`.
    private(set) var reviewModel: ScanReviewViewModel?
    /// La caméra réelle est-elle indisponible (simulateur…) ? Info UI uniquement,
    /// le scan mock reste possible via `MockScanFrameSource`.
    private(set) var isCameraUnavailable = false

    var previewSource: CameraPreviewSource? { camera.previewSource }
    /// Sans pipeline (builds Release tant que CH-3 n'est pas livré), le scan est désactivé.
    var isPipelineAvailable: Bool { pipeline != nil }
    var isScanning: Bool {
        if case .scanning = phase { return true }
        return false
    }

    private let camera: any ScanCameraControlling
    private let pipeline: (any DetectionPipeline)?
    private let repository: any InventoryRepository
    private let aggregatorConfiguration: ScanAggregator.Configuration
    private(set) var scanTask: Task<Void, Never>?

    init(
        repository: any InventoryRepository,
        camera: (any ScanCameraControlling)? = nil,
        pipeline: (any DetectionPipeline)? = nil,
        aggregatorConfiguration: ScanAggregator.Configuration = .standard,
        useDefaultPipelineIfNil: Bool = true
    ) {
        self.repository = repository
        self.camera = camera ?? Self.makeDefaultCamera()
        self.pipeline = pipeline ?? (useDefaultPipelineIfNil ? Self.makeDefaultPipeline() : nil)
        self.aggregatorConfiguration = aggregatorConfiguration
    }

    // MARK: - Composition par défaut

    /// Simulateur : pas de caméra réelle → source de frames factice (DEBUG).
    /// Device : `CameraService` (AVCaptureSession 1920×1080).
    private static func makeDefaultCamera() -> any ScanCameraControlling {
        #if DEBUG && targetEnvironment(simulator)
        MockScanFrameSource()
        #else
        CameraService()
        #endif
    }

    /// DEBUG : pipeline mock (CH-5). Release : aucun pipeline tant que CH-3
    /// (modèles CoreML) n'est pas livré → bouton Scanner désactivé.
    private static func makeDefaultPipeline() -> (any DetectionPipeline)? {
        #if DEBUG
        MockDetectionPipeline()
        #else
        nil
        #endif
    }

    // MARK: - Lifecycle (jalon 5.1 : pause en background / disparition)

    func handleAppear() {
        startCamera()
    }

    func handleDisappear() {
        cancelScan()
        stopCamera()
    }

    func handleScenePhase(isActive: Bool) {
        if isActive {
            startCamera()
        } else {
            cancelScan()
            stopCamera()
        }
    }

    // MARK: - Scan

    func startScan() {
        guard scanTask == nil, !isScanning else { return }
        guard let pipeline else {
            phase = .failed(message: "Le moteur de reconnaissance n'est pas encore disponible (CH-3).")
            return
        }
        scanTask = Task { [weak self] in
            await self?.runScan(pipeline: pipeline)
            self?.scanTask = nil
        }
    }

    func cancelScan() {
        scanTask?.cancel()
        scanTask = nil
        if isScanning {
            phase = .idle
        }
    }

    /// Ferme l'écran de revue et revient à l'état prêt-à-scanner.
    func dismissReview() {
        reviewModel = nil
        if phase == .reviewing {
            phase = .idle
        }
    }

    /// Acquitte une erreur affichée.
    func acknowledgeFailure() {
        if case .failed = phase {
            phase = .idle
        }
    }

    // MARK: - Privé

    private func runScan(pipeline: any DetectionPipeline) async {
        guard !Task.isCancelled else { return }
        let frameCount = aggregatorConfiguration.frameCount
        phase = .scanning(framesAnalyzed: 0, frameCount: frameCount)

        let aggregator = ScanAggregator(configuration: aggregatorConfiguration)
        var lastFrame: CapturedFrame?

        for index in 0..<frameCount {
            guard !Task.isCancelled else { return }
            guard let frame = await camera.nextFrame() else {
                if !Task.isCancelled {
                    phase = .failed(message: "La caméra n'a pas fourni d'image. Réessayez.")
                }
                return
            }
            lastFrame = frame

            do {
                let detections = try await pipeline.detections(in: frame)
                await aggregator.add(frameDetections: detections)
            } catch {
                Self.logger.error("Analyse de frame échouée : \(error)")
                await aggregator.add(frameDetections: [])
            }

            guard !Task.isCancelled else { return }
            phase = .scanning(framesAnalyzed: index + 1, frameCount: frameCount)
        }

        let pieces = await aggregator.aggregate()
        guard !Task.isCancelled else { return }

        reviewModel = ScanReviewViewModel(
            pieces: pieces,
            capturedFrame: lastFrame,
            repository: repository
        )
        phase = .reviewing
    }

    private func startCamera() {
        Task { [weak self] in
            guard let self else { return }
            do {
                try await self.camera.start()
                self.isCameraUnavailable = false
            } catch {
                Self.logger.info("Caméra indisponible (simulateur ?) : \(error)")
                self.isCameraUnavailable = true
            }
        }
    }

    private func stopCamera() {
        let camera = self.camera
        Task.detached {
            await camera.stop()
        }
    }
}
