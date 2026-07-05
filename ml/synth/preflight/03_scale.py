"""Point 3 — Assertion d'échelle (BLOQUANT).

Importe la brique 3001 (2x4), mesure ses dimensions en unités scène, convertit en mm
(1 LDU = 0,4 mm ; scene_scale addon = 0,01 -> 1 unité = 40 mm) et vérifie ~31,8 x 15,8 mm.
Teste aussi l'effet de add_gap_between_parts (True par défaut dans l'addon).

Usage: Blender --background --python 03_scale.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import common

importlib.reload(common)
import bpy  # type: ignore
import numpy as np


def measure(gap: bool) -> dict:
    common.reset_scene()
    before = set(bpy.data.objects)
    bpy.ops.import_scene.importldr(
        filepath=str(common.PARTS_DIR / "3001.dat"),
        ldraw_path=str(common.LDRAW_PATH),
        instance_type="LinkedDuplicates",
        add_gap_between_parts=gap,
    )
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH" and o.data and len(o.data.vertices)]
    assert meshes, "3001.dat: aucun mesh importé"
    pts = []
    for o in meshes:
        n = len(o.data.vertices)
        co = np.empty(n * 3, dtype=np.float64)
        o.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        mw = np.array(o.matrix_world)
        world = co @ mw[:3, :3].T + mw[:3, 3]
        pts.append(world)
    allpts = np.concatenate(pts)
    dims_units = (allpts.max(axis=0) - allpts.min(axis=0)).tolist()
    dims_mm = [d * common.UNIT_TO_MM for d in dims_units]
    # tri décroissant : longueur, largeur, hauteur (hauteur avec tenons ~11,4 mm)
    s = sorted(dims_mm, reverse=True)
    return {
        "add_gap_between_parts": gap,
        "n_vertices": int(sum(len(o.data.vertices) for o in meshes)),
        "dims_units_xyz": dims_units,
        "dims_mm_sorted": s,
        "unit_to_mm": common.UNIT_TO_MM,
    }


def main():
    results = {"part": "3001", "expected_mm": [31.8, 15.8], "measures": []}
    for gap in (True, False):
        m = measure(gap)
        results["measures"].append(m)
        print(f"[scale] gap={gap}: L={m['dims_mm_sorted'][0]:.3f} mm, "
              f"l={m['dims_mm_sorted'][1]:.3f} mm, h={m['dims_mm_sorted'][2]:.3f} mm")

    # verdict sur la config par défaut (gap=True), tolérance +/- 0,5 mm
    ref = results["measures"][0]["dims_mm_sorted"]
    ok = abs(ref[0] - 31.8) <= 0.5 and abs(ref[1] - 15.8) <= 0.5
    results["tolerance_mm"] = 0.5
    results["verdict_ok"] = bool(ok)
    common.json_dump(common.OUT_DIR / "scale_results.json", results)
    print(f"[scale] verdict_ok={ok} -> {common.OUT_DIR / 'scale_results.json'}")


main()
