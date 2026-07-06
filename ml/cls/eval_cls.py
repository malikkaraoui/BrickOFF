"""CH-2 jalon 2.2 — Évaluation CLS : top-1/top-5, 20 pires classes, paires confondues.

Évalue un checkpoint sur un split donné d'une source donnée :
- legobricks (rendus parquet), ou gdansk_photos / gdansk_renders (ImageFolder).
La matrice de confusion est condensée (comptage épars des paires vrai->prédit
hors diagonale) — livrable "paires confondues" du doc 03 jalon 2.2 et entrée
du diagnostic classes confusables (doc 14 §2.3).

Sortie : JSON sur stdout + <out>/eval_cls_<source>_<split>.json.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision.models import mobilenet_v3_large

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import (GdanskFolder, LegoBricksParquet, load_or_build_index,  # noqa: E402
                     rows_for_split, sample_rows_by_rowgroup)

REPO_ROOT = Path(__file__).resolve().parents[2]


def build_dataset(args: argparse.Namespace, classes: dict[str, int], splits: dict):
    if args.source == "legobricks":
        index = load_or_build_index(args.legobricks)
        rows = rows_for_split(index, splits, args.split)
        if args.limit:
            from dataset import _flatten_index
            file_of_row, rg_of_row, _, _ = _flatten_index(index)
            rows = sample_rows_by_rowgroup(rows, rg_of_row, file_of_row,
                                           args.limit, args.seed)
        return LegoBricksParquet(args.legobricks, rows=sorted(rows), train=False,
                                 index=index)
    subset = args.source.removeprefix("gdansk_")
    return GdanskFolder(args.gdansk, classes, subset=subset, split=args.split,
                        splits=splits, train=False, limit=args.limit, seed=args.seed)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--source", default="legobricks",
                        choices=["legobricks", "gdansk_photos", "gdansk_renders"])
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    parser.add_argument("--legobricks", type=Path,
                        default=REPO_ROOT / "data" / "raw" / "legobricks_hf" / "data")
    parser.add_argument("--gdansk", type=Path,
                        default=REPO_ROOT / "data" / "raw" / "gdansk_cls")
    parser.add_argument("--classes", type=Path,
                        default=REPO_ROOT / "data" / "manifests" / "classes_cls_v0.json")
    parser.add_argument("--splits", type=Path,
                        default=REPO_ROOT / "data" / "manifests" / "splits_cls.json")
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="mps", choices=["mps", "cpu", "cuda"])
    parser.add_argument("--worst", type=int, default=20)
    parser.add_argument("--pairs", type=int, default=30)
    parser.add_argument("--min-class-n", type=int, default=5,
                        help="effectif minimal pour figurer dans les pires classes")
    parser.add_argument("--out", type=Path, default=None,
                        help="dossier de sortie (défaut : dossier du checkpoint)")
    args = parser.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device(args.device)

    classes: dict[str, int] = json.loads(args.classes.read_text())["classes"]
    part_of = {i: p for p, i in classes.items()}
    splits: dict = json.loads(args.splits.read_text())
    ds = build_dataset(args, classes, splits)
    if len(ds) == 0:
        raise SystemExit(f"split vide : {args.source}/{args.split}")
    dl = DataLoader(ds, batch_size=args.batch, num_workers=2)

    model = mobilenet_v3_large(weights=None)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, len(classes))
    model.load_state_dict(torch.load(args.weights, map_location="cpu"))
    model = model.to(device).eval()

    top1 = top5 = n = 0
    per_class: dict[int, list[int]] = defaultdict(lambda: [0, 0])  # [correct, total]
    confused: Counter = Counter()
    with torch.no_grad():
        for images, labels in dl:
            logits = model(images.to(device))
            labels = labels.to(device)
            _, pred5 = logits.topk(5, dim=1)
            hits = pred5.eq(labels.unsqueeze(1))
            top1 += int(hits[:, 0].sum())
            top5 += int(hits.any(dim=1).sum())
            n += len(labels)
            for true, pred in zip(labels.tolist(), pred5[:, 0].tolist()):
                per_class[true][1] += 1
                if pred == true:
                    per_class[true][0] += 1
                else:
                    confused[(true, pred)] += 1

    worst = sorted(((c, ok / tot, tot) for c, (ok, tot) in per_class.items()
                    if tot >= args.min_class_n), key=lambda x: (x[1], -x[2]))
    report = {
        "weights": str(args.weights), "source": args.source, "split": args.split,
        "n": n, "num_classes_seen": len(per_class),
        "top1": round(top1 / n, 4), "top5": round(top5 / n, 4),
        "worst_classes": [{"part_id": part_of[c], "top1": round(acc, 4), "n": tot}
                          for c, acc, tot in worst[:args.worst]],
        "confused_pairs": [{"true": part_of[t], "pred": part_of[p], "count": k}
                           for (t, p), k in confused.most_common(args.pairs)],
    }
    out_dir = args.out or args.weights.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"eval_cls_{args.source}_{args.split}.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"-> {out_path}", flush=True)


if __name__ == "__main__":
    main()
