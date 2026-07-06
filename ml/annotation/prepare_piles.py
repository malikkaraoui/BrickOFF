"""S.0 — Ingestion des photos "set TAS" + pré-annotation + export Label Studio.

Pipeline (protocole : docs/plan/PROTOCOLE_PHOTOS_TAS.md ; convention :
data/manifests/annotation_convention.md v1) :

1. Lit data/raw/piles_malik/{session_XX/, holdout/} (JPEG/PNG/HEIC),
   convertit HEIC→JPEG (pillow-heif) et applique l'orientation EXIF.
2. Copie/renomme vers data/processed/realworld_piles/{decision,holdout}/images/
   — le HOLDOUT reste physiquement séparé, il n'est JAMAIS mélangé au set de décision.
3. Pré-annote avec le champion DET (ml/runs/det_v3/best.pt, SSDLite320) au seuil 0.15
   (rappel maximal pour la correction humaine — convention S.0), batch 1 pour ne pas
   gêner un entraînement en cours ; device cpu par défaut (mesuré suffisant sur M1).
4. Exporte des tâches Label Studio (JSON avec pré-annotations bbox) + le config XML
   du projet (label unique "lego" + checkbox per-region "hard" — convention 25 %/hard).
   ⚠️ Le modèle ne prédit PAS le flag `hard` : il est posé par l'annotateur
   (pièces 10-25 % visibles).

Usage (depuis la racine du repo, .venv actif) :
    python ml/annotation/prepare_piles.py                    # tout par défaut
    python ml/annotation/prepare_piles.py --device mps       # si aucun training en cours
    python ml/annotation/prepare_piles.py --skip-preannotation
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pillow_heif
from PIL import Image, ImageOps

pillow_heif.register_heif_opener()

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
CONVENTION = "data/manifests/annotation_convention.md v1 (bbox si >=25% visible ; 10-25% -> flag hard)"

LABELSTUDIO_CONFIG_XML = """\
<View>
  <Image name="image" value="$image" zoom="true" zoomControl="true"
         brightnessControl="true" contrastControl="true"/>
  <RectangleLabels name="label" toName="image">
    <Label value="lego" background="#00c37d"/>
  </RectangleLabels>
  <!-- Convention v1 : piece visible a 10-25% -> bbox + cocher "hard" (par region).
       >=25% -> bbox simple. <10% -> pas de bbox. Bbox = partie VISIBLE uniquement. -->
  <Choices name="hard" toName="image" perRegion="true" choice="single" showInline="true">
    <Choice value="hard"/>
  </Choices>
