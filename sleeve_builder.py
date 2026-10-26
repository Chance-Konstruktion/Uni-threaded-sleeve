import bpy

from .api import create_sleeve_data
from .presets import PRESETS
from .rod_link import (
    get_rod_database,
    get_rod_geometry_engine,
    get_rod_mesh_builder,
    require_rod_compatibility,
)


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


def _remove_object(obj):
    """Best-effort removal of a temporary Blender object without masking errors."""
    if obj is None:
        return
    try:
        bpy.data.objects.remove(obj, do_unlink=True)
    except (ReferenceError, RuntimeError, TypeError):
        # Blender may already have unlinked the object as part of a failed
        # modifier operation. Cleanup should preserve the original exception.
        pass


def _remove_mesh(mesh):
    if mesh is None:
        return
    remove = getattr(bpy.data.meshes, "remove", None)
    if callable(remove):
        try:
            remove(mesh)
        except (ReferenceError, RuntimeError, TypeError):
            pass


def _build_thread_cutter(standard_key, diameter, pitch, length, starts, handedness, clearance):
    geom = get_rod_geometry_engine()
    mb = get_rod_mesh_builder()
    db = get_rod_database()

    standard = db.THREAD_STANDARDS.get(standard_key, {})
    taper_ratio = standard.get("special_params", {}).get("taper_ratio", 0.0)
    tolerance_class = db.get_default_tolerance_class(standard_key, internal=True)

    profile, _warnings = geom.generate_profile(
        standard_key,
        diameter,
        pitch,
        tolerance_class=tolerance_class,
        internal=True,
        clearance=clearance,
        return_warnings=True,
    )

    bm = mb.create_thread_mesh(
        profile_points=profile,
        diameter=diameter,
        pitch=pitch,
        length=length + 2.0,
        starts=starts,
        handedness=handedness,
        end_type="FLAT",
        taper_ratio=taper_ratio,
        lod_level="FINAL",
        segment_override=64,
    )

    mesh = None
    cutter = None
    try:
        mesh = bpy.data.meshes.new("SleeveCutter")
        bm.to_mesh(mesh)
        cutter = bpy.data.objects.new("SleeveCutter", mesh)
        bpy.context.collection.objects.link(cutter)
        cutter.location = (0.0, 0.0, -1.0 * MM)
        return cutter
    except Exception:
        _remove_object(cutter)
        _remove_mesh(mesh)
        raise
    finally:
        bm.free()


def _add_flange(sleeve_obj, outer_dia_mm, length_mm, both_sides=False):
    """Fuse flange operands into the sleeve and clean every temporary object."""
    flange_dia = outer_dia_mm * 1.5
    flange_thick = max(2.0, outer_dia_mm * 0.08)
    radius_m = (flange_dia * 0.5) * MM
    depth_m = flange_thick * MM
    flanges = []

    try:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=64, radius=radius_m, depth=depth_m,
            location=(0.0, 0.0, depth_m * 0.5),
        )
        flanges.append(bpy.context.active_object)

        if both_sides:
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=64, radius=radius_m, depth=depth_m,
                location=(0.0, 0.0, length_mm * MM - depth_m * 0.5),
            )
            flanges.append(bpy.context.active_object)

        for index, flange in enumerate(flanges, start=1):
            modifier = None
            modifier_name = f"FlangeUnion_{index}"
            try:
                bpy.ops.object.select_all(action="DESELECT")
                sleeve_obj.select_set(True)
                bpy.context.view_layer.objects.active = sleeve_obj
                modifier = sleeve_obj.modifiers.new(modifier_name, "BOOLEAN")
                modifier.operation = "UNION"
                modifier.object = flange
                if hasattr(modifier, "solver"):
                    try:
                        modifier.solver = "EXACT"
                    except (AttributeError, TypeError, ValueError):
                        pass
                bpy.ops.object.modifier_apply(modifier=modifier_name)
            finally:
                if modifier is not None:
                    try:
                        if modifier_name in sleeve_obj.modifiers:
                            sleeve_obj.modifiers.remove(modifier)
                    except (ReferenceError, RuntimeError, TypeError):
                        pass
        return sleeve_obj
    finally:
        # If constructing or fusing either flange fails, also remove any
        # operands that have not yet reached their own Boolean iteration.
        for flange in flanges:
            _remove_object(flange)


