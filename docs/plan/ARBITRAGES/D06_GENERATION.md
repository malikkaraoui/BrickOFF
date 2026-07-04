# D06 — Génération de constructions : roadmap du doc 13 officialisée

**Statut : ✅ Tranché (2026-07-04)**

## Contexte

`13_GENERATION_FIGURES.md` ("extension hors brief initial") compare 3 approches pour proposer des
constructions au-delà du matching de sets officiels :

- **A1** — Bibliothèque de blueprints paramétriques (slots + alternatives de pièces + règles couleur, solveur backtracking) 🟢
- **A2** — Recombinaison de sets avec équivalences/substitutions (extension du MatchingEngine CH-7) 🟡
- **A3** — Génération IA de structures originales 🔴 (recherche, offline < 300 Mo non garanti)

Il n'est référencé nulle part dans le Master Plan : sans arbitrage, soit il est ignoré, soit un
exécutant enthousiaste attaque A3 (le plus risqué) en croyant bien faire.

## Décision

**La recommandation finale du doc 13 est adoptée telle quelle comme roadmap officielle :**

```
V1   : Matching de sets uniquement (CH-7, inchangé). AUCUN travail de génération en V1.
V1.5 : A1 (50 blueprints initiaux) + A2 (équivalences/décompositions)
       → chantier "CH-7bis" à rédiger APRÈS la release V1, sur validation du product owner.
V3   : A3 uniquement via le spike time-boxé 2 semaines du doc 13, avec ses Go/No-Go chiffrés.
       No-Go à n'importe quelle étape → abandon pour le cycle, réévaluation à 12 mois.
```

## Justification

1. **Discipline de scope V1** : le Definition of Done du Master Plan ne mentionne pas la génération ; l'ajouter maintenant retarderait la seule chose qui compte (prouver le scan).
2. **A1+A2 = 80 % de la valeur perçue pour 20 % du risque** (analyse du doc 13, cohérente : résultat garanti constructible, zéro ML, offline trivial). C'est vraisemblablement l'approche Brickit — le "wow" ne nécessite pas de génération IA.
3. **A3 sans spike = pari non chiffré** sur 3 problèmes durs non résolus (conditionnement par inventaire, validation physique, taille embarquée). Le protocole de spike du doc 13 transforme ce pari en décision factuelle.

## Points d'anticipation V1 (gratuits, à respecter dès maintenant)

- CH-7 : garder le MatchingEngine extensible — le scoring par pièce est le point d'insertion des équivalences A2 (graphe de substitution, profondeur ≤ 2).
- CH-6/CH-10 : le format blueprint (JSON) transitera par l'OTA prévu en CH-10 — aucune conception supplémentaire requise en V1, juste ne pas verrouiller l'OTA sur le seul `rebrickable.sqlite`.

## Impacts

- `00_MASTER_PLAN.md` §2 : doc 13 à référencer dans l'index (note de renvoi en tête du Master Plan).
- `11_CH10_RELEASE.md` : le backlog V1.1+ mentionne déjà l'extension — cohérent.
- Nouveau chantier CH-7bis : **ne pas rédiger avant la release V1.**
