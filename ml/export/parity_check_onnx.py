"""Garde-fou D01 (Android) — Parité numérique PyTorch CPU vs onnxruntime CPU.

Protocole IDENTIQUE à parity_check.py (voie CoreML, CH-3 jalon 3.2 adapté) :
50 images du test split (échantillon déterministe seed 42), inférence CPU des
deux côtés, seuil produit 0.35, mêmes critères :
- boxes appariées (greedy par score décroissant) : IoU >= 0.95
- |Δ score| < 0.02 sur les paires
- top-1 identique (appariement top-1 à IoU >= 0.95)
- aucune box orpheline (>= seuil) d'un côté sans correspondance de l'autre

Isolation du resize : les DEUX chemins consomment la MÊME image PIL 320x320
(cf. parity_check.py) — on mesure la parité du MODÈLE, pas des pipelines de
resize (la chaîne Bitmap Android reste à valider on-device au vrai chantier).

- Référence : modèle torchvision complet (transform+postprocess d'origine), CPU.
- ONNX : DetModel.onnx via onnxruntime CPUExecutionProvider. L'entrée est
  float32 [1,3,320,320] RGB 0-255 (normalisation in-graph). Si le modèle est
  --nms external, on applique ici le même postprocess (topk 300, NMS iou 0.55).

Sortie : rapport JSON + verdict PASS/FAIL (exit code 1 si FAIL).
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision.models.detection import ssdlite320_mobilenet_v3_large
from torchvision.ops import nms

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_SIZE = 320
IOU_MIN = 0.95
SCORE_DIFF_MAX = 0.02


def iou_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """IoU [len(a), len(b)] pour boxes XYXY."""
    x1 = np.maximum(a[:, None, 0], b[None, :, 0])
    y1 = np.maximum(a[:, None, 1], b[None, :, 1])
    x2 = np.minimum(a[:, None, 2], b[None, :, 2])
    y2 = np.minimum(a[:, None, 3], b[None, :, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    area_a = (a[:, 2] - a[:, 0]) * (a[:, 3] - a[:, 1])
    area_b = (b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])
    return inter / (area_a[:, None] + area_b[None, :] - inter + 1e-9)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path,
                        default=REPO_ROOT / "ml" / "runs" / "det_v3" / "best.pt")
    parser.add_argument("--onnx", type=Path,
                        default=REPO_ROOT / "ml" / "export" / "DetModel.onnx")
    parser.add_argument("--split-dir", type=Path,
                        default=REPO_ROOT / "data" / "processed" / "detection" / "test")
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--score-threshold", type=float, default=0.35,
                        help="seuil produit (contrat CH-5)")
    parser.add_argument("--report", type=Path,
                        default=REPO_ROOT / "ml" / "export" / "parity_report_det_onnx.json")
    args = parser.parse_args()

    import onnxruntime as ort

    torch_model = ssdlite320_mobilenet_v3_large(weights=None, num_classes=2)
    torch_model.load_state_dict(torch.load(args.weights, map_location="cpu"))
    torch_model.eval()

    sess = ort.InferenceSession(str(args.onnx), providers=["CPUExecutionProvider"])
    meta = sess.get_modelmeta().custom_metadata_map
    nms_mode = meta.get("brickoff.nms", "?")
    external_nms = nms_mode.startswith("external")

    images = sorted((args.split_dir / "images").iterdir())
    images = random.Random(args.seed).sample(images, min(args.n, len(images)))

    per_image, all_ious, all_sdiffs = [], [], []
    n_top1_ok = n_top1_total = n_orphans = 0
    for path in images:
        with Image.open(path) as im:
            pil = im.convert("RGB").resize((INPUT_SIZE, INPUT_SIZE), Image.BILINEAR)
        rgb = np.asarray(pil, dtype=np.float32)  # HWC, 0-255

        # --- Référence PyTorch (forward complet torchvision, CPU) ---
        tensor = torch.from_numpy(rgb).permute(2, 0, 1) / 255.0
        with torch.no_grad():
            pred = torch_model([tensor])[0]
        keep = pred["scores"] >= args.score_threshold
        ref_boxes = pred["boxes"][keep].numpy()          # pixels 320
        ref_scores = pred["scores"][keep].numpy()

        # --- onnxruntime (pixels bruts 0-255, normalisation in-graph) ---
        inp = rgb.transpose(2, 0, 1)[None]               # [1,3,320,320]
        onnx_boxes, onnx_scores = sess.run(None, {"image": inp})
        onnx_boxes = onnx_boxes.astype(np.float32) * INPUT_SIZE
        onnx_scores = onnx_scores.astype(np.float32)
        if external_nms:
            order = np.argsort(-onnx_scores)[:300]
            b = torch.from_numpy(onnx_boxes[order])
            s = torch.from_numpy(onnx_scores[order])
            k = nms(b, s, 0.55).numpy()
            onnx_boxes, onnx_scores = onnx_boxes[order][k], onnx_scores[order][k]
        keep = onnx_scores >= args.score_threshold
        onnx_boxes, onnx_scores = onnx_boxes[keep], onnx_scores[keep]

        # --- Appariement greedy par score de référence décroissant ---
        pairs, used = [], set()
        if len(ref_boxes) and len(onnx_boxes):
            m = iou_matrix(ref_boxes, onnx_boxes)
            for i in np.argsort(-ref_scores):
                cand = [(m[i, j], j) for j in range(len(onnx_boxes)) if j not in used]
                if not cand:
                    break
                best_iou, j = max(cand)
                if best_iou <= 0:
                    continue
                used.add(j)
                pairs.append((float(best_iou),
                              float(abs(ref_scores[i] - onnx_scores[j])), int(i), int(j)))
        orphans = (len(ref_boxes) - len(pairs)) + (len(onnx_boxes) - len(pairs))
        n_orphans += orphans
        ious = [p[0] for p in pairs]
        sdiffs = [p[1] for p in pairs]
        all_ious += ious
        all_sdiffs += sdiffs

        top1_ok = None
        if len(ref_boxes) and len(onnx_boxes):
            n_top1_total += 1
            i_ref = int(np.argmax(ref_scores))
            j_onx = int(np.argmax(onnx_scores))
            top1_ok = bool(iou_matrix(ref_boxes[i_ref:i_ref + 1],
                                      onnx_boxes[j_onx:j_onx + 1])[0, 0] >= IOU_MIN)
            n_top1_ok += int(top1_ok)

        per_image.append({
            "image": path.name, "n_ref": len(ref_boxes), "n_onnx": len(onnx_boxes),
            "n_matched": len(pairs), "orphans": orphans,
            "min_iou": round(min(ious), 4) if ious else None,
            "max_score_diff": round(max(sdiffs), 4) if sdiffs else None,
            "top1_match": top1_ok,
        })

    checks = {
        "iou_min_ge_0.95": bool(all_ious) and min(all_ious) >= IOU_MIN,
        "score_diff_max_lt_0.02": bool(all_sdiffs) and max(all_sdiffs) < SCORE_DIFF_MAX,
        "top1_identical_all": n_top1_total > 0 and n_top1_ok == n_top1_total,
        "no_orphan_boxes": n_orphans == 0,
    }
    report = {
        "protocol": "D01 garde-fou Android (miroir CH-3 jalon 3.2 dry-run)",
        "date": datetime.now(timezone.utc).isoformat(),
        "weights": str(args.weights), "onnx": str(args.onnx),
        "onnxruntime_version": ort.__version__,
        "nms_mode": nms_mode, "n_images": len(images), "seed": args.seed,
        "score_threshold": args.score_threshold,
        "matched_pairs": len(all_ious),
        "iou": {"min": round(min(all_ious), 5), "mean": round(float(np.mean(all_ious)), 5)}
               if all_ious else None,
        "score_diff": {"max": round(max(all_sdiffs), 5),
                       "mean": round(float(np.mean(all_sdiffs)), 6)} if all_sdiffs else None,
        "top1": {"ok": n_top1_ok, "total": n_top1_total},
        "orphan_boxes": n_orphans,
        "checks": checks,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "per_image": per_image,
    }
    args.report.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "per_image"}, indent=2))
    raise SystemExit(0 if report["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
