#!/bin/sh
cd /Users/malik/Documents/BrickOFF
.venv/bin/python ml/synth/generate_scenes.py --config ml/synth/config_v2.yaml --n 12000 --dataset-id synth_v2 --out data/processed/synth_v2 --seed 20260708 >> ml/runs/synth_v2.log 2>&1
echo "=== SYNTH V2 TERMINE $(date) ===" >> ml/runs/synth_v2.log
