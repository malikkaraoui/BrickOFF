import SwiftUI

/// Écran Réglages — placeholder CH-4, contenu réel (export inventaire, mode souple…) au chantier CH-8.
struct SettingsView: View {
    var body: some View {
        Form {
            Section {
                LabeledContent("Version", value: appVersion)
            } footer: {
                Text("Les réglages détaillés arriveront au chantier CH-8.")
            }
        }
        .navigationTitle("Réglages")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var appVersion: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "—"
    }
}

#Preview {
    NavigationStack {
        SettingsView()
    }
}
