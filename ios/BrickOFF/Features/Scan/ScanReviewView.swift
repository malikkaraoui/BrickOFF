import SwiftUI

/// Écran de revue du scan (jalon 5.6) : capture figée + pièces consolidées,
/// corrections (suppression / couleur / part_id), section "incertaines" dédiée,
/// puis ajout EXPLICITE à l'inventaire.
struct ScanReviewView: View {
    let model: ScanReviewViewModel
    /// Appelé à la fermeture (annulation ou ajout réussi).
    let onClose: () -> Void

    /// Wrapper Identifiable pour `.sheet(item:)` (pas de conformance rétroactive sur UUID).
    private struct EditingGroup: Identifiable {
        let id: UUID
    }

    @State private var editingGroup: EditingGroup?

    var body: some View {
        NavigationStack {
            List {
                Section {
                    CaptureHeaderView(model: model)
                        .listRowInsets(EdgeInsets())
                }

                if model.groups.isEmpty {
                    ContentUnavailableView(
                        "Aucune pièce détectée",
                        systemImage: "questionmark.square.dashed",
                        description: Text("Rapprochez-vous des pièces et relancez un scan.")
                    )
                } else {
                    if !model.certainGroups.isEmpty {
                        Section("Pièces détectées") {
                            ForEach(model.certainGroups) { group in
                                row(for: group)
                            }
                        }
                    }
                    if !model.uncertainGroups.isEmpty {
                        Section {
                            ForEach(model.uncertainGroups) { group in
                                row(for: group)
                            }
                        } header: {
                            Text("Incertaines")
                        } footer: {
                            Text("Ces détections ne sont jamais ajoutées automatiquement. Corrigez-les ou cochez-les pour les inclure.")
                        }
                    }
                }
            }
            .navigationTitle("Revue du scan")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Annuler", role: .cancel) { onClose() }
                }
            }
            .safeAreaInset(edge: .bottom) {
                addButton
            }
            .sheet(item: $editingGroup) { editing in
                if let group = model.groups.first(where: { $0.id == editing.id }) {
                    GroupEditSheet(model: model, group: group)
                        .presentationDetents([.medium, .large])
                }
            }
            .alert(
                "Erreur",
                isPresented: Binding(
                    get: { model.errorMessage != nil },
                    set: { if !$0 { model.errorMessage = nil } }
                )
            ) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(model.errorMessage ?? "")
            }
        }
        .interactiveDismissDisabled()
    }

    private func row(for group: ScanReviewViewModel.ReviewGroup) -> some View {
        ReviewGroupRow(model: model, group: group) {
            editingGroup = EditingGroup(id: group.id)
        }
    }

    private var addButton: some View {
        Button {
            Task {
                if await model.addToInventory() {
                    onClose()
                }
            }
        } label: {
            if model.isAdding {
                ProgressView()
                    .frame(maxWidth: .infinity)
            } else {
                Text("Ajouter à l'inventaire (\(model.includedPieceCount))")
                    .frame(maxWidth: .infinity)
            }
        }
        .buttonStyle(.borderedProminent)
        .controlSize(.large)
        .disabled(model.includedPieceCount == 0 || model.isAdding)
        .padding()
        .background(.bar)
    }
}

// MARK: - Capture figée + overlay des détections

private struct CaptureHeaderView: View {
    let model: ScanReviewViewModel

