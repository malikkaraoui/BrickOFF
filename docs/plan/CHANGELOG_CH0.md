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

### Plan de remédiation (backlog CH-0, ordonné)

| # | Action | Lève | Qui |
|---|---|---|---|
| R1 | Identifier le dataset de détection/segmentation réel + licence (ou acter qu'il n'existe pas → la voie synthétique DET devient nominale) | Critique 1 | IA |
| R2 | Compléter `ML_LICENSES.md` : clause anti-IA Rebrickable + analyse "curation ≠ entraînement" ; sourcer A1/Blender/CC0 LDraw | Critiques 2, Majeur 10 | IA |
| R3 | **Envoyer l'email Rebrickable** (déjà rédigé dans le livrable 0.1, complété du point classes) | Critique 2, Majeur 7 | **Malik** |
| R4 | **Envoyer l'email Brickognize** (piotr.rybak@brickognize.com) | Majeur 13 | **Malik** |
| R5 | Amender CH-1/doc 14 : données réelles d'entraînement en voie nominale (protocole photos maison en volume, distinct du realworld test) | Critique 3 | IA |
| R6 | Analyse brevets génération d'instructions (revendications, expirations) → registre des risques | Critique 4 | IA (relecture avocat recommandée avant V1.5) |
| R7 | Trancher "images de sets dans l'app" (probable : rendus LDraw maison ou placeholders) + règle screenshots store (brique-à-tenons) | Majeurs 5, 6 | IA + PO |
| R8 | Recherche tmview/EUIPO "BrickOFF" (1 h) + archives Wayback des sources Fair Play | Majeurs 9, 11 | IA |
| R9 | Corriger les plans B Rebrickable (proxy maison, droit sui generis UE) | Majeur 8 | IA |
| R10 | Amender doc 13 : géométrie dans les alternatives de slots + stratégie de validation | Majeur 12 | IA (avant V1.5) |
| R11 | Mineurs 15–19 (citations, étiquetages, règle assets CC0, vocabulaire marketing) | Mineurs | IA |

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
