# CH-0 — Préalables légaux, comptes & environnements

> Durée : 3–5 jours. Aucun autre chantier ne démarre la partie "data" ou "release" sans CH-0 validé.

---

## Jalon 0.1 — Vérification licence Rebrickable

### Tâches
1. Lire les CGU Rebrickable : https://rebrickable.com/api/ (section Terms of Use) et la page downloads
2. Identifier explicitement :
   - L'usage commercial des snapshots CSV est-il autorisé ?
   - L'attribution est-elle requise ? Sous quelle forme ?
   - Y a-t-il une limite de redistribution (embarquer les données dans une app) ?
3. Si ambigu : contacter Rebrickable par email avec description du cas d'usage
4. Documenter la réponse dans `legal/REBRICKABLE_LICENSE.md`

### Livrable
- `legal/REBRICKABLE_LICENSE.md` : verdict (autorisé / autorisé avec attribution / interdit) + preuve (citation CGU ou email)

### Critères d'acceptation
- [ ] Verdict écrit et sourcé
- [ ] Si interdit → plan B documenté (base maison réduite, ou accord commercial)

### ⚠️ Point d'attention IA exécutante
Ne PAS affirmer le contenu de la licence de mémoire. La lire réellement à la date d'exécution.

---

## Jalon 0.2 — Vérification droits marque LEGO

### Tâches
1. Lire la LEGO Fair Play policy : https://www.lego.com/en-us/legal/notices-and-policies/fair-play/
2. Contraintes connues à vérifier et confirmer :
   - Ne pas utiliser "LEGO" dans le nom de l'app
   - Disclaimer obligatoire type "not affiliated with the LEGO Group"
   - Ne pas utiliser le logo ni les visuels officiels
3. Choisir un nom d'app candidat conforme (3 propositions)
4. Vérifier la disponibilité du nom sur l'App Store

### Livrable
- `legal/BRAND_COMPLIANCE.md` : règles applicables + 3 noms candidats validés

### Critères d'acceptation
- [ ] Règles Fair Play résumées et sourcées
- [ ] 3 noms sans "LEGO", disponibles sur l'App Store

---

## Jalon 0.3 — Vérification licence dataset & framework d'entraînement

### Tâches
1. Identifier la licence exacte du dataset LEGOBricks sur Hugging Face (champ License de la model/dataset card)
2. Vérifier la licence d'Ultralytics YOLOv8 : **AGPL-3.0** par défaut → incompatible avec app propriétaire fermée si le modèle est considéré comme dérivé
   - Options : licence Enterprise Ultralytics (payante), ou alternative permissive (YOLOX Apache-2.0, RT-DETR, YOLO-NAS)
3. Trancher et documenter

### Livrable
- `legal/ML_LICENSES.md` : tableau licence par composant (dataset, framework détection, framework classification) + décision

### Critères d'acceptation
- [ ] Chaque composant ML a une licence identifiée et compatible usage commercial
- [ ] Si Ultralytics AGPL retenu → coût licence Enterprise chiffré, OU alternative permissive choisie

### ⚠️ Risque réel
Ce point est souvent ignoré et bloque à la release. L'AGPL d'Ultralytics est un vrai sujet pour une app commerciale fermée. **Alternative permissive recommandée par défaut : YOLOX (Apache-2.0) ou RT-DETR.** À confirmer au moment de l'exécution (l'écosystème évolue vite).

---

## Jalon 0.4 — Comptes & accès

### Checklist
- [ ] Apple Developer Program actif (99 $/an) — nécessaire dès CH-4 pour signer
- [ ] Compte Hugging Face (téléchargement datasets)
- [ ] Compte Rebrickable + clé API (même si snapshot utilisé : utile pour vérifs)
- [ ] Accès GPU pour entraînement : choisir et provisionner
  - Option A : machine locale avec GPU NVIDIA ≥ 16 Go VRAM
  - Option B : cloud (Scaleway GPU, Lambda, RunPod...) — budgéter ~50–200 € pour la phase d'entraînement
- [ ] Repo Git créé : monorepo `lego-ai/` avec dossiers `ml/`, `ios/`, `data/`, `legal/`, `docs/`

### Livrable
- `docs/ACCESS.md` : liste des comptes, qui détient quoi, où sont les secrets (jamais les secrets eux-mêmes en clair dans le repo)

### Critères d'acceptation
- [ ] Tous les accès testés fonctionnels
- [ ] `.gitignore` exclut secrets, datasets bruts, poids de modèles (> Git LFS ou stockage externe)

---

## Jalon 0.5 — Environnements de dev

### Environnement ML (Mac ou Linux)
```bash
# Python 3.11 recommandé
python3.11 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
# Versions à figer dans ml/requirements.txt au moment de l'installation
# Composants attendus : torch, torchvision, framework détection choisi (0.3),
# coremltools, onnx, opencv-python, albumentations, pandas
pip freeze > ml/requirements.txt
```

### Environnement iOS
- Xcode dernière version stable (vérifier au moment de l'exécution)
- macOS à jour
- Device de test physique obligatoire : iPhone avec NPU (A14+ minimum, idéalement un modèle médian type iPhone 13/14 ET un modèle ancien pour le plancher de perfs)
- ⚠️ Le simulateur ne reflète PAS les perfs CoreML réelles → tout benchmark se fait sur device

### Livrable
- `ml/requirements.txt` figé
- `docs/ENVIRONMENTS.md` : versions exactes installées, devices de test listés

### Critères d'acceptation
- [ ] `python -c "import torch; print(torch.__version__)"` OK
- [ ] Build Xcode d'un projet vide → run sur device physique OK
- [ ] Versions documentées

---

## Sortie de chantier CH-0

CH-0 est terminé quand les 5 jalons sont ✅ et que `CHANGELOG_CH0.md` est rédigé (décisions prises, notamment : framework détection retenu, nom d'app candidat, verdict Rebrickable).
