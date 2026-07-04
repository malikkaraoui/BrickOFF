"""CH-1 jalon 1.1 — Contrôle d'intégrité du dataset HF legobricks (format parquet).

Les images sont embarquées dans les fichiers parquet (colonnes image/label) :
on vérifie le nombre total d'exemples, la distribution par classe, et la
décodabilité d'un échantillon d'images par fichier. Complète dataset_stats.json.
"""

from __future__ import annotations

import argparse
import io
import json
import random
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path,
                        default=REPO_ROOT / "data" / "raw" / "legobricks_hf")
    parser.add_argument("--sample-per-file", type=int, default=50,
                        help="images décodées par fichier parquet (contrôle par échantillon)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "data" / "manifests")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    files = sorted(args.dataset_dir.rglob("*.parquet"))
    if not files:
        print("aucun parquet trouvé", file=sys.stderr)
        sys.exit(1)

    total = 0
    per_class: dict[str, int] = defaultdict(int)
    decode_fail: list[str] = []
    sampled = 0
    image_col = label_col = None

    for i, f in enumerate(files):
        table = pq.read_table(f)
        cols = table.column_names
        if image_col is None:
            image_col = next(c for c in cols if "image" in c.lower() or "img" in c.lower())
            label_col = next(c for c in cols if "label" in c.lower() or "class" in c.lower())
        n = table.num_rows
        total += n
        for label, count in zip(*_value_counts(table, label_col)):
            per_class[str(label)] += count
        for idx in rng.sample(range(n), min(args.sample_per_file, n)):
            cell = table.column(image_col)[idx].as_py()
            data = cell["bytes"] if isinstance(cell, dict) else cell
            sampled += 1
            try:
                with Image.open(io.BytesIO(data)) as im:
                    im.verify()
            except Exception:
                decode_fail.append(f"{f.name}#{idx}")
        print(f"  [{i + 1}/{len(files)}] {f.name}: {n} lignes", file=sys.stderr)

    counts = sorted(per_class.values())
    stats = {
        "dataset": "legobricks_hf",
        "format": "parquet (images embarquées)",
        "total_images": total,
        "sampled_decoded": sampled,
        "decode_failures": decode_fail,
        "classes": {
            "count": len(per_class),
            "images_min": counts[0],
            "images_max": counts[-1],
            "images_median": statistics.median(counts),
            "under_50_images": sorted(c for c, v in per_class.items() if v < 50),
        },
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    stats_path = args.out_dir / "dataset_stats.json"
    all_stats = json.loads(stats_path.read_text()) if stats_path.exists() else {}
    all_stats["legobricks_hf"] = stats
    stats_path.write_text(json.dumps(all_stats, indent=2, ensure_ascii=False))

    print(f"[legobricks_hf] {total} images, {len(per_class)} classes, "
          f"échantillon décodé: {sampled}, échecs: {len(decode_fail)}")
    sys.exit(0 if not decode_fail else 1)


def _value_counts(table, col: str) -> tuple[list, list]:
    import pyarrow.compute as pc

    vc = pc.value_counts(table.column(col))
    return ([v["values"] for v in vc.to_pylist()], [v["counts"] for v in vc.to_pylist()])


if __name__ == "__main__":
    main()