    var body: some View {
        Group {
            if let image = model.capturedFrame?.uiImage() {
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
            } else {
                Rectangle()
                    .fill(Color(.systemGray5))
                    .aspectRatio(16 / 9, contentMode: .fit)
                    .overlay {
                        Text("Capture indisponible")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
            }
        }
        .overlay {
            GeometryReader { geometry in
                ForEach(Array(model.overlayBoxes.enumerated()), id: \.offset) { _, entry in
                    Rectangle()
                        .strokeBorder(entry.isUncertain ? Color.orange : Color.green, lineWidth: 2)
                        .frame(
                            width: entry.box.width * geometry.size.width,
                            height: entry.box.height * geometry.size.height
                        )
                        .offset(
                            x: entry.box.origin.x * geometry.size.width,
                            y: entry.box.origin.y * geometry.size.height
                        )
                }
            }
        }
        .clipped()
    }
}

// MARK: - Ligne d'un groupe consolidé

private struct ReviewGroupRow: View {
    let model: ScanReviewViewModel
    let group: ScanReviewViewModel.ReviewGroup
    let onEdit: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            // Vignette v0 : picto de catégorie (les crops réels viendront avec CH-3).
            Image(systemName: PartCategory.heuristic(forPartId: group.partId).systemImage)
                .font(.title3)
                .foregroundStyle(.secondary)
                .frame(width: 28)

            VStack(alignment: .leading, spacing: 2) {
                Text("\(PartCategory.heuristic(forPartId: group.partId).pieceDisplayName) \(group.partId)")
                    .font(.body)
                Text("pièce \(confidenceLabel(group.partConfidence)) · couleur \(confidenceLabel(group.colorConfidence))")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            if group.isUncertain {
                Toggle("Inclure", isOn: Binding(
                    get: { group.includeInInventory },
                    set: { model.setIncluded(group.id, $0) }
                ))
                .labelsHidden()
            }

            PartColorSwatch(colorId: group.colorId, diameter: 18)
            Text("×\(group.quantity)")
                .font(.subheadline.monospacedDigit())
                .foregroundStyle(.secondary)
        }
        .contentShape(Rectangle())
        .onTapGesture(perform: onEdit)
        .swipeActions(edge: .trailing) {
            Button(role: .destructive) {
                model.deleteGroup(group.id)
            } label: {
                Label("Supprimer", systemImage: "trash")
            }
        }
    }

    private func confidenceLabel(_ value: Double) -> String {
        "\(Int((value * 100).rounded())) %"
    }
}

// MARK: - Feuille de correction (couleur + part_id + suppression)

private struct GroupEditSheet: View {
    let model: ScanReviewViewModel
    let group: ScanReviewViewModel.ReviewGroup

    @Environment(\.dismiss) private var dismiss
    @State private var partIdText = ""

    private let swatchColumns = [GridItem(.adaptive(minimum: 44), spacing: 8)]

    var body: some View {
        NavigationStack {
            Form {
                Section("Pièce") {
                    HStack {
                        // v0 : champ texte libre — le top-5 du vrai classifieur viendra avec CH-3.
                        TextField("part_id (ex. 3001)", text: $partIdText)
                            .autocorrectionDisabled()
                            .textInputAutocapitalization(.never)
                        Button("Corriger") {
                            model.setPartId(group.id, partId: partIdText)
                            dismiss()
                        }
                        .disabled(partIdText.trimmingCharacters(in: .whitespaces).isEmpty)
                    }
                }

                Section("Couleur") {
                    LazyVGrid(columns: swatchColumns, spacing: 8) {
                        ForEach(PartColorPalette.knownColorIds, id: \.self) { colorId in
                            Button {
                                model.setColor(group.id, colorId: colorId)
                                dismiss()
                            } label: {
                                PartColorSwatch(colorId: colorId, diameter: 36)
                                    .overlay {
                                        if colorId == group.colorId {
                                            Circle().strokeBorder(.tint, lineWidth: 3)
                                        }
                                    }
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(.vertical, 4)
                }

                Section {
                    Button("Supprimer cette détection", role: .destructive) {
                        model.deleteGroup(group.id)
                        dismiss()
                    }
                }
            }
            .navigationTitle("\(PartCategory.heuristic(forPartId: group.partId).pieceDisplayName) \(group.partId) ×\(group.quantity)")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("OK") { dismiss() }
                }
            }
            .onAppear { partIdText = group.partId }
        }
    }
}
