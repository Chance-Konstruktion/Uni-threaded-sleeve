import bpy
import importlib

def get_rod_api():
    """Sichere Import-Funktion für Uni-threaded-rod"""
    try:
        rod = importlib.import_module("Uni_threaded_rod")
        return rod.api
    except ImportError:
        pass

    try:
        rod = importlib.import_module("Uni-threaded-rod")
        return rod.api
    except ImportError:
        pass

    if "Uni_threaded_rod" in bpy.context.preferences.addons:
        try:
            addon = bpy.context.preferences.addons["Uni_threaded_rod"]
            return addon.module.api
        except:
            pass

    raise ImportError("Uni-threaded-rod wurde nicht gefunden!\nBitte installiere und aktiviere zuerst 'Uni-threaded-rod'.")

def sleeve(spec="M10", length=40.0, wall_thickness=3.5, **kwargs):
    rod_api = get_rod_api()
    thread_data = rod_api.thread(spec=spec, length=length, internal=True, **kwargs)
    
    inner_dia = thread_data["diameter_mm"]
    outer_dia = inner_dia + 2 * wall_thickness + kwargs.get("outer_add", 0)
    
    return {
        **thread_data,
        "outer_diameter": outer_dia,
        "wall_thickness": wall_thickness,
    }