def create_sleeve(props):
    spec = str(getattr(props, "diameter_enum", "10") or "10").strip()
    standard_key = str(getattr(props, "standard", "METRIC_ISO")).strip()
    shape = str(getattr(props, "shape", "CYLINDER")).strip().upper()
    if shape not in {"CYLINDER", "HEX"}:
        raise ValueError("Außenform muss CYLINDER oder HEX sein.")

    raw_length = getattr(props, "length", 40.0)
    raw_starts = getattr(props, "starts", 1)
    handedness = getattr(props, "handedness", "RIGHT")
    raw_clearance = getattr(props, "clearance", 0.0)
    add_flange = bool(getattr(props, "add_flange", False))
    flange_both_sides = bool(getattr(props, "flange_both_sides", False))
    raw_wall_thickness = getattr(props, "wall_thickness", 3.5)
    raw_outer_add = getattr(props, "outer_add", 0.0)
    raw_pitch_override = getattr(props, "pitch_override", 0.0)

    preset_key = getattr(props, "preset", None)
    if preset_key in ("", "NONE"):
        preset_key = None
    preset_cfg = PRESETS.get(preset_key) if preset_key is not None else None
    if preset_key is not None and preset_cfg is None:
        raise ValueError(f"Unbekanntes Sleeve-Preset: {preset_key}")

    if preset_cfg:
        if "flange" in preset_cfg:
            add_flange = bool(preset_cfg["flange"])
        if "wall" in preset_cfg:
            raw_wall_thickness = preset_cfg["wall"]
        if "outer_add" in preset_cfg:
            raw_outer_add = preset_cfg["outer_add"]
        if "clearance" in preset_cfg:
            raw_clearance = preset_cfg["clearance"]
        if "standard" in preset_cfg:
            candidate = preset_cfg["standard"]
            available = get_rod_database().THREAD_STANDARDS
            if candidate not in available:
                raise ValueError(
                    f"Preset {preset_key} benötigt den Rod-Standard {candidate}, "
                    "der in der installierten Uni-threaded-rod-Version fehlt."
                )
            standard_key = candidate

    data = create_sleeve_data(
        spec=spec,
        length=raw_length,
        wall_thickness=raw_wall_thickness,
        outer_add=raw_outer_add,
        clearance=raw_clearance,
        preset=preset_key,
        standard=standard_key,
        starts=raw_starts,
        handedness=handedness,
        pitch_override=raw_pitch_override,
    )

    # Fail before allocating scene objects if this Rod install lacks the
    # Blender-only cutter builder; the data API itself remains bpy-free.
    require_rod_compatibility(include_mesh_builder=True)

    # Only use canonical values that have passed validation.
    length_mm = data["length_mm"]
    starts = data["starts"]
    handedness = data["handedness"]
    clearance = data["clearance"]
    diameter = data["diameter_mm"]
    pitch = data["pitch_mm"]
    outer_dia = data["outer_diameter"]

    sleeve_obj = None
    cutter = None
    try:
        sleeve_obj = _add_outer_body(outer_dia, length_mm, shape)
        if sleeve_obj is None:
            raise RuntimeError("Blender hat keinen Sleeve-Grundkörper erstellt.")
        sleeve_obj.name = f"Sleeve_{standard_key}_{spec}"

        # Fuse the flange(s) before the internal-thread cut. Cutting the entire
        # final body afterwards keeps the bore open through each flange.
        cutter_length_mm = length_mm
        if add_flange:
            sleeve_obj = _add_flange(
                sleeve_obj, outer_dia, length_mm, both_sides=flange_both_sides
            )
            flange_thickness_mm = max(2.0, outer_dia * 0.08)
            cutter_length_mm = max(cutter_length_mm, flange_thickness_mm)

        cutter = _build_thread_cutter(
            standard_key, diameter, pitch, cutter_length_mm, starts, handedness, clearance,
        )
        bpy.context.view_layer.objects.active = sleeve_obj
        mod = sleeve_obj.modifiers.new("ThreadCut", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cutter
        if hasattr(mod, "solver"):
            try:
                mod.solver = "EXACT"
            except (AttributeError, TypeError, ValueError):
                pass
        bpy.ops.object.modifier_apply(modifier="ThreadCut")
        return sleeve_obj
    except Exception:
        _remove_object(sleeve_obj)
        raise
    finally:
        _remove_object(cutter)
