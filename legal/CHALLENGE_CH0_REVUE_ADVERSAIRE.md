# CH-0 — Revue adversaire des livrables (2026-07-04)

> **Pourquoi ce document** : chaque jalon est relu par un agent adversaire indépendant dont la
> mission est de démolir les conclusions (méthode prévue par `12_CONVENTIONS_AI.md` §3.3).
> Les livrables du CH-0 (`REBRICKABLE_LICENSE.md`, `BRAND_COMPLIANCE.md`, `ML_LICENSES.md`,
> `INSTRUCTIONS_FORMATS.md`) restent en l'état **v0 — contesté** tant que les points CRITIQUES
> et MAJEURS ci-dessous ne sont pas levés. Le plan de remédiation est dans `CHANGELOG_CH0.md`.

## Synthèse de l'adversaire

Les quatre livrables sont solides sur la forme (citations verbatim, dates, hypothèses explicites,
plans B), mais trois défauts systémiques : **(1)** les handoffs inter-documents échouent — trois
renvois explicites (garde-fou IA → jalon 0.3, images → jalon 0.2, conséquence schéma → doc 13)
arrivent dans le vide ; **(2)** les découvertes ne remontent pas dans le plan — dataset 100 %
synthétique et gel Brickognize invalident des hypothèses de CH-1/CH-2/doc 14 sans amendement ;
**(3)** les deux seuls risques capables de tuer le produit (forme brique-à-tenons dans un produit
commercial, brevets LEGO sur la génération d'instructions) sont ceux que les verdicts optimistes
contournent.

## Constats — CRITIQUE

1. **Dataset de détection absent de `ML_LICENSES.md`** — jalon 0.3 formellement non atteint.
   CH-1 repose sur un "dataset segmentation académique" (annotations de détection) qui n'est ni
   identifié, ni licencié dans le livrable ; `pvrancx/legobricks` est un dataset de
   *classification* (pièces isolées), inutilisable seul pour la détection de tas.
   → *Lever : identifier le dataset exact + licence, ou constater qu'il n'existe pas.*
2. **La clause Rebrickable "No Rebrickable content may be used in the training of AI models"
   n'est pas propagée** : `ML_LICENSES.md` ne la mentionne pas, alors que CH-1 jalon 1.2 utilise
   `inventory_parts` pour sélectionner les 1000 classes et que les labels sont des part IDs.
   Lecture probablement défendable (curation ≠ entraînement, part IDs = design IDs LEGO repris
   par tout l'écosystème) mais l'analyse doit être écrite et incluse dans l'email à Rebrickable.
3. **Le dataset principal est 100 % synthétique (rendus LDraw) et personne n'en tire la
   conséquence** : le critère de bascule du doc 14 ("> 90 % studio → voie synthétique") est
   satisfait *par construction*, le remède (générer des rendus) est partiellement circulaire, et
   le plan n'a **aucune image réelle d'entraînement** (le realworld set est interdit
   d'entraînement). → *Lever : amender CH-1/doc 14 — source de données réelles d'entraînement
   à constituer (photos maison en volume + auto-annotation).*
4. **Brevets LEGO sur la génération automatique d'instructions** (US8374829, US9821242,
   US11393153) cités par `INSTRUCTIONS_FORMATS.md` sans analyse de liberté d'exploitation, alors
   que V1.5/V3 font exactement cela. → *Lever : analyse revendications + dates d'expiration
   AVANT d'engager V1.5.*

## Constats — MAJEUR (résumés)

5. **Images de sets/pièces dans l'app** : renvoi circulaire 0.1→0.2 jamais résolu ; la réponse
   probable est NON (copyright LEGO, tolérance non-commerciale seulement) → contrainte produit
   CH-7/CH-8 : placeholders définitifs ou rendus LDraw maison.
6. **Forme brique-à-tenons** : traitée pour l'icône, pas pour les rendus 3D du produit dans les
   screenshots store (périmètre "commercial or marketing purposes" de la Fair Play). Précédent
   Brickit à documenter.
7. **Email Rebrickable dégradé de "obligatoire si ambigu" (plan) à "recommandé"** — ambiguïté
   résiduelle reconnue → l'envoyer (déjà rédigé) ou dérogation actée par le PO.
8. **Plan B n°1 de REBRICKABLE_LICENSE contradictoire** (téléchargement par l'app = automation
   interdite §5.3) ; Plan B n°2 ignore le droit sui generis UE des bases de données.
9. **Sources BRAND_COMPLIANCE fragiles** : brochure 2018, miroir tiers pour les guidelines fan
   (périmètre non-commercial) → archiver les captures, requalifier en indices.
10. **ML_LICENSES affirme sans source** sur A1 (poids ImageNet), doc Blender, CC0 LDraw →
    sourcer ou requalifier en opinion.
11. **Clearance marque repoussée à CH-10** = au pire moment ; la recherche tmview/EUIPO coûte
    une heure → à faire maintenant.
12. **Schéma blueprint doc 13 incompatible avec les recommandations R1/R3** (pas de géométrie
    dans les alternatives) → amender doc 13 avant V1.5.
13. **Gel Brickognize non chiffré** : le plan B (annotation manuelle, ≥ 2000 pièces en double
    passe) est précisément le travail que l'API devait accélérer → email à envoyer maintenant,
    coût manuel chiffré.
14. **Marques DANS les données catalogue** (NINJAGO, Star Wars…) : intersection non traitée →
    règle d'affichage référentiel + disclaimer générique.

## Constats — MINEUR

15. Citation Rebrickable §5.3 à double emploi (automation + IA) — citer le paragraphe complet.
16. "1–5 pièces par étape" = choix éditorial BrickOFF, pas un résultat de recherche — étiqueter
    et calibrer en beta.
17. "L'écosystème utilise Brick sans opposition" = raisonnement de survivant — indice, pas preuve.
18. Assets du pipeline synthétique (HDRI, textures) non couverts — règle : CC0 uniquement.
19. Vocabulaire marketing : ne jamais dire publiquement "comme une notice LEGO officielle".
