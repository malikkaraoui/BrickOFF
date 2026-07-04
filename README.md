# BrickOFF 🧱

**Photographiez votre tas de LEGO® en vrac. Choisissez quoi construire. Suivez le guide, pas à pas.**

BrickOFF transforme des pièces LEGO en pagaille en nouvelles constructions : l'app scanne le tas
avec la caméra du téléphone, identifie chaque pièce (référence + couleur), construit votre
inventaire, puis propose des constructions **réalisables avec exactement ce que vous avez** —
et vous guide étape par étape, comme une notice officielle.

**100 % local, 100 % offline.** Aucune photo n'est envoyée sur un serveur : l'IA tourne
entièrement sur le téléphone. Gratuit, financé par la publicité.

> *BrickOFF is not affiliated with, endorsed by, or sponsored by the LEGO Group.*
> *LEGO® is a trademark of the LEGO Group.*

---

## Vision & feuille de route

La vision complète est dans **[docs/VISION.md](docs/VISION.md)**. En résumé :

| Palier | Contenu | Statut |
|---|---|---|
| **V1** — iOS | Scan → inventaire → sets officiels réalisables (catalogue Rebrickable offline) | 🚧 En cours (CH-0) |
| **V1.5** | "Choisis une construction" : blueprints adaptés à VOS pièces + guidage pas-à-pas | Planifié |
| **V2** | Android + catalogue de constructions enrichi en continu (OTA) | Planifié |
| **V3** | Génération libre de plans inédits par IA embarquée | Spike Go/No-Go d'abord |

**Cible produit : iOS et Android.** L'exécution est séquencée iOS d'abord — on prouve le pipeline
de vision sur un parc de devices homogène avant de doubler la surface (justification :
[D01](docs/plan/ARBITRAGES/D01_PLATEFORME.md)).

## Architecture (V1)

Pipeline de vision en 2 étages, entièrement embarqué :

```
Caméra → DET (détection des pièces, mono-classe)
       → CLS (classification ~1000 références, sur crop)
       → COLOR (identification couleur en espace LAB, déterministe)
       → Inventaire local (SQLite) → Matching sets (catalogue Rebrickable embarqué)
```

Pourquoi 2 étages plutôt qu'un détecteur 1000 classes : la détection mono-classe maximise le
rappel (ne rater aucune pièce), la classification sur crop voit chaque pièce en grand (précision),
et les deux modèles s'améliorent indépendamment.

## Le dépôt

```
docs/
├── VISION.md            ← l'étoile du Nord — commencer ici
├── REPRISE.md           ← document de continuité : état instantané + comment reprendre le travail
├── plan/                ← plan d'exécution complet, chantier par chantier (CH-0 → CH-10)
│   ├── 00_MASTER_PLAN.md      ← document racine du plan
│   ├── ARBITRAGES/            ← registre des décisions (D01→D08) — prime sur le reste
│   └── 15_VEILLE_GITHUB.md    ← repos open source étudiés (licences vérifiées)
legal/                   ← vérifications licences & conformité (CH-0)
ml/                      ← entraînement des modèles (CH-1 → CH-3)
data/                    ← datasets & scripts de préparation (non versionnés, voir .gitignore)
ios/                     ← app iOS (CH-4+)
```

**Méthode de travail** : chaque décision structurante est un fichier d'arbitrage daté et justifié
(`docs/plan/ARBITRAGES/`), chaque chantier a des jalons à critères d'acceptation binaires, et le
travail sur du code tiers se fait **en salle blanche** — on étudie les approches des projets open
source (crédités dans la veille), on réécrit depuis notre compréhension, on ne copie jamais de
code non licencié. Pourquoi : le projet est destiné à une distribution commerciale ; la propreté
juridique est vérifiée *avant* d'écrire le code, pas au moment de la release.

## État d'avancement

- ✅ Corpus documentaire consolidé, divergences arbitrées (D01→D08)
- ✅ Veille open source (frameworks Apache-2.0 identifiés, chaîne synthétique LDraw→Blender repérée)
- 🚧 **CH-0 en cours** : vérifications légales (licences Rebrickable, LEGO Fair Play, dataset, frameworks)
- ⬜ CH-1 Dataset → CH-10 Release : à venir, dans l'ordre du [Master Plan](docs/plan/00_MASTER_PLAN.md)
