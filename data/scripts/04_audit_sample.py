"""CH-2 jalon 2.0 (doc 14 Phase 1) — Grille HTML d'audit visuel d'un échantillon de dataset.

Tire N images au hasard (seed fixé), dessine les bboxes si des annotations VOC existent,
et produit une page HTML autonome (vignettes embarquées en base64) pour inspection
humaine/IA. Sert à mesurer : % annotations fausses, % images "studio" vs réalistes,
diversité des angles. Verdict consigné ensuite dans ml/AUDIT_DATASET.md.
"""

from __future__ import annotations

import argparse
import base64
import io
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
THUMB = 320


def voc_boxes(xml_path: Path) -> list[tuple[int, int, int, int]]:
    root = ET.parse(xml_path).getroot()
    out = []
    for obj in root.iter("object"):
        b = obj.find("bndbox")
        out.append(tuple(int(float(b.find(k).text)) for k in ("xmin", "ymin", "xmax", "ymax")))
    return out


def thumb_b64(img_path: Path, boxes: list) -> tuple[str, int]:
    with Image.open(img_path) as im:
        im = im.convert("RGB")
        if boxes:
            draw = ImageDraw.Draw(im)
            for x1, y1, x2, y2 in boxes:
                draw.rectangle([x1, y1, x2, y2], outline=(255, 40, 40), width=max(2, im.width // 400))
        ratio = THUMB / max(im.size)
        im = im.resize((max(1, int(im.width * ratio)), max(1, int(im.height * ratio))))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode(), len(boxes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--annotations-dir", type=Path, default=None,
                        help="dossier des XML VOC (si dataset de détection)")
    parser.add_argument("--sample", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    images = [p for p in sorted(args.dataset_dir.rglob("*"))
              if p.suffix.lower() in IMAGE_EXTS and p.is_file()]
    if not images:
        print("aucune image", file=sys.stderr)
        sys.exit(1)
    rng = random.Random(args.seed)
    sample = rng.sample(images, min(args.sample, len(images)))

    cells = []
    for i, img in enumerate(sample, 1):
        boxes = []
        xml = (args.annotations_dir / (img.stem + ".xml")) if args.annotations_dir \
            else img.with_suffix(".xml")  # gdansk: XML colocalisé avec l'image
        if xml.exists():
            boxes = voc_boxes(xml)
        b64, nb = thumb_b64(img, boxes)
        rel = img.relative_to(args.dataset_dir)
        cells.append(
            f'<figure><img src="data:image/jpeg;base64,{b64}" loading="lazy">'
            f'<figcaption>#{i} · {rel}<br>{nb} bbox</figcaption></figure>')
        if i % 100 == 0:
            print(f"  … {i}/{len(sample)}", file=sys.stderr)

    name = args.dataset_dir.name
    out = args.out or REPO_ROOT / "ml" / f"audit_grid_{name}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "<!doctype html><meta charset='utf-8'>"
        f"<title>Audit {name} (n={len(sample)}, seed={args.seed})</title>"
        "<style>body{font:13px system-ui;background:#111;color:#ddd;margin:16px}"
        "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:10px}"
        "figure{margin:0;background:#1c1c1c;padding:6px;border-radius:6px}"
        "img{max-width:100%;display:block}figcaption{padding-top:4px;color:#9a9}</style>"
        f"<h1>Audit visuel — {name}</h1><p>n={len(sample)} / {len(images)} images, seed={args.seed}</p>"
        f"<main>{''.join(cells)}</main>")
    print(f"grille -> {out}")


if __name__ == "__main__":
    main()
