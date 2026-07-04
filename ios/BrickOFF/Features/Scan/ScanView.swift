import SwiftUI

/// Onglet Scan — placeholder CH-4 : seul le flow de permission caméra est réel,
/// l'interface de scan arrive au chantier CH-8.
struct ScanView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        switch appState.cameraPermission.status {
        case .notDetermined:
            CameraExplanationView()
        case .authorized:
            ContentUnavailableView(
                "Prêt à scanner",
                systemImage: "camera.viewfinder",
                description: Text("L'accès à la caméra est accordé. L'interface de scan arrive au chantier CH-8.")
            )
        case .denied:
            CameraDeniedView()
        }
    }
}

/// Permission jamais demandée : explication + bouton déclenchant la demande système.
private struct CameraExplanationView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "camera.viewfinder")
                .font(.system(size: 56))
                .foregroundStyle(.secondary)
            Text("Accès à la caméra")
                .font(.title2.bold())
            Text("BrickOFF utilise la caméra pour reconnaître vos pièces LEGO et remplir votre inventaire. Rien ne quitte votre appareil.")
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            Button("Autoriser la caméra") {
                Task { await appState.cameraPermission.requestAccess() }
            }
            .buttonStyle(.borderedProminent)
            .padding(.top, 8)
        }
        .padding(32)
    }
}

/// Permission refusée : explication + lien vers l'app Réglages.
private struct CameraDeniedView: View {
    @Environment(\.openURL) private var openURL

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "camera.badge.ellipsis")
                .font(.system(size: 56))
                .foregroundStyle(.secondary)
            Text("Caméra non autorisée")
                .font(.title2.bold())
            Text("Le scan de pièces nécessite la caméra. Vous pouvez autoriser l'accès dans les Réglages de votre appareil.")
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            Button("Ouvrir les Réglages") {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    openURL(url)
                }
            }
            .buttonStyle(.borderedProminent)
            .padding(.top, 8)
        }
        .padding(32)
    }
}

#Preview {
    ScanView()
        .environment(AppState())
}
