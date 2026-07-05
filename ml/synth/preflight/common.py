"""Helpers partagés du préflight S.1-pré (exécutés dans le Python de Blender 5.1).

Pièges API Blender 5.x pris en compte (cf. docs/research/SYNTH_FEASIBILITY.md §7) :
- media_type = 'MULTI_LAYER_IMAGE' AVANT file_format = 'OPEN_EXR_MULTILAYER'
- moteur EEVEE = 'BLENDER_EEVEE' (pas de suffixe _NEXT)
- couches EXR préfixées 'ViewLayer.'
- EEVEE n'écrit pas le pass Object Index -> Cryptomatte (CryptoObject00..).
"""
from __future__ import annotations

import json
import math
import os
import re
import struct
import time
from pathlib import Path

import bpy  # type: ignore
import mathutils  # type: ignore
import numpy as np

PREFLIGHT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PREFLIGHT_DIR.parents[2]
LDRAW_PATH = PROJECT_ROOT / "data" / "raw" / "ldraw" / "ldraw"
PARTS_DIR = LDRAW_PATH / "parts"
OUT_DIR = PREFLIGHT_DIR / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SCENE_SCALE = 0.01  # défaut addon ldr_tools : 1 unité scène = 100 LDU = 40 mm
UNIT_TO_MM = 0.4 / SCENE_SCALE  # 1 LDU = 0,4 mm -> 40 mm par unité scène


# ---------------------------------------------------------------- résolution part_id
def resolve_part_file(pid: str) -> tuple[Path | None, str | None]:
    """Résout un part_id gdansk vers un .dat LDraw (alias a/b, suffixes, composites)."""
    cands: list[str] = [pid, pid.lower()]
    m = re.match(r"^(\d+)[a-z]+$", pid)
    if m:
        cands.append(m.group(1))
    for s in ("a", "b", "c"):
        cands.append(pid + s)
        if m:
            cands.append(m.group(1) + s)
    if "_" in pid:
        for tok in pid.split("_"):
            cands.extend([tok, tok + "a"])
    seen = set()
    for c in cands:
        if c in seen:
            continue
        seen.add(c)
        p = PARTS_DIR / f"{c}.dat"
        if p.exists():
            return p, c
    return None, None


def load_part_ids() -> list[str]:
    src = PROJECT_ROOT / "data" / "raw" / "gdansk_cls" / "photos"
    return sorted(d.name for d in src.iterdir() if d.is_dir())


# ---------------------------------------------------------------- scène
def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # read_factory_settings désactive les addons non-défaut -> réactiver ldr_tools
    try:
        bpy.ops.preferences.addon_enable(module="ldr_tools_blender")
    except Exception:
        pass


def purge_orphans() -> None:
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.objects):
        for block in list(coll):
            if block.users == 0:
                try:
                    coll.remove(block)
                except Exception:
                    pass


def setup_world(strength: float = 1.0, color=(0.9, 0.9, 0.9)) -> None:
    world = bpy.data.worlds.new("World") if bpy.context.scene.world is None else bpy.context.scene.world
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (*color, 1.0)
        bg.inputs[1].default_value = strength


def add_sun(energy: float = 3.0, direction=(0.4, 0.3, -1.0)) -> None:
    light_data = bpy.data.lights.new("Sun", type="SUN")
    light_data.energy = energy
    light = bpy.data.objects.new("Sun", light_data)
    bpy.context.scene.collection.objects.link(light)
    d = mathutils.Vector(direction).normalized()
    light.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def ensure_camera() -> bpy.types.Object:
    cam = bpy.context.scene.camera
    if cam is None:
        cam_data = bpy.data.cameras.new("Camera")
        cam = bpy.data.objects.new("Camera", cam_data)
        bpy.context.scene.collection.objects.link(cam)
        bpy.context.scene.camera = cam
    return cam


