# CHANGELOG CH-2 — Entraînement des modèles

> Journal du chantier. Méthode gouvernée par le doc 14 (décision D05) : audit d'abord,
> baselines time-boxées, une hypothèse à la fois, 6 itérations max, portes de sortie chiffrées.

## 2026-07-04 — Jalon 2.0 (audit dataset, doc 14 Phase 1) ✅ CLOS

- **Statut : ✅** — livrable `ml/AUDIT_DATASET.md`
- **Critères de bascule : aucun déclenché.** Annotations douteuses 2–6 % (seuil 10 %), zéro boîte
  fantôme ; fonds réels variés (28 % studio strict seulement).
- **Découverte structurelle** (plus importante que les critères) : le corpus réel gdansk_det est
  à 82 % mono-pièce, sans scènes de tas ni occlusions. Conséquence actée : la détection de TAS
  (le cas produit) repose sur (a) les scènes synthétiques multi-pièces à générer (doc 14 §2.1)
  et (b) le corpus réel maison du jalon 1.7 ; gdansk_det sert d'ancrage réel mono-pièce et de
  sanity check — pas de socle.
- Recommandations transmises aux jalons 1.3 (préserver le split `-test` des noms de fichiers,
  flagger les pièces coupées au bord) et 1.4 (occlusions synthétiques, petites cibles,
  renforcement éclairage chaud).

### Prochaines étapes
1. Jalon 1.3 (CH-1) — conversions VOC→YOLO et ImageFolder (avec les recommandations d'audit)
2. Pipeline de scènes synthétiques multi-pièces (doc 14 §2.1) — le vrai socle DET
3. Jalon 2.1 — baseline DET sur M1 (D10), time-box 1 semaine, configs par défaut
