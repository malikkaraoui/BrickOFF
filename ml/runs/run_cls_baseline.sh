#!/bin/sh
# CH-2 jalon 2.2 — chaîne CLS v0 (à lancer quand le M1 est libre, via caffeinate) :
#   1. manifestes (idempotent : ne réécrit pas s'ils existent)
#   2. entraînement MobileNetV3-Large : phase 1 tête gelée (5 ep) + phase 2
#      fine-tuning complet, 80 % synthétique legobricks / 20 % photos réelles gdansk
#   3. éval : test legobricks + val/test photos réelles gdansk (+ pires classes,
#      paires confondues) dans ml/runs/cls_v0/eval_cls_*.json
# Suivi : tail -f ml/runs/cls_v0/history.json  (val_top1/val_top5 + real_top1/real_top5)
# Relance après interruption : relancer le script (le run repart de zéro, comme DET v0).
cd /Users/malik/Documents/BrickOFF || exit 1
.venv/bin/python ml/cls/make_splits.py
# 30 epochs (écart au plan "50" consigné au CHANGELOG : projection temps/epoch M1 —
# l'early stopping patience 10 tranchera de toute façon avant)
.venv/bin/python ml/cls/train_cls.py \
  --epochs 30 --head-epochs 5 --batch 64 --patience 10 \
  --mix-real-frac 0.2 --window 64 --workers 4 \
  --out ml/runs/cls_v0 &&
.venv/bin/python ml/cls/eval_cls.py --weights ml/runs/cls_v0/best.pt \
  --source legobricks --split test > /dev/null &&
.venv/bin/python ml/cls/eval_cls.py --weights ml/runs/cls_v0/best.pt \
  --source gdansk_photos --split val > /dev/null &&
.venv/bin/python ml/cls/eval_cls.py --weights ml/runs/cls_v0/best.pt \
  --source gdansk_photos --split test > /dev/null
echo "=== CHAINE CLS v0 TERMINEE $(date) ===" >> ml/runs/cls_chain.log
