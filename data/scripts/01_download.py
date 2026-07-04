"""CH-1 jalon 1.1 — Acquisition des datasets sources.

Datasets et licences : voir docs/research/DATASETS_SURVEY.md (vérifiées le 2026-07-04).
Idempotent : un dataset déjà téléchargé et vérifié est sauté. Reprise supportée (curl -C -).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Sources : URL stable = la page DOI ; l'URL S3 signée est obtenue par redirection à chaque run.
DATASETS: dict[str, dict[str, str]] = {
    "gdansk_det": {
        "description": "Tagged images with LEGO bricks (Boiński, Gdańsk UT) — détection, bbox VOC, photos réelles",
        "license": "CC BY 4.0",
        "doi": "10.34808/anq4-rn44",
        "url": "https://mostwiedzy.pl/en/open-research-data/tagged-images-with-lego-bricks,202309140833448152311-0/download",
        "filename": "gdansk_tagged1.zip",
        "target_dir": "gdansk_det",
    },
    "gdansk_cls": {
        "description": "LEGO bricks for training classification network (Gdańsk UT) — classification, 447 classes, photos réelles + rendus",
        "license": "CC BY 4.0",
        "doi": "10.34808/rcza-jy08",
        "url": "https://mostwiedzy.pl/en/open-research-data/lego-bricks-for-training-classification-network,202309140843579455029-0/download",
        "filename": "gdansk_cls.zip",
        "target_dir": "gdansk_cls",
    },
}

HF_DATASET = "pvrancx/legobricks"  # Apache-2.0, 400k rendus LDraw, 1000 classes


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while data := f.read(chunk):
            h.update(data)
    return h.hexdigest()


def record_manifest(raw_dir: Path, name: str, info: dict) -> None:
    manifest_path = REPO_ROOT / "data" / "manifests" / "downloads.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest[name] = info | {"downloaded_at": datetime.now(timezone.utc).isoformat()}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


def download_zip(name: str, spec: dict[str, str], raw_dir: Path, force: bool) -> None:
    target = raw_dir / spec["target_dir"]
    archive = raw_dir / spec["filename"]
    if target.exists() and any(target.iterdir()) and not force:
        print(f"[{name}] déjà extrait -> skip (--force pour refaire)")
        return
    part = archive.with_suffix(archive.suffix + ".part")
    print(f"[{name}] téléchargement ({spec['doi']}, {spec['license']})…")
    subprocess.run(
        ["curl", "-L", "-C", "-", "--retry", "5", "--retry-delay", "10",
         "-o", str(part), spec["url"]],
        check=True,
    )
    part.rename(archive)
    print(f"[{name}] vérification zip…")
    with zipfile.ZipFile(archive) as zf:
        if (bad := zf.testzip()) is not None:
            raise RuntimeError(f"archive corrompue: {bad}")
        target.mkdir(parents=True, exist_ok=True)
        zf.extractall(target)
    record_manifest(raw_dir, name, {
        "doi": spec["doi"], "license": spec["license"],
        "sha256": sha256_of(archive), "size_bytes": archive.stat().st_size,
        "extracted_to": str(target.relative_to(REPO_ROOT)),
    })
    print(f"[{name}] OK -> {target}")


def download_hf(raw_dir: Path, force: bool) -> None:
    from huggingface_hub import snapshot_download

    target = raw_dir / "legobricks_hf"
    if target.exists() and any(target.iterdir()) and not force:
        print("[legobricks] déjà présent -> skip")
        return
    print(f"[legobricks] snapshot HF {HF_DATASET} (Apache-2.0, ~15,6 Go)…")
    snapshot_download(repo_id=HF_DATASET, repo_type="dataset", local_dir=target)
    record_manifest(raw_dir, "legobricks_hf", {
        "source": f"hf:{HF_DATASET}", "license": "Apache-2.0",
        "extracted_to": str(target.relative_to(REPO_ROOT)),
    })
    print(f"[legobricks] OK -> {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=[*DATASETS, "legobricks", "all"], default="all")
    parser.add_argument("--raw-dir", type=Path, default=REPO_ROOT / "data" / "raw")
    parser.add_argument("--force", action="store_true", help="retélécharge même si présent")
    args = parser.parse_args()

    args.raw_dir.mkdir(parents=True, exist_ok=True)
    selected = [args.dataset] if args.dataset != "all" else [*DATASETS, "legobricks"]
    for name in selected:
        if name == "legobricks":
            download_hf(args.raw_dir, args.force)
        else:
            download_zip(name, DATASETS[name], args.raw_dir, args.force)
    print("Acquisition terminée. Manifest: data/manifests/downloads.json")


if __name__ == "__main__":
    sys.exit(main())
