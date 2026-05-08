import importlib
import bpy

bl_info = {
    "name": "Uni-threaded-sleeve",
    "author": "Chance-Konstruktion + Grok",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Uni-threaded-sleeve",
    "description": "Vollständiger Gewindemuffen / Sleeve Generator basierend auf Uni-threaded-rod",
    "category": "Mesh",
    "warning": "Benötigt Uni-threaded-rod Add-on",
}

def _runtime_module(name):
    full = f"{__name__}.{name}"
    if full in sys.modules:
        return importlib.reload(sys.modules[full])
    return importlib.import_module(f". {name}", __name__)

if bpy:
    try:
        api = _runtime_module("api")
        sleeve_builder = _runtime_module("sleeve_builder")
        presets = _runtime_module("presets")
        ui_panel = _runtime_module("ui_panel")
    except:
        pass

    classes = ui_panel.classes if 'ui_panel' in locals() else []

    def register():
        for cls in classes:
            bpy.utils.register_class(cls)
        if hasattr(ui_panel, 'register_properties'):
            ui_panel.register_properties()

    def unregister():
        for cls in reversed(classes):
            bpy.utils.unregister_class(cls)
        if hasattr(bpy.types.Scene, "sleeve_props"):
            del bpy.types.Scene.sleeve_props
else:
    def register(): pass
    def unregister(): pass