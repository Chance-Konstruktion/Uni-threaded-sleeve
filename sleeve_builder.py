import bpy
import bmesh
from mathutils import Vector

def create_sleeve(props):
    from .api import create_sleeve_data
    data = create_sleeve_data(
        spec=props.diameter_enum,
        length=props.length,
        wall_thickness=props.wall_thickness,
        outer_add=getattr(props, 'outer_add', 0),
        clearance=props.clearance,
        preset=props.preset
    )

    outer_dia = data["outer_diameter"]

    # Außengeometrie
    if getattr(props, 'shape', 'CYLINDER') == 'CYLINDER':
        bpy.ops.mesh.primitive_cylinder_add(radius=outer_dia/2, depth=props.length, location=(0,0,0))
    else:  # HEX
        bpy.ops.mesh.primitive_circle_add(radius=outer_dia/2, fill_type='NGON', vertices=6, location=(0,0,0))
        obj = bpy.context.active_object
        mod = obj.modifiers.new("Solidify", 'SOLIDIFY')
        mod.thickness = props.length
        bpy.ops.object.convert(target='MESH')

    sleeve = bpy.context.active_object
    sleeve.name = f"Sleeve_{props.preset or 'M'}{props.diameter_enum}"

    # Innengewinde mit Screw Modifier + Boolean
    bpy.ops.mesh.primitive_cylinder_add(radius=data["inner_diameter"]/2, depth=props.length+4, location=(0,0,-2))
    cutter = bpy.context.active_object
    mod = cutter.modifiers.new("Screw", 'SCREW')
    mod.angle = 6.283185 * (props.length / data.get("pitch_mm", 1.5))
    mod.steps = 64
    mod.iterations = 1
    mod.screw_offset = props.length

    bool_mod = sleeve.modifiers.new("ThreadCut", 'BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = cutter
    bpy.ops.object.modifier_apply(modifier="ThreadCut")
    bpy.data.objects.remove(cutter, do_unlink=True)

    return sleeve