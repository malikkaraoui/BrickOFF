import SwiftUI

/// Onglet Inventaire — écran fonctionnel CH-6 jalon 6.3 (UI brute, habillage en CH-8).
/// Liste groupée par catégorie (heuristique v0), tri par quantité, recherche,
/// stepper, suppression, annulation du dernier scan, vidage avec confirmation.
struct InventoryView: View {
    @State private var viewModel: InventoryViewModel
    @State private var isClearConfirmationPresented = false

    init(repository: any InventoryRepository) {
        _viewModel = State(initialValue: InventoryViewModel(repository: repository))
    }

    var body: some View {
        @Bindable var viewModel = viewModel

        Group {
            if viewModel.items.isEmpty {
                ContentUnavailableView(
                    "Inventaire vide",
                    systemImage: "square.grid.2x2",
                    description: Text("Scannez vos pièces depuis l'onglet Scan pour remplir l'inventaire.")
                )
            } else if viewModel.sections.isEmpty {
                ContentUnavailableView.search(text: viewModel.searchText)
            } else {
                inventoryList
            }
        }
        .safeAreaInset(edge: .top, spacing: 0) { header }
        .searchable(text: $viewModel.searchText, prompt: "part_id ou nom")
        .toolbar { toolbarContent }
        .confirmationDialog(
            "Vider l'inventaire ?",
            isPresented: $isClearConfirmationPresented,
            titleVisibility: .visible
        ) {
            Button("Tout supprimer", role: .destructive) { viewModel.clearAll() }
            Button("Annuler", role: .cancel) {}
        } message: {
            Text("Toutes les pièces et l'historique de scans seront supprimés.")
        }
        .alert(
            "Erreur",
            isPresented: Binding(
                get: { viewModel.errorMessage != nil },
                set: { if !$0 { viewModel.errorMessage = nil } }
            )
        ) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
        .task { await viewModel.startObserving() }
    }

    // MARK: - Sous-vues

    /// Compteur global en header (spécification 6.3).
    private var header: some View {
        HStack {
            Label("\(viewModel.totalPieceCount) pièces", systemImage: "square.grid.2x2")
                .font(.subheadline.weight(.semibold))
            Spacer()
            Text("\(viewModel.distinctItemCount) références")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(.bar)
        .overlay(alignment: .bottom) { Divider() }
    }

    private var inventoryList: some View {
        List {
            ForEach(viewModel.sections) { section in
                Section {
                    ForEach(section.items) { item in
                        InventoryRowView(
                            item: item,
                            onIncrement: { viewModel.increment(item) },
                            onDecrement: { viewModel.decrement(item) }
                        )
                        .swipeActions(edge: .trailing) {
                            Button("Supprimer", systemImage: "trash", role: .destructive) {
                                viewModel.delete(item)
                            }
                        }
                    }
                } header: {
                    Label(section.category.sectionTitle, systemImage: section.category.systemImage)
                }
            }
        }
        .listStyle(.insetGrouped)
        .animation(.default, value: viewModel.items)
    }

    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
        ToolbarItem(placement: .topBarLeading) {
            Menu {
                Button("Annuler le dernier scan", systemImage: "arrow.uturn.backward") {
                    viewModel.undoLastScan()
                }
                Button("Vider l'inventaire", systemImage: "trash", role: .destructive) {
                    isClearConfirmationPresented = true
                }
                #if DEBUG
                Divider()
                Button("+ scan factice (debug)", systemImage: "wand.and.stars") {
                    viewModel.addFakeScan()
                }
                #endif
            } label: {
                Label("Actions", systemImage: "ellipsis.circle")
            }
        }
    }
}

/// Ligne d'inventaire : picto catégorie + pastille couleur (D09 fallback),
/// nom v0, part_id/couleur, quantité + stepper.
private struct InventoryRowView: View {
    let item: InventoryItem
    let onIncrement: () -> Void
    let onDecrement: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: item.category.systemImage)
                .font(.title3)
                .foregroundStyle(.secondary)
                .frame(width: 28)
                .overlay(alignment: .bottomTrailing) {
                    PartColorSwatch(colorId: item.colorId)
                        .offset(x: 4, y: 4)
                }

            VStack(alignment: .leading, spacing: 2) {
                Text(item.displayName)
                    .font(.body)
                Text("réf. \(item.partId) · couleur \(item.colorId)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Text("\(item.quantity)")
                .font(.body.monospacedDigit().weight(.semibold))
                .contentTransition(.numericText())

            Stepper("Quantité de \(item.displayName)", onIncrement: onIncrement, onDecrement: onDecrement)
                .labelsHidden()
        }
    }
}

#Preview {
    let repository: any InventoryRepository = {
        // Preview : base en mémoire, jamais le user.sqlite réel.
        let repository = GRDBInventoryRepository(database: try! DatabaseManager.inMemory())
        Task {
            try? await repository.setQuantity(partId: "3001", colorId: 4, quantity: 12)
            try? await repository.setQuantity(partId: "3020", colorId: 71, quantity: 7)
            try? await repository.setQuantity(partId: "3068", colorId: -1, quantity: 3)
        }
        return repository
    }()

    NavigationStack {
        InventoryView(repository: repository)
            .navigationTitle("Inventaire")
    }
}
