"""Point 2 — Physique des pièces concaves : CONVEX_HULL vs MESH vs HYBRIDE.

Drop de 20 pièces concaves/complexes du scope (arches, brackets, Technic ajouré,
barre, clip, plaques fines, cheese slope, antenne), même seed pour les 3 méthodes.
Mesure : temps de bake, stabilité (passages sous le sol, éjections, non-settled),
hauteur/compacité du tas (quantifie le "gonflement" convex hull), et rend une image
640 px EEVEE par méthode pour comparaison visuelle.

Usage: Blender --background --python 02_physics.py
"""
import sys
import os
import math
import random
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import bpy  # type: ignore
import mathutils  # type: ignore
import numpy as np

OUT = common.OUT_DIR / "physics"
OUT.mkdir(exist_ok=True)

# (part_id, concave?) — concave -> MESH dans la variante hybride
PARTS = [
    ("3659", True),   # arche 1x4
    ("4490", True),   # arche 1x3
    ("6182", True),   # arche 1x4x2
    ("88292", True),  # arche 1x3x2
    ("92950", True),  # arche 1x5x4
    ("15254", True),  # arche 1x6x2
    ("44728", True),  # bracket 1x2-2x2
    ("99207", True),  # bracket 1x2-2x2 inversé
    ("3185", True),   # barrière 1x4x2 (ajourée)
    ("3700", True),   # Technic brique 1x2 trou
    ("3701", True),   # Technic brique 1x4 trous
    ("32000", True),  # Technic brique 1x2 deux trous
    ("32316", True),  # Technic poutre 5
    ("6541", True),   # Technic brique 1x1 trou
    ("61252", True),  # clip horizontal
    ("30374", False), # barre 4L (fine, convexe)
    ("3023", False),  # plaque 1x2 fine
    ("3623", False),  # plaque 1x3 fine
    ("54200", False), # cheese slope
    ("3957", False),  # antenne 4h
]

FRAME_END = 150
FLOOR_Z = 0.0
SEED = 42

# Variantes testées. Constat run 1 : MESH actif avec margin par défaut (0,04 unité
# = 1,6 mm) et 20 substeps explose (tunneling Bullet sur tri-mesh actifs).
# On teste marges réduites et substeps élevés avant de conclure.
VARIANTS = [
    # (nom, mode, margin (None = défaut 0.04), substeps, geo_scale)
    ("hull_default", "hull", None, 20, 1.0),
    ("hull_m002", "hull", 0.002, 20, 1.0),
    ("hull_m010", "hull", 0.01, 20, 1.0),
    # géométrie x5 : marge Bullet par défaut = 0,32 mm équivalent au lieu de 1,6 mm
    ("hull_scale5", "hull", None, 20, 5.0),
    ("mesh_m002_s60", "mesh", 0.002, 60, 1.0),
    ("hybrid_m002_s60", "hybrid", 0.002, 60, 1.0),
]


def build_scene(method: str, margin, substeps: int, S: float) -> dict:
    common.reset_scene()
    common.setup_world(strength=0.8)
    common.add_sun(energy=4.0)
    common.setup_eevee(res=640, samples=32, transparent=False)
    common.ensure_camera()
    common.ensure_rbworld(frame_end=FRAME_END, substeps=substeps, iterations=20)

    # sol : boîte fine passive
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.05 * S))
    floor = bpy.context.active_object
    floor.name = "floor"
    floor.scale = (12 * S, 12 * S, 0.05 * S)
    bpy.ops.object.transform_apply(scale=True)
    common.add_rigidbody(floor, shape="BOX", active=False, friction=0.8,
                         margin=margin)

    rng = random.Random(SEED)
    pieces = []
    info = []
    for i, (pid, concave) in enumerate(PARTS):
        dat, _ = common.resolve_part_file(pid)
        obj = common.import_part(dat, name=f"p{i:02d}_{pid}")
        if S != 1.0:
            obj.data.transform(mathutils.Matrix.Scale(S, 4))
        common.assign_debug_material(obj, i)
        # position de chute déterministe (même seed pour chaque méthode)
        x = rng.uniform(-0.35, 0.35) * S
        y = rng.uniform(-0.35, 0.35) * S
        z = (0.6 + i * 0.28) * S
        rot = (rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi),
               rng.uniform(0, 2 * math.pi))
        obj.location = (x, y, z)
        obj.rotation_euler = rot

        if method == "hull":
            shape = "CONVEX_HULL"
        elif method == "mesh":
            shape = "MESH"
        else:  # hybrid
            shape = "MESH" if concave else "CONVEX_HULL"
        common.add_rigidbody(obj, shape=shape, active=True, mass=0.01, friction=0.7,
                             margin=margin)
        pieces.append(obj)
        info.append({"pid": pid, "concave": concave, "shape": shape,
                     "n_vertices": len(obj.data.vertices)})
    return {"floor": floor, "pieces": pieces, "info": info}


