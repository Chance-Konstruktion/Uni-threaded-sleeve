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
finally:
    addon.unregister()
