import bpy
from .api import create_sleeve_data
from .sleeve_builder import create_sleeve
from .presets import get_preset_items

class SLEEVE_Properties(bpy.types.PropertyGroup):
    preset: bpy.props.EnumProperty(name="Preset", items=get_preset_items, default="STANDARD_MUFFE")
    
    standard: bpy.props.EnumProperty(name="Norm", default="METRIC_ISO", items=[("METRIC_ISO", "Metrisch", "")])
    diameter_enum: bpy.props.EnumProperty(name="Ø", items=lambda s,c: get_diameter_items(s,c))
    length: bpy.props.FloatProperty(name="Länge", default=40, min=5, max=500, unit='LENGTH')
    
    shape: bpy.props.EnumProperty(name="Form", items=[('CYLINDER', "Rund", ""), ('HEX', "Sechskant", "")], default='CYLINDER')
    
    wall_thickness: bpy.props.FloatProperty(name="Wandstärke", default=3.5, min=1.0, unit='LENGTH')
    outer_add: bpy.props.FloatProperty(name="Extra Außen", default=0, min=0)
    clearance: bpy.props.FloatProperty(name="Spiel", default=0.0, min=0, max=1.0)
    
    add_flange: bpy.props.BoolProperty(name="Flansch", default=False)
    flange_dia: bpy.props.FloatProperty(name="Flansch Ø", default=30)
    flange_thickness: bpy.props.FloatProperty(name="Flanschstärke", default=6)
    flange_both_sides: bpy.props.BoolProperty(name="Beidseitig", default=False)

    starts: bpy.props.IntProperty(name="Gängig", default=1, min=1, max=4)
    handedness: bpy.props.EnumProperty(name="Richtung", items=[("RIGHT","Rechts",""), ("LEFT","Links","")])

def get_diameter_items(self, context):
    try:
        from Uni_threaded_rod.database import get_diameter_items_for_standard
        return get_diameter_items_for_standard(self.standard)
    except:
        return [("10","M10",""), ("12","M12",""), ("16","M16","")]

class SLEEVE_OT_create(bpy.types.Operator):
    bl_idname = "sleeve.create"
    bl_label = "Sleeve erstellen"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.sleeve_props
        create_sleeve(props)
        self.report({'INFO'}, f"Sleeve {props.preset} erstellt!")
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
        layout.prop(p, "diameter_enum")
        layout.prop(p, "length")
        layout.prop(p, "shape")
        
        col = layout.column(align=True)
        col.prop(p, "wall_thickness")
        col.prop(p, "outer_add")
        col.prop(p, "clearance")

        layout.prop(p, "add_flange")
        if p.add_flange:
            layout.prop(p, "flange_dia")
            layout.prop(p, "flange_thickness")
            layout.prop(p, "flange_both_sides")

        layout.separator()
        row = layout.row()
        row.prop(p, "starts")
        row.prop(p, "handedness")

        layout.separator()
        layout.operator("sleeve.create", icon="MOD_SCREW", text="SLEEVE ERZEUGEN")

classes = [SLEEVE_Properties, SLEEVE_OT_create, SLEEVE_PT_main]

def register_properties():
    bpy.types.Scene.sleeve_props = bpy.props.PointerProperty(type=SLEEVE_Properties)