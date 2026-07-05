"""CH-2 jalon 2.1 — Baseline DET v0 : SSDLite320-MobileNetV3, mono-classe "lego_piece".

Rôle de cette baseline (doc 14 Phase 2) : localiser le problème (data ? domain gap ?),
PAS la performance finale. Le framework de production (YOLOX/RT-DETR, D02) reste choisi
en CH-0 0.3 ; SSDLite (torchvision, BSD-3) est retenu ici pour sa compatibilité MPS
immédiate — écart consigné dans CHANGELOG_CH2.md.

Reproductible : seeds fixés, config sur la ligne de commande, métriques JSON par epoch.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchmetrics.detection import MeanAveragePrecision
from torchvision.models.detection import ssdlite320_mobilenet_v3_large

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import LegoDetectionDataset, collate  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def seed_all(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)


def evaluate(model, loader, device) -> dict:
    metric = MeanAveragePrecision(iou_thresholds=[0.5], class_metrics=False)
    model.eval()
    with torch.no_grad():
        for images, targets in loader:
            preds = model([i.to(device) for i in images])
            metric.update([{k: v.cpu() for k, v in p.items()} for p in preds], list(targets))
    m = metric.compute()
    return {"map50": float(m["map_50"]), "mar100": float(m["mar_100"])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=REPO_ROOT / "data" / "processed" / "detection")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--device", default="mps", choices=["mps", "cpu", "cuda"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit", type=int, default=None, help="sous-échantillon (smoke test)")
    parser.add_argument("--aug", default="light", choices=["light", "strong"])
    parser.add_argument("--val-photos-only", action="store_true",
                        help="early stopping sur les photos réelles seules (la val mélangée est gonflée par les rendus)")
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "ml" / "runs" / "det_v0")
    args = parser.parse_args()

    seed_all(args.seed)
    device = torch.device(args.device)
    args.out.mkdir(parents=True, exist_ok=True)

    train_ds = LegoDetectionDataset(args.data / "train", train=True, limit=args.limit, aug=args.aug)
    val_ds = LegoDetectionDataset(args.data / "val", train=False,
                                  limit=max(50, args.limit // 4) if args.limit else None,
                                  photos_only=args.val_photos_only)
    train_dl = DataLoader(train_ds, batch_size=args.batch, shuffle=True,
                          collate_fn=collate, num_workers=4, persistent_workers=True)
    val_dl = DataLoader(val_ds, batch_size=args.batch, collate_fn=collate,
                        num_workers=2, persistent_workers=True)

    # 2 classes = fond + lego_piece (convention torchvision)
    model = ssdlite320_mobilenet_v3_large(weights=None, weights_backbone="DEFAULT",
                                          num_classes=2).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)

    history, best_map, best_epoch = [], -1.0, -1
    config = {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()}
    (args.out / "config.json").write_text(json.dumps(
        config | {"model": "ssdlite320_mobilenet_v3_large", "started_at":
                  datetime.now(timezone.utc).isoformat()}, indent=2))

    for epoch in range(args.epochs):
        model.train()
        t0, total_loss = time.time(), 0.0
        for images, targets in train_dl:
            images = [i.to(device) for i in images]
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
            loss = sum(model(images, targets).values())
            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += float(loss)
        sched.step()
        metrics = evaluate(model, val_dl, device)
        row = {"epoch": epoch, "loss": total_loss / len(train_dl),
               "epoch_seconds": round(time.time() - t0, 1)} | metrics
        history.append(row)
        (args.out / "history.json").write_text(json.dumps(history, indent=2))
        print(json.dumps(row), flush=True)
        if metrics["map50"] > best_map:
            best_map, best_epoch = metrics["map50"], epoch
            torch.save(model.state_dict(), args.out / "best.pt")
        elif epoch - best_epoch >= args.patience:
            print(f"early stopping (pas d'amélioration depuis {args.patience} epochs)", flush=True)
            break

    print(f"best mAP@50={best_map:.4f} (epoch {best_epoch}) -> {args.out}/best.pt", flush=True)


if __name__ == "__main__":
    main()
