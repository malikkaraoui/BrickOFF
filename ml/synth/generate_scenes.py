"""CH-S / S.2 — Orchestrateur du générateur de scènes synthétiques v0.

Pilote Blender headless par BATCHS (~400 scènes, relance du process entre batchs —
fuites mémoire connues) via ml/synth/blender_scene.py, avec communication par fichiers
JSON (job/résultats). Config de randomisation : ml/synth/config_v1.yaml (versionnée).

Sorties par scène (data/processed/<dataset_id>/) :
  images/<scene>.png      beauty EEVEE 640x640
  labels/<scene>.txt      YOLO classe 0 (bbox du masque VISIBLE ; >= 25 % -> positif ;
                          10-25 % -> ligne '# hard' conservée mais ignorée à l'entraînement)
  manifests/<scene>.json  seed, tous les params tirés, coverage par pièce, hash générateur
  run/                    jobs, logs Blender, résultats batch, summary.json

Reproductibilité : seed maître -> seeds par scène (indépendant du découpage en batchs).

Usage :
  .venv/bin/python ml/synth/generate_scenes.py --n 100 --dataset-id synth_v1_val
  .venv/bin/python ml/synth/generate_scenes.py --grid-only --dataset-id synth_v1_val
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import random
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
GENERATOR_FILES = [Path(__file__).resolve(),
                   Path(__file__).resolve().parent / "blender_scene.py",
                   Path(__file__).resolve().parent / "postprocess.py",
                   Path(__file__).resolve().parent / "preflight" / "common.py"]


# ---------------------------------------------------------------------------
# Résolution des part_ids (copie pure-path de preflight/common.resolve_part_file)
# ---------------------------------------------------------------------------


def resolve_part_file(parts_dir: Path, pid: str) -> Path | None:
    cands: list[str] = [pid, pid.lower()]
    m = re.match(r"^(\d+)[a-z]+$", pid)
    if m:
        cands.append(m.group(1))
    for s in ("a", "b", "c"):
        cands.append(pid + s)
        if m:
            cands.append(m.group(1) + s)
    if "_" in pid:
        for tok in pid.split("_"):
            cands.extend([tok, tok + "a"])
    seen: set[str] = set()
    for c in cands:
        if c in seen:
            continue
        seen.add(c)
        p = parts_dir / f"{c}.dat"
        if p.exists():
            return p
    return None


def build_parts_pool(cfg: dict) -> dict:
    """Scope v1 (445 part_ids) + poids empiriques gdansk_cls (cache JSON)."""
    photos = REPO_ROOT / cfg["paths"]["gdansk_cls_photos"]
    parts_dir = REPO_ROOT / cfg["paths"]["ldraw"] / "parts"
    cache = REPO_ROOT / cfg["paths"]["part_freq_cache"]
    if cache.exists():
        counts = json.loads(cache.read_text())
    else:
        print("[parts] comptage des fréquences empiriques gdansk_cls…")
        counts = {d.name: sum(1 for f in d.iterdir() if f.is_file())
                  for d in sorted(photos.iterdir()) if d.is_dir()}
        cache.write_text(json.dumps(counts, indent=0, sort_keys=True))
        print(f"[parts] cache écrit -> {cache}")
    exclude = set(cfg["parts"]["exclude"])
    ids, weights, dat_by_id, skipped = [], [], {}, []
    for pid, n in sorted(counts.items()):
        if pid in exclude:
            continue
        dat = resolve_part_file(parts_dir, pid)
        if dat is None:
            skipped.append(pid)
            continue
        ids.append(pid)
        weights.append(float(n))
        dat_by_id[pid] = str(dat)
    if skipped:
        print(f"[parts] ATTENTION: {len(skipped)} part_ids sans .dat hors liste "
              f"d'exclusion: {skipped}")
    total = sum(weights)
    return {"ids": ids, "weights_empirical": [w / total for w in weights],
            "dat_by_id": dat_by_id, "n_parts": len(ids)}


# ---------------------------------------------------------------------------
# Palette LDraw (LDConfig.ldr — couleurs de l'addon)
# ---------------------------------------------------------------------------

FINISH_KEYWORDS = ("CHROME", "PEARLESCENT", "METAL", "MATTE_METALLIC", "RUBBER",
                   "MATERIAL", "GLITTER", "SPECKLE", "LUMINANCE", "FABRIC")


def load_palette(cfg: dict) -> dict:
    ldconfig = REPO_ROOT / cfg["paths"]["ldraw"] / "LDConfig.ldr"
    solid: list[dict] = []
    trans: list[dict] = []
    by_code: dict[int, dict] = {}
    pat = re.compile(r"^0 !COLOUR (\S+)\s+CODE\s+(\d+)\s+VALUE\s+(#[0-9A-Fa-f]{6})(.*)$")
    for line in ldconfig.read_text(errors="replace").splitlines():
        m = pat.match(line.strip())
        if not m:
            continue
        name, code, hexval, rest = m.group(1), int(m.group(2)), m.group(3), m.group(4)
        entry = {"code": code, "name": name, "hex": hexval}
        by_code[code] = entry
        if code > 511 or "_INK" in name.upper():
            # codes > 511 = couleurs spéciales LDraw (encres 10xxx, Modulex 30xxx…)
            continue
        upper = name.upper()
        if ("ALPHA" in rest and upper.startswith("TRANS")
                and not any(k in rest for k in FINISH_KEYWORDS)
                and not any(k in upper for k in ("GLITTER", "OPAL"))):
            trans.append(entry)  # trans-* purs (test S.3)
            continue
        if "ALPHA" in rest or any(k in rest for k in FINISH_KEYWORDS):
            continue
        if any(k in upper for k in ("TRANS", "CHROME", "PEARL", "METALLIC",
                                    "GLITTER", "OPAL", "RUBBER", "SPECKLE")):
            continue
        solid.append(entry)
    weighted, weighted_w = [], []
    for code, w in cfg["colors"]["weighted_codes"].items():
        entry = by_code.get(int(code))
        if entry is None:
            print(f"[palette] ATTENTION: code LDraw {code} absent de LDConfig — ignoré")
            continue
        weighted.append(entry)
        weighted_w.append(float(w))
    print(f"[palette] {len(weighted)} couleurs pondérées, {len(solid)} solides "
          f"(uniforme), {len(trans)} trans-*")
    return {"weighted": weighted, "weighted_w": weighted_w, "solid": solid,
            "trans": trans}


# ---------------------------------------------------------------------------
# Assets S.1
# ---------------------------------------------------------------------------


def load_assets(cfg: dict) -> tuple[list, list, list]:
    manifest = json.loads((REPO_ROOT / cfg["paths"]["synth_assets_manifest"]).read_text())
    hdris, textures, models = [], [], []
    root = REPO_ROOT / cfg["paths"]["assets_root"]
    for a in manifest["assets"]:
        if a["type"] == "hdri":
            f = REPO_ROOT / a["file"]
            if f.exists():
                hdris.append({"id": a["id"], "file": str(f),
                              "thermal_class": a["thermal_class"]})
        elif a["type"] == "texture_pbr":
            d = root / "textures" / a["id"]
            maps = {k: d / f"{a['id']}_2K-JPG_{s}.jpg"
                    for k, s in (("color", "Color"), ("roughness", "Roughness"),
                                 ("normal", "NormalGL"))}
            if all(p.exists() for p in maps.values()):
                textures.append({"id": a["id"], **{k: str(p) for k, p in maps.items()}})
        elif a["type"] == "distractor_model":
            blend = root / "distractors" / a["id"] / f"{a['id']}_1k.blend"
            if blend.exists():
                models.append({"id": a["id"], "blend": str(blend)})
    print(f"[assets] {len(hdris)} HDRI, {len(textures)} textures, {len(models)} distracteurs")
    assert hdris and textures and models, "assets S.1 introuvables"
    return hdris, textures, models


# ---------------------------------------------------------------------------
# Versioning générateur
# ---------------------------------------------------------------------------


def generator_meta(config_path: Path) -> dict:
    def git(*args: str) -> str | None:
        try:
            return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True,
                                  text=True, timeout=10).stdout.strip() or None
        except Exception:
            return None
    h = hashlib.sha256()
    for f in [*GENERATOR_FILES, config_path]:
        h.update(f.read_bytes())
    try:
        config_rel = str(config_path.relative_to(REPO_ROOT))
    except ValueError:  # config hors dépôt (tests)
        config_rel = str(config_path)
    return {"git_commit": git("rev-parse", "HEAD"),
            "git_dirty": bool(git("status", "--porcelain")),
            "code_config_sha256": h.hexdigest()[:16],
            "config": config_rel}


# ---------------------------------------------------------------------------
# Batchs Blender
# ---------------------------------------------------------------------------


def run_batches(cfg: dict, args, scenes: list[dict], job_base: dict, out_dir: Path,
                run_dir: Path) -> float:
    batch_size = args.batch_size or cfg["batch"]["size"]
    manifests = out_dir / "manifests"
    t0 = time.perf_counter()
    batches = [scenes[i:i + batch_size] for i in range(0, len(scenes), batch_size)]
    for bi, batch in enumerate(batches):
        for attempt in range(cfg["batch"]["max_attempts"]):
            todo = [s for s in batch if not (manifests / f"{s['name']}.json").exists()]
            if not todo:
                break
            job = dict(job_base, batch_id=bi, scenes=todo)
            job_path = run_dir / f"batch_{bi:03d}_job.json"
            job_path.write_text(json.dumps(job))
            log_path = run_dir / f"batch_{bi:03d}_attempt{attempt}.log"
            print(f"[batch {bi}] tentative {attempt + 1}: {len(todo)} scènes "
                  f"(log: {log_path.name})")
            with log_path.open("w") as log:
                proc = subprocess.run(
                    [args.blender, "--background", "--python",
                     str(Path(__file__).parent / "blender_scene.py"), "--",
                     "--job", str(job_path)],
                    stdout=log, stderr=subprocess.STDOUT, timeout=7200)
            if proc.returncode != 0:
                print(f"[batch {bi}] process Blender code retour {proc.returncode}")
        missing = [s["name"] for s in batch
                   if not (manifests / f"{s['name']}.json").exists()]
        if missing:
            print(f"[batch {bi}] ECHEC persistant sur {len(missing)} scènes: "
                  f"{missing[:10]}")
    return time.perf_counter() - t0


# ---------------------------------------------------------------------------
# Auto-contrôles + stats (critère S.2)
# ---------------------------------------------------------------------------


def check_and_summarize(cfg: dict, scenes: list[dict], out_dir: Path,
                        wall_s: float, post_stats: dict | None = None) -> dict:
    errors: list[str] = []
    stats = {"n_scenes_expected": len(scenes), "n_scenes_ok": 0, "n_background": 0,
             "n_with_distractors": 0, "n_pos_total": 0, "n_hard_total": 0,
             "n_rejected_total": 0, "n_pieces_total": 0,
             "regimes": {}, "hdri_classes": {}, "floor_modes": {},
             "scene_s": [], "coverage_pos": []}
    for s in scenes:
        mpath = out_dir / "manifests" / f"{s['name']}.json"
        lpath = out_dir / "labels" / f"{s['name']}.txt"
        if not mpath.exists() or not lpath.exists():
            errors.append(f"{s['name']}: manifest ou label manquant")
            continue
        man = json.loads(mpath.read_text())
        lines = [ln for ln in lpath.read_text().splitlines() if ln.strip()]
        pos_lines = [ln for ln in lines if not ln.startswith("#")]
        hard_lines = [ln for ln in lines if ln.startswith("# hard ")]
        # 1. nb labels = nb pièces éligibles
        n_pos_man = sum(1 for p in man["pieces"] if p.get("status") == "positive")
        n_hard_man = sum(1 for p in man["pieces"] if p.get("status") == "hard")
        if len(pos_lines) != n_pos_man or len(hard_lines) != n_hard_man:
            errors.append(f"{s['name']}: labels ({len(pos_lines)}+{len(hard_lines)}h) != "
                          f"manifest ({n_pos_man}+{n_hard_man}h)")
        # 2. coverage dans [0,1] ; 3. aucune bbox hors image
        for p in man["pieces"]:
            cov = p.get("coverage")
            if cov is not None and not (0.0 <= cov <= 1.0):
                errors.append(f"{s['name']}/{p['part_id']}: coverage {cov} hors [0,1]")
            if p.get("status") == "positive":
                stats["coverage_pos"].append(cov)
        for ln in lines:
            vals = [float(v) for v in ln.split()[-4:]]
            cx, cy, w, h = vals
            if not (0 < w <= 1 and 0 < h <= 1 and cx - w / 2 >= -1e-6
                    and cx + w / 2 <= 1 + 1e-6 and cy - h / 2 >= -1e-6
                    and cy + h / 2 <= 1 + 1e-6):
                errors.append(f"{s['name']}: bbox hors image: {ln}")

        stats["n_scenes_ok"] += 1
        prm = man["params"]
        stats["n_pos_total"] += len(pos_lines)
        stats["n_hard_total"] += len(hard_lines)
        stats["n_pieces_total"] += prm.get("n_pieces", 0)
        stats["n_rejected_total"] += prm.get("n_rejected_out_of_zone", 0)
        stats["scene_s"].append(man.get("scene_s", 0))
        if prm["scene_type"] == "background":
            stats["n_background"] += 1
        if prm.get("distractors"):
            stats["n_with_distractors"] += 1
        for key, field in (("regimes", "n_regime"), ("hdri_classes", "hdri_class"),
                           ("floor_modes", "floor_mode")):
            v = str(prm.get(field))
            stats[key][v] = stats[key].get(v, 0) + 1

    n_ok = max(stats["n_scenes_ok"], 1)
    per_img_blender = sum(stats["scene_s"]) / n_ok
    per_img_wall = wall_s / n_ok
    post_s = (post_stats or {}).get("wall_s", 0.0)
    per_img_total = per_img_wall + post_s / n_ok
    summary = {
        "errors": errors,
        "stats": {k: v for k, v in stats.items() if k not in ("scene_s", "coverage_pos")},
        "coverage_pos_mean": round(sum(stats["coverage_pos"])
                                   / max(len(stats["coverage_pos"]), 1), 3),
        "throughput": {
            "wall_s_total": round(wall_s, 1),
            "s_per_image_blender": round(per_img_blender, 2),
            "s_per_image_wall": round(per_img_wall, 2),
            "postprocess_wall_s": round(post_s, 1),
            "s_per_image_postprocess": round(post_s / n_ok, 3),
            "s_per_image_total": round(per_img_total, 2),
            "projection_10k_h_wall": round(per_img_total * 10000 / 3600, 2),
        },
        "postprocess": post_stats,
    }
    return summary


# ---------------------------------------------------------------------------
# Grille HTML d'inspection (esprit data/scripts/04_audit_sample.py)
# ---------------------------------------------------------------------------


def build_grid(out_dir: Path, grid_path: Path, dataset_id: str, thumb: int = 320,
               limit: int | None = None) -> None:
    from PIL import Image, ImageDraw

    images = sorted([*(out_dir / "images").glob("*.png"),
                     *(out_dir / "images").glob("*.jpg")])
    if limit:
        images = images[:limit]
    cells = []
    for img_path in images:
        name = img_path.stem
        lpath = out_dir / "labels" / f"{name}.txt"
        mpath = out_dir / "manifests" / f"{name}.json"
        boxes = []  # (x0,y0,x1,y1, hard?)
        if lpath.exists():
            for ln in lpath.read_text().splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                hard = ln.startswith("# hard ")
                vals = [float(v) for v in ln.split()[-4:]]
                boxes.append((vals, hard))
        cap = ""
        if mpath.exists():
            prm = json.loads(mpath.read_text())["params"]
            cap = (f"N={prm.get('n_pieces')} · {prm.get('scene_type')} · "
                   f"hdri {prm.get('hdri_class')} · sol {prm.get('floor_mode')} · "
                   f"elev {prm.get('cam_elev_deg')}° · "
                   f"dx {len(prm.get('distractors') or [])}")
        with Image.open(img_path) as im:
            im = im.convert("RGB")
            W, H = im.size
            draw = ImageDraw.Draw(im)
            for (cx, cy, w, h), hard in boxes:
                x0, y0 = (cx - w / 2) * W, (cy - h / 2) * H
                x1, y1 = (cx + w / 2) * W, (cy + h / 2) * H
                color = (255, 160, 20) if hard else (255, 40, 40)
                draw.rectangle([x0, y0, x1, y1], outline=color, width=2)
            im = im.resize((thumb, thumb))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=82)
        b64 = base64.b64encode(buf.getvalue()).decode()
        n_pos = sum(1 for _, hard in boxes if not hard)
        n_hard = sum(1 for _, hard in boxes if hard)
        cells.append(
            f'<figure><img src="data:image/jpeg;base64,{b64}" loading="lazy">'
            f'<figcaption>{name} · <b>{n_pos}</b> pos '
            f'<span class="h">{n_hard} hard</span><br>{cap}</figcaption></figure>')
    grid_path.parent.mkdir(parents=True, exist_ok=True)
    grid_path.write_text(
        "<!doctype html><meta charset='utf-8'>"
        f"<title>S.2 — {dataset_id} (n={len(cells)})</title>"
        "<style>body{font:13px system-ui;background:#111;color:#ddd;margin:16px}"
        "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:10px}"
        "figure{margin:0;background:#1c1c1c;padding:6px;border-radius:6px}"
        "img{max-width:100%;display:block}figcaption{padding-top:4px;color:#9a9}"
        ".h{color:#fa2}</style>"
        f"<h1>Inspection S.2 — {dataset_id}</h1>"
        "<p>bboxes : <span style='color:#f44'>positifs (coverage ≥ 25 %)</span> · "
        "<span style='color:#fa2'>hard (10-25 %, ignorés à l'entraînement)</span></p>"
        f"<main>{''.join(cells)}</main>")
    print(f"[grid] -> {grid_path}")


# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path,
                    default=Path(__file__).parent / "config_v1.yaml")
    ap.add_argument("--n", type=int, default=100, help="nombre de scènes")
    ap.add_argument("--dataset-id", default=None, help="défaut: config dataset_id")
    ap.add_argument("--out", type=Path, default=None,
                    help="défaut: data/processed/<dataset_id>")
    ap.add_argument("--seed", type=int, default=None, help="surcharge master_seed")
    ap.add_argument("--blender", default=DEFAULT_BLENDER)
    ap.add_argument("--batch-size", type=int, default=None)
    ap.add_argument("--grid", type=Path, default=None,
                    help="défaut: ml/synth_val_grid.html")
    ap.add_argument("--no-grid", action="store_true")
    ap.add_argument("--grid-only", action="store_true",
                    help="ne génère pas, reconstruit la grille + summary")
    ap.add_argument("--no-postprocess", action="store_true",
                    help="debug S.3 : garde les PNG bruts, pas de pipeline capteur")
    args = ap.parse_args()

    cfg = yaml.safe_load(args.config.read_text())
    dataset_id = args.dataset_id or cfg["dataset_id"]
    out_dir = args.out or REPO_ROOT / "data" / "processed" / dataset_id
    run_dir = out_dir / "run"
    master_seed = args.seed if args.seed is not None else cfg["master_seed"]

    rng = random.Random(master_seed)
    scenes = [{"index": i, "seed": rng.randrange(2**31),
               "name": f"{dataset_id}_{i:05d}"} for i in range(args.n)]

    wall_s = 0.0
    post_stats: dict | None = None
    if not args.grid_only:
        parts_pool = build_parts_pool(cfg)
        palette = load_palette(cfg)
        hdris, textures, models = load_assets(cfg)
        job_base = {
            "config": cfg, "dataset_id": dataset_id, "out_dir": str(out_dir),
            "run_dir": str(run_dir), "generator": generator_meta(args.config),
            "parts_pool": parts_pool, "palette": palette, "hdris": hdris,
            "textures": textures, "distractor_models": models,
            "master_seed": master_seed,
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir(parents=True, exist_ok=True)
        wall_s = run_batches(cfg, args, scenes, job_base, out_dir, run_dir)

        # S.3 : post-process capteur (APRÈS labels — étape post-batch)
        if cfg.get("postprocess", {}).get("enabled") and not args.no_postprocess:
            from postprocess import process_dataset
            post_stats = process_dataset(out_dir, cfg["postprocess"])

    summary = check_and_summarize(cfg, scenes, out_dir, wall_s, post_stats)
    (run_dir if run_dir.exists() else out_dir).mkdir(parents=True, exist_ok=True)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=1,
                                                     ensure_ascii=False))
    print(json.dumps(summary["stats"], indent=1, ensure_ascii=False))
    print(f"[check] {len(summary['errors'])} erreurs d'auto-contrôle")
    for e in summary["errors"][:20]:
        print(f"  - {e}")
    th = summary["throughput"]
    print(f"[throughput] {th['s_per_image_wall']} s/image rendu (mur, relances "
          f"incluses) + {th['s_per_image_postprocess']} s/image post = "
          f"{th['s_per_image_total']} s/image total ; "
          f"projection 10 k = {th['projection_10k_h_wall']} h")

    if not args.no_grid:
        grid = args.grid or REPO_ROOT / "ml" / "synth_val_grid.html"
        build_grid(out_dir, grid, dataset_id)

    if summary["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
