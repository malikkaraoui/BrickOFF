"""Point 5 — Stabilité des masques sur pièces fines.

Scène statique de 5 pièces fines (barre 30374, cheese slope 54200 posé de chant,
antenne 3957, plaque 1x1 3024, tuile 1x1 3070b). Pour 3 poses caméra proches
(jitter ~1 % de la distance + visée re-calculée), extraction des coverages par
Cryptomatte à 640 px puis à 1280 px. Mesure : dispersion relative du coverage par
pièce entre les 3 rendus, pixels min, et surcoût du rendu x2.

Usage: Blender --background --python 05_thin.py
"""
import sys
import os
import math
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import bpy  # type: ignore
import mathutils  # type: ignore
import numpy as np

OUT = common.OUT_DIR / "thin"
OUT.mkdir(exist_ok=True)

# (pid, position xy, rotation euler) — placement statique, pas de simulation
LAYOUT = [
    ("30374", (-0.5, 0.3), (0, math.pi / 2, 0.4)),        # barre 4L couchée
    ("54200", (0.0, 0.0), (math.pi / 2, 0, 0.2)),          # cheese slope de chant
    ("3957", (0.45, 0.35), (0, 0, 0)),                     # antenne debout
    ("3024", (-0.35, -0.4), (0, 0, 0.7)),                  # plaque 1x1
    ("3070b", (0.4, -0.35), (0, 0, 1.1)),                  # tuile 1x1
]


def build_scene():
    common.reset_scene()
    common.setup_world(strength=0.8)
    common.add_sun(energy=4.0)
    common.ensure_camera()
    pieces = []
    for i, (pid, (x, y), rot) in enumerate(LAYOUT):
        dat, _ = common.resolve_part_file(pid)
        obj = common.import_part(dat, name=f"t{i}_{pid}")
        common.assign_debug_material(obj, i)
        obj.rotation_euler = rot
        bpy.context.view_layer.update()
        # pose la pièce au sol z=0 selon sa bbox tournée
        deps = bpy.context.evaluated_depsgraph_get()
        n = len(obj.data.vertices)
        co = np.empty(n * 3, dtype=np.float32)
        obj.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        m = np.array(obj.matrix_world)
        world = co @ m[:3, :3].T + m[:3, 3]
        obj.location = (x, y, obj.location.z - float(world[:, 2].min()))
        pieces.append(obj)
    return pieces


def camera_pose(pieces, jitter_seed: int | None, margin: float):
    cam = bpy.context.scene.camera
    cam.data.lens = 35
    common.frame_camera(cam, pieces, margin=margin, direction=(0.6, -0.8, 0.9))
    if jitter_seed is not None:
        rng = random.Random(jitter_seed)
        center = sum((o.location for o in pieces), mathutils.Vector((0, 0, 0))) / len(pieces)
        dist = (cam.location - center).length
        cam.location += mathutils.Vector(
            (rng.gauss(0, 0.01 * dist), rng.gauss(0, 0.01 * dist),
             rng.gauss(0, 0.01 * dist)))
        common.look_at(cam, center)


def render_and_decode(pieces, res: int, tag: str, seed: int):
    scene = bpy.context.scene
    common.setup_eevee(res=res, samples=32, transparent=True)
    vl = bpy.context.view_layer
    vl.use_pass_cryptomatte_object = True
    if hasattr(vl, "pass_cryptomatte_depth"):
        vl.pass_cryptomatte_depth = 6
    exr = OUT / f"thin_{tag}_{seed}.exr"
    common.set_output_exr_multilayer(exr)
    t = common.render_still()
    channels, attrs = common.read_exr_all(exr)
    manifest = common.crypto_manifest(attrs)
    if manifest is None:
        manifest = {o.name: common.crypto_name_to_float(o.name) for o in pieces}
    ids, covs = common.crypto_rank_planes(channels)
    out = {}
    for o in pieces:
        mask = common.crypto_coverage_for(ids, covs, manifest[o.name])
        out[o.name] = {"coverage_px": float(mask.sum()),
                       "bbox_thr05": common.mask_bbox(mask, 0.5)}
    exr.unlink()  # 32 bits, lourd — on ne garde que les chiffres
    return t, out


def run_resolution(pieces, res: int, margin: float) -> dict:
    runs = []
    times = []
    for seed in (1, 2, 3):
        camera_pose(pieces, jitter_seed=None if seed == 1 else seed, margin=margin)
        t, cov = render_and_decode(pieces, res, f"r{res}_m{margin}", seed)
        times.append(t)
        runs.append(cov)
        if seed == 1:
            common.set_output_png(OUT / f"beauty_{res}_m{margin}.png")
            common.render_still()
    stats = {}
    for name in runs[0]:
        vals = [r[name]["coverage_px"] for r in runs]
        # normalise sur l'aire (res/640)^2 pour comparer entre résolutions
        norm = (res / 640.0) ** 2
        mean = float(np.mean(vals))
        stats[name] = {
            "coverage_px": [round(v, 1) for v in vals],
            "coverage_px_eq640": [round(v / norm, 1) for v in vals],
            "mean_px": round(mean, 1),
            "rel_spread": round((max(vals) - min(vals)) / mean, 4) if mean > 0 else None,
            "bboxes": [r[name]["bbox_thr05"] for r in runs],
        }
    return {"res": res, "render_s": [round(t, 2) for t in times],
            "render_s_mean": round(float(np.mean(times)), 2), "pieces": stats}


def main():
    pieces = build_scene()
    results = {"layout": [p[0] for p in LAYOUT], "resolutions": []}
    # margin 1.2 = pièces en gros plan ; margin 3.2 = taille apparente type
    # cadrage tas (pièces ~7x plus petites en aire)
    for res, margin in ((640, 1.2), (1280, 1.2), (640, 3.2), (1280, 3.2)):
        r = run_resolution(pieces, res, margin)
        r["margin"] = margin
        results["resolutions"].append(r)
        worst = max((s["rel_spread"] or 0) for s in r["pieces"].values())
        smallest = min(s["mean_px"] for s in r["pieces"].values())
        print(f"[thin] res={res} margin={margin}: render={r['render_s_mean']}s "
              f"pire dispersion relative={worst:.3f} plus petite pièce={smallest:.0f}px")
    common.json_dump(OUT / "thin_results.json", results)
    print(f"[thin] -> {OUT / 'thin_results.json'}")


main()
