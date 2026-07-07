import CoreImage
import CoreVideo
import UIKit

/// Frame capturée, transférée du flux caméra vers le pipeline d'inférence.
///
/// `@unchecked Sendable` : le `CVPixelBuffer` n'est jamais accédé concurremment —
/// le throttling (profondeur 1, cf. `FrameThrottler`) garantit qu'une frame remise
/// au consommateur n'est plus touchée par la couche capture.
struct CapturedFrame: @unchecked Sendable {
    let pixelBuffer: CVPixelBuffer

    /// Frame unie gris moyen — pour les tests et le simulateur (pas de caméra réelle).
    static func blank(width: Int = 1920, height: Int = 1080) -> CapturedFrame? {
        var buffer: CVPixelBuffer?
        let status = CVPixelBufferCreate(
            kCFAllocatorDefault,
            width,
            height,
            kCVPixelFormatType_32BGRA,
            nil,
            &buffer
        )
        guard status == kCVReturnSuccess, let buffer else { return nil }

        CVPixelBufferLockBaseAddress(buffer, [])
        if let base = CVPixelBufferGetBaseAddress(buffer) {
            let size = CVPixelBufferGetBytesPerRow(buffer) * CVPixelBufferGetHeight(buffer)
            memset(base, 0x66, size) // gris sombre uniforme
        }
        CVPixelBufferUnlockBaseAddress(buffer, [])
        return CapturedFrame(pixelBuffer: buffer)
    }

    /// Rendu UIImage de la frame (capture figée de l'écran de revue, jalon 5.6).
    func uiImage() -> UIImage? {
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        guard let cgImage = Self.ciContext.createCGImage(ciImage, from: ciImage.extent) else {
            return nil
        }
        return UIImage(cgImage: cgImage)
    }

    private static let ciContext = CIContext()
}
