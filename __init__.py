import importlib
import bpy
import sys

bl_info = {
    "name": "Uni-threaded-sleeve",
    "author": "Chance-Konstruktion + Grok",
    "version": (1, 2, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Uni-threaded-sleeve",
    "description": "Vollständiger Gewindemuffen-Generator mit allen Typen",
    "category": "Mesh",
    "warning": "Benötigt Uni-threaded-rod",
}

def _runtime_module(name):
    full = f"{__name__}.{name}"
    if full in sys.modules:
        return importlib.reload(sys.modules[full])
    return importlib.import_module(f".{name}", __name__)

if "bpy" in locals():
    api = _runtime_module("api")
    sleeve_builder = _runtime_module("sleeve_builder")
    presets = _runtime_module("presets")
    database = _runtime_module("database")
    ui_panel = _runtime_module("ui_panel")

    classes = getattr(ui_panel, 'classes', [])

    def register():
        for cls in classes:
            bpy.utils.register_class(cls)
        if hasattr(ui_panel, "register_properties"):
            ui_panel.register_properties()

    def unregister():
        for cls in reversed(classes):
            bpy.utils.unregister_class(cls)
        if hasattr(bpy.types.Scene, "sleeve_props"):
            del bpy.types.Scene.sleeve_props
else:
    def register(): pass
    def unregister(): pass