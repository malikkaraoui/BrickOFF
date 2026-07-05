# S.1-pré — Préflight technique CH-S (scripts)

Scripts Blender headless du jalon de gate S.1-pré (plan `docs/plan/16_PIPELINE_SYNTHETIQUE.md` v1.1).
Rapport de résultats : `docs/research/SYNTH_PREFLIGHT.md`.

Exécution (Blender 5.1.2, addon ldr_tools_blender 0.5.1, bibliothèque LDraw dans
`data/raw/ldraw/ldraw/`) :

```sh
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
$BLENDER --background --python 03_scale.py        # point 3 — échelle (bloquant)
zsh run_smoke.sh                                  # point 1 — smoke 447 pièces (reprise sur crash)
$BLENDER --background --python 02_physics.py      # point 2 — hull vs mesh vs hybride
$BLENDER --background --python 04_cryptomatte.py  # point 4 — cryptomatte EEVEE + IoU
$BLENDER --background --python 05_thin.py         # point 5 — pièces fines
```

- `common.py` — helpers partagés (import LDraw aplati, rigid body, EXR multilayer,
  décodage Cryptomatte via OpenImageIO, pièges API 5.x). Base prévue pour S.2.
- Résultats chiffrés dans `out/` (JSON/JSONL + rendus de contrôle).
- `SMOKE_LIMIT=N` limite le smoke-test aux N premières pièces (débogage).
