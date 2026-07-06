import SwiftUI

/// Racine de navigation : TabView 3 onglets (Scan / Inventaire / Constructions),
/// Réglages accessibles depuis la barre de navigation de chaque onglet (sheet).
struct ContentView: View {
    @Environment(AppState.self) private var appState
    @State private var isSettingsPresented = false

    var body: some View {
        TabView {
            featureTab("Scan", systemImage: "camera.viewfinder") {
                ScanView()
            }
            featureTab("Inventaire", systemImage: "square.grid.2x2") {
                InventoryView(repository: appState.inventoryRepository)
            }
            featureTab("Constructions", systemImage: "building.2") {
                MatchesView()
            }
        }
        .sheet(isPresented: $isSettingsPresented) {
            NavigationStack {
                SettingsView()
                    .toolbar {
                        ToolbarItem(placement: .confirmationAction) {
                            Button("OK") { isSettingsPresented = false }
                        }
                    }
            }
        }
    }

    /// Onglet standard : NavigationStack + titre + bouton Réglages en toolbar.
    private func featureTab(
        _ title: String,
        systemImage: String,
        @ViewBuilder content: () -> some View
    ) -> some View {
        NavigationStack {
            content()
                .navigationTitle(title)
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button {
                            isSettingsPresented = true
                        } label: {
                            Label("Réglages", systemImage: "gearshape")
                        }
                    }
                }
        }
        .tabItem {
            Label(title, systemImage: systemImage)
        }
    }
}

#Preview {
    ContentView()
        .environment(AppState())
}
