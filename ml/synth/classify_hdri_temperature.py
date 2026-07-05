#!/usr/bin/env python
"""Classify HDRI color temperature by pixel sampling.

Method (documented for the manifest):
- load the 2k Radiance HDR (linear RGB, float32) with OpenCV;
- downsample to ~256px wide (area filter);
- compute the LUMINANCE-WEIGHTED mean RGB (weights = Rec.709 luminance,
  clipped at the 99.5th percentile so a single tiny sun/lamp pixel cannot
  dominate alone) -> the average color of the light the HDRI actually casts;
- ratio R/B of that mean, and CCT estimate: linear sRGB -> XYZ (D65) -> xy
  -> McCamy 1992 approximation;
- classes: warm  = CCT < 4500 K (or R/B > 1.35),
           cold  = CCT > 5800 K and R/B < 1.05,
           neutral otherwise.
"""
import glob, json, os, sys
import cv2
import numpy as np

# Usage: python classify_hdri_temperature.py <dossier_hdr> [sortie.json]
OUT = sys.argv[2] if len(sys.argv) > 2 else "hdri_thermal.json"

def analyze(path):
    img = cv2.imread(path, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
    if img is None:
        raise RuntimeError("unreadable")
    img = cv2.resize(img, (256, 128), interpolation=cv2.INTER_AREA)
    rgb = img[:, :, ::-1].astype(np.float64)  # BGR -> RGB, linear
    lum = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    cap = np.percentile(lum, 99.5)
    w = np.clip(lum, 0, cap)
    w = w / (w.sum() + 1e-12)
    mean = (rgb * w[:, :, None]).sum(axis=(0, 1))  # weighted mean RGB
    r, g, b = mean
    rb = float(r / max(b, 1e-9))
    # linear sRGB -> XYZ (D65)
    X = 0.4124 * r + 0.3576 * g + 0.1805 * b
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Z = 0.0193 * r + 0.1192 * g + 0.9505 * b
    s = X + Y + Z
    x, y = X / s, Y / s
    n = (x - 0.3320) / (0.1858 - y)
    cct = 449.0 * n**3 + 3525.0 * n**2 + 6823.3 * n + 5520.33  # McCamy
    return rb, float(cct)

def classify(rb, cct):
    if not (1000 <= cct <= 25000):
        # McCamy out of validity range (extreme chromaticity): R/B only
        return "warm" if rb > 1.35 else ("cold" if rb < 1.05 else "neutral")
    if cct < 4500 or rb > 1.35:
        return "warm"
    if cct > 5800 and rb < 1.05:
        return "cold"
    return "neutral"

def main(folder):
    res = {}
    for p in sorted(glob.glob(os.path.join(folder, "*.hdr"))):
        hid = os.path.basename(p).replace("_2k.hdr", "")
        try:
            rb, cct = analyze(p)
            res[hid] = {"rb_ratio": round(rb, 3), "cct_est_K": round(cct),
                        "thermal_class": classify(rb, cct)}
            print(f"{hid:35s} R/B={rb:5.2f}  CCT~{cct:6.0f}K  -> {res[hid]['thermal_class']}")
        except Exception as e:
            print(f"{hid:35s} FAIL {e}")
    counts = {}
    for v in res.values():
        counts[v["thermal_class"]] = counts.get(v["thermal_class"], 0) + 1
    n = len(res)
    print(f"\nTotal {n} | " + " | ".join(f"{k}: {v} ({100*v/n:.0f}%)" for k, v in sorted(counts.items())))
    json.dump(res, open(OUT, "w"), indent=1)

if __name__ == "__main__":
    main(sys.argv[1])
