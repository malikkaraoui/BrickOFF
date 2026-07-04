# D03 — Monétisation : gratuit financé par la publicité

**Statut : ⚠️ RENVERSÉ par le product owner le 2026-07-04 — la décision PO ci-dessous prime**

> **DÉCISION PRODUCT OWNER (2026-07-04)** : le modèle est **app gratuite financée par la
> publicité** — c'est le modèle de revenu du projet, pas une option (voir `docs/VISION.md`).
> La recommandation initiale de cette page (freemium sans pub) est donc écartée.
>
> **Conséquences d'exécution actées :**
> 1. `11_CH10_RELEASE.md` jalon 10.1 : intégration d'un SDK pub **dès la V1** ; la clause
>    "+1 semaine (SDK, ATT prompt, privacy manifest)" du plan s'applique.
> 2. L'argument "Data Not Collected" tombe → le Privacy Nutrition Label et le consentement
>    (ATT sur iOS, UMP/RGPD) deviennent des livrables à part entière de CH-10.
> 3. Contrainte enfant/famille : le public LEGO inclut des mineurs → le choix du SDK et du
>    format pub devra respecter COPPA/DSA/RGPD "famille" (critère de sélection du SDK, CH-10).
> 4. La pub exige du réseau pour se rafraîchir : l'app reste 100 % fonctionnelle offline,
>    la pub est simplement absente hors ligne (déjà prévu par le DoD "fonctionne en mode
>    avion (hors pub)" du Master Plan — cohérent).
> 5. Un premium "sans pub" (achat unique) pourra compléter en V1.1 — non prioritaire.
>
> L'analyse historique ci-dessous est conservée pour mémoire (elle documente les risques à
> gérer : review App Store, taille binaire, privacy — devenus des contraintes d'exécution).

## Contexte & sources en conflit

- `Sans titre.md` §1 : "modèle gratuit financé par **publicité ou freemium**" (les deux ouverts).
- `00_MASTER_PLAN.md` §0 : justifie l'offline-first par "**compatible pub dynamique** + OTA model update" — la pub semble structurante.
- `11_CH10_RELEASE.md` jalon 10.1 : "Pub : **différée à V1.1**", freemium à **achat unique** ; note que ce n'est qu'une "recommandation" à arbitrer.

Trois documents, trois niveaux d'engagement sur la pub. Il faut une position unique.

## Décision

**V1 = freemium, achat unique (non-consommable StoreKit 2), zéro SDK publicitaire.**

- Gratuit : scans illimités, inventaire ≤ 500 pièces, matching top-10.
- Premium : inventaire illimité, matching complet, export, mode souple/strict.
- Pub : **réévaluée en V1.1 uniquement**, sur données réelles (conversion premium, rétention), et seulement si la conversion s'avère insuffisante.

## Justification

1. **"Data Not Collected"** (CH-10 jalon 10.2) est un argument marketing rare et fort pour une app familiale — un SDK pub le détruit immédiatement (ATT prompt, privacy manifest, tracking).
2. Un SDK pub ajoute du risque exactement au pire moment (review App Store, taille binaire, RGPD/COPPA — public potentiellement enfant) pour un revenu incertain au faible volume d'un lancement.
3. L'achat unique est cohérent avec la promesse produit : app-outil offline, pas de coût serveur récurrent à couvrir → pas besoin d'abonnement ni de pub pour être rentable à l'échelle indé.
4. La justification "offline-first compatible pub dynamique" du Master Plan reste vraie *architecturalement* (rien n'empêche d'ajouter la pub en V1.1) — elle ne force pas la pub en V1.

## Conséquence rédactionnelle

La ligne du Master Plan §0 "Mode réseau : Offline-first (sync optionnelle) — compatible pub dynamique + OTA" se lit désormais : l'offline-first est justifié par **la promesse produit (fonctionne partout, vie privée) + OTA catalogue/modèles** ; la compatibilité pub est un bonus optionnel V1.1, pas un pilier.

## Impacts

- `11_CH10_RELEASE.md` : la "recommandation" du jalon 10.1 devient la décision — le paragraphe "⚠️ si le product owner préfère pub dès V1 : +1 semaine" reste valable comme clause de réversibilité.
- `Sans titre.md` §1 : obsolète sur ce point.
- Aucun impact sur CH-0→CH-9 (la monétisation n'intervient qu'en CH-10).
