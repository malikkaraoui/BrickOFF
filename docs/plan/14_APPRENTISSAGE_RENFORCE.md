# 14 — Apprentissage : méthodologie renforcée, alternatives & portes de sortie

> Remplace et approfondit CH-2. Le jalon apprentissage est LE point de défaillance possible du projet.
> Philosophie : ne jamais dépendre d'une seule voie. Chaque étape a un plan B chiffré et un critère de bascule.
>
> **Amendé le 2026-07-04 (post-revue adversaire CH-0)** : le domain gap n'est plus un risque mais
> un état de départ certain (dataset public = rendus LDraw, constat 3) ; la stratégie nominale intègre
> le corpus réel d'entraînement (jalon 1.7) ; l'usage Brickognize est gelé et le coût d'annotation
> manuelle est chiffré (constat 13).

---

## 0. Pourquoi ce jalon peut échouer (lucidité d'abord)

| Cause d'échec | Probabilité | Détectable quand |
|---|---|---|
| Dataset public de qualité insuffisante (annotations bruitées) | Moyenne-haute | Semaine 1–2 (audit) |
| Écart domaine : dataset ≠ photos réelles utilisateur (le "domain gap") | **Certaine — état de départ, plus un risque** : le dataset public est 100 % synthétique (rendus LDraw, vérifié CH-0, constat 3) | Connu dès CH-0 (rien à détecter) |
| Corpus réel d'entraînement (jalon 1.7) trop lent/coûteux à constituer, surtout si Brickognize reste gelé (constat 13) | Moyenne | Premières sessions d'annotation |
| Classes visuellement indiscernables (variantes de molds) | Certaine sur une fraction des classes | Matrice de confusion v0 |
| Sous-performance couleur en éclairage chaud | Haute | Éval COLOR realworld |
| GPU/temps insuffisant pour itérer | Moyenne | Planning |

**Principe directeur (amendé CH-0) : le domain gap n'est plus une hypothèse à surveiller, c'est l'état de départ certain. Stratégie nominale : pré-entraînement synthétique massif (§2.1) + fine-tuning sur le corpus réel maison (jalon 1.7) + évaluation sur le realworld test (jalon 1.6) — pas d'espoir, un plan.**

---

## 1. Méthodologie exacte — séquence renforcée

### Phase 1 — Audit dataset AVANT tout entraînement (3–4 jours) ⚠️ nouveau, obligatoire

1. Échantillonner 500 images au hasard, inspection visuelle outillée (grille HTML générée par script)
2. Mesurer : % annotations fausses, % images "studio" (fond uniforme, éclairage parfait) vs "réalistes", diversité réelle des angles
3. **Critère de bascule** : si > 10% d'annotations fausses → nettoyage prioritaire avant entraînement (semi-automatique : entraîner un modèle rapide, flagger les images où il diverge fortement du label, revue humaine)
4. ~~**Critère de bascule** : si > 90% d'images studio → activer immédiatement la voie synthétique (§2.1)~~ *(amendé CH-0 : critère satisfait par construction — le dataset est 100 % synthétique, donc §2.1 et le jalon 1.7 sont actifs d'office ; l'audit reste utile pour mesurer le bruit d'annotations)*

Livrable : `AUDIT_DATASET.md` avec verdict chiffré et voies activées.

### Phase 2 — Baselines rapides (1 semaine, pas de perfectionnisme)
Identique à CH-2 jalons 2.1/2.2 mais avec une règle : **time-box 1 semaine, configs par défaut.** L'objectif des baselines n'est pas la performance, c'est de **localiser le problème** (data ? domain gap ? classes ?). L'erreur classique est de tuner des hyperparamètres alors que le problème est dans la donnée.

### Phase 3 — Diagnostic structuré (le cœur de la méthode)
Sur le realworld test, classer CHAQUE erreur (script + revue) dans une taxonomie :

| Catégorie d'erreur | Remède associé (voir §2) |
|---|---|
| Pièce non détectée (rappel DET) | Synthétique + augmentation fond/éclairage |
| Détectée mais mal classée — classes similaires | Fusion de classes OU métrique learning (§2.3) |
| Détectée mais mal classée — aléatoire | Plus de données réelles de cette classe |
| Couleur fausse — systématique par éclairage | Calibration balance des blancs (§2.4) |
| Couleur fausse — aléatoire | Améliorer la segmentation fond/pièce |

**Règle : on n'engage un remède que sur la catégorie dominante (> 30% des erreurs). Une action à la fois, mesurée.**

