import AVFoundation
import SwiftUI

/// Preview caméra (`AVCaptureVideoPreviewLayer`) wrappée SwiftUI — jalon 5.1.
/// La preview est branchée directement sur la session : elle reste fluide (30+ fps)
/// indépendamment du throttling d'inférence, qui ne concerne que la sortie vidéo.
struct CameraPreviewView: UIViewRepresentable {
    let source: CameraPreviewSource

    func makeUIView(context: Context) -> PreviewUIView {
        let view = PreviewUIView()
        view.previewLayer.session = source.session
        view.previewLayer.videoGravity = .resizeAspectFill
        return view
    }

    func updateUIView(_ uiView: PreviewUIView, context: Context) {
        if uiView.previewLayer.session !== source.session {
            uiView.previewLayer.session = source.session
        }
    }

    /// UIView dont le layer EST la preview layer (redimensionnement géré par UIKit).
    final class PreviewUIView: UIView {
        override static var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }

        var previewLayer: AVCaptureVideoPreviewLayer {
            layer as! AVCaptureVideoPreviewLayer
        }
    }
}
