"""CH-1 jalon 1.1 — Contrôle d'intégrité des données brutes.

Vérifie : images ouvrables (PIL.verify), doublons exacts (hash MD5 du contenu),
distribution par classe. Produit data/manifests/dataset_stats.json.
Critères d'acceptation : 100 % d'images ouvrables ; doublons listés ; distribution
par classe documentée (min/max/médiane) ; classes < 50 images flaggées.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def md5_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        while data := f.read(chunk):
            h.update(data)
    return h.hexdigest()


def check_tree(root: Path, class_from_parent: bool) -> dict:
    """Parcourt un dataset ; la classe est le nom du dossier parent si class_from_parent."""
    corrupt: list[str] = []
    hashes: dict[str, list[str]] = defaultdict(list)
    per_class: dict[str, int] = defaultdict(int)
    resolutions: dict[str, int] = defaultdict(int)
    total = 0

    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in IMAGE_EXTS or not path.is_file():
            continue
        total += 1
        rel = str(path.relative_to(root))
        try:
            with Image.open(path) as im:
                im.verify()
            with Image.open(path) as im:
                resolutions[f"{im.width}x{im.height}"] += 1
        except Exception:
            corrupt.append(rel)
            continue
        hashes[md5_of(path)].append(rel)
        if class_from_parent:
            per_class[path.parent.name] += 1
        if total % 20000 == 0:
            print(f"  … {total} images", file=sys.stderr)

    duplicates = {h: files for h, files in hashes.items() if len(files) > 1}
    counts = sorted(per_class.values())
    stats: dict = {
        "total_images": total,
        "corrupt": corrupt,
        "corrupt_count": len(corrupt),
        "duplicate_groups": len(duplicates),
        "duplicate_files": sum(len(v) - 1 for v in duplicates.values()),
        "top_resolutions": dict(sorted(resolutions.items(), key=lambda kv: -kv[1])[:10]),
    }
    if per_class:
        under_50 = sorted(c for c, n in per_class.items() if n < 50)
        stats["classes"] = {
            "count": len(per_class),
            "images_min": counts[0],
            "images_max": counts[-1],
            "images_median": statistics.median(counts),
            "under_50_images": under_50,
            "under_50_count": len(under_50),
        }
    # Les listes complètes de doublons partent dans un fichier dédié (volumineux)
    stats["_duplicates_detail_file"] = "duplicates_detail.json"
    return stats, duplicates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, required=True,
                        help="ex: data/raw/legobricks_hf ou data/raw/gdansk_cls")
    parser.add_argument("--classes-from-dirs", action="store_true",
                        help="la classe = nom du dossier parent (format ImageFolder)")
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "data" / "manifests")
    args = parser.parse_args()

    name = args.dataset_dir.name
    print(f"[{name}] scan de {args.dataset_dir}…")
    stats, duplicates = check_tree(args.dataset_dir, args.classes_from_dirs)
    stats["dataset"] = name
    stats["checked_at"] = datetime.now(timezone.utc).isoformat()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stats_path = args.out_dir / "dataset_stats.json"
    all_stats = json.loads(stats_path.read_text()) if stats_path.exists() else {}
    all_stats[name] = stats
    stats_path.write_text(json.dumps(all_stats, indent=2, ensure_ascii=False))
    (args.out_dir / f"duplicates_{name}.json").write_text(
        json.dumps(duplicates, indent=2, ensure_ascii=False))

    ok = not stats["corrupt_count"]
    print(f"[{name}] {stats['total_images']} images | corrompues: {stats['corrupt_count']} "
          f"| groupes de doublons: {stats['duplicate_groups']}")
    print(f"Stats -> {stats_path}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