def look_at(obj: bpy.types.Object, target) -> None:
    direction = (mathutils.Vector(target) - obj.location).normalized()
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def frame_camera(cam, objs, margin: float = 1.35, direction=(1.0, -1.0, 0.8)) -> None:
    pts = []
    for o in objs:
        for corner in o.bound_box:
            pts.append(o.matrix_world @ mathutils.Vector(corner))
    center = sum(pts, mathutils.Vector((0, 0, 0))) / len(pts)
    radius = max((p - center).length for p in pts)
    radius = max(radius, 1e-4)
    fov = cam.data.angle
    dist = radius * margin / math.sin(fov / 2)
    d = mathutils.Vector(direction).normalized()
    cam.location = center + d * dist
    look_at(cam, center)
    cam.data.clip_start = max(1e-4, dist / 100)
    cam.data.clip_end = max(100.0, dist * 10)


def setup_eevee(res: int = 640, samples: int = 32, transparent: bool = True) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = res
    scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = transparent
    scene.eevee.taa_render_samples = samples


def set_output_png(path: Path) -> None:
    s = bpy.context.scene.render.image_settings
    try:
        s.media_type = "IMAGE"
    except Exception:
        pass
    s.file_format = "PNG"
    s.color_mode = "RGBA"
    s.color_depth = "8"
    bpy.context.scene.render.filepath = str(path)


def set_output_exr_multilayer(path: Path) -> None:
    s = bpy.context.scene.render.image_settings
    s.media_type = "MULTI_LAYER_IMAGE"  # AVANT file_format (piège 5.x)
    s.file_format = "OPEN_EXR_MULTILAYER"
    s.color_depth = "32"
    s.exr_codec = "ZIP"
    bpy.context.scene.render.filepath = str(path)


def render_still() -> float:
    t0 = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    return time.perf_counter() - t0


# ---------------------------------------------------------------- import LDraw
def import_part(dat_path: Path, name: str | None = None) -> bpy.types.Object:
    """Importe un .dat, aplatit la hiérarchie (échelle appliquée), origine au centre bbox.

    Retourne un objet MESH unique, transformations identité, prêt pour rigid body.
    """
    before = set(bpy.data.objects)
    bpy.ops.import_scene.importldr(
        filepath=str(dat_path),
        ldraw_path=str(LDRAW_PATH),
        instance_type="LinkedDuplicates",
    )
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH" and o.data and len(o.data.vertices) > 0]
    if not meshes:
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)
        raise RuntimeError(f"import sans mesh: {dat_path.name}")

    # applique la transform monde (échelle du root incluse) dans les données
    for o in meshes:
        o.data.transform(o.matrix_world)
        o.matrix_world = mathutils.Matrix.Identity(4)
        o.parent = None

    main = meshes[0]
    if len(meshes) > 1:  # fusionne les éventuels sous-objets
        override = bpy.context.copy()
        override["active_object"] = main
        override["selected_objects"] = meshes
        override["selected_editable_objects"] = meshes
        with bpy.context.temp_override(**override):
            bpy.ops.object.join()

    # origine au centre de la bbox (COM cohérent pour Bullet)
    n = len(main.data.vertices)
    co = np.empty(n * 3, dtype=np.float32)
    main.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    center = (co.min(axis=0) + co.max(axis=0)) / 2
    main.data.transform(mathutils.Matrix.Translation(-mathutils.Vector(center)))
    main.location = mathutils.Vector(center)

    # supprime les résidus (empties/roots)
    for o in new:
        if o is not main and o.name in bpy.data.objects:
            try:
                bpy.data.objects.remove(o, do_unlink=True)
            except Exception:
                pass
    if name:
        main.name = name
    return main


def object_dims(obj) -> tuple[float, float, float]:
    n = len(obj.data.vertices)
    co = np.empty(n * 3, dtype=np.float32)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    return tuple((co.max(axis=0) - co.min(axis=0)).tolist())


