import bpy
import importlib
import sys

bl_info = {
    "name": "Uni-threaded-sleeve",
    "author": "Chance-Konstruktion + Grok",
    "version": (1, 3, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Uni-threaded-sleeve",
    "description": "Gewindemuffen Generator - benötigt Uni-threaded-rod",
    "category": "Mesh",
    "warning": "Uni-threaded-rod muss zuerst installiert und aktiviert sein!",
}

def _runtime(name):
    full = f"{__name__}.{name}"
    if full in sys.modules:
        return importlib.reload(sys.modules[full])
    return importlib.import_module(f".{name}", __name__)

# Modules laden
api = _runtime("api")
sleeve_builder = _runtime("sleeve_builder")
presets = _runtime("presets")
database = _runtime("database")
ui_panel = _runtime("ui_panel")

classes = getattr(ui_panel, "classes", [])

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