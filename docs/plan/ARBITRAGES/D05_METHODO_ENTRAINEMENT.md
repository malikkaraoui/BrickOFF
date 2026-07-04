# D05 — Méthodologie d'entraînement : le doc 14 gouverne, CH-2 reste la structure

**Statut : ✅ Tranché (2026-07-04)**

## Contexte & sources en conflit

- `03_CH2_TRAINING.md` : jalons 2.1→2.4, boucle d'amélioration limitée à **3 itérations**, pas d'audit
  dataset préalable, pas de plan B structuré.
- `14_APPRENTISSAGE_RENFORCE.md` : s'annonce comme "**remplace et approfondit CH-2**" — audit dataset
  obligatoire avant tout entraînement, baselines time-boxées 1 semaine, diagnostic taxonomique,
  **6 itérations max**, arsenal d'alternatives (synthétique 3D, auto-annotation, métrique learning,
  calibration couleur, distillation, TTA), et 4 portes de sortie chiffrées (S1→S4).
- Problème : ni `00_MASTER_PLAN.md` (index §2) ni CH-2 ne référencent le doc 14. Un exécutant suivant
  l'index officiel exécuterait CH-2 **sans jamais lire le doc 14** — la version la plus faible du plan
  s'appliquerait par défaut, sur le chantier le plus risqué du projet.

## Décision

**Le doc 14 est promu au statut normatif. Articulation officielle :**

1. **CH-2 fournit la structure** (jalons, livrables, critères d'acceptation, configs de départ, cibles chiffrées du jalon 2.4) — inchangée.
2. **Le doc 14 fournit la méthode d'exécution** de CH-2 et **prime en cas de contradiction**. Concrètement :
   - **Phase 1 (audit dataset, 3–4 jours) devient le jalon 2.0, obligatoire**, avant 2.1. Livrable : `AUDIT_DATASET.md`. Critères de bascule : > 10 % annotations fausses → nettoyage prioritaire ; > 90 % images studio → voie synthétique activée immédiatement.
   - Le budget d'itérations du jalon 2.4 passe de **3 à 6**, avec journal d'expériences `ml/EXPERIMENTS.md` obligatoire (une hypothèse, un changement, une mesure).
   - Les cibles finales du jalon 2.4 (pipeline complet ≥ 0.65 realworld) restent le critère de GO vers CH-3 ; en dessous, appliquer **l'arbre de décision du doc 14 §3** (S1 réduction de scope → S2 UX compensatoire → S3 hybride serveur opt-in → S4 repositionnement).
   - La **voie synthétique (LDraw + Blender, doc 14 §2.1) se prépare en parallèle dès le moindre signal de domain gap** — c'est un investissement réutilisable (extension de classes V2), pas un plan B honteux.

## Justification

- Le doc 14 est unanimement plus solide : il traite le risque n°1 du projet (domain gap dataset public vs photos réelles) que CH-2 ignore. Il n'y a pas de "voix" à départager sur le fond — seulement un défaut d'intégration à corriger.
- Le remplacement *total* de CH-2 serait une erreur : CH-2 contient les contrats (configs, métriques, livrables, handoff CH-3) dont dépendent CH-3 et CH-5. La fusion structure (CH-2) + méthode (14) préserve les deux.
- 6 itérations plutôt que 3 : réaliste pour un problème à fort domain gap ; le time-boxing et le journal d'expériences empêchent la dérive que la limite à 3 voulait prévenir.

## Impacts

- `00_MASTER_PLAN.md` §2 (index) : les docs 13 et 14 doivent y figurer (note de renvoi ajoutée en tête du Master Plan).
- `03_CH2_TRAINING.md` : à lire systématiquement AVEC le doc 14 ; le jalon 2.0 (audit) s'insère avant 2.1 ; "Max 3 itérations" (jalon 2.4) est amendé à 6.
- Planning Master Plan §4 : CH-2 "2–4 semaines" devient **3–5 semaines** (audit + itérations supplémentaires) ; le total ~4–5 mois reste plausible car le risque de replanification tardive diminue.
