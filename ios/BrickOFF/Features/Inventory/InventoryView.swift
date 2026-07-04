import SwiftUI

/// Onglet Inventaire — placeholder CH-4, UI réelle au chantier CH-8.
struct InventoryView: View {
    var body: some View {
        ContentUnavailableView(
            "Inventaire vide",
            systemImage: "square.grid.2x2",
            description: Text("Les pièces scannées apparaîtront ici. Interface au chantier CH-8.")
        )
    }
}

#Preview {
    InventoryView()
}
