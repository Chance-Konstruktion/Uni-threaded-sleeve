import bpy

from .sleeve_builder import create_sleeve
from .presets import get_preset_items
from .database import get_standards, get_diameter_items_for_standard


# Caches gegen das bekannte Blender-EnumProperty-GC-Problem (items-Strings
# muessen am Leben bleiben).
_ITEM_CACHE = {
    "presets": [],
    "standards": [],
    "diameters": [],
}


def _preset_items(self, context):
    items = get_preset_items() or [("NONE", "-", "")]
    _ITEM_CACHE["presets"] = items
    return items


def _standard_items(self, context):
    stds = get_standards()
    if stds:
        items = [(k, v.get("name", k), v.get("standard", "")) for k, v in stds.items()]
    else:
        items = [("METRIC_ISO", "Metrisch ISO (Rod nicht geladen)", "")]
    _ITEM_CACHE["standards"] = items
    return items


def _diameter_items(self, context):
    items = list(get_diameter_items_for_standard(self.standard) or [])
    if not items:
        items = [("10", "10", "Fallback")]
    _ITEM_CACHE["diameters"] = items
    return items


class SLEEVE_Properties(bpy.types.PropertyGroup):
    preset: bpy.props.EnumProperty(name="Preset", items=_preset_items)
    standard: bpy.props.EnumProperty(name="Gewindetyp", items=_standard_items)
    diameter_enum: bpy.props.EnumProperty(name="Durchmesser", items=_diameter_items)
    length: bpy.props.FloatProperty(name="Laenge (mm)", default=40.0, min=5.0, max=500.0)
    shape: bpy.props.EnumProperty(
        name="Aussenform",
        items=[("CYLINDER", "Rund", ""), ("HEX", "Sechskant", "")],
        default="CYLINDER",
    )
    wall_thickness: bpy.props.FloatProperty(name="Wandstaerke (mm)", default=3.5, min=1.0)
    outer_add: bpy.props.FloatProperty(name="Extra Aussen (mm)", default=0.0, min=0.0)
    clearance: bpy.props.FloatProperty(name="Spiel (mm)", default=0.0, min=0.0, max=1.0)
    add_flange: bpy.props.BoolProperty(name="Flansch", default=False)
    starts: bpy.props.IntProperty(name="Gaengig", default=1, min=1, max=4)
    handedness: bpy.props.EnumProperty(
        name="Richtung",
        items=[("RIGHT", "Rechts", ""), ("LEFT", "Links", "")],
        default="RIGHT",
    )


class SLEEVE_OT_create(bpy.types.Operator):
    bl_idname = "sleeve.create"
    bl_label = "Sleeve erstellen"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.sleeve_props
        try:
            create_sleeve(props)
        except ImportError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Sleeve-Erzeugung fehlgeschlagen: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Sleeve {props.standard} {props.diameter_enum} erstellt")
        return {"FINISHED"}


class SLEEVE_PT_main(bpy.types.Panel):
    bl_label = "Uni-threaded-sleeve"
    bl_idname = "SLEEVE_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Uni-threaded-sleeve"

    def draw(self, context):
        layout = self.layout
        p = context.scene.sleeve_props
        col = layout.column(align=True)
        col.prop(p, "preset")
        col.prop(p, "standard")
        col.prop(p, "diameter_enum")
        col.separator()
        col.prop(p, "length")
        col.prop(p, "shape")
        col.prop(p, "wall_thickness")
        col.prop(p, "outer_add")
        col.prop(p, "clearance")
        col.prop(p, "add_flange")
        col.prop(p, "starts")
        col.prop(p, "handedness")
        layout.operator("sleeve.create", icon="MOD_SCREW")


classes = [SLEEVE_Properties, SLEEVE_OT_create, SLEEVE_PT_main]


def register_properties():
    bpy.types.Scene.sleeve_props = bpy.props.PointerProperty(type=SLEEVE_Properties)
