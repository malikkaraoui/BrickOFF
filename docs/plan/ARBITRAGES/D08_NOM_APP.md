# D08 — Nom de l'app : "BrickOFF" candidat n°1, validation en CH-0

**Statut : ✅ Tranché comme nom de travail (2026-07-04) — validation formelle CH-0 jalon 0.2 requise avant tout usage public**

## Contexte

- Le dossier projet s'appelle **BrickOFF** — signal fort d'une préférence du product owner (et le "OFF" évoque le mode offline, cohérent avec la promesse).
- `05_CH4_IOS_FOUNDATIONS.md` utilise "**BrickScan**" comme exemple de nom et de structure de dossiers (`ios/BrickScan/`).
- `01_CH0_PREALABLES.md` jalon 0.2 exige : 3 noms candidats sans "LEGO", conformes à la Fair Play policy, disponibles sur l'App Store.

## Décision

1. **"BrickOFF" est le nom de travail officiel** : nom du projet Xcode (`ios/BrickOFF/`), du repo, des documents. "BrickScan" dans CH-4 n'était qu'un exemple illustratif — il est remplacé.
2. La validation **formelle** reste celle de CH-0 jalon 0.2 : vérifier à date (a) conformité Fair Play — "Brick" seul est génériquement utilisé par l'écosystème AFOL, mais à confirmer sur la policy réelle ; (b) disponibilité App Store ; (c) absence de conflit de marque évident (recherche EUIPO/INPI rapide).
3. Deux noms de secours seront quand même produits au jalon 0.2 (exigence maintenue), pour ne pas être bloqué si BrickOFF échoue à une des vérifications.

## Justification

- Fixer le nom de travail maintenant évite la dette du renommage (bundle id, schémas Xcode, docs) — le renommage tardif d'un projet Xcode est notoirement pénible.
- Le nom ne contient pas "LEGO" → compatible avec la contrainte connue de la Fair Play policy ; le disclaimer "not affiliated with the LEGO Group" reste obligatoire quel que soit le nom (CH-8/CH-10).

## Impacts

- `05_CH4_IOS_FOUNDATIONS.md` : lire `ios/BrickScan/` comme `ios/BrickOFF/`.
- CH-0 jalon 0.2 : BrickOFF entre comme candidat n°1 dans le livrable `legal/BRAND_COMPLIANCE.md`.
