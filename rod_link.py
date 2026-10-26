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
    "Uni_threaded_rod_main",
    "uni_threaded_rod",
    "uni_threaded_rod_main",
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


def get_rod_mechanical_validation():
    """Return Rod's validation helpers used for self-consistent API metadata."""
    return _submodule("mechanical_validation")


def require_rod_compatibility(include_mesh_builder=False):
    """Load and validate Rod capabilities required for the requested operation.

    Import remains lazy so Blender can discover/enable this add-on even when
    Rod has not been enabled yet. Generation, however, must not silently run
    against a partial or incompatible Rod installation.
    """
    try:
        modules = {
            "database": get_rod_database(),
            "api": get_rod_api(),
            "geometry_engine": get_rod_geometry_engine(),
            "mechanical_validation": get_rod_mechanical_validation(),
        }
        if include_mesh_builder:
            modules["mesh_builder"] = get_rod_mesh_builder()
    except (ImportError, ModuleNotFoundError, AttributeError) as exc:
        raise ImportError(
            "Uni-threaded-sleeve benötigt eine kompatible Uni-threaded-rod-Installation. "
            "Bitte Rod installieren/aktivieren und aktualisieren."
        ) from exc

    required = {
        "database": ("THREAD_STANDARDS", "get_default_tolerance_class"),
        "api": ("thread",),
        "geometry_engine": ("generate_profile",),
        "mechanical_validation": (
            "allowables_from_property_class",
            "validate_combined_load_case",
        ),
    }
    if include_mesh_builder:
        required["mesh_builder"] = ("create_thread_mesh",)

    missing = []
    for module_name, attributes in required.items():
        module = modules[module_name]
        for attribute in attributes:
            value = getattr(module, attribute, None)
            if attribute == "THREAD_STANDARDS":
                if not isinstance(value, dict) or not value:
                    missing.append(f"{module_name}.{attribute}")
            elif not callable(value):
                missing.append(f"{module_name}.{attribute}")

    thread_function = modules["api"].thread
    try:
        import inspect

        parameters = inspect.signature(thread_function).parameters
        for parameter in ("internal", "starts", "standard", "fit", "material", "length"):
            if parameter not in parameters and not any(
                item.kind == inspect.Parameter.VAR_KEYWORD for item in parameters.values()
            ):
                missing.append(f"api.thread({parameter}=...)")
    except (TypeError, ValueError):
        # Some Blender-wrapped callables do not expose a Python signature;
        # the required keyword contract is then verified by integration tests.
        pass

    if missing:
        raise ImportError(
            "Inkompatible Uni-threaded-rod-Version; fehlende API-Funktionen: "
            + ", ".join(missing)
            + ". Bitte Uni-threaded-rod aktualisieren."
        )

    return modules