def assign_debug_material(obj, idx: int, total: int = 20) -> None:
    name = f"dbg_{idx}"
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        h = (idx * 0.618034) % 1.0
        rgb = mathutils.Color((0, 0, 0))
        rgb.hsv = (h, 0.75, 0.8)
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (rgb.r, rgb.g, rgb.b, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.25
    obj.data.materials.clear()
    obj.data.materials.append(mat)


# ---------------------------------------------------------------- rigid body
def ensure_rbworld(frame_end: int = 150, substeps: int = 20, iterations: int = 20):
    scene = bpy.context.scene
    if scene.rigidbody_world is None:
        bpy.ops.rigidbody.world_add()
    rbw = scene.rigidbody_world
    rbw.enabled = True
    if hasattr(rbw, "substeps_per_frame"):
        rbw.substeps_per_frame = substeps
    rbw.solver_iterations = iterations
    scene.frame_start = 1
    scene.frame_end = frame_end
    rbw.point_cache.frame_start = 1
    rbw.point_cache.frame_end = frame_end
    return rbw


def add_rigidbody(obj, shape: str = "CONVEX_HULL", active: bool = True,
                  mass: float = 0.01, friction: float = 0.7,
                  margin: float | None = None) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.rigidbody.object_add()
    rb = obj.rigid_body
    rb.type = "ACTIVE" if active else "PASSIVE"
    rb.collision_shape = shape
    rb.mass = mass
    rb.friction = friction
    rb.restitution = 0.05
    if shape == "MESH":
        rb.mesh_source = "BASE"
    if margin is not None:
        rb.use_margin = True
        rb.collision_margin = margin


def bake_physics() -> float:
    t0 = time.perf_counter()
    bpy.ops.ptcache.free_bake_all()
    bpy.ops.ptcache.bake_all(bake=True)
    return time.perf_counter() - t0


def eval_matrix(obj, frame: int) -> mathutils.Matrix:
    bpy.context.scene.frame_set(frame)
    deps = bpy.context.evaluated_depsgraph_get()
    return obj.evaluated_get(deps).matrix_world.copy()


def apply_visual_transforms(objs, frame: int) -> None:
    """Fige les transforms simulées au frame donné (découple scène et rendu)."""
    mats = {o.name: eval_matrix(o, frame) for o in objs}
    scene = bpy.context.scene
    if scene.rigidbody_world:
        for o in objs:
            bpy.context.view_layer.objects.active = o
            try:
                bpy.ops.rigidbody.object_remove()
            except Exception:
                pass
    for o in objs:
        o.matrix_world = mats[o.name]
    scene.frame_set(1)


# ---------------------------------------------------------------- cryptomatte
def mmh3_32(data: bytes, seed: int = 0) -> int:
    c1, c2 = 0xCC9E2D51, 0x1B873593
    length = len(data)
    h = seed
    rounded = length & ~3
    for i in range(0, rounded, 4):
        k = int.from_bytes(data[i : i + 4], "little")
        k = (k * c1) & 0xFFFFFFFF
        k = ((k << 15) | (k >> 17)) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        h ^= k
        h = ((h << 13) | (h >> 19)) & 0xFFFFFFFF
        h = (h * 5 + 0xE6546B64) & 0xFFFFFFFF
    tail = data[rounded:]
    k = 0
    if len(tail) >= 3:
        k ^= tail[2] << 16
    if len(tail) >= 2:
        k ^= tail[1] << 8
    if len(tail) >= 1:
        k ^= tail[0]
        k = (k * c1) & 0xFFFFFFFF
        k = ((k << 15) | (k >> 17)) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        h ^= k
    h ^= length
    h ^= h >> 16
    h = (h * 0x85EBCA6B) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0xC2B2AE35) & 0xFFFFFFFF
    h ^= h >> 16
    return h


def crypto_name_to_float(name: str) -> float:
    """Hash Cryptomatte (spec officielle) : mmh3 32 bits + évitement inf/nan/denorm."""
    h = mmh3_32(name.encode("utf-8"))
    exp = (h >> 23) & 0xFF
    if exp in (0, 255):
        h ^= 1 << 23
    return struct.unpack("<f", struct.pack("<I", h & 0xFFFFFFFF))[0]


