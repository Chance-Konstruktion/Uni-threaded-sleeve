import bpy
from .api import create_sleeve_data

def create_sleeve(props):
    data = create_sleeve_data(
        spec=props.diameter_enum,
        length=props.length,
        wall_thickness=props.wall_thickness,
        outer_add=props.outer_add if hasattr(props, "outer_add") else 0,
        clearance=props.clearance,
        preset=props.preset
    )

    outer_dia = data["outer_diameter"]

    if props.shape == 'CYLINDER':
        bpy.ops.mesh.primitive_cylinder_add(
            radius=outer_dia/2, depth=props.length, location=(0,0,0))
    else:  # HEXAGON
        bpy.ops.mesh.primitive_circle_add(radius=outer_dia/2, fill_type='NGON', vertices=6)
        obj = bpy.context.active_object
        mod = obj.modifiers.new("Solidify", 'SOLIDIFY')
        mod.thickness = props.length
        bpy.ops.object.convert(target='MESH')
    
    sleeve = bpy.context.active_object
    sleeve.name = f"Sleeve_{props.preset or 'M'}{props.diameter_enum}"

    # Screw Modifier + Boolean for thread
    bpy.ops.mesh.primitive_cylinder_add(radius=data["inner_diameter"]/2, depth=props.length+4, location=(0,0,-2))
    cutter = bpy.context.active_object
    mod = cutter.modifiers.new("Screw", 'SCREW')
    mod.angle = 6.283185 * (props.length / data.get("pitch_mm", 1.5))
    mod.steps = 64
    mod.iterations = 1
    mod.screw_offset = props.length

    bool_mod = sleeve.modifiers.new("Thread", 'BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = cutter
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)

    return sleeve