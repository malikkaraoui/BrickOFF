"""Dataset détection mono-classe au format YOLO (data/processed/detection/<split>/).

Les transformations géométriques (flips, rotations, zoom-out) passent par
torchvision.transforms.v2 avec des BoundingBoxes tv_tensors : images ET boîtes
sont transformées ensemble — un flip d'image sans flip des boîtes (bug de la v0)
fausse silencieusement la moitié de la supervision.

Niveaux d'augmentation :
- "none"   : resize seul (val/test)
- "light"  : flip horizontal (v0 corrigée)
- "strong" : flips H/V + rotation libre ±180° + zoom-out (petites cibles, reco audit)
             + photométrie forte (éclairage/couleur/flou — reco audit éclairage chaud)
"""

from __future__ import annotations

from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import tv_tensors
from torchvision.transforms import v2


def build_transform(aug: str, size: int) -> v2.Compose:
    # Resize carré AVANT les rotations : une rotation de 90° sur un carré est sans perte
    # avec expand=False, et expand=True a un mismatch d'arrondi image/boxes (torchvision).
    ops: list = [v2.ToImage(), v2.ToDtype(torch.float32, scale=True),
                 v2.Resize((size, size), antialias=True)]
    if aug == "light":
        ops += [v2.RandomHorizontalFlip(0.5)]
    elif aug == "strong":
        ops += [
            v2.RandomHorizontalFlip(0.5),
            v2.RandomVerticalFlip(0.5),
            v2.RandomChoice([v2.Identity()] + [
                v2.RandomRotation(degrees=(a, a), expand=False) for a in (90, 180, 270)]),
            v2.RandomRotation(degrees=20, expand=False, fill=0.0),
            v2.RandomZoomOut(fill=0.0, side_range=(1.0, 2.2), p=0.4),
            v2.ColorJitter(brightness=0.45, contrast=0.4, saturation=0.35, hue=0.08),
            v2.RandomApply([v2.GaussianBlur(kernel_size=5, sigma=(0.1, 2.0))], p=0.3),
        ]
    ops += [v2.ClampBoundingBoxes(), v2.SanitizeBoundingBoxes(min_size=2)]
    return v2.Compose(ops)


class LegoDetectionDataset(Dataset):
    def __init__(self, split_dir: Path, train: bool, size: int = 320,
                 limit: int | None = None, aug: str | None = None,
                 photos_only: bool = False):
        self.images = sorted((split_dir / "images").iterdir())
        if photos_only:
            self.images = [p for p in self.images if p.name.startswith("photos_")]
        if limit:
            self.images = self.images[:limit]
        self.labels_dir = split_dir / "labels"
        self.size = size
        self.transform = build_transform(aug if aug else ("light" if train else "none"), size)

    def __len__(self) -> int:
        return len(self.images)

    def __getitem__(self, i: int):
        path = self.images[i]
        with Image.open(path) as im:
            im = im.convert("RGB")
            w, h = im.size
            img = tv_tensors.Image(im)
        boxes = []
        for line in (self.labels_dir / (path.stem + ".txt")).read_text().splitlines():
            if not line or line.startswith("#"):  # lignes '# hard' : ni positif ni négatif
                continue
            _, cx, cy, bw, bh = map(float, line.split())
            boxes.append([(cx - bw / 2) * w, (cy - bh / 2) * h,
                          (cx + bw / 2) * w, (cy + bh / 2) * h])
        target = {
            "boxes": tv_tensors.BoundingBoxes(
                torch.tensor(boxes, dtype=torch.float32).reshape(-1, 4),
                format="XYXY", canvas_size=(h, w)),
            "labels": torch.ones((len(boxes),), dtype=torch.int64),
        }
        img, target = self.transform(img, target)
        target["boxes"] = torch.as_tensor(target["boxes"], dtype=torch.float32).reshape(-1, 4)
        return img, target


def collate(batch):
    return tuple(zip(*batch))
