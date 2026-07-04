# D01 — Plateforme cible : iOS natif V1, Android V2

**Statut : ✅ Tranché (2026-07-04) — amendé le jour même par le product owner**

> **AMENDEMENT PO (2026-07-04)** : la **cible produit est bi-plateforme : iOS ET Android**
> (décision product owner, voir `docs/VISION.md`). L'analyse ci-dessous reste valable comme
> **séquencement d'exécution** : iOS d'abord (V1), Android engagé en V2 — ce n'est plus un
> "peut-être" mais un engagement produit. Conséquence : les garde-fous de portabilité ci-dessous
> passent de "recommandés" à **obligatoires** (aucune logique métier enfermée dans du code
> Apple-only ; tout algorithme cœur spécifié en format portable avant implémentation Swift).

## Contexte & sources en conflit

- `Sans titre.md` §5 (vision initiale) : exécution visée **iOS (CoreML/Metal) ET Android (TFLite/ONNX Runtime)**.
- `00_MASTER_PLAN.md` §0 (décision actée) : **iOS natif uniquement (Swift/SwiftUI), Android = V2**.
- Tout le plan détaillé (CH-3 → CH-10) est écrit exclusivement pour iOS (CoreML, GRDB, SwiftUI, TestFlight, App Store).

## Options considérées

| Option | Pour | Contre |
|---|---|---|
| A. iOS + Android simultanés (natif ×2) | Marché max dès V1 | Double coût sur TOUTE la chaîne (export modèle, pipeline caméra, DB, UI, QA) ; équipe de 1–2 personnes → planning ×~1.8 |
| B. Cross-platform (Flutter/RN/KMP) | Un seul code UI | Le cœur de l'app est le pipeline caméra + inférence temps réel : c'est précisément là où le cross-platform coûte le plus (bridges, perfs ANE/NNAPI hétérogènes) ; contredit le plan CH-4→CH-8 déjà écrit |
| C. **iOS natif V1, Android V2** ✅ | Valide le produit sur un seul OS homogène (parc de devices prévisible, ANE bien documenté, CoreML mature) ; le plan existe déjà ; monétisation iOS > Android en valeur/utilisateur | Marché Android ignoré ~6 mois |

## Décision

**Option C — la décision du Master Plan est confirmée : V1 = iOS natif (Swift/SwiftUI, CoreML), Android = V2.**

## Justification

1. Le risque n°1 du projet est le ML (domain gap, cf. D05), pas la distribution. Doubler les plateformes avant d'avoir prouvé que le scan marche en conditions réelles serait investir sur le mauvais front.
2. Les artefacts ML restent portables : les poids PyTorch (CH-2) sont la source de vérité ; seul CH-3 (export CoreML) est spécifique iOS. Le portage Android V2 = réexport TFLite/ONNX + réécriture app, pas de retour en arrière sur le ML.
3. Le parc iOS est homogène (A14+ = ANE garanti), ce qui rend les cibles de latence de CH-3 tenables et mesurables. Android mid-range est le pire cas GPU/NPU — le traiter en V2 avec un produit déjà calibré est plus sain.
4. `Sans titre.md` est un document exploratoire antérieur au Master Plan ; il liste Android comme *contrainte d'exécution possible*, pas comme engagement V1.

## Garde-fous pour ne pas hypothéquer Android V2

- Aucune logique métier dans du code Apple-only quand évitable : l'algo COLOR, le MatchingEngine et les formats de données sont spécifiés en JSON/SQL/pseudo-code portables (`12_CONVENTIONS_AI.md`).
- CH-3 conserve les exports intermédiaires ONNX (déjà dans la chaîne PyTorch → ONNX → CoreML) : c'est le point de départ du portage TFLite/ONNX-Runtime Android.

## Impacts

- `Sans titre.md` §5 : marqué obsolète sur ce point (voir D07 — le fichier devient archive).
- Aucun fichier de chantier à modifier : le plan est déjà cohérent avec cette décision.