### Phase 4 — Boucle d'itération mesurée
- Cycle fixe : hypothèse → action unique → réentraînement → éval realworld → garder/jeter
- Journal d'expériences obligatoire (`ml/EXPERIMENTS.md`) : chaque run = id, hypothèse, delta de métriques. Interdiction de deux changements simultanés.
- Budget V1 : **6 itérations max** (vs 3 dans CH-2 initial — réévalué à la hausse, c'est réaliste). Au-delà → activer les portes de sortie (§3).

---

## 2. Arsenal de solutions alternatives (à activer selon diagnostic)

### 2.1 — Données synthétiques par rendu 3D ⭐ levier le plus puissant
**Principe** : les géométries 3D de la quasi-totalité des pièces LEGO existent en open source (bibliothèque LDraw, formats .dat). Pipeline Blender scripté :
- Importer les 1000 pièces du scope (convertisseurs LDraw→Blender existants — vérifier l'état des outils au moment de l'exécution)
- Générer des scènes : pièces posées aléatoirement, fonds variés (textures bois/tissu/sol), éclairages HDRI multiples, angles caméra smartphone réalistes, flou/bruit capteur simulés
- Annotations PARFAITES et gratuites (bbox + classe connues par construction)
- Volume : 50 000–200 000 images en quelques jours de calcul

**Quand l'activer** *(amendé CH-0)* : dès le départ — ce n'est plus un remède conditionnel, c'est la **voie nominale**. Le dataset public EST déjà du synthétique (rendus LDraw) ; la valeur ajoutée du pipeline maison est le réalisme (fonds, HDRI, bruit capteur) et le contrôle total des classes.
**Piège connu** : le synthétique pur crée son propre domain gap — et le dataset public en souffre déjà par construction. Recette nominale (amendée CH-0) : pré-entraînement synthétique massif puis **fine-tuning sur le corpus réel maison du jalon 1.7** (mélange possible, ratio à tester : départ 70/30), évaluation uniquement sur le realworld test (1.6). Générer plus de rendus ne comble PAS le gap à lui seul (remède partiellement circulaire, constat 3) : les données réelles de 1.7 sont indispensables.
**Coût** : ~1–2 semaines de mise en place du pipeline, réutilisable à vie (y compris pour étendre les classes en V2 — c'est un investissement, pas un coût).

### 2.2 — Auto-annotation assistée par grand modèle (bootstrap)
Utiliser un gros modèle de détection serveur (le LocateAnything-3B du doc initial, ou SAM pour la segmentation) pour PRÉ-annoter des photos réelles en masse, puis correction humaine rapide (valider/corriger est 10× plus vite qu'annoter de zéro).
**Quand** : besoin de volume réel rapidement (catégorie "plus de données réelles") — c'est le mécanisme du jalon 1.7.
**Note** : le gros modèle tourne côté serveur/poste de travail pendant le DÉVELOPPEMENT uniquement — aucune contradiction avec l'app offline.
**⚠️ Gel licence (amendé CH-0, constat 13)** : l'usage de **Brickognize est GELÉ par `ML_LICENSES.md`** (ToS non-commercial) tant que l'accord écrit n'est pas obtenu — le pré-annotateur par défaut est donc notre propre baseline entraîné sur synthétique (+ SAM pour les masques), sans risque licence.
**Coût honnête si le gel persiste** : annotation manuelle de zéro ≈ 60–90 s/pièce (bbox + part_id parmi 1000 classes + couleur) → **~85–125 h** pour les 5000 pièces du jalon 1.7, auxquelles s'ajoutent les ~2000 pièces × 2 passes du realworld test 1.6 (**~70–100 h**, incompressibles car ce set doit rester annoté à la main). Avec pré-annotation baseline + correction humaine (~6–10 s/pièce), le 1.7 retombe à **~15–25 h**. À budgéter comme du temps humain réel dans le planning CH-1/CH-2, pas comme un détail.

### 2.3 — Architecture alternative pour les classes confusables : métrique learning
Si la matrice de confusion révèle des grappes de classes indiscernables (probable : variantes de molds quasi identiques) :
- **Option douce** : fusionner les classes en "groupes fonctionnels" (du point de vue construction, deux molds quasi identiques sont interchangeables → la fusion est même PRODUIT-pertinente, pas un aveu d'échec). Mise à jour `classes_v1.json` + équivalences matching.
- **Option technique** : remplacer la tête softmax par un embedding (ArcFace/triplet loss) + recherche du plus proche voisin dans une galerie de prototypes. Avantages : ajout de nouvelles classes SANS réentraînement (énorme pour les V2+), meilleure séparation fine. Coût : complexité +, latence à revérifier.
- **Recommandation** : fusion d'abord (gratuit), métrique learning si la fusion dégrade trop la valeur produit.

### 2.4 — Couleur : calibration active
Si la couleur échoue en éclairage chaud (probable) :
- **Niveau 1** : exploiter les métadonnées de balance des blancs de la capture iOS (AVFoundation expose les gains WB) pour corriger AVANT conversion LAB
- **Niveau 2** : carte de référence — demander à l'utilisateur de scanner une fois une feuille blanche (calibration mémorisée par lieu) — friction UX, à réserver au mode "précision"
- **Niveau 3** : mini-modèle de constance des couleurs (existant en littérature, léger) — dernier recours
- **Niveau 0 (toujours)** : assumer l'incertitude — sous éclairage extrême, retourner "unknown" + suggérer le bon éclairage. Un "je ne sais pas" honnête vaut mieux qu'un rouge devenu orange.

### 2.5 — Distillation depuis un gros modèle
Entraîner d'abord un modèle LOURD (qui n'a aucune contrainte mobile) jusqu'à d'excellentes métriques, puis distiller vers le modèle mobile (le petit apprend les soft labels du gros). Gain typique de quelques points sur le petit modèle, surtout sur les classes difficiles.
**Quand** : le petit modèle plafonne alors que la donnée est bonne (écart gros/petit > 5 pts).

### 2.6 — Test-time augmentation (TTA) côté app
Gratuit côté entraînement : au scan, le multi-frames de l'agrégateur (CH-5) EST déjà une forme de TTA. Renforcement possible : varier légèrement l'exposition entre les 5 frames capturées → diversité d'éclairage gratuite, vote plus robuste. À activer si les métriques single-frame sont limites mais le vote multi-frames rattrape.

---

## 3. Portes de sortie (si les cibles ne sont pas atteintes après 6 itérations)

> Déclenchement : pipeline complet < 0.65 sur realworld après épuisement du budget d'itérations. Décisions PRODUIT, par ordre de préférence :

### Sortie S1 — Réduction de scope assumée 🟢
Passer de 1000 à 300–500 classes (les mieux reconnues + les plus fréquentes dans les sets). Métriques mécaniquement meilleures, produit toujours viable (communication : "pièces les plus courantes"). Le catalogue de sets matchables rétrécit → recalculer la couverture sets et valider qu'elle reste > seuil produit.
**Coût : 1 semaine (re-filtrage + réentraînement). Perte produit : modérée.**

### Sortie S2 — UX compensatoire 🟢
Renforcer le rôle de l'écran de revue : le scan devient une "pré-saisie intelligente" que l'utilisateur valide, avec correction ultra-rapide (top-5 en un tap). Honnête, et c'est déjà l'esprit du jalon 5.6 — il s'agit d'assumer un curseur plus correctif. Ajouter un mode "scan pièce par pièce" (une pièce plein cadre = précision maximale) pour les pièces douteuses.
**Coût : 1–2 semaines UI. Perte produit : friction, mais fiabilité perçue ↑.**

### Sortie S3 — Pivot hybride temporaire 🟡
V1 lancée offline avec le modèle imparfait + option "scan haute précision" envoyant la photo à un gros modèle serveur (opt-in explicite, photo seule, RGPD). Le serveur collecte (avec consentement) des données réelles qui nourrissent le réentraînement → le modèle local rattrape en V1.1/V1.2 et le serveur s'éteint.
**Coût : infra serveur + RGPD. Contredit partiellement la promesse offline → opt-in et transparence obligatoires. C'est aussi une stratégie d'amélioration continue, pas seulement un échec.**

### Sortie S4 — Repositionnement produit 🔴 dernier recours
Si même S1+S2 ne donnent pas un produit digne : pivoter la V1 sur le mode "pièce par pièce" uniquement (identification unitaire fiable, type "Shazam de la brique") + inventaire manuel assisté. Le scan de tas devient la promesse V2, le temps que la voie synthétique (§2.1) mûrisse.
**À ce stade, refaire un point stratégique complet avant d'investir davantage.**

### Arbre de décision
```
Éval finale realworld (après ≤ 6 itérations)
│
├─ pipeline ≥ 0.65 ──────────────► GO CH-3 (plan nominal)
├─ 0.50–0.65 ────────────────────► S1 (réduction scope) + S2 (UX) → re-éval
│                                   └─ toujours < 0.65 ► S3
└─ < 0.50 ───────────────────────► STOP itérations. Audit causes racines.
                                    └─ data irrécupérable ► S4 + investissement §2.1
```

---

## 4. Garde-fous méthodologiques (résumé exécutable)

1. **Auditer la donnée avant d'entraîner** (Phase 1) — non négociable
2. **Le realworld test maison est le seul juge** — jamais de décision sur les métriques du dataset public seul
3. **Une hypothèse, un changement, une mesure** — journal d'expériences obligatoire
4. **Time-box partout** : baselines 1 sem, 6 itérations max, spike A3 2 sem
5. **La voie synthétique (§2.1) se prépare en parallèle dès la Phase 1** si le moindre signal de domain gap apparaît — ne pas attendre l'échec pour la démarrer
6. **Chaque porte de sortie est un produit viable**, pas un abandon — les critères de bascule sont chiffrés à l'avance, donc la décision sera factuelle, pas émotionnelle
