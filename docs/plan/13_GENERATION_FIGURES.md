# 13 — Génération de figures : 3 approches détaillées

> Extension hors brief initial. Objectif : proposer des constructions réalisables avec l'inventaire scanné, au-delà du simple matching de sets existants.

---

## Tableau comparatif

| Critère | A1 — Blueprints paramétriques | A2 — Recombinaison + substitutions | A3 — Génération IA |
|---|---|---|---|
| Difficulté technique | 🟢 Faible-moyenne | 🟡 Moyenne | 🔴 Élevée (recherche) |
| Risque d'échec | Faible | Faible-moyen | **Élevé** |
| Effort | 3–5 sem (dont éditorial) | 2–3 sem | Inconnu (spike requis) |
| Offline mobile | ✅ Trivial | ✅ Trivial | ⚠️ Incertain (< 300 Mo non garanti) |
| Résultat toujours constructible | ✅ Garanti par design | ✅ Garanti (sets réels) | ❌ Validation physique requise |
| Effet "magie" perçu | Moyen-fort | Moyen | Fort (si ça marche) |
| Dépendance ML | Aucune | Aucune | Totale |
| Cible roadmap | **V1.5** | **V1.5** | V3 (après spike) |

---

## A1 — Bibliothèque de blueprints paramétriques 🟢

### Principe
Une bibliothèque de constructions conçues À L'AVANCE (50 → 200 modèles : animaux, véhicules, maisons, robots...), mais définies de façon **flexible** : chaque emplacement du modèle accepte plusieurs pièces alternatives.

### Format blueprint (proposition)
```json
{
  "id": "duck_small",
  "name": "Petit canard",
  "difficulty": 1,
  "slots": [
    {
      "slot_id": "body",
      "alternatives": [
        [{"part_id": "3001", "qty": 2}],
        [{"part_id": "3003", "qty": 4}]
      ],
      "color_group": "A"
    }
  ],
  "color_rules": {"A": "any_uniform", "B": "contrast_with_A"}
}
```
- `alternatives` : listes de pièces interchangeables pour remplir le slot (1 brique 2x4 OU 2 briques 2x2)
- `color_rules` : contraintes souples ("uniforme", "contraste") plutôt que couleurs imposées → maximise la solvabilité

### Solveur
Backtracking simple : pour chaque slot, choisir une alternative satisfiable avec l'inventaire restant ; si impasse, revenir en arrière. Espace de recherche minuscule (modèles < 100 pièces, < 5 alternatives/slot) → résolution en millisecondes.

### Travail réel
- 70% éditorial : concevoir les blueprints (un designer + un outil de saisie, possiblement assisté par IA pour générer les variantes JSON depuis un modèle de référence)
- 30% dev : solveur + écran de présentation + instructions de montage étape par étape (les steps sont dans le blueprint)

### Pourquoi ça marche
C'est vraisemblablement le cœur de l'approche Brickit (non vérifiable, mais cohérent avec leur comportement produit : catalogue fini de "petites idées" adaptées au tas). Résultat garanti constructible, instructions incluses, zéro ML.

### Limites
- Catalogue fini → lassitude possible (mitigé par : ajout continu de blueprints via OTA)
- Coût éditorial récurrent

---

## A2 — Recombinaison de sets/MOC avec équivalences 🟡

### Principe
Étendre le MatchingEngine (CH-7) pour qu'un set devienne réalisable même sans les pièces EXACTES, via trois mécanismes :

1. **Équivalences fonctionnelles** : la table `part_relationships` de Rebrickable liste déjà des paires (molds alternatifs, prints, variantes). À enrichir avec des équivalences "de construction" (pièces géométriquement substituables).
2. **Décomposition dimensionnelle** : 1 brique 2x4 ≡ 2 briques 2x2 ≡ 4 briques 1x2 empilables... Table de décomposition maison (~50 règles couvrent l'essentiel des briques/plates standards).
3. **Relâchement couleur par zone** : déjà prévu (mode souple), affiné : autoriser la substitution couleur uniquement sur les pièces internes/non visibles si l'info existe (sinon, global).

### Impact algorithmique
Le scoring CH-7 devient : pour chaque pièce manquante, chercher une chaîne de substitution dans l'inventaire (recherche dans un graphe d'équivalences, profondeur ≤ 2). Complexité maîtrisée si le graphe est petit et indexé.

### Travail réel
- Construire la table de décomposition (travail fini, ~1 semaine, vérifiable à la main)
- Étendre le solveur + l'UI ("réalisable avec 6 substitutions" affiché clairement)

### Limites
- Le résultat visuel diverge du set officiel (couleurs, surfaces) → à assumer dans l'UI ("votre version")
- N'invente rien : reste borné au catalogue

---

## A3 — Génération IA de structures 🔴

### Principe
Un modèle génératif produit une structure LEGO originale (séquence de placements brique par brique) conditionnée par l'inventaire disponible et éventuellement un prompt ("fais-moi un chien").

### État de l'art (à re-vérifier au moment du spike — domaine mouvant)
- Travaux académiques existants sur la génération de structures LEGO (séquences de placement, voxels → briques, texte → structure). Qualité démontrée sur des cas simples, mais : pas de solution industrielle éprouvée identifiée, et je ne peux pas affirmer qu'un modèle publié soit directement exploitable.
- Trois sous-problèmes durs :
  1. **Génération** sous contrainte d'inventaire (le conditionnement par pièces disponibles est rarement traité)
  2. **Validation physique** : connectivité des studs, stabilité, constructibilité séquentielle (pouvoir poser les briques dans un ordre possible)
  3. **Embarqué offline** : tailles de modèles génératifs incompatibles a priori avec < 300 Mo — alternative : génération côté serveur (contredit offline) ou bibliothèque pré-générée (= retombe sur A1)

### Protocole de spike AVANT tout engagement (2 semaines, time-boxé)
| Jour | Activité | Go/No-Go |
|---|---|---|
| 1–2 | Revue de littérature à date + repos GitHub exploitables | ≥ 1 repo reproductible trouvé, licence OK |
| 3–6 | Reproduire la génération sur 10 exemples | ≥ 5/10 structures valides visuellement |
| 7–9 | Tester le conditionnement par inventaire (contrainte de pièces) | Faisable même grossièrement |
| 10–12 | Validation physique automatique (connectivité) | Vérificateur implémentable |
| 13–14 | Estimation taille/latence embarqué | Trajectoire < 300 Mo crédible OU pivot serveur assumé |
**No-Go à n'importe quelle étape → A3 abandonnée pour ce cycle, réévaluation dans 12 mois.**

### Position recommandée
Ne PAS engager A3 sans spike concluant. Le couple **A1 + A2 livre 80% de la valeur perçue pour 20% du risque.**

---

## Recommandation finale

```
V1   : Matching sets (CH-7, inchangé)
V1.5 : A1 (50 blueprints) + A2 (équivalences) — chantier CH-7bis à rédiger sur validation
V3   : Spike A3 (2 sem) → décision factuelle go/no-go
```
