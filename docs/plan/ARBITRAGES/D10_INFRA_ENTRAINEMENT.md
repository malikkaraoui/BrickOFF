# D10 — Infrastructure d'entraînement : MacBook Pro M1 en nominal, cloud en escalade

**Statut : ✅ Tranché (2026-07-04) — décision PO : matériel personnel proposé (iPad M4 / MacBook M1)**

## Contexte

CH-0 jalon 0.4 demandait de choisir l'accès GPU : machine locale NVIDIA ≥ 16 Go VRAM, ou cloud
(~50–200 € pour la phase). Le PO propose son matériel : **iPad Pro M4** (disponible 1 semaine
non-stop) et **MacBook Pro M1 16 Go** (machine de dev).

## Décision

| Matériel | Rôle retenu | Pourquoi |
|---|---|---|
| **iPad Pro M4** | ❌ Entraînement impossible → **device de test V1 (iPadOS) + rendu Blender d'appoint : non plus** | Ce n'est pas la puce (excellente), c'est **iPadOS** : pas d'environnement Python/PyTorch, pas de processus longs arbitraires, pas d'accès Metal pour un pipeline d'entraînement tiers. Aucun contournement sérieux n'existe. L'iPad reste précieux comme **device de test** (l'app tournera aussi sur iPad) |
| **MacBook Pro M1 16 Go** | ✅ **Nominal** : rendu synthétique Blender, entraînement des baselines et des itérations via PyTorch **MPS** (accélération Metal) | Nos modèles sont volontairement petits (détecteur nano ~1-5 M params, MobileNetV3 ~5 M) : c'est exactement le régime où un M1 est viable. Mémoire unifiée 16 Go = attention à la taille de batch (démarrer bas, 8–16) |
| **Cloud GPU** (RunPod/Lambda, ~0,4–0,7 €/h) | 🟡 **Escalade ponctuelle** | Déclencheur chiffré ci-dessous |

## Critère d'escalade (chiffré, pas émotionnel)

Mesurer le temps d'une epoch DET sur le corpus réel dès le premier run M1 :
- **Si un entraînement complet (100 epochs, early stopping) projette > 48 h** → basculer CE run
  sur cloud (une carte type RTX 4090/A10 : l'entraînement complet passe sous ~6-10 h, coût
  ~5-15 € par run, budget phase ≤ 100 €).
- Les petits runs (classification 224 px, calibrations, reprises) restent sur M1 dans tous les cas.
- La semaine de disponibilité offerte sur l'iPad n'est pas perdue : elle sera utilisée côté
  **QA device** (soak tests, benchmarks CoreML iPad) en CH-9.

## Conséquences pratiques

1. `ml/requirements.txt` ciblera PyTorch avec backend **MPS** (pas de CUDA) ; tout script
   d'entraînement accepte `--device mps|cpu|cuda` pour être portable vers le cloud sans changement.
2. Le rendu Blender (pipeline synthétique) tourne la nuit sur le M1 — il est massivement
   parallélisable et interruptible, donc compatible avec une machine de travail.
3. Les seeds et configs versionnés (conventions §2) garantissent qu'un run M1 et un run cloud
   sont comparables.

## Impacts

- CH-0 jalon 0.4 : case "accès GPU" cochée (option locale Apple Silicon + escalade cloud).
- `03_CH2_TRAINING.md` : les configs de départ restent valables ; batch size à adapter (8–16 sur M1).
