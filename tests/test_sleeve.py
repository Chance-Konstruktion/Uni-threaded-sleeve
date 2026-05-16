"""Unit-Tests fuer Uni-threaded-sleeve mit gemockten Blender- und Rod-APIs."""
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from tests.conftest_mocks import install


install()

import uni_threaded_sleeve as sleeve_pkg  # noqa: E402
from uni_threaded_sleeve import api, database, presets, rod_link  # noqa: E402
from uni_threaded_sleeve import sleeve_builder, ui_panel  # noqa: E402


class TestPresets(unittest.TestCase):
    def test_all_keys_present(self):
        for k in ("STANDARD_MUFFE", "REPARATUR", "ROHR_MUFFE",
                   "HEAVY_DUTY", "FLANSCH", "TRAPEZ"):
            self.assertIn(k, presets.PRESETS)

    def test_required_fields(self):
        for k, v in presets.PRESETS.items():
            self.assertIn("name", v, f"{k} fehlt name")
            self.assertIn("outer_add", v, f"{k} fehlt outer_add")
            self.assertIn("wall", v, f"{k} fehlt wall")

    def test_reparatur_clearance(self):
        self.assertEqual(presets.PRESETS["REPARATUR"]["clearance"], 0.3)

    def test_flansch_flag(self):
        self.assertTrue(presets.PRESETS["FLANSCH"]["flange"])

    def test_trapez_standard(self):
        self.assertEqual(presets.PRESETS["TRAPEZ"]["standard"], "TRAPEZOIDAL")

    def test_get_preset_items_shape(self):
        items = presets.get_preset_items()
        self.assertEqual(len(items), len(presets.PRESETS))
        for tup in items:
            self.assertEqual(len(tup), 3)


class TestRodLink(unittest.TestCase):
    def setUp(self):
        rod_link._rod_cache = None

    def test_get_rod_finds_loaded(self):
        rod = rod_link.get_rod()
        self.assertEqual(rod.bl_info["name"], "Uni-threaded-rod")

    def test_get_rod_caches(self):
        a = rod_link.get_rod()
        b = rod_link.get_rod()
        self.assertIs(a, b)

    def test_submodules(self):
        self.assertTrue(hasattr(rod_link.get_rod_database(), "THREAD_STANDARDS"))
        self.assertTrue(callable(rod_link.get_rod_api().thread))
        self.assertTrue(callable(rod_link.get_rod_geometry_engine().generate_profile))
        self.assertTrue(callable(rod_link.get_rod_mesh_builder().create_thread_mesh))

    def test_no_hyphenated_candidates(self):
        # Bindestrich-Namen sind als Python-Module nicht importierbar.
        for name in rod_link._NAME_CANDIDATES:
            self.assertNotIn("-", name, f"{name} enthaelt einen Bindestrich")

    def test_rod_missing_raises(self):
        rod_link._rod_cache = None
        saved = sys.modules.pop("Uni_threaded_rod")
        for name in rod_link._NAME_CANDIDATES:
            sys.modules.pop(name, None)
        try:
            with self.assertRaises(ImportError):
                rod_link.get_rod()
        finally:
            sys.modules["Uni_threaded_rod"] = saved
            rod_link._rod_cache = None


class TestDatabaseForwarder(unittest.TestCase):
    def test_get_standards(self):
        stds = database.get_standards()
        self.assertIn("METRIC_ISO", stds)

    def test_diameter_items(self):
        self.assertTrue(database.get_diameter_items_for_standard("METRIC_ISO"))

    def test_diameter_items_unknown_standard(self):
        self.assertEqual(
            database.get_diameter_items_for_standard("DOES_NOT_EXIST"), [])

    def test_lazy_standards_iface(self):
        self.assertIn("METRIC_ISO", database.STANDARDS)
        self.assertEqual(list(database.STANDARDS.keys()),
                          list(database.get_standards().keys()))

    def test_graceful_when_rod_gone(self):
        rod_link._rod_cache = None
        saved = sys.modules.pop("Uni_threaded_rod")
        for name in rod_link._NAME_CANDIDATES:
            sys.modules.pop(name, None)
        try:
            self.assertEqual(database.get_standards(), {})
            self.assertEqual(
                database.get_diameter_items_for_standard("METRIC_ISO"), [])
            self.assertIsNone(
                database.resolve_thread_parameters("METRIC_ISO", "M10"))
        finally:
            sys.modules["Uni_threaded_rod"] = saved
            rod_link._rod_cache = None


