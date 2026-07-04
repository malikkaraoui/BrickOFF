import SwiftUI

@main
struct BrickOFFApp: App {
    @Environment(\.scenePhase) private var scenePhase
    @State private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(appState)
        }
        .onChange(of: scenePhase) { _, newPhase in
            // Retour au premier plan : la permission caméra a pu changer dans Réglages.
            if newPhase == .active {
                appState.cameraPermission.refresh()
            }
        }
    }
}
