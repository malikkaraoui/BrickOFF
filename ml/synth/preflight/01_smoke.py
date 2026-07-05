"""Point 1 — Smoke-test des ~450 part_ids cibles.

Pour chaque part_id (dossiers de data/raw/gdansk_cls/photos) :
  1. résolution .dat (alias a/b, suffixes) ;
  2. import ldr_tools ;
  3. rigid body CONVEX_HULL + 4 frames de simulation (force la construction de la
     collision Bullet) ;
  4. rendu vignette EEVEE 128 px + contrôle "pièce visible" (pixels alpha > 0).

Écrit out/smoke_results.jsonl en incrémental (reprise sur crash via run_smoke.sh :
un enregistrement 'attempt' sans résultat final = crash process -> marqué 'crashed').

Usage: Blender --background --python 01_smoke.py
"""
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import bpy  # type: ignore
import numpy as np

JSONL = common.OUT_DIR / "smoke_results.jsonl"
DONE_FLAG = common.OUT_DIR / "smoke_done.flag"
VIGNETTES = common.OUT_DIR / "smoke"
VIGNETTES.mkdir(exist_ok=True)


def load_state():
    """pid -> dernier statut. Un 'attempt' resté final = crash du process précédent."""
    state = {}
    if JSONL.exists():
        for line in JSONL.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            state[rec["pid"]] = rec
    return state


def append(rec):
    with JSONL.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def alpha_pixels(png_path) -> int:
    import OpenImageIO as oiio  # type: ignore

    inp = oiio.ImageInput.open(str(png_path))
    if inp is None:
        return -1
    spec = inp.spec()
    try:
        data = inp.read_image(0, 0, 0, spec.nchannels, "float")
    except TypeError:
        data = inp.read_image("float")
    inp.close()
    arr = np.asarray(data).reshape(spec.height, spec.width, spec.nchannels)
    if spec.nchannels < 4:
        return -1
    return int((arr[:, :, 3] > 0.05).sum())


def build_base_scene():
    common.reset_scene()
    common.setup_world(strength=1.0)
    common.add_sun(energy=3.0)
    common.setup_eevee(res=128, samples=16, transparent=True)
    common.ensure_camera()
    bpy.context.scene.camera.data.lens = 50
    common.ensure_rbworld(frame_end=250, substeps=10, iterations=10)
    # sol passif pour la mini-simulation de validation collision
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.55))
    floor = bpy.context.active_object
    floor.name = "floor"
    floor.scale = (10, 10, 1)
    common.add_rigidbody(floor, shape="BOX", active=False)
    floor.hide_render = True
    return floor


def test_part(pid: str, floor) -> dict:
    rec = {"pid": pid, "status": "fail", "error": None}
    t0 = time.perf_counter()
    dat, resolved = common.resolve_part_file(pid)
    rec["resolved"] = resolved
    if dat is None:
        rec["error"] = "no_dat_file"
        return rec
    scene = bpy.context.scene
    obj = None
    try:
        t_imp = time.perf_counter()
        obj = common.import_part(dat, name=f"part_{pid}")
        rec["import_s"] = round(time.perf_counter() - t_imp, 3)
        rec["n_vertices"] = len(obj.data.vertices)
        dims = common.object_dims(obj)
        rec["dims_mm"] = [round(d * common.UNIT_TO_MM, 2) for d in dims]
        if rec["n_vertices"] < 3:
            rec["error"] = "empty_mesh"
            return rec

        # rigid body + 4 frames de sim (construction réelle du convex hull Bullet)
        obj.location = (0, 0, max(dims) * 1.5 + 0.05)
        common.add_rigidbody(obj, shape="CONVEX_HULL", active=True, mass=0.01)
        scene.frame_set(1)
        for f in (2, 3, 4, 5):
            scene.frame_set(f)
        m = common.eval_matrix(obj, 5)
        loc = list(m.translation)
        if not all(np.isfinite(loc)):
            rec["error"] = "sim_nan"
            return rec
        rec["sim_ok"] = True

        # vignette EEVEE 128 px
        common.frame_camera(scene.camera, [obj], margin=1.3)
        png = VIGNETTES / f"{pid}.png"
        common.set_output_png(png)
        t_r = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        rec["render_s"] = round(time.perf_counter() - t_r, 3)
        vis = alpha_pixels(png)
        rec["alpha_px"] = vis
        if vis < 30:
            rec["error"] = "not_visible_in_render"
            return rec
        rec["status"] = "ok"
        return rec
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"{type(e).__name__}: {e}"
        return rec
    finally:
        rec["total_s"] = round(time.perf_counter() - t0, 3)
        if obj is not None and obj.name in bpy.data.objects:
            try:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.rigidbody.object_remove()
            except Exception:
                pass
            bpy.data.objects.remove(obj, do_unlink=True)
        scene.frame_set(1)


def main():
    part_ids = common.load_part_ids()
    limit = int(os.environ.get("SMOKE_LIMIT", "0"))
    if limit:
        part_ids = part_ids[:limit]
    state = load_state()
    todo = []
    for pid in part_ids:
        prev = state.get(pid)
        if prev is None:
            todo.append(pid)
        elif prev["status"] == "attempt":
            # le process précédent a crashé sur cette pièce
            append({"pid": pid, "status": "crashed", "error": "blender_process_crash"})
    if not todo:
        DONE_FLAG.write_text("done")
        print("[smoke] tout est déjà traité")
        return

    floor = build_base_scene()
    t_start = time.perf_counter()
    n_done = 0
    for pid in todo:
        prev = state.get(pid)
        if prev is not None and prev["status"] == "attempt":
            continue  # déjà marqué crashed ci-dessus
        append({"pid": pid, "status": "attempt"})
        rec = test_part(pid, floor)
        append(rec)
        n_done += 1
        if n_done % 25 == 0:
            common.purge_orphans()
            el = time.perf_counter() - t_start
            print(f"[smoke] {n_done}/{len(todo)} ({el:.0f}s, {el/n_done:.2f}s/pièce)")
    DONE_FLAG.write_text("done")
    print(f"[smoke] terminé: {n_done} pièces en {time.perf_counter()-t_start:.0f}s")


main()
