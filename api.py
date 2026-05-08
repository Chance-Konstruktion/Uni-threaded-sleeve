from Uni_threaded_rod.api import thread
from .presets import PRESETS

def create_sleeve_data(spec="M10", length=40, wall_thickness=3.5, outer_add=0, clearance=0.0, preset=None, **kwargs):
    if preset and preset in PRESETS:
        p = PRESETS[preset]
        wall_thickness = p.get("wall", wall_thickness)
        outer_add = p.get("outer_add", outer_add)
        clearance = p.get("clearance", clearance)

    thread_data = thread(spec, length=length, internal=True, **kwargs)
    
    inner_dia = thread_data["diameter_mm"] + clearance
    outer_dia = inner_dia + 2 * wall_thickness + outer_add

    return {
        **thread_data,
        "outer_diameter": outer_dia,
        "inner_diameter": inner_dia,
        "wall_thickness": wall_thickness,
        "clearance": clearance,
    }