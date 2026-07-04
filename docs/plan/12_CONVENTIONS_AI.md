# Conventions, contrats inter-modules & guide pour IA exécutante

> Fichier de référence transverse. TOUTE implémentation (humaine ou IA) doit s'y conformer.
> Règle d'or : un contrat se modifie ICI d'abord, dans le code ensuite.

---

## 1. Contrats de données (source de vérité)

### 1.1 Identifiants
- `part_id` : String, référence catalogue Rebrickable (ex `"3001"`). Jamais d'entier.
- `color_id` : Int, id couleur Rebrickable. `-1` réservé = "unknown".
- `set_num` : String, format Rebrickable (ex `"31058-1"`).

### 1.2 Sortie pipeline vision (Swift ↔ tests ↔ export JSON)
```json
{
  "scan_id": "uuid",
  "created_at": 1750000000,
  "pieces": [
    {
      "part_id": "3001",
      "color_id": 4,
      "bbox": {"x": 0.12, "y": 0.30, "w": 0.08, "h": 0.06},
      "part_confidence": 0.91,
      "color_confidence": 0.84
    }
  ]
}
```
- bbox : normalisée 0–1, origine en haut à gauche, repère de l'image orientée droite.
- Toute confidence ∈ [0,1].

### 1.3 Export inventaire (Settings → JSON)
```json
{
  "format_version": 1,
  "exported_at": 1750000000,
  "catalog_version": "rebrickable-2026-XX-XX",
  "items": [{"part_id": "3001", "color_id": 4, "quantity": 12}]
}
```

### 1.4 Config couleur partagée Python/Swift
`color_config.json` (un seul fichier, embarqué dans `ml/` ET dans le bundle iOS — synchronisé, jamais dupliqué avec des valeurs divergentes) :
```json
{
  "version": 1,
  "unknown_delta_e_threshold": 20.0,
  "median_sample_min_pixels": 50,
  "bbox_padding_ratio": 0.10
}
```

### 1.5 Contrats I/O des modèles CoreML
| Modèle | Input | Output |
|---|---|---|
| DET | Image 640×640 RGB, normalisation embarquée dans le mlpackage | boxes [N×4] normalisées + scores [N] (+ NMS intégré si retenu en CH-3) |
| CLS | Image 224×224 RGB, normalisation embarquée | probs [1000], mapping via `classes_v1.json` |

`classes_v1.json` :
```json
{"version": "1.0", "classes": {"3001": 0, "3002": 1}}
```

---

## 2. Conventions de code

### Swift
- Swift API Design Guidelines. SwiftLint config de base.
- MVVM : View sans logique métier ; ViewModel sans import AVFoundation/GRDB (passe par les services/repositories).
- Concurrence : async/await ; services d'inférence et agrégateur = actors ; jamais de DB ni d'inférence sur le main thread.
- Erreurs : enums `Error` typées par domaine (`VisionError`, `DatabaseError`, `MatchingError`), messages utilisateur localisés séparés des erreurs techniques.
- Logs : `os.Logger`, un subsystem par module, jamais de données personnelles ni d'images en logs.
- Tests : un fichier de test par service/repository ; nommage `test_<méthode>_<cas>_<attendu>()`.

### Python (ml/)
- Python 3.11, formatage black, type hints obligatoires sur les fonctions publiques.
- Tout script accepte `--help` (argparse) et est rejouable (idempotent ou option `--force`).
- Seeds fixés (`torch`, `numpy`, `random`) dans tout script d'entraînement.
- Aucun chemin en dur : config via argparse ou fichier `config.yaml` versionné.

### Git
- Branches : `ml/<sujet>`, `ios/<sujet>`, `data/<sujet>`.
- Commits : conventional commits (`feat:`, `fix:`, `docs:`, `chore:`).
- Tags de jalons : `models-v1.0`, `coreml-v1.0`, `app-v1.0`.
- Jamais dans git : poids de modèles, datasets, sqlite catalogue, secrets. (Git LFS ou stockage externe documenté dans `docs/ACCESS.md`.)

---

## 3. Guide d'exécution pour une IA

### 3.1 Posture attendue
1. **Lire le fichier de chantier en entier avant de coder.**
2. Exécuter jalon par jalon, dans l'ordre. Un jalon = livrables + critères cochés.
3. **Interdiction d'inventer** : si une version de lib, une URL, un comportement d'API n'est pas vérifiable → STOP, documenter le point, proposer 2–3 hypothèses, demander arbitrage.
4. Les valeurs marquées "à vérifier au moment de l'exécution" (licences, versions Xcode, guidelines App Store, état des frameworks YOLO) doivent être re-vérifiées réellement, pas supposées.
5. Toute déviation au plan → consigner dans le `CHANGELOG_CHx.md` du chantier avec justification.

### 3.2 Format de compte-rendu par jalon (obligatoire)
```markdown
## Jalon X.Y — <nom>
- Statut : ✅ / ❌ / ⏸ bloqué
- Livrables produits : <chemins>
- Critères d'acceptation : <checklist cochée avec preuve (sortie de commande, métrique, screenshot)>
- Écarts au plan : <aucun | détail>
- Blocages / questions : <aucun | détail + hypothèses proposées>
```

### 3.3 Prompts types (à donner à l'IA exécutante)

**Démarrage d'un chantier :**
> Tu exécutes le chantier CH-X du projet LEGO AI Offline. Lis `00_MASTER_PLAN.md`, `12_CONVENTIONS_AI.md` puis `0X_CHX_*.md` en entier. Confirme ta compréhension en listant les jalons et leurs livrables, signale toute ambiguïté AVANT de commencer. Puis exécute le jalon X.1 uniquement, et rends ton compte-rendu au format §3.2.

**Reprise après blocage :**
> Voici l'arbitrage sur ton blocage du jalon X.Y : <décision>. Mets à jour `CHANGELOG_CHX.md`, puis reprends l'exécution du jalon X.Y.

**Revue croisée (recommandé : faire relire chaque jalon par une seconde session IA) :**
> Tu es relecteur. Voici le plan du jalon X.Y (`0X_CHX_*.md`) et l'implémentation produite. Vérifie : conformité aux contrats de `12_CONVENTIONS_AI.md`, critères d'acceptation réellement prouvés, code conforme aux conventions §2. Rends une liste de non-conformités, sans rien corriger toi-même.

### 3.4 Anti-patterns interdits
- Coder plusieurs jalons d'un coup sans validation intermédiaire
- Modifier un contrat (§1) "localement" sans mettre à jour ce fichier
- Affirmer qu'un test passe sans montrer la sortie
- Introduire une dépendance non listée sans justification écrite
- Renommer/déplacer la structure de dossiers définie en CH-4

---

## 4. Glossaire
| Terme | Définition |
|---|---|
| DET | Modèle de détection mono-classe "lego_piece" |
| CLS | Modèle de classification 1000 classes (part_id) |
| COLOR | Pipeline déterministe LAB d'identification couleur |
| Coverage | Σ pièces disponibles / Σ pièces requises d'un set |
| Scope V1 | Les 1000 classes de `classes_v1.json` |
| Realworld test | Set de test photographié maison, jamais vu à l'entraînement |
| Mode souple | Matching sur part_id sans contrainte couleur |
