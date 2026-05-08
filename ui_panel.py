import bpy
from .api import create_sleeve_data
from .sleeve_builder import create_sleeve
from .presets import get_preset_items
from .database import get_diameter_items_for_standard

class SLEEVE_Properties(bpy.types.PropertyGroup):
    preset: bpy.props.EnumProperty(name="Preset", items=get_preset_items, default="STANDARD_MUFFE")
    standard: bpy.props.EnumProperty(name="Gewindetyp", default="METRIC_ISO", items=lambda self, c: [(k, v['name'], v.get('standard','')) for k,v in SLEEVE_Properties.STANDARDS.items()] if hasattr(SLEEVE_Properties, 'STANDARDS') else [("METRIC_ISO", "Metrisch", "")])
    diameter_enum: bpy.props.EnumProperty(name="Durchmesser", items=lambda s,c: get_diameter_items_for_standard(s.standard))
    length: bpy.props.FloatProperty(name="Länge", default=40, min=5, max=500, unit='LENGTH')
    shape: bpy.props.EnumProperty(name="Außenform", items=[('CYLINDER', "Rund", ""), ('HEX', "Sechskant", "")], default='CYLINDER')
    wall_thickness: bpy.props.FloatProperty(name="Wandstärke", default=3.5, min=1.0, unit='LENGTH')
    outer_add: bpy.props.FloatProperty(name="Extra Außen", default=0, min=0)
    clearance: bpy.props.FloatProperty(name="Spiel", default=0.0, min=0, max=1.0)
    add_flange: bpy.props.BoolProperty(name="Flansch", default=False)
    starts: bpy.props.IntProperty(name="Gängig", default=1, min=1, max=4)
    handedness: bpy.props.EnumProperty(name="Richtung", items=[("RIGHT","Rechts",""), ("LEFT","Links","")])

SLEEVE_Properties.STANDARDS = {
    "METRIC_ISO": {"name": "Metrisch ISO"}, "METRIC_FINE": {"name": "Metrisch Fein"},
    "TRAPEZOIDAL": {"name": "Trapez"}, "PIPE_G": {"name": "Rohr G"}, "UNC": {"name": "UNC"}, "NPT": {"name": "NPT"}
}

class SLEEVE_OT_create(bpy.types.Operator):
    bl_idname = "sleeve.create"
    bl_label = "Sleeve erstellen"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.sleeve_props
        create_sleeve(props)
        self.report({'INFO'}, f"✅ Sleeve {props.diameter_enum} erstellt")
        return {'FINISHED'}

class SLEEVE_PT_main(bpy.types.Panel):
    bl_label = "Uni-threaded-sleeve"
    bl_idname = "SLEEVE_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Uni-threaded-sleeve"

    def draw(self, context):
        layout = self.layout
        p = context.scene.sleeve_props
        layout.prop(p, "preset")
        layout.prop(p, "standard")
        layout.prop(p, "diameter_enum")
        layout.prop(p, "length")
        layout.prop(p, "shape")
        layout.prop(p, "wall_thickness")
        layout.prop(p, "outer_add")
        layout.prop(p, "clearance")
        layout.prop(p, "add_flange")
        layout.prop(p, "starts")
        layout.prop(p, "handedness")
        layout.operator("sleeve.create", icon="MOD_SCREW")

classes = [SLEEVE_Properties, SLEEVE_OT_create, SLEEVE_PT_main]

def register_properties():
    bpy.types.Scene.sleeve_props = bpy.props.PointerProperty(type=SLEEVE_Properties)