"""CH-2 jalon 2.2 — Baseline CLS v0 : MobileNetV3-Large, 1000 classes part_id.

Recette (doc 03 jalon 2.2) :
- MobileNetV3-Large pré-entraîné ImageNet, tête remplacée (1000 classes CLS) ;
- phase 1 : backbone gelé, tête seule (--head-epochs, LR --lr-head) ;
- phase 2 : fine-tuning complet (LR --lr-ft, cosine) ;
- CrossEntropy label smoothing 0.1 ; top-1/top-5 par epoch dans history.json ;
- early stopping sur top-1 val legobricks ; si --gdansk est actif, top-1/top-5
  sur les photos réelles val sont AUSSI loggés (real_top1/real_top5) — le juge
  du domain gap, sans piloter l'early stopping en v0.
- --mix-real-frac f : fraction de photos gdansk réelles vues par epoch
  (0.2 = 80 synthétique / 20 réel), échantillonneur MixedRealSampler.

Reproductible : seeds fixés, config.json, history.json par epoch — même
ergonomie que ml/det/train_baseline.py.
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
from torch import nn
from torch.utils.data import ConcatDataset, DataLoader
from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import (GdanskFolder, LegoBricksParquet, MixedRealSampler,  # noqa: E402
                     RowGroupWindowSampler, build_transform, load_or_build_index,
                     rows_for_split, sample_rows_by_rowgroup)

REPO_ROOT = Path(__file__).resolve().parents[2]


def seed_all(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> dict:
    model.eval()
    top1 = top5 = n = 0
    with torch.no_grad():
        for images, labels in loader:
            logits = model(images.to(device))
            labels = labels.to(device)
            _, pred5 = logits.topk(5, dim=1)
            hits = pred5.eq(labels.unsqueeze(1))
            top1 += int(hits[:, 0].sum())
            top5 += int(hits.any(dim=1).sum())
            n += len(labels)
    return {"top1": top1 / max(n, 1), "top5": top5 / max(n, 1), "n": n}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legobricks", type=Path,
                        default=REPO_ROOT / "data" / "raw" / "legobricks_hf" / "data")
    parser.add_argument("--gdansk", type=Path,
                        default=REPO_ROOT / "data" / "raw" / "gdansk_cls")
    parser.add_argument("--no-gdansk", action="store_true",
                        help="désactive la val réelle et le mélange gdansk")
    parser.add_argument("--classes", type=Path,
                        default=REPO_ROOT / "data" / "manifests" / "classes_cls_v0.json")
    parser.add_argument("--splits", type=Path,
                        default=REPO_ROOT / "data" / "manifests" / "splits_cls.json")
    parser.add_argument("--epochs", type=int, default=50, help="total, phase 1 incluse")
    parser.add_argument("--head-epochs", type=int, default=5,
                        help="phase 1 : backbone gelé, tête seule")
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--lr-head", type=float, default=1e-3)
    parser.add_argument("--lr-ft", type=float, default=1e-4)
    parser.add_argument("--mix-real-frac", type=float, default=0.0,
                        help="fraction de photos gdansk réelles par epoch (0 = synth seul)")
    parser.add_argument("--device", default="mps", choices=["mps", "cpu", "cuda"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit", type=int, default=None,
                        help="sous-échantillon train (smoke test) — tire des row groups entiers")
    parser.add_argument("--window", type=int, default=64,
                        help="fenêtre de brassage en row groups (diversité de classes/batch)")
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "ml" / "runs" / "cls_v0")
    args = parser.parse_args()

    seed_all(args.seed)
    device = torch.device(args.device)
    args.out.mkdir(parents=True, exist_ok=True)

    classes: dict[str, int] = json.loads(args.classes.read_text())["classes"]
    splits: dict = json.loads(args.splits.read_text())
    index = load_or_build_index(args.legobricks)

    train_rows = rows_for_split(index, splits, "train")
    val_rows = rows_for_split(index, splits, "val")
    if args.limit:
        from dataset import _flatten_index
        file_of_row, rg_of_row, _, label_of_row = _flatten_index(index)
        train_rows = sample_rows_by_rowgroup(train_rows, rg_of_row, file_of_row,
                                             args.limit, args.seed)
        # val du smoke restreinte aux classes vues en train (sinon top-1 ~ 0 par
        # construction : les row groups sont quasi mono-classe)
        seen = {int(label_of_row[r]) for r in train_rows}
        val_rows = [r for r in val_rows if int(label_of_row[r]) in seen]
        val_rows = sample_rows_by_rowgroup(val_rows, rg_of_row, file_of_row,
                                           max(200, args.limit // 4), args.seed + 1)
    train_parquet = LegoBricksParquet(args.legobricks, rows=train_rows, train=True,
                                      index=index, cache_groups=args.window + 8)
    val_ds = LegoBricksParquet(args.legobricks, rows=sorted(val_rows), train=False,
                               index=index)

    parquet_sampler = RowGroupWindowSampler(train_parquet, window=args.window,
                                            seed=args.seed)
    use_gdansk = not args.no_gdansk and args.gdansk.exists()
    if args.mix_real_frac > 0:
        if not use_gdansk:
            parser.error("--mix-real-frac requiert gdansk")
        real_ds = GdanskFolder(args.gdansk, classes, subset="photos", split="train",
                               splits=splits, train=True,
                               limit=args.limit, seed=args.seed)
        train_ds: torch.utils.data.Dataset = ConcatDataset([train_parquet, real_ds])
        sampler: torch.utils.data.Sampler = MixedRealSampler(
            parquet_sampler, len(train_parquet), len(real_ds),
            args.mix_real_frac, seed=args.seed)
    else:
        train_ds, sampler = train_parquet, parquet_sampler

    real_val_dl = None
    if use_gdansk:
        real_val = GdanskFolder(args.gdansk, classes, subset="photos", split="val",
                                splits=splits, train=False,
                                limit=max(200, args.limit // 4) if args.limit else None,
                                seed=args.seed + 2)
        if len(real_val):
            real_val_dl = DataLoader(real_val, batch_size=args.batch,
                                     num_workers=min(2, args.workers))

    dl_kwargs = dict(num_workers=args.workers,
                     persistent_workers=args.workers > 0)
    train_dl = DataLoader(train_ds, batch_size=args.batch, sampler=sampler, **dl_kwargs)
    val_dl = DataLoader(val_ds, batch_size=args.batch,
                        num_workers=min(2, args.workers))

    model = mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.IMAGENET1K_V2)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, len(classes))
    model = model.to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    # phase 1 : backbone gelé
    for p in model.features.parameters():
        p.requires_grad = False
    opt = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),
                            lr=args.lr_head, weight_decay=1e-4)
    sched = None

    config = {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()}
    (args.out / "config.json").write_text(json.dumps(
        config | {"model": "mobilenet_v3_large", "num_classes": len(classes),
                  "train_size": len(train_ds), "val_size": len(val_ds),
                  "started_at": datetime.now(timezone.utc).isoformat()}, indent=2))

    history, best_top1, best_epoch = [], -1.0, -1
    for epoch in range(args.epochs):
        if epoch == args.head_epochs:  # phase 2 : fine-tuning complet
            for p in model.parameters():
                p.requires_grad = True
            opt = torch.optim.AdamW(model.parameters(), lr=args.lr_ft, weight_decay=1e-4)
            sched = torch.optim.lr_scheduler.CosineAnnealingLR(
                opt, T_max=max(1, args.epochs - args.head_epochs))
        if hasattr(sampler, "set_epoch"):
            sampler.set_epoch(epoch)
        model.train()
        t0, total_loss, n_batches = time.time(), 0.0, 0
        for images, labels in train_dl:
            loss = criterion(model(images.to(device)), labels.to(device))
            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += float(loss)
            n_batches += 1
        if sched is not None:
            sched.step()
        metrics = evaluate(model, val_dl, device)
        row = {"epoch": epoch, "phase": 1 if epoch < args.head_epochs else 2,
               "loss": total_loss / max(n_batches, 1),
               "epoch_seconds": round(time.time() - t0, 1),
               "val_top1": round(metrics["top1"], 4), "val_top5": round(metrics["top5"], 4)}
        if real_val_dl is not None:
            real = evaluate(model, real_val_dl, device)
            row |= {"real_top1": round(real["top1"], 4), "real_top5": round(real["top5"], 4)}
        history.append(row)
        (args.out / "history.json").write_text(json.dumps(history, indent=2))
        print(json.dumps(row), flush=True)
        if metrics["top1"] > best_top1:
            best_top1, best_epoch = metrics["top1"], epoch
            torch.save(model.state_dict(), args.out / "best.pt")
        elif epoch - best_epoch >= args.patience:
            print(f"early stopping (pas d'amélioration depuis {args.patience} epochs)",
                  flush=True)
            break

    print(f"best top-1 val={best_top1:.4f} (epoch {best_epoch}) -> {args.out}/best.pt",
          flush=True)


if __name__ == "__main__":
    main()
