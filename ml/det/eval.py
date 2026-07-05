"""CH-2 — Évaluation d'un checkpoint DET sur un split (mAP@50, rappel)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchmetrics.detection import MeanAveragePrecision
from torchvision.models.detection import ssdlite320_mobilenet_v3_large

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import LegoDetectionDataset, collate  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, default=REPO_ROOT / "ml" / "runs" / "det_v0" / "best.pt")
    parser.add_argument("--split-dir", type=Path,
                        default=REPO_ROOT / "data" / "processed" / "detection" / "test")
    parser.add_argument("--device", default="mps", choices=["mps", "cpu", "cuda"])
    parser.add_argument("--score-threshold", type=float, default=0.35,
                        help="seuil produit (contrat CH-5) pour le rappel opérationnel")
    args = parser.parse_args()

    device = torch.device(args.device)
    model = ssdlite320_mobilenet_v3_large(weights=None, num_classes=2)
    model.load_state_dict(torch.load(args.weights, map_location="cpu"))
    model.to(device).eval()

    ds = LegoDetectionDataset(args.split_dir, train=False)
    dl = DataLoader(ds, batch_size=16, collate_fn=collate, num_workers=2)

    metric = MeanAveragePrecision(iou_thresholds=[0.5])
    tp = fn = 0  # rappel opérationnel au seuil produit (IoU 0.5)
    with torch.no_grad():
        for images, targets in dl:
            preds = model([i.to(device) for i in images])
            preds = [{k: v.cpu() for k, v in p.items()} for p in preds]
            metric.update(preds, list(targets))
            for p, t in zip(preds, targets):
                keep = p["scores"] >= args.score_threshold
                boxes = p["boxes"][keep]
                for gt in t["boxes"]:
                    if len(boxes) == 0:
                        fn += 1
                        continue
                    x1 = torch.maximum(boxes[:, 0], gt[0]); y1 = torch.maximum(boxes[:, 1], gt[1])
                    x2 = torch.minimum(boxes[:, 2], gt[2]); y2 = torch.minimum(boxes[:, 3], gt[3])
                    inter = (x2 - x1).clamp(0) * (y2 - y1).clamp(0)
                    union = ((boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
                             + (gt[2] - gt[0]) * (gt[3] - gt[1]) - inter)
                    (tp, fn) = (tp + 1, fn) if float((inter / union).max()) >= 0.5 else (tp, fn + 1)

    m = metric.compute()
    out = {
        "split": str(args.split_dir), "weights": str(args.weights),
        "n_images": len(ds), "map50": round(float(m["map_50"]), 4),
        "mar100": round(float(m["mar_100"]), 4),
        "recall_at_threshold": round(tp / (tp + fn), 4) if (tp + fn) else None,
        "score_threshold": args.score_threshold,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
