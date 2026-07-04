# 13 — Génération de figures : 3 approches détaillées

> Extension hors brief initial. Objectif : proposer des constructions réalisables avec l'inventaire scanné, au-delà du simple matching de sets existants.
>
> **Amendé le 2026-07-04 (post-revue adversaire CH-0)** : format blueprint A1 mis en conformité avec
> `docs/research/INSTRUCTIONS_FORMATS.md` (R1–R7) — géométrie portée par les alternatives, champ
> `steps` référencé par slots, règle de validation éditoriale (constats 12 et 16).

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

### Format blueprint (proposition — amendée 2026-07-04 selon `docs/research/INSTRUCTIONS_FORMATS.md`, R1–R7)
```json
{
  "id": "duck_small",
  "name": "Petit canard",
  "difficulty": 1,
  "slots": [
    {
      "slot_id": "body",
      "alternatives": [
        {"parts": [
          {"part_id": "3001", "pos": [0, 0, 0], "rot": 0},
          {"part_id": "3001", "pos": [0, 0, 2], "rot": 0}
        ]},
        {"parts": [
          {"part_id": "3003", "pos": [0, 0, 0], "rot": 0},
          {"part_id": "3003", "pos": [2, 0, 0], "rot": 0},
          {"part_id": "3003", "pos": [0, 0, 2], "rot": 0},
          {"part_id": "3003", "pos": [2, 0, 2], "rot": 0}
        ]}
      ],
      "color_group": "A"
    }
  ],
  "steps": [
    {
      "id": 1,
      "placements": [{"slot_id": "body", "pos": [0, 0, 0], "rot": 0}],
      "camera": {"yaw": 30, "pitch": 20}
    }
  ],
  "color_rules": {"A": "any_uniform", "B": "contrast_with_A"}
}
```
- `alternatives` : pièces interchangeables pour remplir le slot (2 briques 2x4 OU 4 briques 2x2) — **chaque alternative porte sa GÉOMÉTRIE** : positions relatives des pièces dans le slot (`pos` = `[x, y, z]`, x/z en studs, y en plates ; convention compatible LDraw : 1 stud = 20 LDU, 1 plate = 8 LDU, 1 brique = 3 plates — cf. R7). Sans cette géométrie, le rendu pas-à-pas serait impossible (R1) — c'était le trou du schéma initial (constat 12)
- `steps` : séquence d'étapes référençant des **`slot_id`, jamais des pièces concrètes** → les mêmes steps restent valides quelle que soit l'alternative choisie par le solveur ; l'inventaire d'étape est dérivé après résolution, jamais stocké (R1/R6). `camera` optionnel : absent = angle hérité de l'étape précédente, présent = rotation explicite (équivalent `ROTSTEP` LDraw, R4)
- Granularité des steps : **1 à 5 pièces nouvelles par étape selon `difficulty` — CHOIX ÉDITORIAL BrickOFF à calibrer en beta**, pas un standard LEGO (LEGO ne publie aucun chiffre, cf. constat 16 et R2)
- `color_rules` : contraintes souples ("uniforme", "contraste") plutôt que couleurs imposées → maximise la solvabilité

### Règle de validation (outil éditorial — R3)
La connectivité et la stabilité de chaque **préfixe d'étapes** (après chaque étape, le modèle partiel tient seul, aucune pièce flottante, bottom-up par défaut) sont vérifiées **côté OUTIL ÉDITORIAL**, jamais sur mobile — le mobile fait confiance au blueprint, cohérent avec "garanti par design". La validation doit couvrir **toutes les combinaisons d'alternatives** ; pour maîtriser l'explosion combinatoire, **contrainte d'édition** : les alternatives d'un même slot doivent être **géométriquement équivalentes** (même encombrement, mêmes points de connexion exposés) — c'est ce qui rend la validation slot par slot suffisante. Détails et justifications sourcées : `docs/research/INSTRUCTIONS_FORMATS.md` (R1–R7).

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