</View>
"""


def sanitize(stem: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_") or "img"


def discover(raw_dir: Path) -> list[tuple[str, str, Path]]:
    """-> [(split, session, path)] trié. holdout/ -> split 'holdout', le reste -> 'decision'."""
    items: list[tuple[str, str, Path]] = []
    for sub in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        split = "holdout" if sub.name.lower() == "holdout" else "decision"
        for f in sorted(sub.rglob("*")):
            if f.is_file() and f.suffix.lower() in IMAGE_EXTS and not f.name.startswith("."):
                items.append((split, sub.name, f))
    return items


def ingest(items, out_dir: Path, quality: int) -> list[dict]:
    """HEIC->JPEG, orientation EXIF, renommage déterministe. -> records manifest."""
    records, used = [], set()
    for split, session, src in items:
        name = f"{sanitize(session)}__{sanitize(src.stem)}.jpg"
        i = 1
        while (split, name) in used:  # collision de stems entre sous-dossiers
            name = f"{sanitize(session)}__{sanitize(src.stem)}_{i}.jpg"
            i += 1
        used.add((split, name))
        dst = out_dir / split / "images" / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as im:
            orientation = im.getexif().get(274, 1)  # 274 = tag Orientation
            im = ImageOps.exif_transpose(im).convert("RGB")
            w, h = im.size
            im.save(dst, "JPEG", quality=quality)
        records.append({
            "source": str(src.relative_to(REPO_ROOT) if src.is_relative_to(REPO_ROOT) else src),
            "image": f"{split}/images/{name}", "split": split, "session": session,
            "width": w, "height": h,
            "heic_converted": src.suffix.lower() in {".heic", ".heif"},
            "exif_orientation_applied": int(orientation) != 1,
        })
    return records


def load_model(weights: Path, device: str):
    import torch
    from torchvision.models.detection import ssdlite320_mobilenet_v3_large

    model = ssdlite320_mobilenet_v3_large(weights=None, num_classes=2)
    model.load_state_dict(torch.load(weights, map_location="cpu"))
    model.to(torch.device(device)).eval()
    return model


def preannotate(records: list[dict], out_dir: Path, weights: Path, device: str,
                threshold: float, max_side: int) -> dict:
    """Inférence batch 1 (léger : n'entre pas en concurrence avec un training MPS)."""
    import torch
    from torchvision.transforms.functional import pil_to_tensor

    model = load_model(weights, device)
    timings = []
    with torch.no_grad():
        for rec in records:
            t0 = time.perf_counter()
            with Image.open(out_dir / rec["image"]) as im:
                scale = min(1.0, max_side / max(im.size))
                if scale < 1.0:
                    im = im.resize((round(im.width * scale), round(im.height * scale)))
                w, h = im.size
                tensor = pil_to_tensor(im).float().div(255).to(torch.device(device))
            pred = model([tensor])[0]
            keep = pred["scores"] >= threshold
            boxes = pred["boxes"][keep].cpu().tolist()
            scores = pred["scores"][keep].cpu().tolist()
            # -> % de l'image (format Label Studio, indépendant de la résolution)
            rec["predictions"] = [
                {"x": 100 * x1 / w, "y": 100 * y1 / h,
                 "width": 100 * (x2 - x1) / w, "height": 100 * (y2 - y1) / h,
                 "score": round(s, 4)}
                for (x1, y1, x2, y2), s in zip(boxes, scores)]
            timings.append(time.perf_counter() - t0)
            print(f"  {rec['image']}: {len(boxes)} bbox >= {threshold} "
                  f"({timings[-1]:.2f}s)", flush=True)
    return {"device": device, "n_images": len(timings),
            "mean_s_per_image": round(sum(timings) / max(len(timings), 1), 3),
            "max_s_per_image": round(max(timings, default=0.0), 3)}


def make_tasks(records: list[dict], model_version: str) -> dict[str, list]:
    """Tâches Label Studio par split, avec pré-annotations dans 'predictions'."""
    tasks: dict[str, list] = {"decision": [], "holdout": []}
    for rec in records:
        result = [
            {"id": f"pred_{i:03d}", "type": "rectanglelabels",
             "from_name": "label", "to_name": "image",
             "original_width": rec["width"], "original_height": rec["height"],
             "image_rotation": 0, "score": p["score"],
             "value": {"x": p["x"], "y": p["y"], "width": p["width"],
                       "height": p["height"], "rotation": 0,
                       "rectanglelabels": ["lego"]}}
            for i, p in enumerate(rec.get("predictions", []))]
        task = {"data": {"image": f"/data/local-files/?d={rec['image']}"}}
        if "predictions" in rec:
            scores = [p["score"] for p in rec["predictions"]]
            task["predictions"] = [{
                "model_version": model_version,
                "score": round(sum(scores) / len(scores), 4) if scores else 0.0,
                "result": result}]
        tasks[rec["split"]].append(task)
    return tasks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw-dir", type=Path, default=REPO_ROOT / "data" / "raw" / "piles_malik")
    parser.add_argument("--out-dir", type=Path,
                        default=REPO_ROOT / "data" / "processed" / "realworld_piles")
    parser.add_argument("--weights", type=Path,
                        default=REPO_ROOT / "ml" / "runs" / "det_v3" / "best.pt")
    parser.add_argument("--score-threshold", type=float, default=0.15,
                        help="seuil bas volontaire : maximiser le rappel de la pré-annotation")
    parser.add_argument("--device", default="cpu", choices=["cpu", "mps"],
                        help="cpu par défaut (~0.5 s/img, ne touche pas au GPU si un "
                             "entraînement tourne) ; mps si la machine est libre")
    parser.add_argument("--max-side", type=int, default=1280,
                        help="redimensionnement max avant inférence (le modèle travaille en 320²)")
    parser.add_argument("--jpeg-quality", type=int, default=92)
    parser.add_argument("--skip-preannotation", action="store_true")
    args = parser.parse_args()

    if not args.raw_dir.is_dir():
        raise SystemExit(f"Répertoire introuvable : {args.raw_dir} "
                         "(attendu : session_XX/ et holdout/ — cf. PROTOCOLE_PHOTOS_TAS.md)")
    items = discover(args.raw_dir)
    if not items:
        raise SystemExit(f"Aucune image dans {args.raw_dir} (extensions : {sorted(IMAGE_EXTS)})")
    n_hold = sum(1 for s, _, _ in items if s == "holdout")
    print(f"{len(items)} images : {len(items) - n_hold} decision / {n_hold} holdout")
    if n_hold == 0:
        print("⚠️  Aucun holdout/ trouvé — le protocole S.0 en exige >= 20 photos.")

    print("— Ingestion (HEIC→JPEG, orientation EXIF, renommage)…")
    records = ingest(items, args.out_dir, args.jpeg_quality)

    timing = None
    model_version = f"{args.weights.parent.name}_t{args.score_threshold}"
    if not args.skip_preannotation:
        print(f"— Pré-annotation {args.weights.parent.name} @ {args.score_threshold} "
              f"(device={args.device}, batch=1)…")
        timing = preannotate(records, args.out_dir, args.weights, args.device,
                             args.score_threshold, args.max_side)
        print(f"  → {timing['mean_s_per_image']} s/image en moyenne")

    ls_dir = args.out_dir / "labelstudio"
    ls_dir.mkdir(parents=True, exist_ok=True)
    (ls_dir / "labelstudio_config.xml").write_text(LABELSTUDIO_CONFIG_XML)
    tasks = make_tasks(records, model_version)
    for split, split_tasks in tasks.items():
        if split_tasks:
            path = ls_dir / f"tasks_{split}.json"
            path.write_text(json.dumps(split_tasks, indent=1, ensure_ascii=False))
            print(f"  {path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path}"
                  f" : {len(split_tasks)} tâches")

    manifest = {
        "dataset_id": "realworld_piles_v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "convention": CONVENTION,
        "raw_dir": str(args.raw_dir),
        "preannotation": None if args.skip_preannotation else {
            "weights": str(args.weights), "score_threshold": args.score_threshold,
            "model_version": model_version, "max_side": args.max_side, **(timing or {})},
        "splits": {s: sum(1 for r in records if r["split"] == s)
                   for s in ("decision", "holdout")},
        "holdout_note": "holdout/ = juge final It.3, jamais utilisé pour les décisions d'itération",
        "images": [{k: v for k, v in r.items() if k != "predictions"} for r in records],
    }
    (args.out_dir / "manifest_ingest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False))
    print(f"Manifest : {args.out_dir / 'manifest_ingest.json'}")
    print("Config Label Studio :", ls_dir / "labelstudio_config.xml")


if __name__ == "__main__":
    main()
