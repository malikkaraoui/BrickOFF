"""S.0 — Aides à l'annotation par agents visuels.

render : dessine sur l'image les boîtes @0.20 (rouges, ids K#) et les candidates
@0.05 non redondantes (cyan, ids C#) → l'agent choisit par identifiant, les
coordonnées restent celles du détecteur (précision pixel).
apply  : compile les verdicts JSON des agents en labels YOLO finaux (+ flags hard)
         selon la convention data/manifests/annotation_convention.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
# BASE surchargeable pour d'autres corpus (ex. batch 2) via $BRICKOFF_PILES_BASE
import os
BASE = Path(os.environ.get("BRICKOFF_PILES_BASE",
                           REPO_ROOT / "data" / "processed" / "realworld_piles"))
IMAGES = BASE / "decision" / "images"
LS = BASE / "labelstudio"


def load_boxes(image_name: str) -> tuple[list, list]:
    """Retourne (keep_boxes K#, candidate_boxes C#) en coords normalisées 0-1 (x,y,w,h)."""
    def extract(tasks):
        for t in tasks:
            if Path(t["data"]["image"]).name == image_name:
                out = []
                for p in t.get("predictions", []):
                    for r in p["result"]:
                        v = r["value"]
                        out.append({"x": v["x"] / 100, "y": v["y"] / 100,
                                    "w": v["width"] / 100, "h": v["height"] / 100,
                                    "score": r.get("score", p.get("score"))})
                return out
        return []

    strong = extract(json.load(open(LS / "tasks_decision.json")))
    weak_all = extract(json.load(open(LS / "candidates_low_threshold.json")))

    def iou(a, b):
        ax2, ay2 = a["x"] + a["w"], a["y"] + a["h"]
        bx2, by2 = b["x"] + b["w"], b["y"] + b["h"]
        ix = max(0, min(ax2, bx2) - max(a["x"], b["x"]))
        iy = max(0, min(ay2, by2) - max(a["y"], b["y"]))
        inter = ix * iy
        union = a["w"] * a["h"] + b["w"] * b["h"] - inter
        return inter / union if union else 0

    weak_pool = [c for c in weak_all if all(iou(c, s) < 0.5 for s in strong)]
    # NMS entre candidates (greedy par score) + plafond : lisibilité de la grille
    weak_pool.sort(key=lambda c: -(c["score"] or 0))
    weak: list = []
    for c in weak_pool:
        if all(iou(c, w) < 0.4 for w in weak):
            weak.append(c)
        if len(weak) >= 15:
            break
    return strong, weak


def render(image_name: str, out_path: Path) -> None:
    strong, weak = load_boxes(image_name)
    im = Image.open(IMAGES / image_name).convert("RGB")
    scale = 1600 / max(im.size)
    if scale < 1:
        im = im.resize((int(im.width * scale), int(im.height * scale)))
    d = ImageDraw.Draw(im)
    W, H = im.size
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
    except Exception:
        font = ImageFont.load_default()

    for i, b in enumerate(weak):
        x1, y1 = b["x"] * W, b["y"] * H
        d.rectangle([x1, y1, x1 + b["w"] * W, y1 + b["h"] * H], outline=(0, 220, 255), width=2)
        d.text((x1 + 2, y1 + 2), f"C{i}", fill=(0, 220, 255), font=font)
    for i, b in enumerate(strong):
        x1, y1 = b["x"] * W, b["y"] * H
        d.rectangle([x1, y1, x1 + b["w"] * W, y1 + b["h"] * H], outline=(255, 40, 40), width=3)
        d.text((x1 + 2, y1 + 2), f"K{i}", fill=(255, 60, 60), font=font)
    im.save(out_path)
    print(f"{out_path} | K: {len(strong)} rouges, C: {len(weak)} cyan")


def apply(verdicts_dir: Path, out_labels: Path) -> None:
    """Compile ml/annotation/verdicts/*.json -> labels YOLO + manifest.

    Format verdict par image :
    {"image": "...jpg", "keep": ["K0","K2"], "hard": ["K2","C5"],
     "add": ["C3","C5"], "manual": [{"x":..,"y":..,"w":..,"h":..,"hard":false}],
     "notes": "..."}
    (les ids absents de keep/add sont supprimés)
    """
    out_labels.mkdir(parents=True, exist_ok=True)
    stats = {"images": 0, "pos": 0, "hard": 0, "deleted": 0, "manual": 0}
    for vf in sorted(verdicts_dir.glob("*.json")):
        for v in json.load(open(vf)):
            name = v["image"]
            strong, weak = load_boxes(name)
            hard_ids = set(v.get("hard", []))
            lines = []
            kept = 0
            for ids, pool, prefix in ((v.get("keep", []), strong, "K"),
                                      (v.get("add", []), weak, "C")):
                for bid in ids:
                    b = pool[int(bid[1:])]
                    cx, cy = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
                    line = f"0 {cx:.6f} {cy:.6f} {b['w']:.6f} {b['h']:.6f}"
                    if bid in hard_ids:
                        lines.append("# hard " + line)
                        stats["hard"] += 1
                    else:
                        lines.append(line)
                        stats["pos"] += 1
                    kept += 1
            for m in v.get("manual", []):
                cx, cy = m["x"] + m["w"] / 2, m["y"] + m["h"] / 2
                line = f"0 {cx:.6f} {cy:.6f} {m['w']:.6f} {m['h']:.6f}"
                lines.append(("# hard " + line) if m.get("hard") else line)
                stats["hard" if m.get("hard") else "pos"] += 1
                stats["manual"] += 1
            stats["deleted"] += len(strong) - len(v.get("keep", []))
            stats["images"] += 1
            (out_labels / (Path(name).stem + ".txt")).write_text("\n".join(lines) + "\n")
    (BASE / "manifest_annotations_decision.json").write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("image_name")
    r.add_argument("--out", type=Path, required=True)
    a = sub.add_parser("apply")
    a.add_argument("--verdicts", type=Path, default=REPO_ROOT / "ml" / "annotation" / "verdicts")
    a.add_argument("--out-labels", type=Path, default=BASE / "decision" / "labels")
    args = p.parse_args()
    if args.cmd == "render":
        render(args.image_name, args.out)
    else:
        apply(args.verdicts, args.out_labels)
