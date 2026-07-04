# CH-9 — QA, performance & beta

> Durée : 2 semaines. Dépend de CH-8.

---

## Jalon 9.1 — Plan de tests fonctionnels

### Matrice de tests manuels (à dérouler intégralement, consigner dans un tableur)
| # | Scénario | Attendu |
|---|---|---|
| T01 | Scan 20 pièces étalées, lumière du jour | ≥ 17 identifiées correctement (pièce+couleur) |
| T02 | Scan même scène, LED intérieure | ≥ 15 correctes |
| T03 | Scan même scène, lampe chaude | ≥ 14 correctes ; pas de couleur aberrante (blanc→jaune toléré flagué unknown) |
| T04 | Scan 0 pièce (table vide) | 0 détection, pas de crash, message adapté |
| T05 | Scan pièce hors scope (rare) | "non identifiée", jamais un mauvais part_id à haute confiance |
| T06 | Corriger pièce + couleur en revue, ajouter | Inventaire exact |
| T07 | Annuler dernier scan | État antérieur exact |
| T08 | Inventaire 500 pièces → matching | Résultats < cibles CH-7, plausibles |
| T09 | Toggle strict/souple | Coverage change de façon cohérente |
| T10 | Mode avion intégral | Tout fonctionne sauf liens web (dégradés proprement) |
| T11 | Interruption (appel) pendant scan | Reprise propre, pas d'état corrompu |
| T12 | Kill app pendant écriture inventaire | Pas de corruption DB (relancer, vérifier) |
| T13 | iPhone ancien (device plancher) | Parcours complet utilisable, latences acceptables |
| T14 | Stockage quasi plein | Erreurs propres, pas de crash |
| T15 | VoiceOver parcours complet | Navigable |

### Critères d'acceptation
- [ ] 15/15 scénarios passés (ou échec documenté + corrigé + re-testé)

---

## Jalon 9.2 — Tests automatisés & stabilité

1. Couverture tests unitaires : Core/ ≥ 70% (Vision services, Matching, Repositories)
2. UI tests XCUITest : 3 parcours critiques (scan→ajout, recherche inventaire, matching→détail)
3. Soak test : 50 scans consécutifs → mémoire stable (pas de fuite, Instruments Leaks)
4. Thread Sanitizer + Main Thread Checker activés sur une passe complète

### Critères d'acceptation
- [ ] CI verte avec UI tests
- [ ] Zéro leak détecté, zéro data race

---

## Jalon 9.3 — Performance finale

Re-dérouler les benchmarks CH-3 (latences) et CH-7 (matching) sur build Release, App final (pas l'app de test). Mesurer en plus :
- Cold start < 2 s (device médian)
- Taille IPA téléchargée — confirmer < 350 Mo (App Store affiche la taille, dissuasion forte au-delà)
- Consommation batterie : 10 min de scan continu, drain mesuré et documenté

### Critères d'acceptation
- [ ] Toutes cibles tenues, rapport `PERF_FINAL.md`

---

## Jalon 9.4 — Beta TestFlight

1. Build signé, upload TestFlight, notes de test rédigées (FR/EN)
2. Recruter 10–20 testeurs (idéalement des AFOL — communautés LEGO FR : forums, Reddit r/lego francophone)
3. Formulaire de feedback structuré : précision perçue du scan, pertinence des sets proposés, bugs
4. 2 semaines de beta minimum, 1 build correctif minimum
5. Intégrer un mécanisme de report in-app simple : "signaler une mauvaise détection" → export local de la photo + prédictions (avec consentement explicite, données envoyées uniquement si l'utilisateur partage — RGPD)

### Critères d'acceptation
- [ ] ≥ 10 testeurs actifs, ≥ 30 sessions
- [ ] Crash-free ≥ 99%
- [ ] Top-5 retours qualitatifs traités ou priorisés V1.1

---

## Sortie de chantier CH-9

- App stable, performante, validée beta
- `CHANGELOG_CH9.md` + backlog V1.1 priorisé
