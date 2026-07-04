# CH-10 — Monétisation & release

> Durée : 1–2 semaines. Dépend de CH-9.

---

## Jalon 10.1 — Monétisation V1

### Modèle retenu (décision actée, offline-first)
**Freemium** :
- Gratuit : scans illimités, inventaire jusqu'à 500 pièces, matching limité au top-10 des sets
- Premium (achat unique recommandé V1 — plus simple qu'un abonnement à justifier) : inventaire illimité, matching complet, export, mode souple/strict
- Pub : **différée à V1.1** — raison : intégrer un SDK pub à la release ajoute du risque (review, privacy, taille) ; valider d'abord le produit

⚠️ Ce choix (pas de pub V1, achat unique) est une recommandation. Si le product owner préfère pub dès V1 : prévoir +1 semaine (SDK, ATT prompt, privacy manifest).

### Tâches
1. Intégration StoreKit 2 : produit non-consommable "premium"
2. Paywall sobre : déclenché aux limites (501e pièce, 11e set), jamais bloquant le scan
3. Restore purchases, gestion erreurs StoreKit
4. Tests StoreKit configuration locale + sandbox

### Critères d'acceptation
- [ ] Achat + restore testés en sandbox sur device
- [ ] Aucune limite premium ne provoque de perte de données (l'inventaire > 500 reste stocké, juste l'ajout est bloqué)

---

## Jalon 10.2 — Conformité App Store & privacy

1. Privacy Nutrition Label : si zéro collecte (V1 sans pub ni analytics) → déclaration "Data Not Collected" (gros argument marketing, à mettre en avant)
2. Privacy manifest (PrivacyInfo.xcprivacy) à jour
3. Page App Store : screenshots (6.7" + 6.1"), description FR/EN, mots-clés, **disclaimer non-affiliation LEGO dans la description** (exigence Fair Play)
4. Vérifier les guidelines en vigueur au moment de la soumission (elles évoluent — ne pas se fier à la mémoire)

### Critères d'acceptation
- [ ] Fiche complète, disclaimer présent
- [ ] Privacy manifest validé par l'archive Xcode sans warning

---

## Jalon 10.3 — Mécanisme OTA (préparation V1.1, implémentation minimale V1)

### V1 (minimal)
1. `app_meta` stocke les versions catalogue/modèles
2. Settings affiche ces versions
3. Endpoint de version distant : simple fichier JSON statique hébergé (versions disponibles) — l'app le consulte si réseau, affiche "mise à jour du catalogue disponible" → V1 : renvoie vers la mise à jour App Store

### V1.1 (cible, documenter seulement)
- Téléchargement différentiel du `rebrickable.sqlite` et des `.mlpackage` (MLModel supporte la compilation à chaud de modèles téléchargés)
- Signature/checksum des fichiers téléchargés obligatoire

### Critères d'acceptation
- [ ] Versions visibles in-app
- [ ] Design OTA V1.1 documenté dans `docs/OTA_DESIGN.md`

---

## Jalon 10.4 — Soumission & lancement

1. Build final, archive, soumission
2. Plan de réponse review : si rejet, analyser le motif, corriger, resoumettre (prévoir 1 semaine de marge)
3. Post-lancement J+7 : vérifier crash reports (organizer Xcode), reviews, premières métriques de vente

### Critères d'acceptation
- [ ] App publiée
- [ ] Rapport J+7 rédigé → alimente le backlog V1.1

---

## Sortie de chantier CH-10 = V1 livrée 🎉

Backlog V1.1 prêt : pub (si décidé), OTA complet, extension classes, Android (CH-11+).
