# ARBITRAGES — Index & guide de reprise

> **But de ce dossier** : le corpus documentaire contenait plusieurs visions divergentes
> (`Sans titre.md` = synthèse exploratoire initiale, `00_MASTER_PLAN.md` + CH-0→CH-10 = plan structuré,
> docs 13/14 = extensions non intégrées). Chaque divergence a été challengée et **tranchée**
> dans un fichier dédié `Dxx_*.md`. Ce dossier est la **couche de décision au-dessus du plan** :
> en cas de contradiction entre un fichier de chantier et un arbitrage, **l'arbitrage prime**.

**Date d'arbitrage : 2026-07-04. Arbitre : session IA (documentaliste/architecte), à faire valider par le product owner (Malik).**

---

## Rappel des fondamentaux du projet (pour reprise à froid)

- **Produit** : app mobile qui scanne un tas de pièces LEGO (étalées), identifie pièce + couleur,
  construit un inventaire local, et propose des sets/constructions réalisables. **100% offline.**
- **Cible plateforme V1 : iOS natif uniquement (Swift/SwiftUI). Android = V2.** → voir [D01](D01_PLATEFORME.md)
- **Architecture vision** : 2 stages — DET (détection mono-classe) + CLS (classification 1000 classes) + COLOR (pipeline LAB déterministe, pas ML).
- **Données sets** : snapshot Rebrickable embarqué en SQLite (licence à valider en CH-0).
- **Ordre de lecture pour un nouvel exécutant** :
  1. `00_MASTER_PLAN.md` (plan racine)
  2. `ARBITRAGES/` (ce dossier — corrige/complète le plan)
  3. `12_CONVENTIONS_AI.md` (contrats & conventions, obligatoire avant tout code)
  4. Le fichier du chantier en cours

---

## Registre des décisions

| ID | Sujet | Décision (résumé) | Statut |
|---|---|---|---|
| [D01](D01_PLATEFORME.md) | Plateforme cible | **Cible produit : iOS ET Android** (décision PO) ; exécution séquencée iOS V1 → Android V2 | ✅ Tranché + amendé PO |
| [D02](D02_FRAMEWORK_DETECTION.md) | Framework de détection | **Licence permissive par défaut (YOLOX/RT-DETR)** ; YOLOv8/AGPL seulement si licence Enterprise chiffrée et acceptée | ✅ Tranché |
| [D03](D03_MONETISATION.md) | Monétisation | **Gratuit financé par la pub** (décision PO du 2026-07-04, renverse la reco initiale) ; premium "sans pub" possible en V1.1 | ✅ Tranché par le PO |
| [D04](D04_BUDGETS_TAILLE.md) | Budgets taille | Budgets du Master Plan confirmés (modèles ≤ 50 Mo, app < 350 Mo) ; le "< 300 Mo modèle" de `Sans titre.md` est **obsolète** | ✅ Tranché |
| [D05](D05_METHODO_ENTRAINEMENT.md) | Méthodologie entraînement | **Le doc 14 gouverne** : audit dataset obligatoire, 6 itérations max, voie synthétique, portes de sortie. CH-2 reste la structure de jalons | ✅ Tranché |
| [D06](D06_GENERATION.md) | Génération de constructions | Roadmap du doc 13 **officialisée** : V1 = matching seul ; V1.5 = blueprints (A1) + équivalences (A2) ; A3 = spike V3 | ✅ Tranché |
| [D07](D07_HYGIENE_DOCUMENTAIRE.md) | Hygiène documentaire | `1RR-brief-design.md` = **hors projet** (autre produit) ; doublons "copie" à supprimer ; `Sans titre.md` = archive historique | ✅ Tranché (actions manuelles restantes) |
| [D08](D08_NOM_APP.md) | Nom de l'app | **"BrickOFF" = nom de travail candidat n°1**, validation formelle en CH-0 jalon 0.2 | ✅ Tranché — clearance R8 : voie libre |
| [D09](D09_VISUELS_SETS.md) | Visuels sets/pièces | **Jamais d'images officielles ni Rebrickable** : vignettes et rendus LDraw maison (même pipeline que l'entraînement) ; carte set sans photo de boîte | ✅ Tranché |
| [D10](D10_INFRA_ENTRAINEMENT.md) | Infra d'entraînement | **MacBook M1 (PyTorch MPS) en nominal**, cloud en escalade chiffrée (> 48 h projetées) ; iPad M4 = device de test, pas d'entraînement (limite iPadOS) | ✅ Tranché (matériel PO) |

---

## Ressources

- `../15_VEILLE_GITHUB.md` (2026-07-04) : repos GitHub exploitables par chantier (frameworks Apache-2.0
  confirmés, chaîne synthétique LDraw→Blender existante en MIT, `rebrickable-sqlite` pour CH-7,
  Brickognize pour la pré-annotation). Non normatif ; à re-vérifier à l'exécution.

## Ce qui n'est PAS encore tranché (à traiter au fil des chantiers)

- Verdict licence Rebrickable (CH-0 jalon 0.1 — nécessite lecture réelle des CGU à date)
- Choix final YOLOX vs RT-DETR vs autre (CH-0 jalon 0.3 — l'écosystème bouge, D02 fixe seulement le critère : licence permissive)
- NMS embarqué dans le modèle CoreML ou en Swift (CH-3 jalon 3.1)
- Pub V1.1 : go/no-go après les chiffres de la V1 (D03)

## État d'avancement global

**Aucun chantier n'a démarré.** Prochaine étape d'exécution : **CH-0 (préalables légaux)**,
en intégrant D02 (framework permissif par défaut) et D08 (BrickOFF candidat n°1).

## Procédure pour tout nouvel arbitrage

1. Créer `Dxx_<SUJET>.md` ici, sur le modèle : Contexte / Sources en conflit / Options / Décision / Justification / Impacts.
2. L'ajouter au registre ci-dessus.
3. Mettre à jour les fichiers de chantier impactés (ou les lister en "Impacts" si non faits).
4. Faire valider par le product owner si la décision touche une "décision actée" du Master Plan (§0).
