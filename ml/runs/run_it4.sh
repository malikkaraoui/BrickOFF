#!/bin/sh
cd /Users/malik/Documents/BrickOFF
.venv/bin/python ml/det/train_baseline.py --epochs 40 --batch 16 --patience 10 --aug strong --val-photos-only --synth-dir data/processed/synth_v12 --synth-frac 0.3 --out ml/runs/det_v3 &&
.venv/bin/python ml/det/eval.py --weights ml/runs/det_v3/best.pt --split-dir data/processed/detection/test > ml/runs/det_v3/eval_test.json 2>/dev/null
echo "=== IT4 TERMINEE $(date) ===" >> ml/runs/s5_chain.log
