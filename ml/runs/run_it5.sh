#!/bin/sh
cd /Users/malik/Documents/BrickOFF
.venv/bin/python ml/det/train_baseline.py --epochs 60 --batch 16 --patience 12 --aug strong \
  --val-photos-only --data data/processed/detection_it5 \
  --synth-dir data/processed/synth_v2 --synth-frac 0.3 --out ml/runs/det_v4 &&
# Éval 1 : régression sur le test mono-pièce (ne doit pas chuter vs 0.826)
.venv/bin/python ml/det/eval.py --weights ml/runs/det_v4/best.pt \
  --split-dir data/processed/detection/test > ml/runs/det_v4/eval_monopiece.json 2>/dev/null
# Éval 2 : LE VERDICT — juge TAS corrigé PO (baseline det_v3 = mAP 0.656, recall@0.20 0.568)
for th in 0.20 0.25 0.35; do
  .venv/bin/python ml/det/eval.py --weights ml/runs/det_v4/best.pt \
    --split-dir data/processed/realworld_piles/decision --score-threshold $th \
    > ml/runs/det_v4/eval_judge_$th.json 2>/dev/null
done
echo "=== IT5 TERMINE $(date) ===" >> ml/runs/it5.log
