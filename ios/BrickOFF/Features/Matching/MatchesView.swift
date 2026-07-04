import SwiftUI

/// Onglet Constructions (matching de sets) — placeholder CH-4, UI réelle au chantier CH-8.
struct MatchesView: View {
    var body: some View {
        ContentUnavailableView(
            "Aucune construction",
            systemImage: "building.2",
            description: Text("Les sets constructibles avec vos pièces apparaîtront ici. Interface au chantier CH-8.")
        )
    }
}

#Preview {
    MatchesView()
}
