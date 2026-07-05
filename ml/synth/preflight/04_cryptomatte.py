"""Point 4 — Cryptomatte-EEVEE en headless : décodage + alignement.

Pour 3 seeds : tas simulé de 15 pièces qui se chevauchent -> UN rendu EEVEE
multilayer EXR (Combined + CryptoObject00..02, film transparent, sol caché) ->
décodage des masques par pièce via OpenImageIO (manifest du header EXR, fallback
hash mmh3 des noms d'objets) -> bbox visible + coverage par pièce ->
IoU(union des masques, silhouette alpha du beauty) — critère >= 0,99.

Usage: Blender --background --python 04_cryptomatte.py
"""
import sys
import os
import math
import random
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import bpy  # type: ignore
import numpy as np

OUT = common.OUT_DIR / "crypto"
OUT.mkdir(exist_ok=True)

PARTS_POOL = ["3023", "3623", "2420", "11477", "54200", "3070b", "3024", "6141",
              "4070", "98138", "3062", "63864", "3710", "3666", "2431"]
FRAME_END = 120
RES = 640


def build_pile(seed: int):
    common.reset_scene()
    common.setup_world(strength=0.8)
    common.add_sun(energy=4.0)
    common.ensure_camera()
    common.ensure_rbworld(frame_end=FRAME_END, substeps=20, iterations=20)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.05))
    floor = bpy.context.active_object
    floor.name = "floor"
    floor.scale = (12, 12, 0.05)
    bpy.ops.object.transform_apply(scale=True)
    common.add_rigidbody(floor, shape="BOX", active=False, friction=0.8)

    rng = random.Random(seed)
    pieces = []
    for i, pid in enumerate(PARTS_POOL):
        dat, _ = common.resolve_part_file(pid)
        obj = common.import_part(dat, name=f"c{i:02d}_{pid}")
        common.assign_debug_material(obj, i)
        # chute serrée -> chevauchements écran garantis
        obj.location = (rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12),
                        0.4 + i * 0.22)
        obj.rotation_euler = (rng.uniform(0, 2 * math.pi),
                              rng.uniform(0, 2 * math.pi),
                              rng.uniform(0, 2 * math.pi))
        common.add_rigidbody(obj, shape="CONVEX_HULL", active=True, mass=0.01,
                             friction=0.7)
        pieces.append(obj)
    common.bake_physics()
    common.apply_visual_transforms(pieces, FRAME_END)
    floor.hide_render = True  # silhouette alpha = pièces uniquement
    return pieces


def render_crypto_exr(pieces, exr_path, res: int) -> float:
    scene = bpy.context.scene
    common.setup_eevee(res=res, samples=32, transparent=True)
    vl = bpy.context.view_layer
    vl.use_pass_cryptomatte_object = True
    if hasattr(vl, "pass_cryptomatte_depth"):
        vl.pass_cryptomatte_depth = 6
    # ignore les pièces éjectées loin du tas pour le cadrage
    kept = [o for o in pieces if o.location.length < 1.5] or pieces
    common.frame_camera(scene.camera, kept, margin=1.15, direction=(0.5, -0.6, 1.0))
    common.set_output_exr_multilayer(exr_path)
    return common.render_still()


def decode(exr_path, piece_names):
    t0 = time.perf_counter()
    channels, attrs = common.read_exr_all(exr_path)
    manifest = common.crypto_manifest(attrs)
    source = "manifest_exr"
    if manifest is None:
        manifest = {n: common.crypto_name_to_float(n) for n in piece_names}
        source = "mmh3_fallback"
    ids, covs = common.crypto_rank_planes(channels)

    alpha = None
    for key, arr in channels.items():
        if key.endswith("Combined.A"):
            alpha = arr
            break

    per_piece = {}
    union = np.zeros_like(covs[0])
    for name in piece_names:
        fid = manifest.get(name)
        if fid is None:
            per_piece[name] = {"error": "absent_du_manifest"}
            continue
        mask = common.crypto_coverage_for(ids, covs, fid)
        union += mask
        per_piece[name] = {
            "coverage_px": round(float(mask.sum()), 1),
            "bbox_thr05": common.mask_bbox(mask, 0.5),
            "bbox_thr0": common.mask_bbox(mask, 1e-3),
        }
    decode_s = time.perf_counter() - t0

    iou = None
    if alpha is not None:
        u = union >= 0.5
        a = alpha >= 0.5
        inter = float(np.logical_and(u, a).sum())
        uni = float(np.logical_or(u, a).sum())
        iou = inter / uni if uni else 0.0
    return {"per_piece": per_piece, "iou_union_vs_alpha": iou,
            "manifest_source": source, "decode_s": round(decode_s, 2),
            "union": union, "alpha": alpha}


def viz(exr_channels_union, alpha, path):
    """PNG de contrôle : union des masques (R) vs alpha (G) — mismatch = couleurs pures."""
    h, w = alpha.shape
    rgb = np.zeros((h, w, 3), dtype=np.float32)
    rgb[:, :, 0] = np.clip(exr_channels_union, 0, 1)
    rgb[:, :, 1] = np.clip(alpha, 0, 1)
    common.write_png_rgb(path, rgb)


def main():
    results = {"res": RES, "n_pieces": len(PARTS_POOL), "scenes": []}
    for seed in (101, 102, 103):
        pieces = build_pile(seed)
        names = [o.name for o in pieces]
        exr = OUT / f"scene_{seed}.exr"
        t_render = render_crypto_exr(pieces, exr, RES)
        dec = decode(exr, names)
        viz(dec["union"], dec["alpha"], OUT / f"align_{seed}.png")
        # beauty PNG de contrôle visuel
        common.set_output_png(OUT / f"beauty_{seed}.png")
        common.render_still()
        n_visible = sum(1 for v in dec["per_piece"].values()
                        if v.get("bbox_thr05") is not None)
        rec = {
            "seed": seed,
            "render_s": round(t_render, 2),
            "decode_s": dec["decode_s"],
            "manifest_source": dec["manifest_source"],
            "iou_union_vs_alpha": round(dec["iou_union_vs_alpha"], 5)
            if dec["iou_union_vs_alpha"] is not None else None,
            "n_pieces_visibles_thr05": n_visible,
            "per_piece": dec["per_piece"],
            "exr_mb": round(exr.stat().st_size / 1e6, 2),
        }
        results["scenes"].append(rec)
        print(f"[crypto] seed={seed} IoU={rec['iou_union_vs_alpha']} "
              f"render={rec['render_s']}s decode={rec['decode_s']}s "
              f"manifest={rec['manifest_source']} visibles={n_visible}/15")
    common.json_dump(OUT / "crypto_results.json", results)
    print(f"[crypto] -> {OUT / 'crypto_results.json'}")


main()
