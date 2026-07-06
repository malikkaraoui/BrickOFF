"""S.0 — Conversion export Label Studio (JSON) → labels YOLO + flags hard + manifest.

Format de sortie IDENTIQUE au synthétique (ml/synth) et lu par ml/det/dataset.py :
  data/processed/realworld_piles/{decision,holdout}/labels/<stem>.txt
    0 cx cy w h            # pièce >= 25 % visible (positif)
    # hard 0 cx cy w h     # pièce 10-25 % visible (ni positif ni faux négatif)

Entrée : export Label Studio au format **JSON** (pas JSON-MIN) — liste de tâches avec
leurs "annotations". Le flag hard vient de la checkbox per-region "hard" du config XML
(résultat "choices" portant le même id de région que la bbox).

Usage :
    python ml/annotation/labelstudio_to_yolo.py --export export_decision.json
    python ml/annotation/labelstudio_to_yolo.py --export export_holdout.json
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
CONVENTION = "data/manifests/annotation_convention.md v1 (bbox si >=25% visible ; 10-25% -> flag hard)"


def image_relpath(task: dict) -> str:
    """'/data/local-files/?d=decision/images/x.jpg' -> 'decision/images/x.jpg'."""
    url = task["data"].get("image", "")
    if "?d=" in url:
        return unquote(parse_qs(urlparse(url).query)["d"][0])
    return unquote(urlparse(url).path).lstrip("/")


def pick_annotation(task: dict) -> dict | None:
    """Dernière annotation non annulée (skip = was_cancelled)."""
    anns = [a for a in task.get("annotations", []) if not a.get("was_cancelled")]
    return anns[-1] if anns else None


def extract_boxes(annotation: dict) -> list[dict]:
    """Regroupe les résultats par id de région : bbox 'rectanglelabels' + choix 'hard'."""
    regions: dict[str, dict] = defaultdict(dict)
    for res in annotation.get("result", []):
        rid = res.get("id", "")
        if res.get("type") == "rectanglelabels":
            regions[rid]["value"] = res["value"]
        elif res.get("type") == "choices" and "hard" in res["value"].get("choices", []):
            regions[rid]["hard"] = True
    boxes = []
    for rid, reg in regions.items():
        v = reg.get("value")
        if v is None:  # choix orphelin (région supprimée) — ignoré
            continue
        if v.get("rotation", 0) not in (0, 0.0):
            print(f"  ⚠️  bbox avec rotation != 0 (région {rid}) : rotation ignorée, "
                  "à corriger dans Label Studio (dessiner sans rotation).")
        # Label Studio : x, y, width, height en % de l'image -> YOLO normalisé
        cx = (v["x"] + v["width"] / 2) / 100
        cy = (v["y"] + v["height"] / 2) / 100
        w, h = v["width"] / 100, v["height"] / 100
        cx, cy = min(max(cx, 0.0), 1.0), min(max(cy, 0.0), 1.0)
        w, h = min(max(w, 0.0), 1.0), min(max(h, 0.0), 1.0)
        boxes.append({"cx": cx, "cy": cy, "w": w, "h": h,
                      "hard": bool(reg.get("hard", False)), "region_id": rid})
    return boxes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--export", type=Path, required=True,
                        help="export Label Studio au format JSON (liste de tâches)")
    parser.add_argument("--out-dir", type=Path,
                        default=REPO_ROOT / "data" / "processed" / "realworld_piles",
                        help="racine contenant {decision,holdout}/images ; les labels "
                             "sont écrits à côté ({split}/labels/)")
    args = parser.parse_args()

    tasks = json.loads(args.export.read_text())
    if not isinstance(tasks, list):
        raise SystemExit("Export inattendu : liste de tâches requise (format JSON, pas JSON-MIN).")

    per_split: dict[str, list[dict]] = defaultdict(list)
    n_skipped = 0
    for task in tasks:
        rel = image_relpath(task)  # ex : decision/images/session_01__IMG_0001.jpg
        parts = Path(rel).parts
        split = parts[0] if parts and parts[0] in ("decision", "holdout") else "decision"
        stem = Path(rel).stem
        if not (args.out_dir / split / "images" / (stem + ".jpg")).exists():
            print(f"  ⚠️  image absente de {split}/images/ : {rel} (labels écrits quand même)")
        ann = pick_annotation(task)
        if ann is None:
            n_skipped += 1
            print(f"  ⚠️  tâche sans annotation (non annotée ou skippée) : {rel}")
            continue
        boxes = extract_boxes(ann)
        lines = []
        for b in boxes:  # positifs d'abord, hard ensuite (lignes '#' ignorées par dataset.py)
            if not b["hard"]:
                lines.append(f"0 {b['cx']:.6f} {b['cy']:.6f} {b['w']:.6f} {b['h']:.6f}")
        for b in boxes:
            if b["hard"]:
                lines.append(f"# hard 0 {b['cx']:.6f} {b['cy']:.6f} {b['w']:.6f} {b['h']:.6f}")
        label_path = args.out_dir / split / "labels" / (stem + ".txt")
        label_path.parent.mkdir(parents=True, exist_ok=True)
        label_path.write_text("\n".join(lines) + ("\n" if lines else ""))
        per_split[split].append({
            "image": rel, "label": f"{split}/labels/{stem}.txt",
            "n_pos": sum(1 for b in boxes if not b["hard"]),
            "n_hard": sum(1 for b in boxes if b["hard"]),
            "lead_time_s": round(ann.get("lead_time") or 0.0, 1),
        })

    for split, recs in sorted(per_split.items()):
        images_dir = args.out_dir / split / "images"
        labelled = {Path(r["image"]).stem for r in recs}
        missing = sorted(p.stem for p in images_dir.glob("*.jpg")
                         if p.stem not in labelled) if images_dir.is_dir() else []
        manifest = {
            "dataset_id": "realworld_piles_v1",
            "split": split,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "convention": CONVENTION,
            "labelstudio_export": args.export.name,
            "n_images_labelled": len(recs),
            "n_pos_total": sum(r["n_pos"] for r in recs),
            "n_hard_total": sum(r["n_hard"] for r in recs),
            "mean_lead_time_s": round(sum(r["lead_time_s"] for r in recs) / len(recs), 1)
            if recs else None,
            "images_without_labels": missing,
            "images": recs,
        }
        path = args.out_dir / f"manifest_annotations_{split}.json"
        path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
        print(f"[{split}] {len(recs)} images → labels ; "
              f"{manifest['n_pos_total']} positifs + {manifest['n_hard_total']} hard ; "
              f"manifest : {path}")
        if missing:
            print(f"  ⚠️  {len(missing)} image(s) de {split}/images sans label : "
                  f"{', '.join(missing[:5])}{'…' if len(missing) > 5 else ''}")
    if n_skipped:
        print(f"⚠️  {n_skipped} tâche(s) sans annotation dans l'export.")
    if not per_split:
        raise SystemExit("Aucune annotation convertie.")


if __name__ == "__main__":
    main()
