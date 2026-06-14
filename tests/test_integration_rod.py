"""Echter Integrationstest: Sleeve gegen die reale Uni-threaded-rod-Engine.

Im Gegensatz zu ``test_sleeve.py`` (komplett gemockte Rod-API) laedt dieser
Test die *echten* Rod-Module (``database``/``geometry_engine``/``api``) und
prueft den Sleeve<->Rod-Vertrag end-to-end ohne Blender. Damit faellt eine
inkompatible Aenderung an Rods API/DB auf, die der Mock nicht abbilden kann.

Die Rod-Datenmodule importieren ``bpy`` nicht auf Top-Level, deshalb laeuft
das ohne Blender. Der Mesh-/Boolean-Pfad bleibt Blender-Sache (Smoke-Test).

Rod-Quelle: ``UNI_THREADED_ROD_PATH`` oder Schwester-Verzeichnis. Fehlt das
Repo, wird das Modul sauber uebersprungen (statt zu scheitern).
"""
import importlib
import os
import sys
import types
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_ROD_KEYS = (
    "Uni_threaded_rod",
    "Uni_threaded_rod.database",
    "Uni_threaded_rod.api",
    "Uni_threaded_rod.geometry_engine",
    "Uni_threaded_rod.mesh_builder",
)


def _find_rod_repo():
    candidates = []
    env = os.environ.get("UNI_THREADED_ROD_PATH")
    if env:
        candidates.append(Path(env))
    parent = REPO_ROOT.parent
    for name in ("Uni-threaded-rod", "uni-threaded-rod", "Uni-threaded-rod-main"):
        candidates.append(parent / name)
    for path in candidates:
        if (path / "api.py").is_file() and (path / "database.py").is_file():
            return path
    return None


_ROD_PATH = _find_rod_repo()
_saved_modules = {}
_saved_cache = None


def _register_real_rod(rod_path):
    """Registriert das echte Rod-Repo als Paket ``Uni_threaded_rod`` und laedt
    die bpy-freien Submodule. Das bpy-lastige ``__init__.py`` wird bewusst
    nicht ausgefuehrt."""
    pkg = types.ModuleType("Uni_threaded_rod")
    pkg.__path__ = [str(rod_path)]
    pkg.bl_info = {"name": "Uni-threaded-rod"}
    sys.modules["Uni_threaded_rod"] = pkg
    database = importlib.import_module("Uni_threaded_rod.database")
    importlib.import_module("Uni_threaded_rod.geometry_engine")
    importlib.import_module("Uni_threaded_rod.api")
    pkg.database = database
    pkg.THREAD_STANDARDS = database.THREAD_STANDARDS


def setUpModule():
    if _ROD_PATH is None:
        raise unittest.SkipTest(
            "Uni-threaded-rod nicht gefunden - UNI_THREADED_ROD_PATH setzen "
            "oder das Repo als Schwester-Verzeichnis auschecken."
        )
    # bpy-Mock + (gemocktes) Rod + Sleeve-Paket ueber die oeffentliche Setup-API.
    from tests.conftest_mocks import install

    install()
    from uni_threaded_sleeve import rod_link

    # Den gemockten Rod-Zustand sichern, damit test_sleeve danach unveraendert laeuft.
    global _saved_modules, _saved_cache
    _saved_modules = {key: sys.modules.get(key) for key in _ROD_KEYS}
    _saved_cache = rod_link._rod_cache

    for key in _ROD_KEYS:
        sys.modules.pop(key, None)
    _register_real_rod(_ROD_PATH)
    rod_link._rod_cache = None


def tearDownModule():
    from uni_threaded_sleeve import rod_link

    for key in [m for m in sys.modules if m == "Uni_threaded_rod" or m.startswith("Uni_threaded_rod.")]:
        sys.modules.pop(key, None)
    for key, value in _saved_modules.items():
        if value is not None:
            sys.modules[key] = value
    rod_link._rod_cache = _saved_cache


class TestRealRodIntegration(unittest.TestCase):
    def setUp(self):
        from uni_threaded_sleeve import rod_link

        rod_link._rod_cache = None

    def test_rod_link_resolves_real_engine(self):
        from uni_threaded_sleeve import rod_link

        self.assertEqual(rod_link.get_rod().bl_info["name"], "Uni-threaded-rod")
        standards = rod_link.get_rod_database().THREAD_STANDARDS
        self.assertIn("METRIC_ISO", standards)
        # Echte DB (26 Normen), nicht der 2-Eintrag-Mock aus conftest_mocks.
        self.assertGreaterEqual(len(standards), 20)

    def test_create_sleeve_data_metric_iso_m10(self):
        from uni_threaded_sleeve import api

        data = api.create_sleeve_data(spec="M10", standard="METRIC_ISO", wall_thickness=3.5)
        self.assertAlmostEqual(data["diameter_mm"], 10.0)
        self.assertAlmostEqual(data["pitch_mm"], 1.5)  # echte ISO-Regelsteigung M10
        self.assertAlmostEqual(data["outer_diameter"], 17.0)  # 10 + 2*3.5
        self.assertTrue(data["profile_points"])  # echte Geometrie-Engine liefert Punkte
        self.assertIn("mechanics", data)

    def test_internal_true_is_accepted_by_real_rod(self):
        # Kern-Vertrag: Rods thread() muss internal=True akzeptieren und eine
        # echte Steigung liefern - genau das kann ein Mock nicht garantieren.
        from uni_threaded_sleeve import api

        data = api.create_sleeve_data(spec="M12", standard="METRIC_ISO")
        self.assertAlmostEqual(data["diameter_mm"], 12.0)
        self.assertAlmostEqual(data["pitch_mm"], 1.75)

    def test_pitch_override_with_real_rod(self):
        from uni_threaded_sleeve import api

        data = api.create_sleeve_data(spec="M10", standard="METRIC_ISO", pitch_override=1.0)
        self.assertAlmostEqual(data["pitch_mm"], 1.0)

    def test_database_forwarder_returns_real_values(self):
        from uni_threaded_sleeve import database

        self.assertTrue(database.get_diameter_items_for_standard("METRIC_ISO"))
        self.assertEqual(database.resolve_thread_parameters("METRIC_ISO", "10"), (10.0, 1.5))
        self.assertEqual(database.get_diameter_items_for_standard("DOES_NOT_EXIST"), [])

    def test_every_thread_standard_resolves_through_sleeve(self):
        """Regression: jeder von Rod angebotene Gewindetyp muss sich über die
        Sleeve-API auflösen lassen, nicht nur die metrischen "ersten" Normen.

        Früher hat Rods ``api.thread()`` den Spec großgeschrieben und ein
        führendes ``M`` abgeschnitten; dadurch waren case-sensitive Tokens wie
        ``Pg7`` (PG/CONDUIT_PG), ``M8x1`` (SPARK_PLUG) und ``M12x1.5``
        (CABLE_GLAND_M) im Sleeve nicht baubar.
        """
        from uni_threaded_sleeve import api, database

        standards = database.get_standards()
        self.assertGreaterEqual(len(standards), 20)
        for standard_key in standards:
            items = database.get_diameter_items_for_standard(standard_key)
            self.assertTrue(items, f"{standard_key} liefert keine Durchmesser")
            token = items[0][0]
            with self.subTest(standard=standard_key, token=token):
                data = api.create_sleeve_data(spec=token, standard=standard_key)
                self.assertGreater(data["diameter_mm"], 0.0)
                self.assertGreater(data["pitch_mm"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
