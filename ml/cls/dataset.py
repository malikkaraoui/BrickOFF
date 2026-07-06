"""CH-2 jalon 2.2 — Datasets classification (CLS v0).

Deux sources :
- LegoBricksParquet : 400 000 rendus / 1000 classes, 51 fichiers parquet HF
  (colonne image = struct{bytes, path}, colonne label = index HF). Lecture LAZY :
  index par fichier mis en cache (JSON), décodage des bytes à la volée, cache LRU
  de row groups. ⚠️ Les row groups (~100 lignes) sont quasi mono-classe : un accès
  purement aléatoire relit ~6 Mo de parquet PAR IMAGE. D'où RowGroupWindowSampler :
  brassage à deux niveaux (row groups mélangés, fenêtre de W groups mélangée en
  interne) → lecture quasi-séquentielle + diversité ~W classes par fenêtre.
- GdanskFolder : ImageFolder photos/ ou renders/ filtré sur le mapping
  classes_cls_v0.json, split par GROUPES anti-fuite :
  * photos  : groupe = token 3 du nom (`c0_1_<TAG>_<hash>_original_<ts>.jpg`) —
    les frames multi-caméras d'un même passage/session restent du même côté ;
  * renders : groupe = couleur (`<part>_<Couleur>_<i>_<ts>.jpeg`) — les rendus
    d'un même couple pièce+couleur sont des quasi-doublons d'angle.

Augmentation train : hue shift AGRESSIF autorisé (la couleur est traitée par le
pipeline COLOR, pas par CLS — doc 03 jalon 2.2), flips H/V, rotation libre ±180°,
crop-zoom. Val/test : letterbox 224² sans augmentation.
"""

from __future__ import annotations

import json
import random
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Iterator

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset, Sampler
from torchvision.transforms import v2

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


class SquarePad(torch.nn.Module):
    """Letterbox : pad au carré (fond noir) pour préserver le ratio du crop."""

    def forward(self, img: torch.Tensor) -> torch.Tensor:
        h, w = img.shape[-2:]
        side = max(h, w)
        left, top = (side - w) // 2, (side - h) // 2
        return v2.functional.pad(img, [left, top, side - w - left, side - h - top], fill=0.0)


def build_transform(train: bool, size: int = 224) -> v2.Compose:
    ops: list = [v2.ToImage(), v2.ToDtype(torch.float32, scale=True), SquarePad()]
    if train:
        ops += [
            v2.Resize(int(size * 1.15), antialias=True),
            v2.RandomRotation(degrees=180, fill=0.0),
            v2.RandomResizedCrop(size, scale=(0.55, 1.0), ratio=(0.8, 1.25), antialias=True),
            v2.RandomHorizontalFlip(0.5),
            v2.RandomVerticalFlip(0.5),
            # hue=0.5 = décalage de teinte maximal : CLS doit être aveugle à la couleur
            v2.ColorJitter(brightness=0.4, contrast=0.4, saturation=(0.2, 1.8), hue=0.5),
            v2.RandomGrayscale(p=0.05),
            v2.RandomApply([v2.GaussianBlur(kernel_size=5, sigma=(0.1, 2.0))], p=0.25),
        ]
    else:
        ops += [v2.Resize((size, size), antialias=True)]
    ops += [v2.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)]
    return v2.Compose(ops)


# ---------------------------------------------------------------------------
# LegoBricks (parquet HF)
# ---------------------------------------------------------------------------

def load_or_build_index(data_dir: Path, cache_path: Path | None = None,
                        force: bool = False) -> dict:
    """Index par fichier parquet : nb de lignes, tailles de row groups, labels.

    Une seule passe colonne `label` (rapide) puis cache JSON — les images ne sont
    jamais lues ici. Retourne aussi `class_names` (mapping HF index -> part_id).
    """
    import pyarrow.parquet as pq

    cache_path = cache_path or data_dir / "_cls_index.json"
    files = sorted(p.name for p in data_dir.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"aucun parquet dans {data_dir}")
    if cache_path.exists() and not force:
        index = json.loads(cache_path.read_text())
        if index.get("files") == files:
            return index
    index: dict = {"files": files, "row_group_sizes": [], "labels_by_file": [],
                   "class_names": None}
    for name in files:
        f = pq.ParquetFile(data_dir / name)
        if index["class_names"] is None:
            meta = json.loads(f.schema_arrow.metadata[b"huggingface"])
            index["class_names"] = meta["info"]["features"]["label"]["names"]
        sizes = [f.metadata.row_group(i).num_rows for i in range(f.metadata.num_row_groups)]
        labels = f.read(columns=["label"]).column("label").to_pylist()
        index["row_group_sizes"].append(sizes)
        index["labels_by_file"].append(labels)
    cache_path.write_text(json.dumps(index))
    return index


