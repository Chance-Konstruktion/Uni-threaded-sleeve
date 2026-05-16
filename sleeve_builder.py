import bpy

from .api import create_sleeve_data
from .presets import PRESETS
from .rod_link import get_rod_database, get_rod_geometry_engine, get_rod_mesh_builder


MM = 0.001  # Rods mesh_builder skaliert intern mm -> Blender-Meter


def _add_outer_body(outer_dia_mm, length_mm, shape):
    radius_m = (outer_dia_mm * 0.5) * MM
    depth_m = length_mm * MM
    if shape == "HEX":
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=6, radius=radius_m, depth=depth_m,
            location=(0.0, 0.0, depth_m * 0.5),
        )
    else:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=64, radius=radius_m, depth=depth_m,
            location=(0.0, 0.0, depth_m * 0.5),
        )
    return bpy.context.active_object


def _build_thread_cutter(standard_key, diameter, pitch, length, starts, handedness, clearance):
    geom = get_rod_geometry_engine()
    mb = get_rod_mesh_builder()
    db = get_rod_database()

    standard = db.THREAD_STANDARDS.get(standard_key, {})
    taper_ratio = standard.get("special_params", {}).get("taper_ratio", 0.0)

    profile, _warnings = geom.generate_profile(
        standard_key,
        diameter,
        pitch,
        tolerance_class="6H",
        internal=True,
        clearance=clearance,
        return_warnings=True,
    )

    bm = mb.create_thread_mesh(
        profile_points=profile,
        diameter=diameter,
        pitch=pitch,
        length=length + 2.0,  # Ueberstand fuer sauberes Boolean
        starts=max(1, int(starts)),
        handedness=handedness,
        end_type="FLAT",
        taper_ratio=taper_ratio,
        lod_level="FINAL",
        segment_override=64,
    )

    mesh = bpy.data.meshes.new("SleeveCutter")
    bm.to_mesh(mesh)
    bm.free()
    cutter = bpy.data.objects.new("SleeveCutter", mesh)
    bpy.context.collection.objects.link(cutter)
    cutter.location = (0.0, 0.0, -1.0 * MM)  # 1 mm unter den Sleeve schieben
    return cutter


def _add_flange(sleeve_obj, outer_dia_mm, length_mm, both_sides=False):
    """Sehr einfache Flanschplatte unten (und optional oben)."""
    flange_dia = outer_dia_mm * 1.5
    flange_thick = max(2.0, outer_dia_mm * 0.08)
    radius_m = (flange_dia * 0.5) * MM
    depth_m = flange_thick * MM

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64, radius=radius_m, depth=depth_m,
        location=(0.0, 0.0, depth_m * 0.5),
    )
    bottom_flange = bpy.context.active_object

    objs = [sleeve_obj, bottom_flange]
    if both_sides:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=64, radius=radius_m, depth=depth_m,
            location=(0.0, 0.0, length_mm * MM - depth_m * 0.5),
        )
        objs.append(bpy.context.active_object)

    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = sleeve_obj
    bpy.ops.object.join()
    return bpy.context.active_object


def create_sleeve(props):
    spec = getattr(props, "diameter_enum", "10") or "10"
    standard_key = getattr(props, "standard", "METRIC_ISO")
    length_mm = float(props.length)
    starts = int(getattr(props, "starts", 1))
    handedness = getattr(props, "handedness", "RIGHT")
    clearance = float(getattr(props, "clearance", 0.0))
    shape = getattr(props, "shape", "CYLINDER")
    add_flange = bool(getattr(props, "add_flange", False))
    flange_both_sides = bool(getattr(props, "flange_both_sides", False))
    wall_thickness = float(props.wall_thickness)
    outer_add = float(getattr(props, "outer_add", 0.0))
    pitch_override = float(getattr(props, "pitch_override", 0.0))

    preset_key = getattr(props, "preset", None)
    preset_cfg = PRESETS.get(preset_key) if preset_key and preset_key != "NONE" else None
    if preset_cfg:
        if "flange" in preset_cfg:
            add_flange = bool(preset_cfg["flange"])
        if "wall" in preset_cfg:
            wall_thickness = float(preset_cfg["wall"])
        if "outer_add" in preset_cfg:
            outer_add = float(preset_cfg["outer_add"])
        if "clearance" in preset_cfg:
            clearance = float(preset_cfg["clearance"])
        if "standard" in preset_cfg:
            candidate = preset_cfg["standard"]
            try:
                available = get_rod_database().THREAD_STANDARDS
            except Exception:
                available = {}
            if candidate in available:
                standard_key = candidate
            # Sonst: still beim manuell ausgewaehlten Standard bleiben statt
            # Rod mit einem unbekannten Key in den Fehler zu schicken.

    data = create_sleeve_data(
        spec=spec,
        length=length_mm,
        wall_thickness=wall_thickness,
        outer_add=outer_add,
        clearance=clearance,
        preset=preset_key,
        standard=standard_key,
        starts=starts,
        handedness=handedness,
        pitch_override=pitch_override,
    )

    diameter = data["diameter_mm"]
    pitch = data["pitch_mm"]
    outer_dia = data["outer_diameter"]

    sleeve = _add_outer_body(outer_dia, length_mm, shape)
    sleeve.name = f"Sleeve_{standard_key}_{spec}"

    cutter = _build_thread_cutter(
        standard_key, diameter, pitch, length_mm, starts, handedness, clearance,
    )
    try:
        bpy.context.view_layer.objects.active = sleeve
        mod = sleeve.modifiers.new("ThreadCut", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cutter
        if hasattr(mod, "solver"):
            try:
                mod.solver = "EXACT"
            except Exception:
                pass
        bpy.ops.object.modifier_apply(modifier="ThreadCut")
    finally:
        bpy.data.objects.remove(cutter, do_unlink=True)

    if add_flange:
        sleeve = _add_flange(sleeve, outer_dia, length_mm, both_sides=flange_both_sides)

    return sleeve