def hex_to_float(hexstr: str) -> float:
    """Hash brut du manifest -> float32 pixel (correction d'exposant de la spec :
    le manifest stocke le mmh3 brut, le pixel évite inf/nan/denorm en flippant
    le bit 23 si l'exposant vaut 0 ou 255)."""
    h = int(hexstr, 16) & 0xFFFFFFFF
    exp = (h >> 23) & 0xFF
    if exp in (0, 255):
        h ^= 1 << 23
    return struct.unpack("<f", struct.pack("<I", h))[0]


def read_exr_all(path: Path):
    """Lit toutes les couches d'un EXR multilayer via l'OpenImageIO embarqué.

    Retourne (channels: dict nom_complet -> np.ndarray HxW, attrs: dict).
    """
    import OpenImageIO as oiio  # type: ignore

    inp = oiio.ImageInput.open(str(path))
    if inp is None:
        raise RuntimeError(f"EXR illisible: {path}")
    channels: dict[str, np.ndarray] = {}
    attrs: dict[str, object] = {}
    sub = 0
    while inp.seek_subimage(sub, 0):
        spec = inp.spec()
        for i in range(len(spec.extra_attribs)):
            a = spec.extra_attribs[i]
            attrs[a.name] = a.value
        # OIIO 3.x : read_image(subimage, miplevel, chbegin, chend, format) —
        # les variantes "subimage courant" lisent silencieusement le subimage 0.
        try:
            data = inp.read_image(sub, 0, 0, spec.nchannels, "float")
        except TypeError:
            data = inp.read_image("float")
        arr = np.asarray(data).reshape(spec.height, spec.width, spec.nchannels)
        subname = spec.getattribute("name") or f"sub{sub}"
        for i, cn in enumerate(spec.channelnames):
            key = cn if str(subname) in cn else f"{subname}.{cn}"
            channels[key] = arr[:, :, i].copy()
        sub += 1
    inp.close()
    return channels, attrs


def crypto_manifest(attrs: dict) -> dict[str, float] | None:
    for k, v in attrs.items():
        if re.search(r"cryptomatte/[0-9a-f]+/manifest", str(k)):
            try:
                mapping = json.loads(v)
                return {name: hex_to_float(h) for name, h in mapping.items()}
            except Exception:
                return None
    return None


def crypto_rank_planes(channels: dict[str, np.ndarray], token: str = "CryptoObject"):
    """Ordonne les canaux CryptoObjectNN.[RGBA] en paires (id, coverage)."""
    order = {"R": 0, "G": 1, "B": 2, "A": 3}
    found = []
    for key, arr in channels.items():
        m = re.search(rf"{token}(\d+)\.([RGBArgba])$", key)
        if m:
            found.append(((int(m.group(1)), order[m.group(2).upper()]), arr))
    found.sort(key=lambda t: t[0])
    planes = [arr for _, arr in found]
    ids = planes[0::2]
    covs = planes[1::2]
    return np.stack(ids), np.stack(covs)


def crypto_coverage_for(ids: np.ndarray, covs: np.ndarray, fid: float) -> np.ndarray:
    return np.where(ids == np.float32(fid), covs, 0.0).sum(axis=0)


def mask_bbox(mask: np.ndarray, thr: float = 0.5):
    ys, xs = np.where(mask > thr)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def write_png_gray(path: Path, arr: np.ndarray) -> None:
    import OpenImageIO as oiio  # type: ignore

    a = np.clip(arr, 0, 1).astype(np.float32)
    spec = oiio.ImageSpec(a.shape[1], a.shape[0], 1, "uint8")
    out = oiio.ImageOutput.create(str(path))
    out.open(str(path), spec)
    out.write_image((a * 255).astype(np.uint8))
    out.close()


def write_png_rgb(path: Path, arr: np.ndarray) -> None:
    import OpenImageIO as oiio  # type: ignore

    a = np.clip(arr, 0, 1).astype(np.float32)
    spec = oiio.ImageSpec(a.shape[1], a.shape[0], 3, "uint8")
    out = oiio.ImageOutput.create(str(path))
    out.open(str(path), spec)
    out.write_image((a * 255).astype(np.uint8))
    out.close()


def json_dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False))
