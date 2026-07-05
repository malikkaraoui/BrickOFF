# CH-S — Revue adversaire du plan (2026-07-05)

> Revue menée par agent adversaire indépendant AVANT lancement du chantier. 24 constats
> (5 critiques, 13 majeurs, 6 mineurs). Le plan `16_PIPELINE_SYNTHETIQUE.md` a été révisé en
> v1.1 en réponse — la table de remédiation est en fin de ce document.

## Synthèse de l'attaque

Le plan reposait sur une faisabilité solide **mais qui a testé un cas dégénéré** (5 briques
convexes, matériaux stables, une passe IDs, pas de profondeur de champ) et en extrapolait un
budget qui s'effondre dès qu'on applique ses propres specs. Les trois trous les plus dangereux :
**(1)** le juge S.0 était circulaire (pré-annoté par le modèle qu'il doit juger), sous-puissant
statistiquement et sans convention d'annotation écrite ; **(2)** le coût réel (occlusion par
pièce, entraînements 20 k, re-générations) était 2-4× l'enveloppe annoncée ; **(3)** la physique
CONVEX_HULL sur pièces concaves n'a jamais été testée et conditionne le réalisme des tas.

## Constats (résumé — sévérité, sujet)

**CRITIQUES**
1. Circularité de la vérité terrain S.0 : det_v1 pré-annote le set qui jugera det_v1 → biais systématique contre la mesure du gain.
2. Puissance statistique : +5 pts sur ~800 instances clusterisées en 50 scènes = zone de bruit (IC réel ±6-8 pts) ; variance inter-seeds jamais mesurée.
3. Seuil de visibilité 25 % "cohérent gdansk" : faux — gdansk n'a AUCUNE convention d'occlusion (que de la troncature au cadre) ; 3 superviseurs pouvaient diverger.
8. Physique validée sur 5 pièces convexes en CONVEX_HULL ; les ~450 pièces réelles (arches, brackets, Technic) ne s'imbriquent pas sous convex hull → tas "gonflés" ; MESH sur LDraw non-manifold jamais testé.
14-15. Budget : le taux d'occlusion par pièce (+8-16 s/image) et les entraînements 20 k (25-50 h/recette) détruisent le "4-5 jours" → 8-12 jours calendaires réalistes.

**MAJEURS (résumé)**
4. Set TAS mono-foyer/mono-téléphone, surapprentissage méthodologique du juge sur les itérations, collision future avec le jalon 1.7 (même foyer au train) → holdout tiers requis.
5. Critère +5 pts fixé avant de connaître la baseline → recalibrer après mesure.
6. S.0 "sous-ensemble du 1.6" incohérent (1.6 exige part_id+couleur, S.0 n'annote que les bbox) → re-annotation future à chiffrer ou statut distinct.
7. Annotation 2-3 h sous-estimée ×3-5 (pré-annotations lacunaires sur tas) → pilote 5 scènes chronométré.
9. Aucun test d'import/rendu des 450 part_ids cibles → smoke-test préalable obligatoire.
10. Échelle physique jamais validée (assertion 2×4 = 31,8 mm requise).
11. Passe IDs 1 spp non validée sur pièces fines (labels instables autour du seuil).
12. Alignement EEVEE/Cycles affirmé, jamais mesuré (IoU silhouette à prouver ≥ 0,99).
13. Profondeur de champ au cahier des charges casse l'alignement masques/beauty → DoF en post-process après labels, ou désactivé v1.
16. S.3 (matériaux randomisés par pièce) invalide la borne basse du throughput → shader partagé piloté par attributs, re-mesure après S.3.
17. Coût de re-génération par itération non budgété → séparer scène (bake, conservé) et rendu ; itérer sur 5 k.
18. Dépendance cachée : fréquences Rebrickable absentes (action PO) → fallback fréquences empiriques gdansk.
19. Contradiction de ratio réel/synth : plan 30/70 vs doctrine 70/30 → arbitrage tracé requis.
20. Distracteurs non-LEGO, négatifs fond-seul et run "synth seul" (sanity check) supprimés sans justification → réintégrés.

**MINEURS** : 21 incohérences chiffrées plan/design doc (HDRI, résolution, régimes N, compteur d'itérations) ; 22 early stopping sur val mono-pièce (catch-22 à écrire) ; 23 versioning générateur/seeds/dataset_id (NB : l'affirmation "pas un dépôt git" du relecteur est erronée — le repo existe — mais le fond sur le versioning des manifests est retenu) ; 24 "0 €" masque 15-25 h de temps PO + critère S.3 non falsifiable.

## Remédiations → plan v1.1

Toutes les remédiations sont intégrées dans `16_PIPELINE_SYNTHETIQUE.md` v1.1 : nouveau jalon
**S.1-pré (préflight technique)** qui instrumente les constats 8-13 en ~½ journée AVANT tout
engagement ; S.0 réécrit (convention écrite d'abord, passe aveugle, pilote chronométré, ~100
scènes, holdout tiers, baseline mesurée avant critère) ; annotations par **Cryptomatte-EEVEE**
(même rendu → alignement garanti + occlusion sans passes multiples) avec fallback ; budget
recalculé honnêtement (8-12 j calendaires, temps PO explicité) ; premier tir 10 k ; recette C
"synth seul" réintégrée ; distracteurs + négatifs réintégrés ; ratio arbitré 70 réel/30 synth ;
shader partagé ; politique de seeds + version du générateur dans chaque manifest.
