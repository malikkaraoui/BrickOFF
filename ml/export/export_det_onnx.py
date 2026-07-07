"""Garde-fou D01 (amendement) — Export DET SSDLite320-MobileNetV3 (mono-classe) vers ONNX.

Voie Android (V2) : on valide DÈS MAINTENANT que le même champion (det_v3/best.pt)
et le MÊME wrapper de traçage que la voie CoreML (export_det.py : backbone + head
+ decode SSD tensoriel + anchors précalculées) s'exportent proprement vers ONNX.

Chaîne : best.pt -> SSDLiteDetCore (réutilisé tel quel depuis export_det.py)
-> wrapper normalisation in-graph -> torch.onnx.export (TorchScript exporter,
opset 18) -> DetModel.onnx.

Décisions (miroir des pièges CoreML documentés dans CHANGELOG_CH3.md) :

1. NORMALISATION IN-GRAPH. CoreML l'embarque via ImageType(scale=2/255, bias=-1) ;
   ONNX n'a pas d'équivalent ImageType, donc on l'embarque comme premier op du
   graphe : x_norm = image * 2/255 - 1. Contrat d'entrée Android :
   "image" float32 [1,3,320,320], RGB, ordre CHW, pixels BRUTS 0-255,
   resize scaleFill (PAS aspect-preserving — même contrat qu'iOS).
   => côté Android, zéro constante de normalisation à maintenir (juste
   bitmap RGB -> float 0-255 CHW), symétrie parfaite avec le mlpackage.

2. NMS : --nms embedded (défaut) via l'op ONNX standard `NonMaxSuppression`
   (torchvision::nms est converti par le symbolic torchvision, opset >= 11).
   Justification : NonMaxSuppression est un op ONNX standard supporté par
   ONNX Runtime (y c. Mobile, package android "full ops") -> même contrat de
   sortie qu'iOS (boxes [N<=300,4] XYXY normalisé 0-1 + scores [N] post-NMS,
   iou 0.55). Le client Android filtre juste score >= 0.35, comme Swift.
   Fallback --nms external (3234 sorties brutes, NMS client) conservé : requis
   si la cible devient TFLite/LiteT (les convertisseurs onnx2tf gèrent mal
   NonMaxSuppression) ou si un EP accéléré (NNAPI/QNN) rejette l'op et coupe
   le graphe en deux (NMS retombe alors sur CPU — acceptable, mais à profiler).

3. Shapes dynamiques post-NMS (N variable) : déclarées via dynamic_axes.
   Même piège qu'ANE côté iOS : les délégués NPU n'aiment pas ; d'où le
   fallback external à taille fixe 3234.

Sortie : DetModel.onnx (+ métadonnées metadata_props préfixe brickoff.*),
vérifié par onnx.checker + un forward onnxruntime CPU de contrôle.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch
from torch import Tensor, nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_det import (  # noqa: E402 — réutilisation du wrapper CoreML
    INPUT_SIZE, NMS_IOU, SCORE_THRESHOLD_PRODUCT, TOPK, build_core,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPSET = 18  # NonMaxSuppression dispo depuis opset 10/11 ; 18 = récent et stable


class DetOnnxModel(nn.Module):
    """SSDLiteDetCore + normalisation in-graph (pixels RGB 0-255 -> [-1, 1])."""

    def __init__(self, core: nn.Module) -> None:
        super().__init__()
        self.core = core

    def forward(self, image: Tensor) -> tuple[Tensor, Tensor]:
        # Équivalent exact de ct.ImageType(scale=2/255, bias=-1) côté CoreML,
        # soit (pixel/255 - 0.5) / 0.5 (transform torchvision mean=std=0.5).
        x = image * (2.0 / 255.0) - 1.0
        return self.core(x)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path,
                        default=REPO_ROOT / "ml" / "runs" / "det_v3" / "best.pt")
    parser.add_argument("--out", type=Path,
                        default=REPO_ROOT / "ml" / "export" / "DetModel.onnx")
    parser.add_argument("--nms", default="embedded", choices=["embedded", "external"],
                        help="embedded = op ONNX NonMaxSuppression dans le graphe ; "
                             "external = 3234 sorties brutes (requis pour voie TFLite)")
    args = parser.parse_args()

    embed_nms = args.nms == "embedded"
    core = build_core(args.weights, embed_nms=embed_nms)  # mêmes asserts normalisation
    model = DetOnnxModel(core).eval()
    example = torch.rand(1, 3, INPUT_SIZE, INPUT_SIZE) * 255.0

    dynamic_axes = ({"boxes": {0: "num_detections"}, "scores": {0: "num_detections"}}
                    if embed_nms else None)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with torch.no_grad():
        torch.onnx.export(
            model, (example,), str(args.out),
            input_names=["image"], output_names=["boxes", "scores"],
            opset_version=OPSET,
            dynamic_axes=dynamic_axes,
            dynamo=False,  # exporter TorchScript : symbolic torchvision::nms
        )

    import onnx

    m = onnx.load(str(args.out))
    onnx.checker.check_model(m)
    meta = {
        "brickoff.chantier": "D01 garde-fou Android — dry-run export ONNX",
        "brickoff.source_weights": str(args.weights.relative_to(REPO_ROOT)
                                       if args.weights.is_relative_to(REPO_ROOT)
                                       else args.weights),
        "brickoff.export_date": datetime.now(timezone.utc).isoformat(),
        "brickoff.opset": str(OPSET),
        "brickoff.input": f"image float32 [1,3,{INPUT_SIZE},{INPUT_SIZE}] CHW RGB, "
                          "pixels 0-255, resize scaleFill (pas d'aspect ratio), "
                          "normalisation IN-GRAPH (mean=std=0.5)",
        "brickoff.output": "boxes [N,4] XYXY normalisé 0-1 ; scores [N] proba lego_piece",
        "brickoff.nms": (f"embedded (op NonMaxSuppression) iou={NMS_IOU} topk={TOPK}"
                         if embed_nms else "external — client doit appliquer NMS iou=0.55"),
        "brickoff.score_threshold_product": str(SCORE_THRESHOLD_PRODUCT),
        "brickoff.classes": json.dumps({"1": "lego_piece"}),
    }
    del m.metadata_props[:]
    for k, v in meta.items():
        m.metadata_props.add(key=k, value=v)
    m.producer_name = "BrickOFF export_det_onnx"
    m.doc_string = ("DET lego_piece mono-classe — SSDLite320-MobileNetV3 (det_v3), "
                    f"decode SSD intégré, NMS {args.nms}")
    onnx.save(m, str(args.out))

    # Forward de contrôle onnxruntime CPU (sanity, pas la parité — voir
    # parity_check_onnx.py pour le protocole complet).
    import numpy as np
    import onnxruntime as ort

    sess = ort.InferenceSession(str(args.out), providers=["CPUExecutionProvider"])
    boxes, scores = sess.run(None, {"image": example.numpy()})
    nms_ops = sorted({n.op_type for n in m.graph.node if "NonMax" in n.op_type})

    size_mb = args.out.stat().st_size / 1e6
    print(json.dumps({
        "out": str(args.out), "nms": args.nms, "opset": OPSET,
        "size_mb": round(size_mb, 2),
        "onnx_checker": "OK",
        "ort_smoke": {"providers": sess.get_providers(),
                      "boxes_shape": list(boxes.shape), "scores_shape": list(scores.shape)},
        "nms_ops_in_graph": nms_ops,
    }, indent=2))


if __name__ == "__main__":
    main()
