# CH-7 — Moteur de matching (sets réalisables)

> Durée : 2 semaines. Dépend de CH-6 + snapshot Rebrickable (CH-0).
> Feature différenciante de l'app. La performance est le risque principal.

---

## Jalon 7.1 — Construction de `rebrickable.sqlite`

### Pipeline (script Python, côté `ml/` ou `data/scripts/`)
1. Télécharger le snapshot CSV Rebrickable (sets, inventories, inventory_parts, parts, colors, themes)
2. Filtrer :
   - Sets uniquement (pas les minifigs seules) — V1
   - **Sets dont ≥ 95% des pièces appartiennent au scope `classes_v1.json`** → un set avec des pièces hors scope n'est jamais matchable, inutile de l'embarquer
   - Exclure les sets > 1500 pièces (V1 : peu pertinents pour un tas scanné)
3. Construire le SQLite :

```sql
CREATE TABLE sets (
    set_num   TEXT PRIMARY KEY,
    name      TEXT NOT NULL,
    year      INTEGER NOT NULL,
    theme_id  INTEGER NOT NULL,
    num_parts INTEGER NOT NULL
);

CREATE TABLE set_parts (
    set_num  TEXT NOT NULL,
    part_id  TEXT NOT NULL,
    color_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (set_num, part_id, color_id)
);
CREATE INDEX idx_set_parts_part ON set_parts(part_id, color_id);

CREATE TABLE themes (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE catalog_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL); -- version snapshot, date, scope classes
```

4. Mesurer la taille finale ; si > 80 Mo : resserrer les filtres (année min, nb sets max par thème)

### Livrable
- `data/scripts/07_build_catalog.py` + `rebrickable.sqlite` versionné (stockage externe, pas git)
- `docs/CATALOG_STATS.md` : nb de sets retenus, distribution par thème/année, taille

### Critères d'acceptation
- [ ] ≤ 80 Mo
- [ ] ≥ 3 000 sets matchables embarqués (sinon revoir le scope — discuter)
- [ ] Vérification manuelle : 3 sets connus → liste de pièces conforme au site Rebrickable

---

## Jalon 7.2 — MatchingEngine (algorithme)

### Algorithme V1
```
Input  : inventaire [(part_id, color_id, qty)]
Output : [SetMatchResult] trié par coverage desc

1. PRÉ-FILTRE (SQL, rapide) :
   candidats = sets ayant au moins K pièces distinctes en commun avec l'inventaire
   (jointure sur idx_set_parts_part ; K départ = 5)
   ET num_parts <= total_inventaire * 1.5   -- inutile d'évaluer un set 4x trop gros

2. SCORING (Swift, par candidat) :
   pour chaque (part_id, color_id, qty_requise) du set :
       dispo = min(qty_inventaire, qty_requise)
   coverage = Σ dispo / Σ qty_requise

3. MODE "couleur stricte" vs "couleur souple" (toggle utilisateur) :
   souple = matcher sur part_id seul (ignorer color_id) → coverage_souple
   V1 : calculer les deux, afficher le mode choisi

4. FILTRE : coverage >= 0.7 (configurable)
5. TRI : coverage desc, puis num_parts desc
6. missingParts = pièces où dispo < requis (pour l'écran détail)
```

### Implémentation
- `MatchingEngine` en Swift, injecté avec les deux DB (lecture seule sur rebrickable, lecture inventaire via repository)
- Calcul intégral hors main thread (Task.detached ou actor dédié)
- Cache : résultat invalidé sur modification d'inventaire (hash de l'inventaire comme clé)

### Tests
1. Tests unitaires sur mini-catalogue fixture (5 sets synthétiques) : coverage exacts attendus, mode souple/strict, pièces manquantes exactes
2. Test de non-régression : inventaire de référence → top-10 sets figé

### Critères d'acceptation
- [ ] Tests verts, valeurs de coverage vérifiées à la main sur les fixtures
- [ ] Zéro accès DB sur le main thread (vérifier avec Main Thread Checker)

---

## Jalon 7.3 — Performance

### Protocole de benchmark
- Inventaires synthétiques : 100 / 500 / 2000 pièces (générés depuis des sets réels mélangés)
- Mesure : temps total matching, sur les 2 devices de test

### Cibles
| Inventaire | Device médian | Device ancien |
|---|---|---|
| 100 pièces | ≤ 500 ms | ≤ 1.5 s |
| 500 pièces | ≤ 2 s | ≤ 5 s |
| 2000 pièces | ≤ 5 s | ≤ 12 s |

### Plan B si cibles ratées (dans l'ordre)
1. Resserrer le pré-filtre K
2. Pré-calculer un index inversé part_id → [set_num] chargé en mémoire au lancement
3. Limiter les candidats aux 2 000 sets les plus proches en taille
4. Affichage progressif (résultats en streaming) — change l'UX, dernier recours

### Critères d'acceptation
- [ ] Cibles atteintes OU Plan B appliqué + nouvelles mesures documentées
- [ ] UI jamais bloquée pendant le calcul (indicateur de progression)

---

## Jalon 7.4 — Écrans matching (fonctionnels, UI brute)

1. Liste des sets réalisables : visuel placeholder, nom, année, coverage en %, badge "complet" si 100%
2. Toggle strict/souple visible et persistant (UserDefaults)
3. Détail d'un set : infos, liste pièces requises avec dispo/manquant, lien web Rebrickable (si réseau — dégradé propre sinon)
4. État vide intelligent : si inventaire < 30 pièces, message "scannez plus de pièces" plutôt qu'une liste vide

### Critères d'acceptation
- [ ] Navigation liste → détail fluide
- [ ] États vide / chargement / erreur tous gérés

---

## Sortie de chantier CH-7

- Matching bout en bout : scan → inventaire → sets proposés
- `CHANGELOG_CH7.md`