def _flatten_index(index: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Tables plates par ligne globale : file_idx, row_group_idx, offset, label."""
    file_idx, rg_idx, offset, label = [], [], [], []
    for fi, sizes in enumerate(index["row_group_sizes"]):
        labels = index["labels_by_file"][fi]
        pos = 0
        for gi, n in enumerate(sizes):
            file_idx += [fi] * n
            rg_idx += [gi] * n
            offset += range(n)
            label += labels[pos:pos + n]
            pos += n
    return (np.asarray(file_idx, dtype=np.int32), np.asarray(rg_idx, dtype=np.int32),
            np.asarray(offset, dtype=np.int32), np.asarray(label, dtype=np.int64))


def rows_for_split(index: dict, splits: dict | None, split: str) -> list[int]:
    """Ids de lignes globaux pour un split ("train" = complément de val∪test)."""
    n_by_file = [sum(s) for s in index["row_group_sizes"]]
    starts = np.concatenate([[0], np.cumsum(n_by_file)])
    if splits is None:
        return list(range(int(starts[-1])))
    lb = splits["legobricks"]
    held = {"val": set(), "test": set()}
    for part in ("val", "test"):
        for fname, rows in lb[part].items():
            base = int(starts[index["files"].index(fname)])
            held[part].update(base + r for r in rows)
    if split in ("val", "test"):
        return sorted(held[split])
    excluded = held["val"] | held["test"]
    return [i for i in range(int(starts[-1])) if i not in excluded]


def sample_rows_by_rowgroup(rows: list[int], rg_of_row: np.ndarray,
                            file_of_row: np.ndarray, limit: int, seed: int) -> list[int]:
    """Sous-échantillon ~limit lignes en tirant des row groups ENTIERS (seedé).

    Un tirage uniforme de lignes disperserait les accès sur ~limit row groups
    (6 Mo relus par image) ; tirer des groups entiers garde la lecture locale.
    """
    by_rg: dict[tuple[int, int], list[int]] = defaultdict(list)
    for r in rows:
        by_rg[(int(file_of_row[r]), int(rg_of_row[r]))].append(r)
    keys = sorted(by_rg)
    random.Random(seed).shuffle(keys)
    out: list[int] = []
    for k in keys:
        out += by_rg[k]
        if len(out) >= limit:
            break
    return out[:limit]


class LegoBricksParquet(Dataset):
    """Lecture lazy des parquet HF avec cache LRU de row groups (bytes encodés)."""

    def __init__(self, data_dir: Path, rows: list[int] | None = None, train: bool = True,
                 size: int = 224, cache_groups: int = 96,
                 index: dict | None = None, transform: v2.Compose | None = None):
        self.data_dir = Path(data_dir)
        self.index = index or load_or_build_index(self.data_dir)
        self.file_of_row, self.rg_of_row, self.off_of_row, self.label_of_row = \
            _flatten_index(self.index)
        self.rows = np.asarray(rows if rows is not None
                               else range(len(self.label_of_row)), dtype=np.int64)
        self.cache_groups = cache_groups
        self.transform = transform or build_transform(train, size)
        self._handles: dict = {}          # ouverts lazy (picklable pour les workers)
        self._cache: OrderedDict = OrderedDict()

    def __len__(self) -> int:
        return len(self.rows)

    def label(self, pos: int) -> int:
        return int(self.label_of_row[self.rows[pos]])

    def rg_key(self, pos: int) -> tuple[int, int]:
        r = self.rows[pos]
        return int(self.file_of_row[r]), int(self.rg_of_row[r])

    def _row_group_bytes(self, key: tuple[int, int]) -> list[bytes]:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        import pyarrow.parquet as pq
        fi, gi = key
        if fi not in self._handles:
            self._handles[fi] = pq.ParquetFile(self.data_dir / self.index["files"][fi])
        col = self._handles[fi].read_row_group(gi, columns=["image"]).column("image")
        data = [v["bytes"] for v in col.to_pylist()]
        self._cache[key] = data
        while len(self._cache) > self.cache_groups:
            self._cache.popitem(last=False)
        return data

    def __getitem__(self, pos: int):
        r = self.rows[pos]
        raw = self._row_group_bytes((int(self.file_of_row[r]), int(self.rg_of_row[r])))
        import io
        with Image.open(io.BytesIO(raw[int(self.off_of_row[r])])) as im:
            img = self.transform(im.convert("RGB"))
        return img, int(self.label_of_row[r])


class RowGroupWindowSampler(Sampler[int]):
    """Brassage à deux niveaux compatible cache : row groups mélangés, puis
    mélange interne par fenêtres de `window` groups (~window classes par fenêtre)."""

    def __init__(self, dataset: LegoBricksParquet, window: int = 64, seed: int = 42):
        self.window, self.seed, self.epoch = window, seed, 0
        self.by_rg: dict[tuple[int, int], list[int]] = defaultdict(list)
        for pos in range(len(dataset)):
            self.by_rg[dataset.rg_key(pos)].append(pos)
        self.n = len(dataset)

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch

    def __len__(self) -> int:
        return self.n

    def __iter__(self) -> Iterator[int]:
        rng = random.Random(self.seed * 100_003 + self.epoch)
        keys = sorted(self.by_rg)
        rng.shuffle(keys)
        for w in range(0, len(keys), self.window):
            block = [p for k in keys[w:w + self.window] for p in self.by_rg[k]]
            rng.shuffle(block)
            yield from block


class MixedRealSampler(Sampler[int]):
    """Mélange synthétique (parquet, ordre fenêtré préservé) + réel (gdansk, aléatoire)
    pour ConcatDataset([parquet, gdansk]). `real_frac` = fraction de réel vue par epoch."""

    def __init__(self, parquet_sampler: RowGroupWindowSampler, parquet_len: int,
                 real_len: int, real_frac: float, seed: int = 42):
        if not 0.0 < real_frac < 1.0:
            raise ValueError("real_frac doit être dans ]0,1[")
        self.ps, self.parquet_len, self.real_len = parquet_sampler, parquet_len, real_len
        self.real_frac, self.seed, self.epoch = real_frac, seed, 0
        self.n_real = round(parquet_len * real_frac / (1.0 - real_frac))

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch
        self.ps.set_epoch(epoch)

    def __len__(self) -> int:
        return self.parquet_len + self.n_real

    def __iter__(self) -> Iterator[int]:
        rng = random.Random(self.seed * 999_983 + self.epoch)
        synth = list(self.ps)
        real = [self.parquet_len + rng.randrange(self.real_len) for _ in range(self.n_real)]
        total = len(synth) + len(real)
        real_slots = set(rng.sample(range(total), len(real)))
        si, ri = iter(synth), iter(real)
        for slot in range(total):
            yield next(ri) if slot in real_slots else next(si)


# ---------------------------------------------------------------------------
# Gdansk (ImageFolder photos/ + renders/)
# ---------------------------------------------------------------------------

def gdansk_group_key(subset: str, filename: str) -> str:
    """Clé de groupe anti-fuite (voir docstring module)."""
    parts = filename.split("_")
    return parts[2] if subset == "photos" else parts[1]


class GdanskFolder(Dataset):
    """gdansk_cls filtré sur le mapping classes + split par groupes anti-fuite."""

    EXTS = {".jpg", ".jpeg", ".png"}

    def __init__(self, root: Path, classes: dict[str, int], subset: str = "photos",
                 split: str = "train", splits: dict | None = None, train: bool = True,
                 size: int = 224, limit: int | None = None, seed: int = 42,
                 transform: v2.Compose | None = None):
        if subset not in ("photos", "renders"):
            raise ValueError(f"subset inconnu : {subset}")
        self.transform = transform or build_transform(train, size)
        held: dict[str, dict[str, set]] = {"val": {}, "test": {}}
        if splits is not None:
            for part in ("val", "test"):
                held[part] = {c: set(g) for c, g in splits["gdansk"][subset][part].items()}
        self.samples: list[tuple[Path, int]] = []
        base = Path(root) / subset
        for class_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            label = classes.get(class_dir.name)
            if label is None:
                continue
            v = held["val"].get(class_dir.name, set())
            t = held["test"].get(class_dir.name, set())
            for f in sorted(class_dir.iterdir()):
                if f.suffix.lower() not in self.EXTS:
                    continue
                g = gdansk_group_key(subset, f.name)
                side = "val" if g in v else ("test" if g in t else "train")
                if splits is None or side == split:
                    self.samples.append((f, label))
        if limit is not None and limit < len(self.samples):
            rng = random.Random(seed)
            self.samples = sorted(rng.sample(self.samples, limit))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, pos: int):
        path, label = self.samples[pos]
        with Image.open(path) as im:
            img = self.transform(im.convert("RGB"))
        return img, label
