"""CH-S / S.3 — Post-process capteur smartphone (PIL + numpy, hors Blender).

Appliqué sur les PNG rendus APRÈS extraction des labels — ne touche JAMAIS aux
labels (plan 16, décision "DoF jamais dans le rendu"). Pipeline par image, tous
les paramètres tirés PAR IMAGE (seed scène + offset) et tracés dans le manifest
(clé "postprocess") :

  1. DoF simulé simple    flou progressif hors zone centrale (approximation)
  2. Flou de bougé        directionnel <= 1,5 px (moyenne de décalages sub-pixel)
  3. Vignettage léger     assombrissement radial
  4. Dérive AWB           ±800 K (gains RGB en linéaire)
  5. Bruit ISO            gaussien (lecture) + poisson léger (photons), en linéaire
  6. Compression JPEG     qualité 70-95 — l'image finale devient .jpg (.png supprimé)

Usage :
  .venv/bin/python ml/synth/postprocess.py --dataset-dir data/processed/synth_v11_val
  (ou automatiquement via generate_scenes.py ; --no-postprocess pour debug)
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

SEED_OFFSET = 1000003  # seed image = seed scène + offset (reproductible, décorrélé)


# ---------------------------------------------------------------------------
# Couleur
# ---------------------------------------------------------------------------


def kelvin_to_rgb(t: float) -> np.ndarray:
    """Approximation Tanner Helland (identique à blender_scene.py)."""
    t = min(max(t, 1000.0), 12000.0) / 100.0
    if t <= 66:
        r = 255.0
        g = 99.4708025861 * math.log(t) - 161.1195681661
    else:
        r = 329.698727446 * ((t - 60) ** -0.1332047592)
        g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    if t >= 66:
        b = 255.0
    elif t <= 19:
        b = 0.0
    else:
        b = 138.5177312231 * math.log(t - 10) - 305.0447927307
    rgb = np.array([min(max(v, 0.0), 255.0) / 255.0 for v in (r, g, b)])
    return rgb / rgb.max()


def srgb_to_linear(a: np.ndarray) -> np.ndarray:
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(a: np.ndarray) -> np.ndarray:
    a = np.clip(a, 0.0, 1.0)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)


# ---------------------------------------------------------------------------
# Tirage des paramètres (par image, tracé dans le manifest)
# ---------------------------------------------------------------------------


def draw_params(rng: random.Random, cfg: dict) -> dict:
    prm: dict = {}
    if rng.random() < cfg["dof_p"]:
        prm["dof"] = {
            "sharp_radius": round(rng.uniform(*cfg["dof_sharp_radius"]), 3),
            "max_sigma": round(rng.uniform(*cfg["dof_max_sigma"]), 3),
            "cx": round(0.5 + rng.uniform(-1, 1) * cfg["dof_center_jitter"], 3),
            "cy": round(0.5 + rng.uniform(-1, 1) * cfg["dof_center_jitter"], 3),
        }
    if rng.random() < cfg["motion_blur_p"]:
        prm["motion"] = {"length_px": round(rng.uniform(*cfg["motion_blur_px"]), 3),
                         "angle_deg": round(rng.uniform(0.0, 180.0), 1)}
    if rng.random() < cfg["vignette_p"]:
        prm["vignette"] = round(rng.uniform(*cfg["vignette_strength"]), 3)
    prm["wb_delta_k"] = round(rng.uniform(*cfg["wb_delta_k"]), 1)
    prm["noise_read_sigma"] = round(rng.uniform(*cfg["noise_read_sigma"]), 5)
    prm["noise_photon_fullwell"] = round(rng.uniform(*cfg["noise_photon_fullwell"]))
    prm["jpeg_quality"] = rng.randint(*cfg["jpeg_quality"])
    prm["sat_boost"] = round(rng.uniform(*cfg["sat_boost"]), 3)
    prm["contrast_s"] = round(rng.uniform(*cfg["contrast_s"]), 3)
    return prm


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def radial_map(h: int, w: int, cx: float = 0.5, cy: float = 0.5) -> np.ndarray:
    """Distance normalisée au centre (1.0 = demi-diagonale)."""
    ys, xs = np.mgrid[0:h, 0:w]
    dx = (xs + 0.5) / w - cx
    dy = (ys + 0.5) / h - cy
    return np.sqrt(dx * dx + dy * dy) / (math.sqrt(2.0) / 2.0)


def apply_dof(img: Image.Image, d: dict) -> Image.Image:
    """Flou progressif hors zone centrale — approximation DoF acceptée au plan."""
    blurred = img.filter(ImageFilter.GaussianBlur(radius=d["max_sigma"]))
    r = radial_map(img.height, img.width, d["cx"], d["cy"])
    rs = d["sharp_radius"]
    wgt = np.clip((r - rs) / max(1.0 - rs, 1e-3), 0.0, 1.0) ** 1.5
    a = np.asarray(img, dtype=np.float32)
    b = np.asarray(blurred, dtype=np.float32)
    out = a * (1.0 - wgt[..., None]) + b * wgt[..., None]
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))


def apply_motion_blur(img: Image.Image, m: dict) -> Image.Image:
    """Segment <= 1,5 px : moyenne de K copies décalées sub-pixel (bilinéaire)."""
    length = m["length_px"]
    ang = math.radians(m["angle_deg"])
    k = 5
    acc = np.zeros((img.height, img.width, 3), dtype=np.float32)
    for i in range(k):
        t = (i / (k - 1) - 0.5) * length
        dx, dy = t * math.cos(ang), t * math.sin(ang)
        sh = img.transform(img.size, Image.AFFINE, (1, 0, dx, 0, 1, dy),
                           resample=Image.BILINEAR)
        acc += np.asarray(sh, dtype=np.float32)
    return Image.fromarray(np.clip(acc / k + 0.5, 0, 255).astype(np.uint8))


def apply_sensor(img: Image.Image, prm: dict, nprng: np.random.Generator,
                 base_k: float) -> Image.Image:
    """Vignettage + dérive AWB + bruit ISO — travaillés en linéaire."""
    a = np.asarray(img, dtype=np.float32) / 255.0
    lin = srgb_to_linear(a)
    if "vignette" in prm:
        r = radial_map(img.height, img.width)
        lin *= (1.0 - prm["vignette"] * r * r)[..., None]
    gains = kelvin_to_rgb(base_k) / kelvin_to_rgb(base_k + prm["wb_delta_k"])
    gains = gains / gains[1]  # normalisé au canal vert (exposition inchangée)
    lin *= gains[None, None, :].astype(np.float32)
    sigma = np.sqrt(np.clip(lin, 0.0, None) / prm["noise_photon_fullwell"]
                    + prm["noise_read_sigma"] ** 2)
    lin += nprng.standard_normal(lin.shape, dtype=np.float32) * sigma
    out = linear_to_srgb(np.clip(lin, 0.0, 1.0))
    # signature ISP téléphone : vibrance + courbe en S en espace d'affichage,
    # après AWB — corrige le voile pastel désaturé (spot-the-fake, tell n°3)
    luma = (0.2126 * out[..., 0] + 0.7152 * out[..., 1] + 0.0722 * out[..., 2])[..., None]
    out = np.clip(luma + (out - luma) * prm.get("sat_boost", 1.0), 0.0, 1.0)
    c = prm.get("contrast_s", 0.0)
    out = np.clip(out + c * (out * out * (3.0 - 2.0 * out) - out), 0.0, 1.0)
    return Image.fromarray(np.clip(out * 255.0 + 0.5, 0, 255).astype(np.uint8))


def process_image(png_path: Path, jpg_path: Path, seed: int, cfg: dict) -> dict:
    rng = random.Random(seed)
    nprng = np.random.default_rng(seed)
    prm = draw_params(rng, cfg)
    with Image.open(png_path) as im:
        img = im.convert("RGB")
    if "dof" in prm:
        img = apply_dof(img, prm["dof"])
    if "motion" in prm:
        img = apply_motion_blur(img, prm["motion"])
    img = apply_sensor(img, prm, nprng, cfg["wb_base_k"])
    img.save(jpg_path, "JPEG", quality=prm["jpeg_quality"], subsampling=1)
    return prm


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


def process_dataset(out_dir: Path, cfg: dict, overwrite: bool = False,
                    keep_png: bool = False, limit: int | None = None) -> dict:
    """Post-traite toutes les scènes du dataset (manifests/ = source de vérité).

    Idempotent : une scène déjà post-traitée (manifest "postprocess" + .jpg
    présent) est sautée sauf --overwrite. Met à jour chaque manifest :
    params tirés + champ image -> .jpg. Les labels ne sont JAMAIS touchés.
    """
    manifests = sorted((out_dir / "manifests").glob("*.json"))
    if limit:
        manifests = manifests[:limit]
    t0 = time.perf_counter()
    n_done = n_skip = 0
    errors: list[str] = []
    for mpath in manifests:
        man = json.loads(mpath.read_text())
        name = man["scene_id"]
        png = out_dir / "images" / f"{name}.png"
        jpg = out_dir / "images" / f"{name}.jpg"
        if man.get("postprocess") and jpg.exists() and not overwrite:
            n_skip += 1
            continue
        if not png.exists():
            errors.append(f"{name}: PNG source manquant")
            continue
        seed = int(man["seed"]) + SEED_OFFSET
        try:
            ts = time.perf_counter()
            prm = process_image(png, jpg, seed, cfg)
            prm["seed"] = seed
            prm["post_s"] = round(time.perf_counter() - ts, 3)
            man["postprocess"] = prm
            man["image"] = f"images/{name}.jpg"
            mpath.write_text(json.dumps(man, indent=1, ensure_ascii=False))
            if not keep_png:
                png.unlink()
            n_done += 1
        except Exception as e:  # noqa: BLE001
            errors.append(f"{name}: {type(e).__name__}: {e}")
    wall = time.perf_counter() - t0
    stats = {"n_done": n_done, "n_skipped": n_skip, "errors": errors,
             "wall_s": round(wall, 1),
             "s_per_image": round(wall / max(n_done, 1), 3)}
    print(f"[post] {n_done} images post-traitées, {n_skip} sautées, "
          f"{len(errors)} erreurs — {stats['s_per_image']} s/image")
    for e in errors[:10]:
        print(f"  - {e}")
    return stats


def main() -> None:
    import yaml

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path,
                    default=Path(__file__).parent / "config_v1.yaml")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--keep-png", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    cfg = yaml.safe_load(args.config.read_text())["postprocess"]
    stats = process_dataset(args.dataset_dir, cfg, overwrite=args.overwrite,
                            keep_png=args.keep_png, limit=args.limit)
    run_dir = args.dataset_dir / "run"
    if run_dir.exists():
        (run_dir / "postprocess_stats.json").write_text(json.dumps(stats, indent=1))
    if stats["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
