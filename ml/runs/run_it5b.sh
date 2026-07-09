#!/bin/sh
cd /Users/malik/Documents/BrickOFF
.venv/bin/python ml/det/train_baseline.py --epochs 60 --batch 16 --patience 12 --aug strong \
  --val-photos-only --data data/processed/detection_it5 \
  --synth-dir data/processed/synth_v2 --synth-frac 0.3 --out ml/runs/det_v4b &&
# juge SPARSE (batch1) — non-régression
.venv/bin/python ml/det/eval.py --weights ml/runs/det_v4b/best.pt --split-dir data/processed/realworld_piles/decision --score-threshold 0.20 > ml/runs/det_v4b/eval_sparse.json 2>/dev/null
# juge DENSE HOLDOUT (4 tas jamais vus) — LE VERDICT ÉQUITABLE
for th in 0.20 0.25; do
  .venv/bin/python ml/det/eval.py --weights ml/runs/det_v4b/best.pt --split-dir data/processed/judge_dense_holdout --score-threshold $th > ml/runs/det_v4b/eval_dense_holdout_$th.json 2>/dev/null
done
# mono-pièce
.venv/bin/python ml/det/eval.py --weights ml/runs/det_v4b/best.pt --split-dir data/processed/detection/test > ml/runs/det_v4b/eval_monopiece.json 2>/dev/null
echo "=== IT5b TERMINE $(date) ===" >> ml/runs/it5.log
