"""Headless Blender smoke test for the Uni-threaded-sleeve add-on.

Requires the Uni-threaded-rod engine (thread data + geometry). Point at it via
``UNI_THREADED_ROD_PATH`` or have it checked out as a sibling directory.

Run via:
blender -b --factory-startup --python scripts/blender_smoke_test.py
"""

import importlib.util
import math
import os
import pathlib
import sys

if importlib.util.find_spec("bpy") is None:
    raise SystemExit("bpy is required. Run this script through Blender.")

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

SLEEVE_ROOT = pathlib.Path(__file__).resolve().parents[1]
_env = os.environ.get("UNI_THREADED_ROD_PATH")
ROD_ROOT = pathlib.Path(_env) if _env else SLEEVE_ROOT.parent / "Uni-threaded-rod"

if not (ROD_ROOT / "__init__.py").is_file():
    raise SystemExit(f"Uni-threaded-rod engine not found at {ROD_ROOT}")


def _load(module_name, root):
    spec = importlib.util.spec_from_file_location(
        module_name, root / "__init__.py", submodule_search_locations=[str(root)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# The Rod engine must be importable under a name the sleeve's rod_link accepts.
_load("Uni_threaded_rod", ROD_ROOT)
addon = _load("uni_threaded_sleeve_addon", SLEEVE_ROOT)

addon.register()
try:
    scene = bpy.context.scene
    props = scene.sleeve_props
    props.preset = "NONE"
    props.standard = "METRIC_ISO"
    props.diameter_enum = "10.0"
    props.length = 20.0
    props.wall_thickness = 3.5
    props.shape = "CYLINDER"
    props.starts = 1

    result = bpy.ops.sleeve.create()
    assert "FINISHED" in result, f"Operator did not finish: {result}"

    created = next((o for o in bpy.data.objects if o.name.startswith("Sleeve_")), None)
    assert created is not None, "No Sleeve_* object was created"
    assert created.type == "MESH", f"Created object is not a mesh: {created.type}"

    mesh = created.data
    assert len(mesh.vertices) > 0, "Sleeve mesh has no vertices"

    radii = [math.hypot(v.co.x, v.co.y) for v in mesh.vertices]
    outer_radius_m = (10.0 + 2.0 * 3.5) / 2000.0  # 17 mm OD -> 0.0085 m
    assert max(radii) >= outer_radius_m - 0.0005, f"Outer radius too small: {max(radii)}"
    assert max(radii) <= outer_radius_m + 0.0015, f"Outer radius too large: {max(radii)}"

    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        volume = abs(bm.calc_volume())
    finally:
        bm.free()

    solid_outer = math.pi * outer_radius_m**2 * (20.0 / 1000.0)
    assert volume > 0.0, "Sleeve has zero volume"
    assert volume < solid_outer * 0.95, (
        f"Sleeve is not hollow (volume {volume:.3e} vs solid {solid_outer:.3e}) - "
        "the internal thread bore was not cut"
    )

    print(
        f"[smoke] sleeve OK: verts={len(mesh.vertices)} "
        f"max_r={max(radii):.5f} volume={volume:.3e} solid_outer={solid_outer:.3e}"
    )

    # Regression: the flange used to be added after the thread cutter and
    # could cap the bore. Test both ends on a size whose flange is > 2 mm thick.
    metric_items = addon.database.get_diameter_items_for_standard("METRIC_ISO")
    size_token = None
    for token, _label, _description in metric_items:
        try:
            if math.isclose(float(token), 30.0, abs_tol=1e-6):
                size_token = token
                break
        except (TypeError, ValueError):
            continue
    assert size_token is not None, "METRIC_ISO size M30 missing from Rod database"

    props.preset = "NONE"
    props.standard = "METRIC_ISO"
    props.diameter_enum = size_token
    props.length = 20.0
    props.wall_thickness = 3.5
    props.outer_add = 0.0
    props.clearance = 0.0
    props.pitch_override = 0.0
    props.shape = "CYLINDER"
    props.starts = 1
    props.handedness = "RIGHT"
    props.add_flange = True
    props.flange_both_sides = True

    result = bpy.ops.sleeve.create()
    assert "FINISHED" in result, f"Flanged sleeve operator did not finish: {result}"
    flanged = bpy.context.active_object
    assert flanged is not None and flanged.type == "MESH", "Flanged sleeve mesh missing"

    flange_thickness_m = max(2.0, 37.0 * 0.08) / 1000.0
    world_bottom_flange_z = flange_thickness_m * 0.5
    world_top_flange_z = 0.020 - flange_thickness_m * 0.5
    bm = bmesh.new()
    try:
        bm.from_mesh(flanged.data)
        bm.transform(flanged.matrix_world)
        non_manifold = [edge for edge in bm.edges if not edge.is_manifold]
        assert not non_manifold, (
            f"Flanged sleeve is not a single manifold solid: {len(non_manifold)} non-manifold edges"
        )
        tree = BVHTree.FromBMesh(bm)
        for label, z_m in (
            ("bottom flange", world_bottom_flange_z),
            ("top flange", world_top_flange_z),
        ):
            hit, _normal, _face_index, distance = tree.ray_cast(
                Vector((0.0, 0.0, z_m)), Vector((1.0, 0.0, 0.0)), 0.05
            )
            assert hit is not None, f"No surface hit while checking {label} bore"
            assert distance < 0.020, (
                f"{label} bore appears blocked: first radial surface at {distance:.4f} m"
            )
    finally:
        bm.free()

    print(
        f"[smoke] flanged sleeve OK: verts={len(flanged.data.vertices)} "
        f"bottom_z={world_bottom_flange_z:.5f} top_z={world_top_flange_z:.5f}"
    )

    # Integration matrix: real cutter with pitch override + left-hand,
    # multi-start thread and hexagonal outer body.
    props.preset = "NONE"
    props.standard = "METRIC_ISO"
    props.diameter_enum = "10.0"
    props.length = 20.0
    props.wall_thickness = 3.5
    props.outer_add = 0.0
    props.clearance = 0.1
    props.pitch_override = 1.0
    props.shape = "HEX"
    props.starts = 2
    props.handedness = "LEFT"
    props.add_flange = False
    props.flange_both_sides = False

    result = bpy.ops.sleeve.create()
    assert "FINISHED" in result, f"Hex/left-hand/override sleeve did not finish: {result}"
    variant = bpy.context.active_object
    assert variant is not None and variant.type == "MESH", "Variant sleeve mesh missing"
    bm = bmesh.new()
    try:
        bm.from_mesh(variant.data)
        bm.transform(variant.matrix_world)
        non_manifold = [edge for edge in bm.edges if not edge.is_manifold]
        assert not non_manifold, (
            f"Hex/left-hand/override sleeve is not manifold: {len(non_manifold)} edges"
        )
        volume = abs(bm.calc_volume())
        assert volume > 0.0, "Hex/left-hand/override sleeve has zero volume"
        variant_radii = [math.hypot(v.co.x, v.co.y) for v in bm.verts]
        assert max(variant_radii) >= 0.0080, (
            f"Hex outer body dimensions look incorrect: max radius {max(variant_radii):.5f} m"
        )
    finally:
        bm.free()

    print(
        f"[smoke] hex/left-hand/pitch-override sleeve OK: "
        f"verts={len(variant.data.vertices)} volume={volume:.3e}"
    )
finally:
    addon.unregister()
