#!/bin/sh
cd /Users/malik/Documents/BrickOFF
.venv/bin/python ml/det/train_baseline.py --epochs 25 --batch 16 --patience 8 --aug strong --val-photos-only --synth-dir data/processed/synth_v12 --synth-frac 1.0 --out ml/runs/det_v2C &&
.venv/bin/python ml/det/eval.py --weights ml/runs/det_v2C/best.pt --split-dir data/processed/detection/test > ml/runs/det_v2C/eval_test.json 2>/dev/null
.venv/bin/python ml/det/train_baseline.py --epochs 30 --batch 16 --patience 10 --lr 3e-4 --aug strong --val-photos-only --init-weights ml/runs/det_v2C/best.pt --out ml/runs/det_v2B &&
.venv/bin/python ml/det/eval.py --weights ml/runs/det_v2B/best.pt --split-dir data/processed/detection/test > ml/runs/det_v2B/eval_test.json 2>/dev/null
.venv/bin/python ml/det/train_baseline.py --epochs 40 --batch 16 --patience 10 --aug strong --val-photos-only --synth-dir data/processed/synth_v12 --synth-frac 0.3 --out ml/runs/det_v2A &&
.venv/bin/python ml/det/eval.py --weights ml/runs/det_v2A/best.pt --split-dir data/processed/detection/test > ml/runs/det_v2A/eval_test.json 2>/dev/null
echo "=== CHAINE S5 TERMINEE $(date) ===" >> ml/runs/s5_chain.log
