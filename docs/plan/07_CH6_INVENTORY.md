# CH-6 — Inventaire local (persistance)

> Durée : 1 semaine. Dépend de CH-4. Parallélisable avec CH-5.

---

## Jalon 6.1 — Schéma base de données (GRDB)

### Deux bases distinctes (décision d'architecture)
1. **`user.sqlite`** — données utilisateur, lecture/écriture, sauvegardée (iCloud backup OK)
2. **`rebrickable.sqlite`** — catalogue en lecture seule, embarquée dans le bundle, remplaçable par OTA (CH-10)

Justification : séparer le mutable du référentiel simplifie les updates OTA et les migrations.

### Schéma `user.sqlite`
```sql
CREATE TABLE inventory (
    part_id   TEXT NOT NULL,
    color_id  INTEGER NOT NULL,
    quantity  INTEGER NOT NULL CHECK (quantity >= 0),
    updated_at INTEGER NOT NULL,          -- epoch seconds
    PRIMARY KEY (part_id, color_id)
);

CREATE TABLE scan_history (
    id         TEXT PRIMARY KEY,           -- UUID
    created_at INTEGER NOT NULL,
    piece_count INTEGER NOT NULL,
    payload    TEXT NOT NULL               -- JSON [DetectedPiece] pour audit/annulation
);

CREATE TABLE app_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL                    -- versions de schéma, du catalogue, etc.
);
```

### Critères d'acceptation
- [ ] Migrations GRDB en place (DatabaseMigrator, migration "v1")
- [ ] Contrainte quantity ≥ 0 testée (l'insertion négative échoue)

---

## Jalon 6.2 — InventoryRepository

### API attendue (contrat)
```swift
protocol InventoryRepository {
    func addPieces(_ pieces: [DetectedPiece]) async throws   // incrémente les quantités
    func setQuantity(partId: String, colorId: Int, quantity: Int) async throws // 0 = suppression
    func allItems() async throws -> [InventoryItem]
    func totalPieceCount() async throws -> Int
    func clear() async throws
    func observeItems() -> AsyncStream<[InventoryItem]>      // pour l'UI réactive (ValueObservation GRDB)
}
```

### Règles métier
1. `addPieces` regroupe par (part_id, color_id) et incrémente — transaction unique
2. Chaque scan ajouté crée une entrée `scan_history` → permet "annuler le dernier scan"
3. Toute écriture passe par le repository — aucune requête SQL hors de `Core/Database/`

### Tests
- Ajout, incrément, mise à zéro, annulation de scan, observation réactive : 1 test chacun minimum

### Critères d'acceptation
- [ ] Tests verts
- [ ] Annulation de scan restaure exactement l'état antérieur (test avec quantités croisées)

---

## Jalon 6.3 — Écran inventaire (fonctionnel, UI brute)

### Spécifications
1. Liste groupée : par catégorie de pièce (briques / plates / tiles / autres — mapping catégorie depuis le catalogue), puis tri par quantité décroissante
2. Chaque ligne : visuel de pièce (voir note), nom, pastille couleur, quantité avec stepper
3. Recherche par nom de pièce / part_id
4. Actions : modifier quantité, supprimer, "annuler le dernier scan", vider l'inventaire (confirmation)
5. Compteur global de pièces en header

### Note visuels de pièces
Rebrickable fournit des URLs d'images de pièces — mais offline-first. Options :
- **V1 recommandé** : pictos génériques par catégorie + nom + pastille couleur (zéro asset à embarquer)
- V2 : bundle d'images des 1000 pièces du scope (vérifier licence images Rebrickable AVANT — peut différer de la licence des données)

### Critères d'acceptation
- [ ] Inventaire de 1000 lignes scrolle fluide (LazyVStack, pas de jank)
- [ ] Recherche réactive < 100ms
- [ ] Toutes les actions CRUD opérationnelles avec UI réactive (observeItems)

---

## Sortie de chantier CH-6

- Persistance complète testée, écran inventaire fonctionnel
- `CHANGELOG_CH6.md`
