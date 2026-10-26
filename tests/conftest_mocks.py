"""Mocks fuer bpy und Uni-threaded-rod plus Paket-Bootstrap.

Wird vor dem Import des Sleeve-Pakets ausgefuehrt. Die Repo-Wurzel heisst
``Uni-threaded-sleeve`` (mit Bindestrichen, also nicht direkt importierbar);
wir registrieren sie hier unter dem Python-konformen Namen
``uni_threaded_sleeve`` in ``sys.modules``.
"""
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock


REPO_ROOT = Path(__file__).resolve().parent.parent


def _mk_bpy_mock():
    bpy = types.ModuleType("bpy")

    def _enum_prop(items=None, name="", default=None, **kw):
        return ("ENUM", name, items, default)

    def _float_prop(name="", default=0.0, min=None, max=None, **kw):
        return ("FLOAT", name, default, min, max)

    def _int_prop(name="", default=0, min=None, max=None, **kw):
        return ("INT", name, default, min, max)

    def _bool_prop(name="", default=False, **kw):
        return ("BOOL", name, default)

    def _pointer_prop(type=None, **kw):
        return ("POINTER", type)

    bpy.props = types.SimpleNamespace(
        EnumProperty=_enum_prop,
        FloatProperty=_float_prop,
        IntProperty=_int_prop,
        BoolProperty=_bool_prop,
        PointerProperty=_pointer_prop,
    )

    class _Base:
        pass

    bpy.types = types.SimpleNamespace(
        PropertyGroup=_Base, Panel=_Base, Operator=_Base,
        Scene=types.SimpleNamespace(),
    )
    bpy.utils = types.SimpleNamespace(
        register_class=lambda c: None,
        unregister_class=lambda c: None,
    )
    bpy.ops = types.SimpleNamespace(
        mesh=types.SimpleNamespace(primitive_cylinder_add=MagicMock()),
        object=types.SimpleNamespace(
            select_all=MagicMock(),
            join=MagicMock(),
            modifier_apply=MagicMock(),
        ),
    )

    class _Active:
        def __init__(self):
            self.modifiers = MagicMock()
            self.name = "MockObj"
            self.location = (0, 0, 0)

        def select_set(self, v):
            pass

    active = _Active()

    class _CtxCollection:
        def __init__(self):
            self.objects = MagicMock()
            self.objects.link = MagicMock()

    bpy.context = types.SimpleNamespace(
        active_object=active,
        view_layer=types.SimpleNamespace(
            objects=types.SimpleNamespace(active=None),
        ),
        scene=types.SimpleNamespace(sleeve_props=None),
        collection=_CtxCollection(),
    )
    bpy.data = types.SimpleNamespace(
        meshes=types.SimpleNamespace(
            new=MagicMock(return_value=MagicMock()),
            remove=MagicMock(),
        ),
        objects=types.SimpleNamespace(
            new=MagicMock(return_value=active),
            remove=MagicMock(),
        ),
    )
    return bpy


def _mk_rod_mock():
    rod = types.ModuleType("Uni_threaded_rod")
    rod.bl_info = {"name": "Uni-threaded-rod"}

    db = types.ModuleType("Uni_threaded_rod.database")
    db.THREAD_STANDARDS = {
        "METRIC_ISO": {"name": "Metrisch ISO", "standard": "ISO 68-1",
                         "special_params": {"taper_ratio": 0.0}},
        "TRAPEZOIDAL": {"name": "Trapez", "standard": "DIN 103",
                          "special_params": {"taper_ratio": 0.0}},
    }

    def _dia_items(key):
        if key in db.THREAD_STANDARDS:
            return [("8", "M8", ""), ("10", "M10", ""), ("12", "M12", "")]
        return []

    db.get_diameter_items_for_standard = _dia_items
    db.get_default_tolerance_class = lambda key, internal=False: "6H" if internal else "6g"
    db.resolve_thread_parameters = lambda key, token: (10.0, 1.5)
    rod.database = db
    rod.THREAD_STANDARDS = db.THREAD_STANDARDS

    api = types.ModuleType("Uni_threaded_rod.api")

    def _thread(spec="M10", fit="6g/6H", material="8.8", length=40.0,
                  standard="METRIC_ISO", internal=True, starts=1, **kw):
        digits = "".join(c for c in str(spec) if c.isdigit() or c == ".")
        d = float(digits) if digits else 10.0
        return {
            "diameter_mm": d,
            "pitch_mm": 1.5,
            "spec": spec,
            "standard": standard,
            "length_mm": length,
            "tolerance_class": "6H" if internal else "6g",
            "property_class": "8.8",
            "profile_points": [(d / 2, 0.0), (d / 2 - 0.5, 0.75), (d / 2, 1.5)],
            "ratio_warnings": [],
            "mechanics": {"pitch_mm": 1.5, "engagement_length": min(length, d)},
        }

    api.thread = _thread
    rod.api = api

    geom = types.ModuleType("Uni_threaded_rod.geometry_engine")
    geom.generate_profile = MagicMock(return_value=([(0, 0), (1, 0), (1, 1)], []))
    rod.geometry_engine = geom

    mb = types.ModuleType("Uni_threaded_rod.mesh_builder")
    mb.create_thread_mesh = MagicMock(return_value=MagicMock())
    rod.mesh_builder = mb
    mech = types.ModuleType("Uni_threaded_rod.mechanical_validation")
    mech.allowables_from_property_class = lambda property_class: {
        "allowable_tensile_mpa": 200.0,
        "allowable_shear_mpa": 100.0,
    }

    def _validate_combined_load_case(**kwargs):
        return {
            "pitch_mm": kwargs["pitch"],
            "engagement_length": kwargs["engagement_length"],
            "standard": kwargs["standard_key"],
        }

    mech.validate_combined_load_case = _validate_combined_load_case
    rod.mechanical_validation = mech


    sys.modules["Uni_threaded_rod"] = rod
    sys.modules["Uni_threaded_rod.database"] = db
    sys.modules["Uni_threaded_rod.api"] = api
    sys.modules["Uni_threaded_rod.geometry_engine"] = geom
    sys.modules["Uni_threaded_rod.mesh_builder"] = mb
    sys.modules["Uni_threaded_rod.mechanical_validation"] = mech
    return rod


def _bootstrap_package():
    """Repo-Wurzel als Python-Paket ``uni_threaded_sleeve`` laden."""
    name = "uni_threaded_sleeve"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name,
        str(REPO_ROOT / "__init__.py"),
        submodule_search_locations=[str(REPO_ROOT)],
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def install():
    """Idempotenter Setup-Aufruf fuer Tests."""
    if "bpy" not in sys.modules:
        sys.modules["bpy"] = _mk_bpy_mock()
    if "Uni_threaded_rod" not in sys.modules:
        _mk_rod_mock()
    return _bootstrap_package()
