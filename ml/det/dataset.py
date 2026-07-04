"""Dataset détection mono-classe au format YOLO (data/processed/detection/<split>/)."""

from __future__ import annotations

from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision.transforms import v2


class LegoDetectionDataset(Dataset):
    """Images + bboxes YOLO normalisées -> tenseurs torchvision (boxes xyxy pixels, labels=1)."""

    def __init__(self, split_dir: Path, train: bool, size: int = 320, limit: int | None = None):
        self.images = sorted((split_dir / "images").iterdir())
        if limit:
            self.images = self.images[:limit]
        self.labels_dir = split_dir / "labels"
        self.size = size
        aug: list = [v2.ToImage(), v2.ToDtype(torch.float32, scale=True)]
        if train:
            aug += [v2.RandomHorizontalFlip(0.5), v2.ColorJitter(brightness=0.2, contrast=0.2)]
        self.transform = v2.Compose(aug + [v2.Resize((size, size), antialias=True)])

    def __len__(self) -> int:
        return len(self.images)

    def __getitem__(self, i: int):
        path = self.images[i]
        with Image.open(path) as im:
            im = im.convert("RGB")
            w, h = im.size
            img = self.transform(im)
        boxes = []
        lbl = self.labels_dir / (path.stem + ".txt")
        for line in lbl.read_text().splitlines():
            _, cx, cy, bw, bh = map(float, line.split())
            # xyxy en pixels de l'image REDIMENSIONNÉE (size×size)
            boxes.append([(cx - bw / 2) * self.size, (cy - bh / 2) * self.size,
                          (cx + bw / 2) * self.size, (cy + bh / 2) * self.size])
        target = {
            "boxes": torch.tensor(boxes, dtype=torch.float32).reshape(-1, 4),
            "labels": torch.ones((len(boxes),), dtype=torch.int64),
        }
        return img, target


def collate(batch):
    return tuple(zip(*batch))