def pile_metrics(pieces, frame: int, S: float = 1.0) -> dict:
    mats = {}
    bpy.context.scene.frame_set(frame)
    deps = bpy.context.evaluated_depsgraph_get()
    for o in pieces:
        mats[o.name] = np.array(o.evaluated_get(deps).matrix_world)
    zs, radii, all_top = [], [], []
    per_piece = []
    for o in pieces:
        m = mats[o.name]
        loc = m[:3, 3]
        n = len(o.data.vertices)
        co = np.empty(n * 3, dtype=np.float32)
        o.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        world = co @ m[:3, :3].T + m[:3, 3]
        zmin, zmax = float(world[:, 2].min()), float(world[:, 2].max())
        r = float(np.linalg.norm(loc[:2]))
        zs.append(loc[2])
        radii.append(r)
        all_top.append(zmax)
        per_piece.append({
            "name": o.name,
            "loc": [round(float(v), 4) for v in loc],
            "zmin": round(zmin, 4), "zmax": round(zmax, 4),
            "below_floor": bool(zmin < FLOOR_Z - 0.02 * S),
            "ejected": bool(r > 2.0 * S),
            "finite": bool(np.all(np.isfinite(m))),
        })
    return {
        "pile_height": round(max(all_top), 4),
        "mean_radius": round(float(np.mean(radii)), 4),
        "per_piece": per_piece,
    }


def settling(pieces, f0: int, f1: int) -> float:
    """Déplacement max des origines entre f0 et f1 (tas posé si ~0)."""
    a = {o.name: np.array(common.eval_matrix(o, f0).translation) for o in pieces}
    b = {o.name: np.array(common.eval_matrix(o, f1).translation) for o in pieces}
    return round(max(float(np.linalg.norm(a[k] - b[k])) for k in a), 5)


def run_method(name: str, method: str, margin, substeps: int, S: float) -> dict:
    print(f"[physics] === variante {name} ===")
    scene_objs = build_scene(method, margin, substeps, S)
    pieces = scene_objs["pieces"]

    t_bake = common.bake_physics()
    print(f"[physics] bake {name}: {t_bake:.1f}s")

    metrics = pile_metrics(pieces, FRAME_END, S)
    move = settling(pieces, FRAME_END - 20, FRAME_END)
    n_below = sum(p["below_floor"] for p in metrics["per_piece"])
    n_eject = sum(p["ejected"] for p in metrics["per_piece"])
    n_nan = sum(not p["finite"] for p in metrics["per_piece"])

    # fige les transforms et rend l'image de comparaison
    common.apply_visual_transforms(pieces, FRAME_END)
    cam = bpy.context.scene.camera
    visible = [o for o in pieces if o.location.length < 3.0 * S]
    common.frame_camera(cam, visible or pieces, margin=1.1, direction=(1.0, -1.0, 0.65))
    png = OUT / f"pile_{name}.png"
    common.set_output_png(png)
    t_render = common.render_still()

    return {
        "variant": name,
        "method": method,
        "margin": margin,
        "substeps": substeps,
        "geo_scale": S,
        "bake_s": round(t_bake, 2),
        "render_s": round(t_render, 2),
        "settle_move_130_150": round(move / S, 5),
        "pile_height_units": metrics["pile_height"],
        "pile_height_mm": round(metrics["pile_height"] * common.UNIT_TO_MM / S, 1),
        "mean_radius_units": metrics["mean_radius"],
        "n_below_floor": n_below,
        "n_ejected": n_eject,
        "n_nan": n_nan,
        "per_piece": metrics["per_piece"],
        "shapes": scene_objs["info"],
        "render": str(png),
    }


def main():
    global FRAME_END
    only = os.environ.get("PHYS_ONLY")
    FRAME_END = int(os.environ.get("PHYS_FRAMES", FRAME_END))
    variants = [v for v in VARIANTS if only is None or v[0] == only]
    out_json = OUT / ("physics_results.json" if only is None
                      else f"physics_results_{only}_f{FRAME_END}.json")
    results = {"seed": SEED, "n_pieces": len(PARTS), "frame_end": FRAME_END,
               "methods": []}
    for name, method, margin, substeps, S in variants:
        results["methods"].append(run_method(name, method, margin, substeps, S))
    common.json_dump(out_json, results)
    for r in results["methods"]:
        print(f"[physics] {r['variant']:16s} bake={r['bake_s']:7.2f}s "
              f"h_tas={r['pile_height_mm']:6.1f}mm below={r['n_below_floor']} "
              f"eject={r['n_ejected']} nan={r['n_nan']} settle={r['settle_move_130_150']}")
    print(f"[physics] -> {OUT / 'physics_results.json'}")


main()
