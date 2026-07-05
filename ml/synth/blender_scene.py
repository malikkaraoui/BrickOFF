"""CH-S / S.2 — Script scène exécuté PAR Blender (headless), piloté par generate_scenes.py.

Reçoit un job JSON (config résolue + liste de scènes {index, seed, name}), génère chaque
scène : sol PBR + HDRI + tas de pièces LDraw (drop rigid body CONVEX_HULL, parois de
confinement) + distracteurs éventuels, rend UN EXR multilayer EEVEE 640² (Combined +
Cryptomatte), en extrait le beauty PNG, les bbox visibles et le coverage par pièce
(convention data/manifests/annotation_convention.md), écrit label YOLO + manifest JSON.

Réutilise ml/synth/preflight/common.py (import LDraw aplati, rigid body, décodage
Cryptomatte OIIO — pièges API Blender 5.x déjà résolus).

Usage : Blender --background --python blender_scene.py -- --job <job.json>
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "preflight"))

import bpy  # type: ignore
import mathutils  # type: ignore
import numpy as np

import common  # préflight S.1-pré — fondations S.2

# ---------------------------------------------------------------------------
# Job
# ---------------------------------------------------------------------------


def parse_job() -> dict:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 2 or argv[0] != "--job":
        raise SystemExit("usage: blender --background --python blender_scene.py -- --job job.json")
    return json.loads(Path(argv[1]).read_text())


# ---------------------------------------------------------------------------
# Tirages
# ---------------------------------------------------------------------------


def pick_weighted(rng: random.Random, items: list, weights: list[float]):
    return rng.choices(items, weights=weights, k=1)[0]


def pick_regime(rng: random.Random, regimes: list[dict]) -> tuple[int, dict]:
    r = rng.random()
    acc = 0.0
    for i, reg in enumerate(regimes):
        acc += reg["p"]
        if r <= acc:
            return i, reg
    return len(regimes) - 1, regimes[-1]


def kelvin_to_rgb(t: float) -> tuple[float, float, float]:
    """Approximation Tanner Helland (suffisant pour une lampe de scène)."""
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
    rgb = tuple(min(max(v, 0.0), 255.0) / 255.0 for v in (r, g, b))
    m = max(rgb)
    return tuple(v / m for v in rgb) if m > 0 else (1.0, 1.0, 1.0)


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear_rgb(hexstr: str) -> tuple[float, float, float]:
    h = hexstr.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


# ---------------------------------------------------------------------------
# Matériaux
# ---------------------------------------------------------------------------

PIECE_MAT_NAME = "bo_piece_shared"


def make_piece_material() -> bpy.types.Material:
    """UN node-tree partagé pour TOUTES les pièces, paramétré par attributs objet
    (décision plan 16 : pas de node-tree par pièce ; hooks S.3) :
      - obj.color                  -> Base Color (Object Info)
      - obj["bo_rough_min"/"max"]  -> plage de la roughness bruitée (Attribute OBJECT)
      - obj["bo_sss"]              -> poids subsurface
      - obj["bo_bump"]             -> intensité micro-normales
    """
    mat = bpy.data.materials.get(PIECE_MAT_NAME)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(PIECE_MAT_NAME)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    out = nt.nodes.get("Material Output")

    obj_info = nt.nodes.new("ShaderNodeObjectInfo")
    nt.links.new(obj_info.outputs["Color"], bsdf.inputs["Base Color"])

    # roughness bruitée entre bo_rough_min et bo_rough_max (esprit ldr_tools_blender)
    def attr(name: str):
        n = nt.nodes.new("ShaderNodeAttribute")
        n.attribute_type = "OBJECT"
        n.attribute_name = name
        return n

    noise_r = nt.nodes.new("ShaderNodeTexNoise")
    noise_r.inputs["Scale"].default_value = float(make_piece_material.rough_noise_scale)
    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(noise_r.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(attr("bo_rough_min").outputs["Fac"], mr.inputs["To Min"])
    nt.links.new(attr("bo_rough_max").outputs["Fac"], mr.inputs["To Max"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])

    # subsurface léger (ABS translucide)
    if "Subsurface Weight" in bsdf.inputs:
        nt.links.new(attr("bo_sss").outputs["Fac"], bsdf.inputs["Subsurface Weight"])
        if "Subsurface Scale" in bsdf.inputs:
            bsdf.inputs["Subsurface Scale"].default_value = 0.05

    # micro-normales (bump bruité, intensité par objet)
    noise_b = nt.nodes.new("ShaderNodeTexNoise")
    noise_b.inputs["Scale"].default_value = float(make_piece_material.bump_noise_scale)
    bump = nt.nodes.new("ShaderNodeBump")
    nt.links.new(noise_b.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(attr("bo_bump").outputs["Fac"], bump.inputs["Strength"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


make_piece_material.rough_noise_scale = 30.0
make_piece_material.bump_noise_scale = 350.0


def simple_material(name: str, rgb, rough: float, metallic: float = 0.0) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def make_floor_material(rng: random.Random, cfg: dict, texture: dict | None,
                        params: dict) -> bpy.types.Material:
    mat = bpy.data.materials.new("bo_floor")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if texture is None:  # fond uni clair (type table/nappe)
        col = mathutils.Color((0, 0, 0))
        col.hsv = (rng.random(),
                   rng.uniform(*cfg["floor"]["plain_saturation"]),
                   rng.uniform(*cfg["floor"]["plain_value"]))
        rough = rng.uniform(*cfg["floor"]["plain_roughness"])
        bsdf.inputs["Base Color"].default_value = (col.r, col.g, col.b, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        params["floor_plain_rgb"] = [round(col.r, 4), round(col.g, 4), round(col.b, 4)]
        params["floor_plain_roughness"] = round(rough, 3)
        return mat

    scale_units = rng.uniform(*cfg["floor"]["texture_scale_units"])
    rot = math.radians(rng.uniform(*cfg["floor"]["texture_rotation_deg"]))
    params["floor_texture"] = texture["id"]
    params["floor_texture_scale_units"] = round(scale_units, 2)
    params["floor_texture_rot_deg"] = round(math.degrees(rot), 1)

    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Rotation"].default_value = (0.0, 0.0, rot)
    s = 1.0 / scale_units
    mapping.inputs["Scale"].default_value = (s, s, s)
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])

    def img_node(path: str, non_color: bool):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(path, check_existing=True)
        if non_color:
            n.image.colorspace_settings.name = "Non-Color"
        n.projection = "BOX"
        n.projection_blend = 0.2
        nt.links.new(mapping.outputs["Vector"], n.inputs["Vector"])
        return n

    nt.links.new(img_node(texture["color"], False).outputs["Color"],
                 bsdf.inputs["Base Color"])
    nt.links.new(img_node(texture["roughness"], True).outputs["Color"],
                 bsdf.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 1.0
    nt.links.new(img_node(texture["normal"], True).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


# ---------------------------------------------------------------------------
# Construction de scène
# ---------------------------------------------------------------------------


def setup_hdri(rng: random.Random, cfg: dict, hdris: list[dict], params: dict) -> None:
    weights_by_class = cfg["hdri"]["class_weights"]
    classes = [h["thermal_class"] for h in hdris]
    weights = [weights_by_class.get(c, 0.0) / max(1, classes.count(c)) for c in classes]
    hdri = pick_weighted(rng, hdris, weights)
    rot = math.radians(rng.uniform(*cfg["hdri"]["rotation_deg"]))
    strength = rng.uniform(*cfg["hdri"]["strength"])
    params.update({"hdri": hdri["id"], "hdri_class": hdri["thermal_class"],
                   "hdri_rot_deg": round(math.degrees(rot), 1),
                   "hdri_strength": round(strength, 3)})

    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes.get("Background")
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(hdri["file"], check_existing=True)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Rotation"].default_value = (0.0, 0.0, rot)
    nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength


def setup_key_light(rng: random.Random, cfg: dict, params: dict) -> None:
    kl = cfg["key_light"]
    if rng.random() >= kl["p"]:
        params["key_light"] = None
        return
    is_area = rng.random() < kl["p_area"]
    temp = rng.uniform(*kl["temp_k"])
    elev = math.radians(rng.uniform(*kl["elevation_deg"]))
    azim = rng.uniform(0, 2 * math.pi)
    dist = rng.uniform(*kl["distance"])
    rgb = kelvin_to_rgb(temp)
    if is_area:
        data = bpy.data.lights.new("Key", type="AREA")
        data.energy = rng.uniform(*kl["area_power"])
        data.size = rng.uniform(*kl["area_size"])
    else:
        data = bpy.data.lights.new("Key", type="SUN")
        data.energy = rng.uniform(*kl["sun_energy"])
    data.color = rgb
    light = bpy.data.objects.new("Key", data)
    bpy.context.scene.collection.objects.link(light)
    light.location = (dist * math.cos(elev) * math.cos(azim),
                      dist * math.cos(elev) * math.sin(azim),
                      dist * math.sin(elev))
    common.look_at(light, (0.0, 0.0, 0.0))
    params["key_light"] = {"type": "AREA" if is_area else "SUN",
                           "energy": round(data.energy, 1), "temp_k": round(temp),
                           "elev_deg": round(math.degrees(elev), 1),
                           "azim_deg": round(math.degrees(azim), 1),
                           "dist": round(dist, 2),
                           "size": round(getattr(data, "size", 0.0), 2)}


def add_floor(rng: random.Random, cfg: dict, textures: list[dict], params: dict):
    size = cfg["floor"]["size_units"]
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.05))
    floor = bpy.context.active_object
    floor.name = "floor"
    floor.scale = (size / 2, size / 2, 0.05)
    bpy.ops.object.transform_apply(scale=True)
    common.add_rigidbody(floor, shape="BOX", active=False, friction=0.8)
    plain = rng.random() < cfg["floor"]["p_plain"]
    params["floor_mode"] = "plain" if plain else "texture"
    tex = None if plain else textures[rng.randrange(len(textures))]
    mat = make_floor_material(rng, cfg, tex, params)
    floor.data.materials.clear()
    floor.data.materials.append(mat)
    return floor


def add_walls(extent: float, cfg: dict) -> list:
    """Parois invisibles pendant le bake (préflight : 2-4 pièces/scène éjectées sinon)."""
    r = extent + cfg["sim"]["wall_margin"]
    h = cfg["sim"]["wall_height"]
    walls = []
    ln = 2 * r + 0.6  # longueur couvrant les coins
    for i, (x, y, sx, sy) in enumerate([(r, 0, 0.2, ln), (-r, 0, 0.2, ln),
                                        (0, r, ln, 0.2), (0, -r, ln, 0.2)]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, h / 2))
        w = bpy.context.active_object
        w.name = f"wall{i}"
        # échelle laissée SUR L'OBJET : transform_apply sur ces boîtes corrompt la
        # shape Bullet en 5.1 (impulsions fantômes mesurées — dépénétration comme si
        # les actifs étaient DANS le mur). Vérifié : sans apply, sim stable.
        w.scale = (sx, sy, h)  # cube taille 1 -> demi-hauteur h/2, ancré au sol
        w.hide_render = True
        common.add_rigidbody(w, shape="BOX", active=False, friction=0.1)
        walls.append(w)
    return walls


def sample_pieces(rng: random.Random, cfg: dict, parts_pool: dict, palette: dict,
                  n: int) -> list[dict]:
    """Tire N (part_id, couleur, params matière) : 70 % fréq. empiriques / 30 % uniforme."""
    ids = parts_pool["ids"]
    emp_w = parts_pool["weights_empirical"]
    pm = cfg["piece_material"]
    out = []
    for _ in range(n):
        if rng.random() < cfg["parts"]["p_empirical"]:
            pid = pick_weighted(rng, ids, emp_w)
            src = "empirical"
        else:
            pid = ids[rng.randrange(len(ids))]
            src = "uniform"
        if rng.random() < cfg["colors"]["p_uniform_solid"]:
            col = palette["solid"][rng.randrange(len(palette["solid"]))]
            csrc = "uniform_solid"
        else:
            col = pick_weighted(rng, palette["weighted"], palette["weighted_w"])
            csrc = "weighted"
        rmin = rng.uniform(*pm["rough_min"])
        out.append({
            "part_id": pid, "dat": parts_pool["dat_by_id"][pid], "part_source": src,
            "color_code": col["code"], "color_name": col["name"], "color_hex": col["hex"],
            "color_source": csrc,
            "rough_min": round(rmin, 4),
            "rough_max": round(rmin + rng.uniform(*pm["rough_span"]), 4),
            "sss": round(rng.uniform(*pm["sss_weight"]), 4),
            "bump": round(rng.uniform(*pm["bump_strength"]), 4),
        })
    return out


def build_pile(rng: random.Random, cfg: dict, specs: list[dict], params: dict) -> list:
    n = len(specs)
    extent = max(cfg["sim"]["drop_extent_min"],
                 cfg["sim"]["drop_extent_base"] * math.sqrt(n / 20.0))
    params["drop_extent"] = round(extent, 3)
    walls = add_walls(extent, cfg)
    shared = make_piece_material()
    pieces = []
    placed: list[tuple[float, float, float, float]] = []  # (x, y, z, rayon englobant)
    gap = cfg["sim"]["drop_gap"]
    for i, spec in enumerate(specs):
        obj = common.import_part(Path(spec["dat"]), name=f"p{i:02d}_{spec['part_id']}")
        obj.data.materials.clear()
        obj.data.materials.append(shared)
        obj.data.polygons.foreach_set(
            "material_index", np.zeros(len(obj.data.polygons), dtype=np.int32))
        rgb = hex_to_linear_rgb(spec["color_hex"])
        obj.color = (*rgb, 1.0)
        obj["bo_rough_min"] = spec["rough_min"]
        obj["bo_rough_max"] = spec["rough_max"]
        obj["bo_sss"] = spec["sss"]
        obj["bo_bump"] = spec["bump"]
        # spawn SANS interpénétration (sphères englobantes) : l'empilement à pas
        # fixe créait des chevauchements -> impulsions de dépénétration explosives
        dims = common.object_dims(obj)
        rad = 0.5 * math.sqrt(sum(d * d for d in dims))
        x = rng.uniform(-extent, extent)
        y = rng.uniform(-extent, extent)
        z = cfg["sim"]["drop_z0"] + rad
        for px, py, pz, pr in placed:
            if math.hypot(x - px, y - py) < rad + pr + gap:
                z = max(z, pz + pr + rad + gap)
        placed.append((x, y, z, rad))
        obj.location = (x, y, z)
        obj.rotation_euler = (rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi),
                              rng.uniform(0, 2 * math.pi))
        spec["drop_loc"] = [round(v, 4) for v in obj.location]
        spec["drop_rot"] = [round(v, 4) for v in obj.rotation_euler]
        common.add_rigidbody(obj, shape="CONVEX_HULL", active=True,
                             mass=cfg["sim"]["mass"], friction=cfg["sim"]["friction"])
        obj.rigid_body.restitution = cfg["sim"]["restitution"]
        pieces.append(obj)

    t0 = time.perf_counter()
    common.bake_physics()
    params["bake_s"] = round(time.perf_counter() - t0, 2)
    common.apply_visual_transforms(pieces, cfg["sim"]["frame_end"])
    for w in walls:
        bpy.data.objects.remove(w, do_unlink=True)

    kept = []
    n_rejected = 0
    for obj, spec in zip(pieces, specs):
        r = math.hypot(obj.location.x, obj.location.y)
        if r > cfg["sim"]["reject_radius"] or obj.location.z < -0.1:
            spec["status"] = "rejected_out_of_zone"
            n_rejected += 1
            bpy.data.objects.remove(obj, do_unlink=True)
        else:
            spec["obj_name"] = obj.name
            kept.append(obj)
    params["n_rejected_out_of_zone"] = n_rejected
    return kept


# ---------------------------------------------------------------------------
# Caméra
# ---------------------------------------------------------------------------


def world_bounds(objs) -> tuple[mathutils.Vector, float]:
    pts = []
    for o in objs:
        pts.extend(o.matrix_world @ mathutils.Vector(c) for c in o.bound_box)
    center = sum(pts, mathutils.Vector()) / len(pts)
    radius = max((p - center).length for p in pts)
    return center, max(radius, 1e-3)


def setup_camera(rng: random.Random, cfg: dict, pieces: list, params: dict):
    cam = common.ensure_camera()
    ccfg = cfg["camera"]
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = ccfg["sensor_mm"]
    focal = rng.uniform(*ccfg["focal_mm_eq"])
    cam.data.lens = focal
    fov = 2.0 * math.atan(ccfg["sensor_mm"] / (2.0 * focal))

    if pieces:
        center, radius = world_bounds(pieces)
    else:  # fond seul : visée fictive
        center = mathutils.Vector((rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5), 0.0))
        radius = rng.uniform(*ccfg["bg_virtual_radius"])

    ridx, reg = pick_regime(rng, ccfg["elevation_regimes"])
    elev = math.radians(rng.uniform(reg["min"], reg["max"]))
    azim = rng.uniform(0, 2 * math.pi)
    fill = rng.uniform(*ccfg["fill_fraction"])
    dist = radius / math.tan(max(fill * fov / 2.0, 1e-3))
    dist = max(dist, radius * 1.15)  # garde-fou : ne pas entrer dans le tas

    aim = center.copy()
    off_ang = rng.uniform(0, 2 * math.pi)
    off = rng.uniform(0, ccfg["aim_offset_frac"]) * radius
    aim.x += off * math.cos(off_ang)
    aim.y += off * math.sin(off_ang)

    cam.location = aim + mathutils.Vector((dist * math.cos(elev) * math.cos(azim),
                                           dist * math.cos(elev) * math.sin(azim),
                                           dist * math.sin(elev)))
    common.look_at(cam, aim)
    roll = math.radians(rng.uniform(-ccfg["tilt_deg"], ccfg["tilt_deg"]))
    cam.rotation_euler.rotate_axis("Z", roll)
    cam.data.clip_start = max(1e-3, dist / 200.0)
    cam.data.clip_end = max(200.0, dist * 20.0)
    bpy.context.view_layer.update()

    params.update({
        "cam_elev_regime": ridx, "cam_elev_deg": round(math.degrees(elev), 1),
        "cam_azim_deg": round(math.degrees(azim), 1), "cam_focal_mm_eq": round(focal, 2),
        "cam_fill": round(fill, 3), "cam_dist": round(dist, 3),
        "cam_roll_deg": round(math.degrees(roll), 1),
        "cam_aim_offset": round(off, 3),
        "pile_center": [round(v, 3) for v in center], "pile_radius": round(radius, 3),
    })
    return cam


def camera_matrices(cam, res: int):
    deps = bpy.context.evaluated_depsgraph_get()
    # Blender 5.x : calc_matrix_camera est sur l'Object ; <5 : sur le Camera data
    if hasattr(cam, "calc_matrix_camera"):
        proj = cam.calc_matrix_camera(deps, x=res, y=res)
    else:
        proj = cam.data.calc_matrix_camera(deps, x=res, y=res)
    view = cam.matrix_world.inverted()
    M = np.array(proj @ view, dtype=np.float64)
    return M, np.linalg.inv(M)


def unproject_pixel(Minv: np.ndarray, px: float, py: float, res: int):
    """Rayon monde passant par le centre du pixel (px, py)."""
    x = (px + 0.5) / res * 2.0 - 1.0
    y = (1.0 - (py + 0.5) / res) * 2.0 - 1.0
    p0 = Minv @ np.array([x, y, -1.0, 1.0])
    p1 = Minv @ np.array([x, y, 1.0, 1.0])
    p0 = p0[:3] / p0[3]
    p1 = p1[:3] / p1[3]
    d = p1 - p0
    return p0, d / np.linalg.norm(d)


def project_verts(M: np.ndarray, verts: np.ndarray, res: int) -> np.ndarray:
    """Projette des sommets monde -> pixels (Nx2), NaN si derrière la caméra."""
    ones = np.ones((verts.shape[0], 1))
    clip = np.hstack([verts, ones]) @ M.T
    w = clip[:, 3:4]
    with np.errstate(divide="ignore", invalid="ignore"):
        ndc = clip[:, :3] / w
    px = (ndc[:, 0] * 0.5 + 0.5) * res
    py = (1.0 - (ndc[:, 1] * 0.5 + 0.5)) * res
    px[w[:, 0] <= 1e-9] = np.nan
    py[w[:, 0] <= 1e-9] = np.nan
    return np.stack([px, py], axis=1)


def solo_area_estimate(obj, M, Minv, res: int, max_samples: int) -> float:
    """Aire (px) de la silhouette NON occluse de la pièce, clippée au cadre :
    grille de rayons caméra -> BVH de la pièce seule. Dénominateur du coverage."""
    from mathutils.bvhtree import BVHTree  # type: ignore

    mesh = obj.data
    nv = len(mesh.vertices)
    co = np.empty(nv * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    mw = np.array(obj.matrix_world, dtype=np.float64)
    world = co @ mw[:3, :3].T + mw[:3, 3]

    pix = project_verts(M, world, res)
    if np.all(np.isnan(pix[:, 0])):
        return 0.0
    x0 = max(0.0, np.nanmin(pix[:, 0]))
    x1 = min(float(res), np.nanmax(pix[:, 0]))
    y0 = max(0.0, np.nanmin(pix[:, 1]))
    y1 = min(float(res), np.nanmax(pix[:, 1]))
    bw, bh = x1 - x0, y1 - y0
    if bw <= 0 or bh <= 0:
        return 0.0

    # BVH de la pièce en coordonnées monde
    polys = []
    for p in mesh.polygons:
        polys.append(tuple(p.vertices))
    bvh = BVHTree.FromPolygons([tuple(v) for v in world], polys)

    area_px = bw * bh
    step = max(1.0, math.sqrt(area_px / max_samples))
    xs = np.arange(x0, x1, step)
    ys = np.arange(y0, y1, step)
    if len(xs) == 0 or len(ys) == 0:
        return area_px  # bbox sub-pixel
    hits = 0
    total = 0
    for py in ys:
        for px in xs:
            o, d = unproject_pixel(Minv, px, py, res)
            total += 1
            if bvh.ray_cast(mathutils.Vector(o), mathutils.Vector(d))[0] is not None:
                hits += 1
    if total == 0:
        return 0.0
    return area_px * hits / total


# ---------------------------------------------------------------------------
# Distracteurs (jamais annotés)
# ---------------------------------------------------------------------------


def fix_appended_image_paths(blend_path: Path) -> None:
    """Répare les chemins relatifs des textures des .blend Poly Haven après append."""
    tex_dir = blend_path.parent / "textures"
    for img in bpy.data.images:
        if img.packed_file or not img.filepath:
            continue
        p = Path(bpy.path.abspath(img.filepath))
        if not p.exists():
            cand = tex_dir / Path(img.filepath.replace("\\", "/")).name
            if cand.exists():
                img.filepath = str(cand)


def append_distractor_model(rng: random.Random, model: dict, scale: float):
    blend = Path(model["blend"])
    with bpy.data.libraries.load(str(blend), link=False) as (data_from, data_to):
        data_to.objects = list(data_from.objects)
    meshes = [o for o in data_to.objects if o is not None and o.type == "MESH"]
    if not meshes:
        return None
    chosen = meshes[rng.randrange(len(meshes))]
    for o in data_to.objects:
        if o is not None and o is not chosen:
            try:
                bpy.data.objects.remove(o, do_unlink=True)
            except Exception:
                pass
    bpy.context.scene.collection.objects.link(chosen)
    chosen.parent = None
    fix_appended_image_paths(blend)
    chosen.matrix_world = mathutils.Matrix.Scale(scale, 4) @ chosen.matrix_world
    return chosen


def make_procedural_distractor(rng: random.Random, kind: str):
    """Plan B S.1 : monnaie / dé / câble / bouchon en primitives (1 u = 40 mm)."""
    if kind == "coin":
        bpy.ops.mesh.primitive_cylinder_add(radius=0.29, depth=0.05, vertices=48)
        obj = bpy.context.active_object
        tone = rng.choice([(0.85, 0.75, 0.35), (0.75, 0.75, 0.78), (0.72, 0.45, 0.2)])
        obj.data.materials.append(simple_material("bo_coin", tone, 0.35, metallic=1.0))
    elif kind == "die":
        bpy.ops.mesh.primitive_cube_add(size=0.4)
        obj = bpy.context.active_object
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = 0.06
        mod.segments = 3
        tone = rng.choice([(0.9, 0.9, 0.9), (0.05, 0.05, 0.05), (0.6, 0.05, 0.05)])
        obj.data.materials.append(simple_material("bo_die", tone, 0.3))
    elif kind == "cork":
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.0, vertices=32)
        obj = bpy.context.active_object
        obj.data.materials.append(simple_material("bo_cork", (0.55, 0.4, 0.25), 0.8))
        if rng.random() < 0.7:  # couché
            obj.rotation_euler = (math.pi / 2, 0, rng.uniform(0, 2 * math.pi))
    else:  # cable
        curve = bpy.data.curves.new("bo_cable", type="CURVE")
        curve.dimensions = "3D"
        curve.bevel_depth = 0.045
        curve.bevel_resolution = 4
        sp = curve.splines.new("BEZIER")
        npts = rng.randint(4, 6)
        sp.bezier_points.add(npts - 1)
        x, y, ang = 0.0, 0.0, rng.uniform(0, 2 * math.pi)
        for bp in sp.bezier_points:
            bp.co = (x, y, 0.045)
            bp.handle_left_type = bp.handle_right_type = "AUTO"
            ang += rng.uniform(-1.2, 1.2)
            step = rng.uniform(0.5, 1.1)
            x += step * math.cos(ang)
            y += step * math.sin(ang)
        obj = bpy.data.objects.new("bo_cable", curve)
        bpy.context.scene.collection.objects.link(obj)
        tone = rng.choice([(0.02, 0.02, 0.02), (0.9, 0.9, 0.9), (0.02, 0.02, 0.35)])
        obj.data.materials.append(simple_material("bo_cable_m", tone, 0.45))
    return obj


def place_distractors(rng: random.Random, cfg: dict, models: list[dict], pieces: list,
                      cam, Minv, res: int, params: dict) -> None:
    dcfg = cfg["distractors"]
    params["distractors"] = []
    if rng.random() >= dcfg["p_scene"]:
        return
    count = rng.randint(*dcfg["count"])
    circles = []
    for o in pieces:
        pts = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
        cx = sum(p.x for p in pts) / 8
        cy = sum(p.y for p in pts) / 8
        r = max(math.hypot(p.x - cx, p.y - cy) for p in pts)
        circles.append((cx, cy, r))
    m = dcfg["img_margin"]
    for _ in range(count):
        use_model = rng.random() < dcfg["p_model"]
        if use_model:
            model = models[rng.randrange(len(models))]
            obj = append_distractor_model(rng, model, dcfg["model_scale"])
            if obj is None:
                continue
            kind = model["id"]
        else:
            kind = dcfg["procedural"][rng.randrange(len(dcfg["procedural"]))]
            obj = make_procedural_distractor(rng, kind)
        obj.name = f"dx_{kind}_{rng.randrange(10**6)}"
        obj.rotation_euler.z += rng.uniform(0, 2 * math.pi)
        bpy.context.view_layer.update()
        pts = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
        r_obj = max(math.hypot(p.x - sum(q.x for q in pts) / 8,
                               p.y - sum(q.y for q in pts) / 8) for p in pts)
        zmin = min(p.z for p in pts)

        placed = False
        for _try in range(dcfg["max_place_tries"]):
            u, v = rng.uniform(m, 1 - m), rng.uniform(m, 1 - m)
            o, d = unproject_pixel(Minv, u * res, v * res, res)
            if abs(d[2]) < 1e-6:
                continue
            t = -o[2] / d[2]
            if t <= 0:
                continue
            x, y = float(o[0] + t * d[0]), float(o[1] + t * d[1])
            if all(math.hypot(x - cx, y - cy) > r + r_obj + dcfg["min_gap_units"]
                   for cx, cy, r in circles):
                cx0 = sum(p.x for p in pts) / 8
                cy0 = sum(p.y for p in pts) / 8
                obj.location.x += x - cx0
                obj.location.y += y - cy0
                obj.location.z += -zmin
                circles.append((x, y, r_obj))
                placed = True
                break
        if not placed:
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        params["distractors"].append({"kind": kind,
                                      "source": "model" if use_model else "procedural",
                                      "loc": [round(v, 3) for v in obj.location]})


# ---------------------------------------------------------------------------
# Rendu + labels
# ---------------------------------------------------------------------------


def render_scene(exr_path: Path, png_path: Path, res: int, samples: int) -> dict:
    common.setup_eevee(res=res, samples=samples, transparent=False)
    vl = bpy.context.view_layer
    vl.use_pass_cryptomatte_object = True
    if hasattr(vl, "pass_cryptomatte_depth"):
        vl.pass_cryptomatte_depth = 6
    common.set_output_exr_multilayer(exr_path)
    t_render = common.render_still()
    # beauty PNG extrait du MÊME rendu (view transform de la scène appliqué)
    t0 = time.perf_counter()
    try:
        common.set_output_png(png_path)
        bpy.data.images["Render Result"].save_render(str(png_path),
                                                     scene=bpy.context.scene)
        png_mode = "save_render"
    except Exception:
        common.set_output_png(png_path)
        common.render_still()
        png_mode = "second_render"
    return {"render_s": round(t_render, 2),
            "png_s": round(time.perf_counter() - t0, 2), "png_mode": png_mode}


def extract_labels(exr_path: Path, specs: list[dict], cam, res: int, cfg: dict) -> dict:
    """Cryptomatte -> masque visible par pièce ; coverage = visibles / silhouette solo."""
    lcfg = cfg["labels"]
    t0 = time.perf_counter()
    channels, attrs = common.read_exr_all(exr_path)
    manifest = common.crypto_manifest(attrs)
    ids, covs = common.crypto_rank_planes(channels)
    M, Minv = camera_matrices(cam, res)

    lines: list[str] = []
    n_pos = 0
    n_hard = 0
    for spec in specs:
        if spec.get("status") == "rejected_out_of_zone":
            continue
        name = spec["obj_name"]
        fid = manifest.get(name) if manifest else common.crypto_name_to_float(name)
        if fid is None:
            fid = common.crypto_name_to_float(name)
        mask = common.crypto_coverage_for(ids, covs, fid)
        visible_px = float(mask.sum())
        bbox = common.mask_bbox(mask, cfg["render"]["mask_threshold"])
        spec["visible_px"] = round(visible_px, 1)
        if bbox is None or visible_px < lcfg["min_visible_px"]:
            spec["status"] = "dropped_invisible" if visible_px <= 0 else "dropped_low_px"
            spec["coverage"] = 0.0 if visible_px <= 0 else None
            continue

        obj = bpy.data.objects[name]
        solo_px = solo_area_estimate(obj, M, Minv, res, lcfg["solo_max_samples"])
        coverage = min(1.0, visible_px / solo_px) if solo_px > 1e-6 else 1.0
        spec["coverage"] = round(coverage, 4)
        spec["solo_px_est"] = round(solo_px, 1)
        spec["bbox_px"] = bbox

        x0, y0, x1, y1 = bbox
        cx = (x0 + x1 + 1) / 2.0 / res
        cy = (y0 + y1 + 1) / 2.0 / res
        w = (x1 - x0 + 1) / res
        h = (y1 - y0 + 1) / res
        # auto-contrôles (critère S.2)
        assert 0.0 <= coverage <= 1.0, f"coverage hors [0,1]: {coverage}"
        assert 0.0 < w <= 1.0 and 0.0 < h <= 1.0, f"bbox invalide: {bbox}"
        assert 0.0 <= cx - w / 2 + 1e-6 and cx + w / 2 <= 1.0 + 1e-6, f"bbox hors image: {bbox}"
        assert 0.0 <= cy - h / 2 + 1e-6 and cy + h / 2 <= 1.0 + 1e-6, f"bbox hors image: {bbox}"
        yolo = f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"
        spec["bbox_yolo"] = [round(v, 6) for v in (cx, cy, w, h)]
        if coverage >= lcfg["coverage_positive"]:
            spec["status"] = "positive"
            lines.append(yolo)
            n_pos += 1
        elif coverage >= lcfg["coverage_hard"]:
            spec["status"] = "hard"
            lines.append(f"# hard {yolo}")
            n_hard += 1
        else:
            spec["status"] = "dropped_coverage_lt10"

    n_eligible = sum(1 for s in specs if s.get("status") == "positive")
    assert n_pos == n_eligible, f"labels positifs ({n_pos}) != pièces éligibles ({n_eligible})"
    return {"lines": lines, "n_pos": n_pos, "n_hard": n_hard,
            "decode_s": round(time.perf_counter() - t0, 2)}


# ---------------------------------------------------------------------------
# Assertion d'échelle (démarrage de CHAQUE batch — critère S.2)
# ---------------------------------------------------------------------------


def assert_scale(job: dict) -> None:
    cfg = job["config"]["scale_assert"]
    common.reset_scene()
    dat = job["parts_pool"]["dat_by_id"].get(cfg["part_id"])
    if dat is None:
        p, _ = common.resolve_part_file(cfg["part_id"])
        dat = str(p)
    obj = common.import_part(Path(dat), name="scale_check")
    dims_mm = sorted((d * common.UNIT_TO_MM for d in common.object_dims(obj)), reverse=True)
    exp = sorted(cfg["expected_mm"], reverse=True)
    for got, want in zip(dims_mm, exp):
        assert abs(got - want) <= cfg["tol_mm"], (
            f"ECHELLE INVALIDE: {cfg['part_id']} = {[round(d, 2) for d in dims_mm]} mm, "
            f"attendu {exp} ±{cfg['tol_mm']}")
    print(f"[scale] OK {cfg['part_id']} = {[round(d, 2) for d in dims_mm]} mm")


# ---------------------------------------------------------------------------
# Scène complète
# ---------------------------------------------------------------------------


def generate_scene(job: dict, scene_def: dict) -> dict:
    cfg = job["config"]
    res = cfg["render"]["resolution"]
    rng = random.Random(scene_def["seed"])
    t_scene = time.perf_counter()
    params: dict = {}
    rec = {"scene_id": scene_def["name"], "index": scene_def["index"],
           "seed": scene_def["seed"], "dataset_id": job["dataset_id"],
           "generator": job["generator"], "params": params}

    make_piece_material.rough_noise_scale = cfg["piece_material"]["rough_noise_scale"]
    make_piece_material.bump_noise_scale = cfg["piece_material"]["bump_noise_scale"]

    common.reset_scene()
    scene = bpy.context.scene
    common.ensure_rbworld(frame_end=cfg["sim"]["frame_end"],
                          substeps=cfg["sim"]["substeps"],
                          iterations=cfg["sim"]["iterations"])
    setup_hdri(rng, cfg, job["hdris"], params)
    setup_key_light(rng, cfg, params)
    add_floor(rng, cfg, job["textures"], params)

    background_only = rng.random() < cfg["scene"]["p_background_only"]
    params["scene_type"] = "background" if background_only else "pile"
    specs: list[dict] = []
    pieces: list = []
    if not background_only:
        ridx, reg = pick_regime(rng, cfg["scene"]["n_pieces_regimes"])
        n = rng.randint(reg["min"], reg["max"])
        params["n_regime"] = ridx
        params["n_pieces"] = n
        specs = sample_pieces(rng, cfg, job["parts_pool"], job["palette"], n)
        pieces = build_pile(rng, cfg, specs, params)
    else:
        params["n_pieces"] = 0

    cam = setup_camera(rng, cfg, pieces, params)
    _, Minv = camera_matrices(cam, res)
    place_distractors(rng, cfg, job["distractor_models"], pieces, cam, Minv, res, params)

    out = Path(job["out_dir"])
    png = out / "images" / f"{scene_def['name']}.png"
    exr = Path(job["run_dir"]) / f"{scene_def['name']}.exr"
    rt = render_scene(exr, png, res, cfg["render"]["eevee_samples"])
    params.update(rt)

    if pieces:
        lab = extract_labels(exr, specs, cam, res, cfg)
    else:
        lab = {"lines": [], "n_pos": 0, "n_hard": 0, "decode_s": 0.0}
    (out / "labels" / f"{scene_def['name']}.txt").write_text(
        "\n".join(lab["lines"]) + ("\n" if lab["lines"] else ""))
    if not cfg["render"]["keep_exr"]:
        exr.unlink(missing_ok=True)

    rec["pieces"] = [{k: v for k, v in s.items() if k != "dat"} for s in specs]
    rec["n_labels_positive"] = lab["n_pos"]
    rec["n_labels_hard"] = lab["n_hard"]
    rec["decode_s"] = lab["decode_s"]
    rec["scene_s"] = round(time.perf_counter() - t_scene, 2)
    rec["image"] = str(png.relative_to(out))
    rec["label"] = f"labels/{scene_def['name']}.txt"
    (out / "manifests" / f"{scene_def['name']}.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False))
    return rec


def main() -> None:
    job = parse_job()
    out = Path(job["out_dir"])
    for sub in ("images", "labels", "manifests"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    run_dir = Path(job["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)
    results_path = run_dir / f"batch_{job['batch_id']:03d}_results.jsonl"

    assert_scale(job)

    t0 = time.perf_counter()
    n_ok = 0
    for scene_def in job["scenes"]:
        manifest = out / "manifests" / f"{scene_def['name']}.json"
        if manifest.exists():
            continue
        try:
            rec = generate_scene(job, scene_def)
            n_ok += 1
            with results_path.open("a") as f:
                f.write(json.dumps({"scene_id": rec["scene_id"], "ok": True,
                                    "scene_s": rec["scene_s"],
                                    "n_pos": rec["n_labels_positive"],
                                    "n_hard": rec["n_labels_hard"]}) + "\n")
            print(f"[scene] {rec['scene_id']} ok {rec['scene_s']}s "
                  f"N={rec['params'].get('n_pieces')} pos={rec['n_labels_positive']} "
                  f"hard={rec['n_labels_hard']}", flush=True)
        except Exception as e:  # noqa: BLE001
            with results_path.open("a") as f:
                f.write(json.dumps({"scene_id": scene_def["name"], "ok": False,
                                    "error": f"{type(e).__name__}: {e}"}) + "\n")
            print(f"[scene] {scene_def['name']} ECHEC: {type(e).__name__}: {e}",
                  flush=True)
    dt = time.perf_counter() - t0
    print(f"[batch {job['batch_id']}] {n_ok}/{len(job['scenes'])} scènes en {dt:.1f}s "
          f"({dt / max(n_ok, 1):.2f}s/scène)", flush=True)


if __name__ == "__main__":
    main()
