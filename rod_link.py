"""Robuster Zugriff auf das Uni-threaded-rod Addon.

Blender installiert Addons aus ZIPs gerne unter Ordnernamen wie
`Uni-threaded-rod-main`. Python kann solche Namen nicht direkt importieren
(Dashes sind ungueltig). Wir scannen daher `sys.modules` nach dem geladenen
Rod-Modul anhand seines `bl_info["name"]` und fallen auf die ueblichen
Namensvarianten zurueck.
"""
import importlib
import sys

_ROD_BL_NAME = "Uni-threaded-rod"
_rod_cache = None

_NAME_CANDIDATES = (
    "Uni_threaded_rod",
    "Uni-threaded-rod",
    "Uni_threaded_rod_main",
    "Uni-threaded-rod-main",
    "uni_threaded_rod",
    "uni-threaded-rod",
)


def _scan_loaded():
    for mod in list(sys.modules.values()):
        if mod is None:
            continue
        info = getattr(mod, "bl_info", None)
        if isinstance(info, dict) and info.get("name") == _ROD_BL_NAME:
            if hasattr(mod, "THREAD_STANDARDS") or hasattr(mod, "database"):
                return mod
    return None


def get_rod():
    """Liefert das geladene Rod-Hauptmodul oder wirft ImportError."""
    global _rod_cache
    if _rod_cache is not None:
        return _rod_cache
    mod = _scan_loaded()
    if mod is not None:
        _rod_cache = mod
        return mod
    for name in _NAME_CANDIDATES:
        try:
            _rod_cache = importlib.import_module(name)
            return _rod_cache
        except Exception:
            continue
    raise ImportError(
        "Uni-threaded-rod wurde nicht gefunden. Bitte zuerst das Addon "
        "'Uni-threaded-rod' installieren und aktivieren."
    )


def _submodule(name):
    rod = get_rod()
    full = f"{rod.__name__}.{name}"
    if full in sys.modules:
        return sys.modules[full]
    return importlib.import_module(full)


def get_rod_database():
    return _submodule("database")


def get_rod_api():
    return _submodule("api")


def get_rod_geometry_engine():
    return _submodule("geometry_engine")


def get_rod_mesh_builder():
    return _submodule("mesh_builder")
