# LEGO AI Offline — Master Plan

> Document racine. Tout exécutant (humain ou IA) commence ici.
> Chaque chantier référence un fichier dédié avec jalons, livrables, critères d'acceptation.

> ⚠️ **AMENDEMENTS (2026-07-04)** : les divergences entre documents ont été arbitrées dans
> **`ARBITRAGES/`** (lire `../VISION.md` puis `ARBITRAGES/00_INDEX.md` juste après ce fichier —
> vision et arbitrages priment). Amendements directs à ce plan :
> **D01 amendé** (cible produit = iOS ET Android ; exécution iOS d'abord),
> **D02** (détecteur = licence permissive type YOLOX/RT-DETR, pas YOLOv8n),
> **D03 renversé par le PO** (gratuit financé par la pub dès V1 — la ligne "pub différée V1.1"
> de CH-10 est caduque), **D05** (le doc `14_APPRENTISSAGE_RENFORCE.md` gouverne la méthode de
> CH-2 ; jalon 2.0 audit dataset obligatoire ; 6 itérations max), **D06** (doc 13 = roadmap
> V1.5/V3, désormais adossée à la vision produit), **D08** (nom de travail = BrickOFF).
> Les docs 13 et 14, absents de l'index §2, sont normatifs (voir D05/D06).

---

## 0. Décisions actées (figées pour V1)

| Décision | Valeur V1 | Justification |
|---|---|---|
| Mode réseau | **Offline-first** (sync optionnelle) | Compatible pub dynamique + OTA model update |
| UX scan | **Étalement pièces obligatoire** | Évite l'occlusion, YOLO standard suffit |
| Couverture classes | **1 000 classes** (pièces communes) | Dataset LEGOBricks disponible, scope assumé |
| Pipeline couleur | **Séparé** (LAB + palette officielle) | Découplé, maintenable, léger |
| Source sets | **Rebrickable snapshot** (licence à valider — voir CH-0) | Seule base offline exploitable |
| Plateforme V1 | **iOS natif uniquement** (Swift/SwiftUI) | Android = V2 |
| Modèle vision | **YOLOv8n détection + MobileNetV3 classification** | 2 stages, < 50 Mo total |

⚠️ Toute modification d'une décision actée doit être validée par le product owner avant de continuer.

---

## 1. Vue d'ensemble des chantiers

```
CH-0  Préalables légaux & data ──────────┐
                                          ▼
CH-1  Dataset & préparation ───► CH-2  Entraînement modèles ───► CH-3  Export & optimisation mobile
                                                                          │
CH-4  Fondations app iOS ◄────────────────────────────────────────────────┘
        │
        ▼
CH-5  Pipeline scan (caméra + inférence)
        │
        ▼
CH-6  Inventaire local (SQLite/GRDB)
        │
        ▼
CH-7  Moteur matching (sets réalisables)
        │
        ▼
CH-8  UI/UX complète (liquid glass)
        │
        ▼
CH-9  QA, performance, beta
        │
        ▼
CH-10 Monétisation & release
```

**Parallélisation possible :** CH-1→CH-3 (équipe ML) et CH-4→CH-6 (équipe iOS) avancent en parallèle. Point de jonction obligatoire : fin CH-3 livre les modèles `.mlpackage` à CH-5.

---

## 2. Index des fichiers

| Fichier | Chantier | Contenu |
|---|---|---|
| `00_MASTER_PLAN.md` | — | Ce fichier. Décisions, vue d'ensemble, conventions |
| `01_CH0_PREALABLES.md` | CH-0 | Licences, comptes, environnements |
| `02_CH1_DATASET.md` | CH-1 | Acquisition, nettoyage, annotation, splits |
| `03_CH2_TRAINING.md` | CH-2 | Entraînement YOLO + classifier, métriques cibles |
| `04_CH3_EXPORT_MOBILE.md` | CH-3 | Conversion CoreML, quantization, validation parité |
| `05_CH4_IOS_FOUNDATIONS.md` | CH-4 | Projet Xcode, architecture, dépendances, CI |
| `06_CH5_SCAN_PIPELINE.md` | CH-5 | Caméra, inférence temps réel, agrégation |
| `07_CH6_INVENTORY.md` | CH-6 | Schéma DB, persistance, CRUD inventaire |
| `08_CH7_MATCHING.md` | CH-7 | Import Rebrickable, algo matching, perfs |
| `09_CH8_UI_UX.md` | CH-8 | Design system, écrans, navigation, accessibilité |
| `10_CH9_QA_BETA.md` | CH-9 | Plan de tests, benchmarks, TestFlight |
| `11_CH10_RELEASE.md` | CH-10 | Monétisation, App Store, OTA updates |
| `12_CONVENTIONS_AI.md` | — | Conventions code, contrats inter-modules, prompts types pour IA exécutante |

---

## 3. Règles d'exécution (pour humain ou IA)

1. **Un jalon = un livrable vérifiable.** Pas de jalon "en cours". Chaque jalon a des critères d'acceptation binaires (✅/❌).
2. **Ne jamais passer au jalon suivant si les critères d'acceptation du jalon courant ne sont pas tous ✅.**
3. **Tout fichier produit suit la nomenclature** définie dans `12_CONVENTIONS_AI.md`.
4. **Les contrats inter-modules (formats JSON, schémas DB, signatures API internes) sont figés** dans `12_CONVENTIONS_AI.md`. Toute évolution = mise à jour du fichier de conventions D'ABORD, implémentation ENSUITE.
5. **Si une information manque ou est ambiguë : STOP.** Documenter le blocage, proposer 2–3 hypothèses, demander arbitrage. Ne jamais inventer une valeur (URL d'API, version de lib, comportement non vérifié).
6. **Chaque chantier produit un fichier `CHANGELOG_CHx.md`** listant ce qui a été fait, les écarts au plan, les décisions prises.

---

## 4. Estimations macro (1 dev ML + 1 dev iOS, ou IA pilotée)

| Chantier | Durée estimée | Dépendances |
|---|---|---|
| CH-0 | 3–5 j | — |
| CH-1 | 2–3 sem | CH-0 |
| CH-2 | 2–4 sem (selon GPU dispo) | CH-1 |
| CH-3 | 1 sem | CH-2 |
| CH-4 | 1 sem | CH-0 |
| CH-5 | 2–3 sem | CH-3 + CH-4 |
| CH-6 | 1 sem | CH-4 |
| CH-7 | 2 sem | CH-6 + CH-0 (snapshot) |
| CH-8 | 2–3 sem | CH-5/6/7 |
| CH-9 | 2 sem | CH-8 |
| CH-10 | 1–2 sem | CH-9 |
| **Total** | **~4–5 mois** | (avec parallélisation ML/iOS) |

⚠️ Estimations indicatives, à recalibrer après CH-1 (qualité réelle du dataset = principal facteur de risque planning).

---

## 5. Définition of Done globale V1

- [ ] App iOS installable via TestFlight
- [ ] Scan d'un étalement de pièces → inventaire avec ≥ 85% précision (pièces du scope 1000 classes)
- [ ] Identification couleur ≥ 80% précision en éclairage intérieur standard
- [ ] Matching : sets réalisables affichés en < 2s pour un inventaire de 500 pièces
- [ ] Fonctionne intégralement en mode avion (hors pub)
- [ ] Taille app < 350 Mo (modèles inclus)
- [ ] Crash-free rate > 99% sur la beta
