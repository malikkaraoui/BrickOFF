"""CH-1 jalon 1.3 — Conversion détection : gdansk_det VOC → format YOLO mono-classe.

Recommandations d'audit appliquées (ml/AUDIT_DATASET.md) :
- les fichiers portant le marqueur "-test" (split de test du dataset d'origine) restent en test ;
- le reste est réparti train/val par image source (pas de fuite : une image = un seul split) ;
- les bboxes touchant le bord de l'image sont comptées et tracées (pas exclues : le modèle doit
  apprendre les pièces partiellement cadrées).
Un auto-contrôle d'aller-retour (YOLO → pixels vs VOC d'origine) valide chaque conversion.
Les images sont liées en symlink (pas de copie : ~6 Go économisés, source en lecture seule).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
EDGE_TOL = 2  # px : bbox à moins de 2 px du bord = "au bord"


def voc_parse(xml_path: Path) -> tuple[int, int, list[tuple[float, float, float, float]]]:
    root = ET.parse(xml_path).getroot()
    size = root.find("size")
    w, h = int(size.find("width").text), int(size.find("height").text)
    boxes = []
    for obj in root.iter("object"):
        b = obj.find("bndbox")
        boxes.append(tuple(float(b.find(k).text) for k in ("xmin", "ymin", "xmax", "ymax")))
    return w, h, boxes


def to_yolo(w: int, h: int, box: tuple[float, float, float, float]) -> tuple[float, ...]:
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2 / w, (y1 + y2) / 2 / h, (x2 - x1) / w, (y2 - y1) / h)


def roundtrip_ok(w: int, h: int, box: tuple, yolo: tuple, tol: float = 1.0) -> bool:
    cx, cy, bw, bh = yolo
    rx1, ry1 = (cx - bw / 2) * w, (cy - bh / 2) * h
    rx2, ry2 = (cx + bw / 2) * w, (cy + bh / 2) * h
    return all(abs(a - b) <= tol for a, b in zip(box, (rx1, ry1, rx2, ry2)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=REPO_ROOT / "data" / "raw" / "gdansk_det")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "data" / "processed" / "detection")
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.out.exists() and any(args.out.iterdir()) and not args.force:
        print("déjà converti -> skip (--force pour refaire)")
        return

    images = [p for p in sorted(args.source.rglob("*"))
              if p.suffix.lower() in IMAGE_EXTS and p.with_suffix(".xml").exists()]
    if not images:
        print("aucune paire image/xml", file=sys.stderr)
        sys.exit(1)

    rng = random.Random(args.seed)
    splits: dict[str, list[Path]] = {"train": [], "val": [], "test": []}
    for img in images:
        if "-test" in img.stem:
            splits["test"].append(img)
    rest = [i for i in images if "-test" not in i.stem]
    rng.shuffle(rest)
    n_val = round(len(rest) * args.val_ratio)
    splits["val"] = rest[:n_val]
    splits["train"] = rest[n_val:]

    stats = Counter()
    edge_boxes: list[str] = []
    manifest: dict[str, list[str]] = {}
    for split, imgs in splits.items():
        img_dir = args.out / split / "images"
        lbl_dir = args.out / split / "labels"
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)
        manifest[split] = []
        for img in imgs:
            w, h, boxes = voc_parse(img.with_suffix(".xml"))
            lines = []
            for box in boxes:
                yolo = to_yolo(w, h, box)
                if not roundtrip_ok(w, h, box, yolo):
                    print(f"ÉCHEC aller-retour: {img}", file=sys.stderr)
                    sys.exit(1)
                if box[0] <= EDGE_TOL or box[1] <= EDGE_TOL or box[2] >= w - EDGE_TOL or box[3] >= h - EDGE_TOL:
                    edge_boxes.append(str(img.relative_to(args.source)))
                lines.append("0 " + " ".join(f"{v:.6f}" for v in yolo))
            # nom unique : sous-dossier + nom (évite les collisions entre dossiers 1..32)
            uniq = f"{img.parent.parent.name}_{img.parent.name}_{img.name}"
            link = img_dir / uniq
            if not link.exists():
                link.symlink_to(img.resolve())
            (lbl_dir / (Path(uniq).stem + ".txt")).write_text("\n".join(lines) + "\n")
            manifest[split].append(str(img.relative_to(args.source)))
            stats[split] += 1
            stats[f"{split}_boxes"] += len(boxes)

    out_manifest = {
        "source": str(args.source.relative_to(REPO_ROOT)),
        "seed": args.seed,
        "val_ratio": args.val_ratio,
        "rule": "-test dans le nom -> test (split d'origine préservé) ; reste: train/val seedé",
        "counts": dict(stats),
        "edge_box_images": sorted(set(edge_boxes)),
        "converted_at": datetime.now(timezone.utc).isoformat(),
        "files": manifest,
    }
    mpath = REPO_ROOT / "data" / "manifests" / "splits_detection.json"
    mpath.write_text(json.dumps(out_manifest, indent=2, ensure_ascii=False))
    print(f"train {stats['train']} / val {stats['val']} / test {stats['test']} images "
          f"({stats['train_boxes']}/{stats['val_boxes']}/{stats['test_boxes']} boxes), "
          f"{len(set(edge_boxes))} images avec bbox au bord")
    print(f"manifest -> {mpath}")


if __name__ == "__main__":
    main()
