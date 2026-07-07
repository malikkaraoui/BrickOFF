# REPRISE — document de continuité ("le testament")

> **Si l'exécutant actuel (humain ou IA) disparaît, ce document permet de reprendre le projet
> sans perte.** Il est mis à jour à chaque étape significative. Dernière mise à jour :
> **2026-07-07 (bilan d'étape committé)**.

## 1. Ordre de lecture pour reprendre à froid

1. `docs/VISION.md` — ce qu'on construit et pourquoi (normatif, formulation du PO)
2. `docs/plan/ARBITRAGES/00_INDEX.md` — les 10 décisions D01→D10 (priment sur tout le reste)
3. `docs/plan/00_MASTER_PLAN.md` — le plan chantier par chantier (amendé, voir bandeau en tête)
4. Les `docs/plan/CHANGELOG_CHx.md` existants (CH-0, CH-1, CH-4) — où en est chaque chantier
5. `docs/plan/12_CONVENTIONS_AI.md` — conventions de code et contrats AVANT d'écrire une ligne
6. Ce fichier — état instantané et prochaines actions

## 2. État instantané des chantiers

| Chantier | État | Détail |
|---|---|---|
| CH-0 Légal | **95 %** | 8/11 remédiations levées. Restent : R3/R4 (emails PO), R7 ✅ (D09). Voir `CHANGELOG_CH0.md` |
| CH-1 Dataset | **jalon 1.1 ✅ clos** | 3 sources acquises + certifiées (1,03 M images, manifests versionnés). Voir `CHANGELOG_CH1.md` |
| CH-2 Training | **jalon 2.0 ✅ clos** | Audit : feu vert, aucun critère de bascule ; corpus réel 82 % mono-pièce → tas = synthétique + jalon 1.7. Voir `CHANGELOG_CH2.md` + `ml/AUDIT_DATASET.md` |
| CH-4 iOS | **✅ CLOS (4.1→4.4)** | 22 tests verts, CI GitHub Actions (macos-26). Reste : run sur device physique (PO). Voir `CHANGELOG_CH4.md` |
| CH-6 Inventaire | **✅ CLOS (6.1→6.3)** | 48 tests verts, undo de scan exact, écran fonctionnel. Voir `CHANGELOG_CH6.md` |
| Design | ⏳ parallèle | Session Claude dédiée lancée par le PO avec `docs/design/BRIEF_CLAUDE_DESIGN.md` |
| Autres | ⬜ | Dans l'ordre du Master Plan |

## 3. Tâches de fond éventuellement en cours (à vérifier en reprenant)

- **CHAÎNE S.5 EN COURS — DÉMON DÉTACHÉ (relancée 2026-07-06 ~4h30, ~12-17 h)** : après deux
  interruptions des tâches de session, la chaîne tourne en nohup hors session :
  script `ml/runs/run_s5_chain.sh`, log `ml/runs/s5_chain.log`, ordre C→B→A avec éval test auto.
  Relance en cas de mort : éditer le script (commenter les recettes déjà évaluées) puis
  `nohup caffeinate -ims ml/runs/run_s5_chain.sh >> ml/runs/s5_chain.log 2>&1 &`.
  ⚠️ MacBook branché secteur + couvercle OUVERT pendant les calculs.
  État CH-S : préflight ✅ · S.1 ✅ · S.2 ✅ · S.3 ✅ · **S.4 ✅ CLOS (10 000 scènes, 0 erreur,
  manifest versionné)** · S.5 🔄 · S.0 photos PO ⏳ **toujours attendues — sans elles, pas de
  verdict "tas"** (les évals test actuelles restent mono-pièce). Les 3 runs DET (v0, v0_1, v1) sont
  TERMINÉS — rapports `ml/runs/det_v0/EVAL_DET_V0.md` et `ml/runs/det_v1/EVAL_DET_V1.md`.
  Meilleur modèle : `ml/runs/det_v1/best.pt` (mAP@50 test 0.773, rappel max 0.985).
- Datasets : acquisition et intégrité TERMINÉES (jalon 1.1 clos) — ne rien relancer.

## 4. File d'attente des prochaines actions

**Le plan de vol adapté fait foi : `docs/plan/17_BILAN_ENTRAINEMENTS.md` §4** (verdict TAS →
bilan CLS → itérations post-TAS → branchement modèle réel CH-5 → CSV Rebrickable → CH-3 réel).
Les 3 itérations DET restantes sont GELÉES jusqu'au verdict TAS. D11 : SSDLite = candidat production.

## 5. Actions en attente côté product owner (Malik)

- [ ] **PHOTOS DE TAS (S.0, nouveau, ~3-4 h)** : ~100 scènes de tas (10-40 pièces), 3 éclairages
  dont chaud, 3+ fonds, dont ≥ 20 scènes hors domicile principal ou 2e téléphone (holdout).
  Protocole détaillé fourni par l'exécutant avant la première photo. Déposer dans data/raw/piles_malik/
- [ ] Envoyer l'email Rebrickable (brouillon : `legal/REBRICKABLE_LICENSE.md`) — confirmation, non bloquant
- [ ] Envoyer l'email Brickognize (brouillon : `legal/ML_LICENSES.md`) — débloque la pré-annotation
- [ ] Enregistrer les domaines brickoff.app / brickoff.fr (libres au 2026-07-04)
- [ ] Dépôt marque EUIPO classes 9+42 (avant CH-8)
- [ ] Vérifier adhésion Apple Developer Program active (le compte existe)
- [ ] Entériner : cible iOS 17 + XcodeGen (écarts CH-4), décision D03 pub (renversée par PO, actée)
- [ ] Brancher un iPhone pour valider le run sur device (critère CH-4 en attente)

## 6. Spécificités machine & environnement (M1, 16 Go)

- Python : `.venv/` (3.12) à la racine — `source .venv/bin/activate`. Deps gelées : `ml/requirements.txt`.
  torch 2.12.1, **MPS vérifié actif** (D10 : entraînement local nominal, escalade cloud si > 48 h projetées).
- iOS : Xcode 26.6, **XcodeGen** (`cd ios && xcodegen generate`) — le `.xcodeproj` est un artefact,
  seul `ios/project.yml` fait foi. Tests : `xcodebuild build test -scheme BrickOFF -destination
  'platform=iOS Simulator,name=iPhone 17'`.
- Git : remote SSH `git@github.com:malikkaraoui/BrickOFF.git`, tout sur `main`, commits fréquents.
  Style de message : **le POURQUOI, jamais le comment**. Identité locale du repo : karaoui.malik@gmail.com
  (le config global a une typo @hmail.com, ne pas s'y fier).
- `research/` = clones d'étude **gitignorés** : certains sans licence → **ne jamais publier ni copier
  leur code** (salle blanche : lire, comprendre, fermer, réécrire). `_hors_projet/` = hors BrickOFF.
- `data/raw/`, `data/processed/`, poids, sqlite : gitignorés. Les **manifests** (provenance, sha256,
  stats) sont versionnés — c'est la preuve d'acceptation des jalons data.

## 7. Méthode de travail (à perpétuer)

- Un jalon = livrables + critères binaires prouvés. Compte-rendu format `12_CONVENTIONS_AI.md` §3.2.
- **Chaque lot de livrables sensibles passe par une revue adversaire** (agent indépendant chargé de
  démolir) avant d'être considéré acquis — cf. `legal/CHALLENGE_CH0_REVUE_ADVERSAIRE.md`.
- Toute décision structurante = un fichier `Dxx` dans `docs/plan/ARBITRAGES/` + ligne dans l'index.
- **Le README (feuille de route + tableau d'avancement par chantier) se met à jour à CHAQUE étape
  significative, en même temps que ce fichier et le CHANGELOG du chantier** — demande explicite du
  PO : le README GitHub est sa vue de pilotage.
- Paralléliser par sous-agents quand les tâches sont indépendantes ; toujours faire écrire les
  livrables dans le repo, committer depuis la session principale.
- En cas de doute juridique : lecture conservatrice + question dans l'email de confirmation concerné.
