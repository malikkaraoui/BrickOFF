# CHANGELOG CH-0 — Préalables légaux, comptes & environnements

> Journal du chantier, tenu au fil de l'exécution (exigence Master Plan §3.6).

## 2026-07-04 — Ouverture du chantier, jalons 0.1–0.3 exécutés en v0, revue adversaire passée

### Statut des jalons

| Jalon | Statut | Livrable | Verdict provisoire |
|---|---|---|---|
| 0.1 Licence Rebrickable | ⏸ v0 contesté | `legal/REBRICKABLE_LICENSE.md` | **AUTORISÉ AVEC CONDITIONS** ("any purpose, including commercial", attribution appréciée non obligatoire) — email de confirmation à envoyer (action PO) |
| 0.2 Marque LEGO & nom | ⏸ v0 contesté | `legal/BRAND_COMPLIANCE.md` | **"BrickOFF" viable** (pas de "LEGO" dans le nom, "brick" générique, nom libre sur les stores) — clearance EUIPO/INPI à avancer |
| 0.3 Licences ML | ⏸ v0 contesté | `legal/ML_LICENSES.md` | Chaîne permissive confirmée (LDraw CC BY, dataset Apache-2.0, YOLOX/RT-DETR Apache-2.0) **SAUF** Brickognize (non-commercial → gelé) et dataset de détection (non identifié → bloquant) |
| 0.4 Comptes & accès | 🔶 partiel | — | ✅ Compte Apple existant (confirmé PO 2026-07-04). Restent : vérifier l'adhésion Developer Program active, compte HF, compte Rebrickable + clé API, choix GPU (local vs cloud ~50–200 €) |
| 0.5 Environnements | 🔶 partiel | — | ✅ Xcode déjà installé (confirmé PO 2026-07-04). Restent : env Python ML, devices de test physiques |

### Découvertes majeures (remontées au plan)

1. **Clause anti-IA Rebrickable** : "No Rebrickable content may be used in the training of AI
   models". Nos modèles ne s'entraînent PAS sur du contenu Rebrickable (images LDraw + photos
   maison), mais la sélection des 1000 classes via `inventory_parts` (CH-1 jalon 1.2) doit être
   juridiquement qualifiée (curation ≠ entraînement) et confirmée dans l'email à Rebrickable.
2. **Le dataset public LEGOBricks est 100 % synthétique** (rendus LDraw) → le "domain gap" du
   doc 14 n'est plus un risque, c'est un **état de départ certain**. CH-1 doit intégrer une
   source d'images réelles d'entraînement (photos maison en volume) dès le début, pas en plan B.
3. **API Brickognize non-commerciale** (ToS §2) → usage gelé ; email d'autorisation à envoyer
   (action PO) ; sinon annotation manuelle à chiffrer.
4. **Brevets LEGO sur la génération automatique d'instructions** (US8374829 et famille) →
   analyse de liberté d'exploitation requise AVANT tout engagement V1.5.

### Revue adversaire

Passée le 2026-07-04, 19 constats (4 critiques, 10 majeurs, 5 mineurs) :
`legal/CHALLENGE_CH0_REVUE_ADVERSAIRE.md`. Les livrables restent "v0 — contesté" jusqu'à levée
des critiques. Pourquoi on committe quand même : un verdict provisoire tracé et contesté vaut
mieux qu'un document parfait invisible — la contestation fait partie du livrable.

### Plan de remédiation (backlog CH-0, ordonné) — état au 2026-07-04 soir

| # | Action | Lève | Qui | Statut |
|---|---|---|---|---|
| R1 | Identifier le dataset de détection réel + licence | Critique 1 | IA | ✅ **Trouvé** : "Tagged images with LEGO bricks" (Gdańsk UT, CC BY 4.0, 2 933 scènes réelles annotées) + 77k crops réels de classification (447/1000 classes) → `docs/research/DATASETS_SURVEY.md`. Synthétique = voie de volume, réel = fine-tuning |
| R2 | Clause anti-IA Rebrickable analysée + sourçage ML_LICENSES | Critique 2, Majeur 10 | IA | ✅ Fait (v0.1). Découverte : clause ajoutée post-février 2026 |
| R3 | **Envoyer l'email Rebrickable** (brouillon prêt, question classes incluse) | Critique 2, Majeur 7 | **Malik** | ⏳ En attente PO |
| R4 | **Envoyer l'email Brickognize** (piotr.rybak@brickognize.com) | Majeur 13 | **Malik** | ⏳ En attente PO |
| R5 | Corpus réel d'entraînement en voie nominale (jalon 1.7 créé) | Critique 3 | IA | ✅ Fait — CH-1 et doc 14 amendés |
| R6 | Analyse brevets → `legal/PATENTS_ANALYSIS.md` | Critique 4 | IA | ✅ Fait. **Risque nul pour A1.** Garde-fous : pas d'étapes auto par désassemblage avant 2028-03, pas d'AR sur flux caméra avant 2032-05 (EP2714223 actif FR, litigé). Relecture conseil PI avant V1.5 |
| R7 | Trancher "images de sets dans l'app" + règle screenshots store | Majeurs 5, 6 | IA + PO | ⬜ **Reste à faire** (piste : rendus LDraw maison — décision D09 à rédiger) |
| R8 | Clearance marque + archives sources | Majeurs 9, 11 | IA | ✅ Fait. Voie libre (TMview/EUIPO/USPTO/INPI : 0 conflit). → PO : enregistrer brickoff.app/.fr (libres), dépôt EUIPO cl. 9+42 avant CH-8 |
| R9 | Plans B Rebrickable corrigés (CDN maison, droit sui generis UE) | Majeur 8 | IA | ✅ Fait (v0.1) |
| R10 | Doc 13 : géométrie des alternatives + steps par slots + validation éditoriale | Majeur 12 | IA | ✅ Fait |
| R11 | Mineurs 15–19 | Mineurs | IA | ✅ Fait (sources FSF/Blender/CC0 LDraw, assets CC0 only, interdits marketing) |

**Bilan : 8/11 remédiations levées le jour même. Restent : R3+R4 (emails, action PO) et R7 (décision produit images de sets).**

### Confirmations product owner (2026-07-04, oral)

- Compte Apple existant ; Xcode installé sur la machine de dev.
- Séquencement re-confirmé : **iOS d'abord, bascule Android seulement une fois iOS validé** (aligné D01).
- Brevets génération d'instructions : position PO = analyser et **contourner** (design-around,
  innovation, pas de copie) → R6 orientée liberté d'exploitation + stratégie de contournement.
- Piste design (icône, assets stores) lancée en parallèle dans une session Claude dédiée :
  brief autonome dans `docs/design/BRIEF_CLAUDE_DESIGN.md`.

### Écarts au plan

- Jalons exécutés en parallèle (0.1/0.2/0.3) et non séquentiellement — justification : ils sont
  indépendants entre eux, et la revue adversaire croisée est plus riche sur un lot complet.
- L'étude `docs/research/INSTRUCTIONS_FORMATS.md` (hors périmètre CH-0) a été produite en avance
  de phase — justification : la vision PO du 2026-07-04 (guidage pas-à-pas) en fait un intrant
  de conception du format blueprint, moins cher à étudier maintenant qu'à rétrofitter.
