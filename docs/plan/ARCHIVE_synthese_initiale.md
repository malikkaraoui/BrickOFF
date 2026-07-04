# LEGO AI Offline — Synthèse technique & stratégie (discussion consolidée)

## 1. Objectif du projet

Construire une application mobile capable de :

- Scanner un tas de pièces LEGO via caméra
- Identifier les pièces (type + couleur + position)
- Construire un inventaire local
- Proposer des modèles réalisables avec les pièces disponibles
- Fonctionner **100% offline**
- Être distribuable en modèle gratuit financé par publicité ou freemium

---

## 2. État de l’existant (produits similaires)

### Brickit
- Application propriétaire mobile
- Fonction principale :
  - scan d’un tas de LEGO
  - détection des pièces
  - suggestions de constructions
- Architecture supposée :
  - vision model propriétaire
  - moteur de recommandation
  - base de modèles LEGO
- ⚠️ Aucun code open source public exploitable identifié

---

## 3. Modèles IA récents pertinents

### LocateAnything-3B (NVIDIA)
- Vision-Language Model (3B paramètres)
- Capable de :
  - détection d’objets
  - grounding (localisation dans image)
- Limites :
  - trop lourd pour mobile en version brute (~plusieurs Go FP16)
  - non optimisé tel quel pour embarqué (<300 Mo cible impossible sans adaptation forte)

---

## 4. Datasets LEGO disponibles

### Dataset LEGOBricks (Hugging Face)
- ~400 000 images
- ~1000 classes de pièces LEGO
- Variations multiples (rotation, couleur, angles)
- Données adaptées classification pièces

### Dataset segmentation LEGO (recherche académique)
- images réelles + synthétiques
- segmentation d’objets LEGO
- bounding boxes disponibles

### Dataset construction LEGO (texte → structure)
- couples description ↔ structure LEGO
- utile pour génération de modèles

---

## 5. Contraintes produit

### Objectif mobile
- Taille modèle cible : < 300 Mo
- Latence : temps réel ou quasi temps réel
- Exécution :
  - iOS (CoreML / Metal)
  - Android (TFLite / ONNX Runtime)

---

## 6. Approches techniques possibles

## Option A — YOLO / modèle detection spécialisé (RECOMMANDÉ)

### Pipeline
- YOLO nano / YOLOv8 small
- entraîné sur dataset LEGO annoté

### Output
```json
[
  {
    "piece": "3001",
    "color": "red",
    "bbox": [x,y,w,h]
  }
]