class TestApi(unittest.TestCase):
    def test_default(self):
        d = api.create_sleeve_data()
        self.assertEqual(d["diameter_mm"], 10.0)
        self.assertNotIn("inner_diameter", d)
        self.assertEqual(d["outer_diameter"], 10.0 + 2 * 3.5)
        self.assertEqual(d["wall_thickness"], 3.5)
        self.assertEqual(d["pitch_mm"], 1.5)  # Rod-Default

    def test_with_clearance(self):
        d = api.create_sleeve_data(spec="M12", clearance=0.3, wall_thickness=4.0,
                                       outer_add=8.0)
        self.assertEqual(d["diameter_mm"], 12.0)
        self.assertAlmostEqual(d["clearance"], 0.3)
        self.assertAlmostEqual(d["outer_diameter"], 28.0)

    def test_pitch_override_applies(self):
        d = api.create_sleeve_data(spec="M10", pitch_override=1.0)
        self.assertAlmostEqual(d["pitch_mm"], 1.0)

    def test_pitch_override_zero_keeps_rod_default(self):
        d = api.create_sleeve_data(spec="M10", pitch_override=0.0)
        self.assertAlmostEqual(d["pitch_mm"], 1.5)

    def test_pitch_override_negative_ignored(self):
        d = api.create_sleeve_data(spec="M10", pitch_override=-1.0)
        self.assertAlmostEqual(d["pitch_mm"], 1.5)

    def test_alias_sleeve(self):
        self.assertEqual(api.sleeve(spec="M8", length=20.0)["diameter_mm"], 8.0)

    def test_preserves_rod_data(self):
        d = api.create_sleeve_data(spec="M10")
        self.assertIn("pitch_mm", d)
        self.assertEqual(d["preset"], None)
        self.assertEqual(d["handedness"], "RIGHT")


class TestSleeveBuilder(unittest.TestCase):
    def _props(self, **overrides):
        defaults = dict(
            diameter_enum="10", standard="METRIC_ISO", length=40.0,
            starts=1, handedness="RIGHT", clearance=0.0, shape="CYLINDER",
            add_flange=False, flange_both_sides=False,
            wall_thickness=3.5, outer_add=0.0, pitch_override=0.0,
            preset=None,
        )
        defaults.update(overrides)
        return types.SimpleNamespace(**defaults)

    def test_basic_call(self):
        with patch.object(sleeve_builder, "_add_outer_body") as outer, \
             patch.object(sleeve_builder, "_build_thread_cutter") as cutter, \
             patch.object(sleeve_builder, "_add_flange") as flange:
            outer.return_value = MagicMock()
            cutter.return_value = MagicMock()
            sleeve_builder.create_sleeve(self._props())
            outer.assert_called_once()
            cutter.assert_called_once()
            flange.assert_not_called()

    def test_outer_dia_formula(self):
        with patch.object(sleeve_builder, "_add_outer_body") as outer, \
             patch.object(sleeve_builder, "_build_thread_cutter"):
            outer.return_value = MagicMock()
            sleeve_builder.create_sleeve(
                self._props(diameter_enum="12", wall_thickness=4.0, outer_add=6.0))
            self.assertAlmostEqual(outer.call_args[0][0], 26.0)  # 12+8+6

    def test_preset_flansch_activates_flange(self):
        with patch.object(sleeve_builder, "_add_outer_body") as outer, \
             patch.object(sleeve_builder, "_build_thread_cutter"), \
             patch.object(sleeve_builder, "_add_flange") as flange:
            outer.return_value = MagicMock()
            sleeve_builder.create_sleeve(
                self._props(preset="FLANSCH", wall_thickness=2.0, outer_add=0.0))
            self.assertAlmostEqual(outer.call_args[0][0], 26.0)  # 10+8+8
            flange.assert_called_once()

    def test_preset_reparatur_clearance(self):
        with patch.object(sleeve_builder, "_add_outer_body") as outer, \
             patch.object(sleeve_builder, "_build_thread_cutter") as cutter:
            outer.return_value = MagicMock()
            cutter.return_value = MagicMock()
            sleeve_builder.create_sleeve(
                self._props(preset="REPARATUR", clearance=0.0))
            self.assertAlmostEqual(cutter.call_args[0][-1], 0.3)

    def test_preset_trapez_overrides_standard(self):
        with patch.object(sleeve_builder, "_add_outer_body") as outer, \
             patch.object(sleeve_builder, "_build_thread_cutter") as cutter:
            outer.return_value = MagicMock()
            cutter.return_value = MagicMock()
            sleeve_builder.create_sleeve(
                self._props(preset="TRAPEZ", standard="METRIC_ISO"))
            self.assertEqual(cutter.call_args[0][0], "TRAPEZOIDAL")

    def test_unknown_preset_standard_falls_back(self):
        """Falls Rod den im Preset genannten Standard nicht kennt, behalten wir
        den manuell ausgewaehlten Standard statt blind durchzureichen."""
        with patch.dict(presets.PRESETS, {
            "BROKEN": {"name": "Broken", "outer_add": 5.0, "wall": 3.0,
                         "standard": "DOES_NOT_EXIST"},
        }):
            with patch.object(sleeve_builder, "_add_outer_body") as outer, \
                 patch.object(sleeve_builder, "_build_thread_cutter") as cutter:
                outer.return_value = MagicMock()
                cutter.return_value = MagicMock()
                sleeve_builder.create_sleeve(
                    self._props(preset="BROKEN", standard="METRIC_ISO"))
                self.assertEqual(cutter.call_args[0][0], "METRIC_ISO")

    def test_pitch_override_propagates(self):
        with patch.object(sleeve_builder, "_add_outer_body") as outer, \
             patch.object(sleeve_builder, "_build_thread_cutter") as cutter:
            outer.return_value = MagicMock()
            cutter.return_value = MagicMock()
            sleeve_builder.create_sleeve(self._props(pitch_override=1.0))
            # _build_thread_cutter(standard_key, diameter, pitch, ...)
            self.assertAlmostEqual(cutter.call_args[0][2], 1.0)

    def test_pitch_override_zero_uses_rod_default(self):
        with patch.object(sleeve_builder, "_add_outer_body") as outer, \
             patch.object(sleeve_builder, "_build_thread_cutter") as cutter:
            outer.return_value = MagicMock()
            cutter.return_value = MagicMock()
            sleeve_builder.create_sleeve(self._props(pitch_override=0.0))
            self.assertAlmostEqual(cutter.call_args[0][2], 1.5)

    def test_cutter_cleanup_on_apply_failure(self):
        with patch.object(sleeve_builder, "_add_outer_body") as outer, \
             patch.object(sleeve_builder, "_build_thread_cutter") as cutter:
            outer.return_value = MagicMock()
            cutter_obj = MagicMock()
            cutter.return_value = cutter_obj
            import bpy as _bpy
            _bpy.ops.object.modifier_apply.side_effect = RuntimeError("boom")
            _bpy.data.objects.remove.reset_mock()
            try:
                with self.assertRaises(RuntimeError):
                    sleeve_builder.create_sleeve(self._props())
                _bpy.data.objects.remove.assert_called_once_with(
                    cutter_obj, do_unlink=True)
            finally:
                _bpy.ops.object.modifier_apply.side_effect = None


