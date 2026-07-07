import SwiftUI

/// Onglet Scan : flow de permission caméra (CH-4) puis, une fois autorisé,
/// la session de scan déclenché (CH-5 : preview + bouton "Scanner" →
/// 5 frames analysées → agrégation → écran de revue).
struct ScanView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        switch appState.cameraPermission.status {
        case .notDetermined:
            CameraExplanationView()
        case .authorized:
            ScanSessionView(repository: appState.inventoryRepository)
        case .denied:
            CameraDeniedView()
        }
    }
}

/// Session de scan (jalons 5.1 + 5.5 + 5.6) : preview caméra (ou placeholder au
/// simulateur — pas de caméra réelle, le pipeline mock permet quand même de tester
/// scan → revue → inventaire), bouton central "Scanner", progression, revue en cover.
private struct ScanSessionView: View {
    @Environment(\.scenePhase) private var scenePhase
    @State private var viewModel: ScanViewModel

    init(repository: any InventoryRepository) {
        _viewModel = State(initialValue: ScanViewModel(repository: repository))
    }

    var body: some View {
        ZStack {
            background

            VStack(spacing: 16) {
                Spacer()
                statusOverlay
                scanButton
                    .padding(.bottom, 24)
            }
        }
        .onAppear { viewModel.handleAppear() }
        .onDisappear { viewModel.handleDisappear() }
        .onChange(of: scenePhase) { _, newPhase in
            // Jalon 5.1 : session stoppée en background, relancée au retour.
            viewModel.handleScenePhase(isActive: newPhase == .active)
        }
        .fullScreenCover(
            isPresented: Binding(
                get: { viewModel.phase == .reviewing },
                set: { if !$0 { viewModel.dismissReview() } }
            )
        ) {
            if let review = viewModel.reviewModel {
                ScanReviewView(model: review) {
                    viewModel.dismissReview()
                }
            }
        }
        .alert(
            "Scan impossible",
            isPresented: Binding(
                get: {
                    if case .failed = viewModel.phase { return true }
                    return false
                },
                set: { if !$0 { viewModel.acknowledgeFailure() } }
            )
        ) {
            Button("OK", role: .cancel) {}
        } message: {
            if case .failed(let message) = viewModel.phase {
                Text(message)
            }
        }
    }

    @ViewBuilder
    private var background: some View {
        if let source = viewModel.previewSource {
            CameraPreviewView(source: source)
                .ignoresSafeArea()
        } else {
            // Simulateur / caméra indisponible : le scan mock reste fonctionnel.
            LinearGradient(
                colors: [Color(.systemGray5), Color(.systemGray3)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()
            .overlay {
                VStack(spacing: 8) {
                    Image(systemName: "camera.on.rectangle")
                        .font(.system(size: 40))
                        .foregroundStyle(.secondary)
                    Text("Preview caméra indisponible (simulateur)")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                    Text("Le scan de démonstration reste disponible.")
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }
            }
        }
    }

    @ViewBuilder
    private var statusOverlay: some View {
        if case .scanning(let done, let total) = viewModel.phase {
            VStack(spacing: 6) {
                ProgressView(value: Double(done), total: Double(total))
                    .frame(width: 160)
                Text("Tenez l'appareil stable — image \(min(done + 1, total))/\(total)")
                    .font(.footnote.weight(.medium))
            }
            .padding(12)
            .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
        } else if !viewModel.isPipelineAvailable {
            Text("Reconnaissance indisponible : les modèles arrivent avec CH-3.")
                .font(.footnote)
                .padding(10)
                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
        }
    }

    /// Bouton "Scanner" central : déclenche la séquence 5 frames → agrégation → revue.
    private var scanButton: some View {
        Button {
            viewModel.startScan()
        } label: {
            ZStack {
                Circle()
                    .fill(viewModel.isScanning ? Color(.systemGray3) : Color.accentColor)
                    .frame(width: 76, height: 76)
                if viewModel.isScanning {
                    ProgressView()
                        .tint(.white)
                } else {
                    Image(systemName: "sparkle.magnifyingglass")
                        .font(.title2)
                        .foregroundStyle(.white)
                }
            }
            .overlay(Circle().strokeBorder(.white.opacity(0.8), lineWidth: 3).padding(-5))
        }
        .buttonStyle(.plain)
        .disabled(viewModel.isScanning || !viewModel.isPipelineAvailable)
        .accessibilityLabel("Scanner")
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
