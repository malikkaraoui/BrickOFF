"""CH-2 jalon 2.2 — Manifestes CLS v0 : classes_cls_v0.json + splits_cls.json.

Stratégie v0 (consignée dans CHANGELOG_CH2.md) :
- classes = les 1000 de legobricks_hf, index = label HF d'origine (aucun remap des
  parquet nécessaire) ; gdansk_cls est mappé dessus quand le nom de dossier
  (part_id) correspond exactement — 382/448 classes gdansk dans l'intersection,
  les 66 restantes (souvent des variantes de mold, ex 3068 vs 3068b) sont
  ignorées en v0 et listées dans le manifeste.
- Splits stratifiés par classe, seedés :
  * legobricks : par ligne, 90/5/5 ;
  * gdansk : par GROUPE anti-fuite (photos = session/passage, renders = couleur),
    une classe avec < min-groups groupes part entièrement en train.

Rejouable : mêmes entrées + même seed => mêmes manifestes. --force pour réécrire.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import GdanskFolder, gdansk_group_key, load_or_build_index  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def split_legobricks(index: dict, val_frac: float, test_frac: float,
                     seed: int) -> dict:
    """Répartition stratifiée par classe, exprimée en lignes locales par fichier."""
    rows_by_class: dict[int, list[tuple[str, int]]] = defaultdict(list)
    for fname, labels in zip(index["files"], index["labels_by_file"]):
        for row, label in enumerate(labels):
            rows_by_class[label].append((fname, row))
    rng = random.Random(seed)
    out: dict = {"val": defaultdict(list), "test": defaultdict(list)}
    for label in sorted(rows_by_class):
        rows = rows_by_class[label]
        rng.shuffle(rows)
        n_val, n_test = round(len(rows) * val_frac), round(len(rows) * test_frac)
        for part, chunk in (("val", rows[:n_val]), ("test", rows[n_val:n_val + n_test])):
            for fname, row in chunk:
                out[part][fname].append(row)
    return {part: {f: sorted(r) for f, r in sorted(d.items())} for part, d in out.items()}


def split_gdansk(root: Path, classes: dict[str, int], subset: str, val_frac: float,
                 test_frac: float, min_groups: int, seed: int) -> tuple[dict, dict]:
    """Répartition par groupes anti-fuite. Retourne ({val:{cls:[groupes]}, test:...}, stats)."""
    rng = random.Random(seed)
    out: dict = {"val": {}, "test": {}}
    stats = {"images": 0, "groups": 0, "classes": 0, "classes_all_train": 0}
    base = root / subset
    for class_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        if class_dir.name not in classes:
            continue
        groups: dict[str, int] = defaultdict(int)
        for f in class_dir.iterdir():
            if f.suffix.lower() in GdanskFolder.EXTS:
                groups[gdansk_group_key(subset, f.name)] += 1
        if not groups:
            continue
        stats["classes"] += 1
        stats["groups"] += len(groups)
        total = sum(groups.values())
        stats["images"] += total
        if len(groups) < min_groups:
            stats["classes_all_train"] += 1
            continue
        names = sorted(groups)
        rng.shuffle(names)
        got, val_g, test_g = 0, [], []
        for g in names:
            if got < total * val_frac:
                val_g.append(g)
            elif got < total * (val_frac + test_frac):
                test_g.append(g)
            else:
                break
            got += groups[g]
        out["val"][class_dir.name] = sorted(val_g)
        out["test"][class_dir.name] = sorted(test_g)
    return out, stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legobricks", type=Path,
                        default=REPO_ROOT / "data" / "raw" / "legobricks_hf" / "data")
    parser.add_argument("--gdansk", type=Path,
                        default=REPO_ROOT / "data" / "raw" / "gdansk_cls")
    parser.add_argument("--out-classes", type=Path,
                        default=REPO_ROOT / "data" / "manifests" / "classes_cls_v0.json")
    parser.add_argument("--out-splits", type=Path,
                        default=REPO_ROOT / "data" / "manifests" / "splits_cls.json")
    parser.add_argument("--val-frac", type=float, default=0.05)
    parser.add_argument("--test-frac", type=float, default=0.05)
    parser.add_argument("--min-groups", type=int, default=3,
                        help="classes gdansk avec moins de groupes => tout en train")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.out_splits.exists() and not args.force:
        print(f"{args.out_splits} existe déjà (--force pour réécrire)")
        return

    index = load_or_build_index(args.legobricks)
    class_names: list[str] = index["class_names"]
    classes = {name: i for i, name in enumerate(class_names)}

    gdansk_dirs = {p.name for sub in ("photos", "renders")
                   for p in (args.gdansk / sub).iterdir() if p.is_dir()}
    inter = sorted(gdansk_dirs & set(classes))
    outside = sorted(gdansk_dirs - set(classes))

    lb_splits = split_legobricks(index, args.val_frac, args.test_frac, args.seed)
    gd_splits, gd_stats = {}, {}
    for subset in ("photos", "renders"):
        gd_splits[subset], gd_stats[subset] = split_gdansk(
            args.gdansk, classes, subset, args.val_frac, args.test_frac,
            args.min_groups, args.seed)

    args.out_classes.parent.mkdir(parents=True, exist_ok=True)
    args.out_classes.write_text(json.dumps({
        "version": "cls_v0",
        "source": "legobricks_hf (ordre des labels HF conservé)",
        "num_classes": len(classes),
        "gdansk_intersection": {"count": len(inter), "classes": inter},
        "gdansk_outside": {"count": len(outside), "classes": outside},
        "classes": classes,
    }, indent=1))

    n_rows = sum(len(labels) for labels in index["labels_by_file"])
    args.out_splits.write_text(json.dumps({
        "version": "cls_v0", "seed": args.seed,
        "fractions": {"val": args.val_frac, "test": args.test_frac},
        "notes": {
            "legobricks": "lignes locales par fichier parquet ; train = complément",
            "gdansk": ("groupes anti-fuite par classe (photos: session token 3, "
                       "renders: couleur) ; train = complément ; classes avec "
                       f"< {args.min_groups} groupes entièrement en train"),
            "stats": {"legobricks_rows": n_rows, "gdansk": gd_stats},
        },
        "legobricks": lb_splits,
        "gdansk": gd_splits,
    }, indent=1))

    n_val = sum(len(r) for r in lb_splits["val"].values())
    n_test = sum(len(r) for r in lb_splits["test"].values())
    print(f"classes_cls_v0.json : {len(classes)} classes, intersection gdansk "
          f"{len(inter)}/{len(gdansk_dirs)} (hors mapping : {len(outside)})")
    print(f"legobricks : {n_rows} lignes -> val {n_val} / test {n_test} / "
          f"train {n_rows - n_val - n_test}")
    for subset in ("photos", "renders"):
        s = gd_stats[subset]
        print(f"gdansk {subset} : {s['images']} images, {s['groups']} groupes, "
              f"{s['classes']} classes mappées ({s['classes_all_train']} classes "
              f"entièrement en train, trop peu de groupes)")
    print(f"-> {args.out_classes}\n-> {args.out_splits}")


if __name__ == "__main__":
    main()