class TestDynamicStandards(unittest.TestCase):
    """Sobald Rod ein neues Gewinde kennt, taucht es ohne Code-Aenderung auf."""

    def test_new_standard_propagates_to_ui_dropdown(self):
        import bpy  # gemockt
        db_mock = rod_link.get_rod_database()
        original = dict(db_mock.THREAD_STANDARDS)
        try:
            db_mock.THREAD_STANDARDS["UNF"] = {
                "name": "Unified Fine", "standard": "ANSI",
                "special_params": {"taper_ratio": 0.0},
            }
            items = ui_panel._standard_items(None, None)
            keys = {tup[0] for tup in items}
            self.assertIn("UNF", keys)
        finally:
            db_mock.THREAD_STANDARDS.clear()
            db_mock.THREAD_STANDARDS.update(original)


class TestUiPanel(unittest.TestCase):
    def test_preset_items_includes_none_first(self):
        items = ui_panel._preset_items(None, None)
        self.assertEqual(items[0][0], "NONE")
        keys = {tup[0] for tup in items}
        for k in presets.PRESETS:
            self.assertIn(k, keys)

    def test_standard_items(self):
        items = ui_panel._standard_items(None, None)
        self.assertTrue(len(items) >= 1)

    def test_diameter_items(self):
        fake = types.SimpleNamespace(standard="METRIC_ISO")
        items = ui_panel._diameter_items(fake, None)
        self.assertTrue(len(items) >= 1)

    def test_diameter_items_fallback(self):
        fake = types.SimpleNamespace(standard="DOES_NOT_EXIST")
        items = ui_panel._diameter_items(fake, None)
        self.assertTrue(len(items) >= 1)

    def test_classes_complete(self):
        names = [c.__name__ for c in ui_panel.classes]
        for n in ("SLEEVE_Properties", "SLEEVE_OT_create", "SLEEVE_PT_main"):
            self.assertIn(n, names)

    def test_none_preset_keeps_manual(self):
        with patch.object(sleeve_builder, "_add_outer_body") as outer, \
             patch.object(sleeve_builder, "_build_thread_cutter") as cutter, \
             patch.object(sleeve_builder, "_add_flange") as flange:
            outer.return_value = MagicMock()
            cutter.return_value = MagicMock()
            props = types.SimpleNamespace(
                diameter_enum="10", standard="METRIC_ISO", length=40.0,
                starts=1, handedness="RIGHT", clearance=0.0, shape="CYLINDER",
                add_flange=False, flange_both_sides=False,
                wall_thickness=2.5, outer_add=1.0, pitch_override=0.0,
                preset="NONE",
            )
            sleeve_builder.create_sleeve(props)
            self.assertAlmostEqual(outer.call_args[0][0], 16.0)
            flange.assert_not_called()


class TestPackage(unittest.TestCase):
    def test_blinfo(self):
        self.assertEqual(sleeve_pkg.bl_info["name"], "Uni-threaded-sleeve")
        self.assertEqual(sleeve_pkg.bl_info["version"], (1, 4, 0))

    def test_register_unregister(self):
        sleeve_pkg.register()
        sleeve_pkg.unregister()


if __name__ == "__main__":
    unittest.main(verbosity=2)
