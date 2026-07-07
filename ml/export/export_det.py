"""CH-3 jalon 3.1 (DRY-RUN) — Export DET SSDLite320-MobileNetV3 (mono-classe) vers CoreML.

Chaîne : best.pt -> wrapper traçable (backbone+head+decode[+NMS]) -> torch.jit.trace
-> coremltools (ML Program, FP16 par défaut) -> .mlpackage.

Pourquoi un wrapper : le forward torchvision embarque GeneralizedRCNNTransform
(resize+normalisation, listes d'images de tailles variables) et un postprocess en
boucles Python — non traçable proprement. On exporte donc le cœur à taille fixe
320x320 et on ré-implémente le decode SSD (box_coder weights (10,10,5,5)) en ops
tensorielles, anchors précalculées (constantes pour une entrée fixe).

Pièges du plan (04_CH3_EXPORT_MOBILE.md) traités ici :
- Normalisation EMBARQUÉE : mean=std=0.5 (transform torchvision) => ImageType
  scale=2/255, bias=[-1,-1,-1]. Le mlpackage mange des pixels RGB 0-255 bruts.
- RGB confirmé (color_layout=RGB ; torchvision travaille en RGB).
- NMS : --nms embedded (défaut, torchvision::nms converti par coremltools>=9)
  ou --nms external (sorties brutes 3234 anchors, NMS côté client).

Contrat I/O (12_CONVENTIONS_AI.md §1.5, adapté 320) :
- input  "image"  : RGB 320x320 (resize scaleFill côté client — le transform
  torchvision ne préserve PAS l'aspect ratio : fixed_size=(320,320)).
- output "boxes"  : [N,4] XYXY normalisé 0-1 ; "scores" : [N] proba classe lego.
  embedded : N<=300 (post-NMS iou 0.55) ; external : N=3234 (tout décodé).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch
from torch import Tensor, nn
from torchvision.models.detection import ssdlite320_mobilenet_v3_large
from torchvision.models.detection.image_list import ImageList
from torchvision.ops import nms

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_SIZE = 320
NMS_IOU = 0.55          # défaut torchvision SSDLite, conservé (contrat)
TOPK = 300              # topk_candidates / detections_per_img torchvision
SCORE_THRESHOLD_PRODUCT = 0.35  # seuil produit CH-5 (métadonnée, pas appliqué ici)


class SSDLiteDetCore(nn.Module):
    """Backbone + head + decode SSD (+ NMS optionnel), entrée normalisée fixe."""

    def __init__(self, model: nn.Module, embed_nms: bool) -> None:
        super().__init__()
        self.backbone = model.backbone
        self.head = model.head
        self.embed_nms = embed_nms
        # Anchors constantes pour 320x320 (générateur déterministe).
        with torch.no_grad():
            dummy = torch.zeros(1, 3, INPUT_SIZE, INPUT_SIZE)
            feats = list(self.backbone(dummy).values())
            anchors = model.anchor_generator(
                ImageList(dummy, [(INPUT_SIZE, INPUT_SIZE)]), feats)[0]
        self.register_buffer("anchors", anchors)  # [3234, 4] XYXY pixels
        w = model.box_coder.weights  # (10, 10, 5, 5)
        self.register_buffer("coder_w", torch.tensor(w).reshape(1, 4))
        self.bbox_xform_clip = math.log(1000.0 / 16)

    def _decode(self, rel: Tensor) -> Tensor:
        """torchvision BoxCoder.decode_single en tensoriel pur."""
        a = self.anchors
        widths = a[:, 2] - a[:, 0]
        heights = a[:, 3] - a[:, 1]
        ctr_x = a[:, 0] + 0.5 * widths
        ctr_y = a[:, 1] + 0.5 * heights
        d = rel / self.coder_w
        dw = d[:, 2].clamp(max=self.bbox_xform_clip)
        dh = d[:, 3].clamp(max=self.bbox_xform_clip)
        pred_ctr_x = d[:, 0] * widths + ctr_x
        pred_ctr_y = d[:, 1] * heights + ctr_y
        half_w = 0.5 * torch.exp(dw) * widths
        half_h = 0.5 * torch.exp(dh) * heights
        return torch.stack([pred_ctr_x - half_w, pred_ctr_y - half_h,
                            pred_ctr_x + half_w, pred_ctr_y + half_h], dim=1)

    def forward(self, x: Tensor) -> tuple[Tensor, Tensor]:
        feats = list(self.backbone(x).values())
        head = self.head(feats)
        boxes = self._decode(head["bbox_regression"][0])
        boxes = boxes.clamp(min=0.0, max=float(INPUT_SIZE))  # clip AVANT NMS (comme torchvision)
        scores = torch.softmax(head["cls_logits"][0], dim=-1)[:, 1]  # classe 1 = lego_piece
        if self.embed_nms:
            scores, idx = scores.topk(TOPK)
            boxes = boxes[idx]
            keep = nms(boxes, scores, NMS_IOU)
            boxes, scores = boxes[keep], scores[keep]
        return boxes / INPUT_SIZE, scores


def build_core(weights: Path, embed_nms: bool) -> SSDLiteDetCore:
    model = ssdlite320_mobilenet_v3_large(weights=None, num_classes=2)
    model.load_state_dict(torch.load(weights, map_location="cpu"))
    model.eval()
    # Sanity : la normalisation qu'on embarque doit être celle du transform.
    assert model.transform.image_mean == [0.5, 0.5, 0.5], model.transform.image_mean
    assert model.transform.image_std == [0.5, 0.5, 0.5], model.transform.image_std
    core = SSDLiteDetCore(model, embed_nms=embed_nms)
    core.eval()
    return core


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path,
                        default=REPO_ROOT / "ml" / "runs" / "det_v3" / "best.pt")
    parser.add_argument("--out", type=Path,
                        default=REPO_ROOT / "ml" / "export" / "DetModel.mlpackage")
    parser.add_argument("--nms", default="embedded", choices=["embedded", "external"],
                        help="embedded = NMS dans le mlpackage ; external = 3234 sorties brutes")
    parser.add_argument("--precision", default="fp16", choices=["fp16", "fp32"])
    args = parser.parse_args()

    import coremltools as ct  # import tardif : lourd

    core = build_core(args.weights, embed_nms=(args.nms == "embedded"))
    example = torch.rand(1, 3, INPUT_SIZE, INPUT_SIZE) * 2 - 1
    with torch.no_grad():
        traced = torch.jit.trace(core, example)

    # Normalisation embarquée (piège n°1 du plan) : pixel_norm = pixel*2/255 - 1
    # == (pixel/255 - mean)/std avec mean=std=0.5.
    image_input = ct.ImageType(name="image", shape=(1, 3, INPUT_SIZE, INPUT_SIZE),
                               scale=2.0 / 255.0, bias=[-1.0, -1.0, -1.0],
                               color_layout=ct.colorlayout.RGB)
    mlmodel = ct.convert(
        traced,
        inputs=[image_input],
        outputs=[ct.TensorType(name="boxes"), ct.TensorType(name="scores")],
        convert_to="mlprogram",
        compute_precision=(ct.precision.FLOAT16 if args.precision == "fp16"
                           else ct.precision.FLOAT32),
        compute_units=ct.ComputeUnit.ALL,
        minimum_deployment_target=ct.target.iOS17,
    )

    mlmodel.author = "BrickOFF CH-3"
    mlmodel.short_description = ("DET lego_piece mono-classe — SSDLite320-MobileNetV3 "
                                 f"(det_v3), decode SSD intégré, NMS {args.nms}")
    mlmodel.version = "dry-run-det_v3"
    meta = {
        "brickoff.chantier": "CH-3 dry-run",
        "brickoff.source_weights": str(args.weights.relative_to(REPO_ROOT)
                                       if args.weights.is_relative_to(REPO_ROOT)
                                       else args.weights),
        "brickoff.export_date": datetime.now(timezone.utc).isoformat(),
        "brickoff.precision": args.precision,
        "brickoff.input": f"RGB {INPUT_SIZE}x{INPUT_SIZE}, resize scaleFill (pas d'aspect ratio), "
                          "normalisation embarquée (mean=std=0.5)",
        "brickoff.output": "boxes [N,4] XYXY normalisé 0-1 ; scores [N] proba lego_piece",
        "brickoff.nms": (f"embedded iou={NMS_IOU} topk={TOPK}" if args.nms == "embedded"
                         else "external — client doit appliquer NMS iou=0.55"),
        "brickoff.score_threshold_product": str(SCORE_THRESHOLD_PRODUCT),
        "brickoff.classes": json.dumps({"1": "lego_piece"}),
    }
    for k, v in meta.items():
        mlmodel.user_defined_metadata[k] = v

    args.out.parent.mkdir(parents=True, exist_ok=True)
    mlmodel.save(str(args.out))
    size_mb = sum(f.stat().st_size for f in args.out.rglob("*") if f.is_file()) / 1e6
    print(json.dumps({"out": str(args.out), "nms": args.nms,
                      "precision": args.precision, "size_mb": round(size_mb, 2)},
                     indent=2))


if __name__ == "__main__":
    main()
