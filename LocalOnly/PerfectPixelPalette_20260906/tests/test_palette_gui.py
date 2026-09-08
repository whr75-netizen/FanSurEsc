"""Headless helper tests: no Tk window, no real art processing or output image."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import palette_gui as gui
from perfect_pixel import PaletteOptions, scaled_grid


class Var:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class OptionsStub:
    def __init__(self, **values):
        self.values = values

    def validate(self):
        return None


def source_snapshot(detected=(100, 120), warning=None):
    pixels = np.zeros((3, 4, 3), dtype=np.uint8)
    pixels.setflags(write=False)
    return gui.SourceSnapshot(Path("source.png"), b"unchanged", pixels, "test-hash", detected, warning)


def app_without_tk(method="color_ranges"):
    app = gui.PaletteLab.__new__(gui.PaletteLab)
    app.source = source_snapshot()
    app.options_type = OptionsStub
    values = dict(base_w="100", base_h="120", scale="1.1", families="6", tones="3",
                  flatten=.75, feature=1.5, refine=.2, priorities="#FFCCAA=2", range_hue_width=15)
    for name, value in values.items():
        setattr(app, name, Var(value))
    app.palette_method = Var(next(label for label, key in gui.METHOD_CHOICES.items() if key == method))
    return app


class GridTests(unittest.TestCase):
    def test_gui_uses_core_minimum_and_extended_scales(self):
        for base, scale in [((1, 1), ".1"), ((70, 91), ".9"), ((256, 257), "1.1"), ((512, 512), "4")]:
            with self.subTest(base=base, scale=scale):
                self.assertEqual(gui.target_dimensions(base, scale), scaled_grid(base, scale))
        self.assertEqual(gui.target_dimensions((1, 1), ".1"), (1, 1))
        self.assertEqual(gui.target_dimensions((70, 91), ".9"), (63, 81))

    def test_gui_uses_core_caps_and_invalid_input_rules(self):
        for base, scale in [((4096, 4096), "1"), ((4096, 1), "2"), ((256, 256), ".09"),
                            ((256, 256), "4.01"), ((0, 1), "1"), ((1, 1), "NaN")]:
            with self.subTest(base=base, scale=scale), self.assertRaises(ValueError):
                gui.target_dimensions(base, scale)


class DecodeTests(unittest.TestCase):
    def decode_mocked(self, detector):
        decoded = np.arange(36, dtype=np.uint8).reshape(3, 4, 3)
        fake_image = Mock()
        fake_image.getbands.return_value = ("R", "G", "B")
        fake_image.info = {}
        fake_image.convert.return_value = decoded
        fake_context = Mock()
        fake_context.__enter__ = Mock(return_value=fake_image)
        fake_context.__exit__ = Mock(return_value=False)
        with patch.object(Path, "read_bytes", return_value=b"unchanged-original-bytes"), \
             patch.object(gui.Image, "open", return_value=fake_context):
            result = gui.decode_source(Path("fixture.png"), detector)
        return result, decoded

    def test_detection_failure_retains_original_for_manual_grid(self):
        def broken(pixels):
            pixels[:] = 0  # A detector must only receive a disposable copy.
            raise ValueError("no intrinsic grid")
        result, expected = self.decode_mocked(broken)
        self.assertIsNone(result.detected_base_grid)
        self.assertIn("자동 격자 검출 실패", result.detection_warning)
        self.assertIn("no intrinsic grid", result.detection_warning)
        self.assertEqual(result.original_bytes, b"unchanged-original-bytes")
        np.testing.assert_array_equal(result.pixels, expected)
        self.assertFalse(result.pixels.flags.writeable)

    def test_valid_detection_calls_once_without_warning(self):
        detector = Mock(return_value=(2, 3))
        result, _ = self.decode_mocked(detector)
        detector.assert_called_once()
        self.assertEqual(result.detected_base_grid, (2, 3))
        self.assertIsNone(result.detection_warning)

    def test_invalid_detection_becomes_explicit_manual_state(self):
        for invalid in (None, (0, 3), (3,), (2.5, 3), (4097, 3)):
            with self.subTest(invalid=invalid):
                result, _ = self.decode_mocked(Mock(return_value=invalid))
                self.assertIsNone(result.detected_base_grid)
                self.assertTrue(result.detection_warning)


class CaptureTests(unittest.TestCase):
    def test_actual_core_options_contract_for_both_methods(self):
        for method in ("color_ranges", "legacy"):
            app = app_without_tk(method)
            app.options_type = PaletteOptions
            with self.subTest(method=method):
                task = app._capture_task()
                options = PaletteOptions(**task.option_values)
                options.validate()
                self.assertEqual(options.palette_method, method)
                self.assertEqual(options.tones_per_family, 3)

    def test_color_range_options_and_three_tones_are_captured(self):
        app = app_without_tk()
        app.families = Var("ignored while disabled")
        task = app._capture_task()
        self.assertEqual(task.option_values["palette_method"], "color_ranges")
        self.assertEqual(task.option_values["range_hue_width"], 15)
        self.assertEqual(task.option_values["tones_per_family"], 3)
        self.assertEqual(task.option_values["color_families"], 6)
        self.assertEqual(task.target_size, (110, 132))
        self.assertEqual(task.base_grid, (100, 120))
        app.base_w.value = "900"
        self.assertEqual(task.base_grid, (100, 120))

    def test_legacy_family_and_inactive_range_control(self):
        app = app_without_tk("legacy")
        app.families = Var("8")
        app.range_hue_width = Var("ignored while disabled")
        task = app._capture_task()
        self.assertEqual(task.option_values["palette_method"], "legacy")
        self.assertEqual(task.option_values["color_families"], 8)
        self.assertEqual(task.option_values["range_hue_width"], 15)

    def test_range_width_bounds_are_validated(self):
        for invalid in (4.9, 60.1, float("nan"), float("inf")):
            app = app_without_tk()
            app.range_hue_width.value = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                app._capture_task()

    def test_manual_grid_after_failed_detection_is_usable(self):
        app = app_without_tk()
        app.source = source_snapshot(None, "explicit detection failure")
        self.assertEqual(app._capture_task().base_grid, (100, 120))
        app.base_w.value = ""
        with self.assertRaises(ValueError):
            app._capture_task()


class ExportLimitTests(unittest.TestCase):
    @staticmethod
    def comparison(shape_a, shape_b=None):
        return SimpleNamespace(original_image=SimpleNamespace(shape=shape_a),
                               palette_image=SimpleNamespace(shape=shape_b or shape_a))

    def test_limit_checked_before_any_directory_or_file(self):
        oversized = self.comparison((1000, 3001, 3))
        with patch.object(Path, "mkdir") as mkdir, patch.object(Path, "write_bytes") as write:
            with self.assertRaisesRegex(ValueError, "24MP"):
                gui.save_bundle(oversized, Path("must-not-be-created"), 3)
            mkdir.assert_not_called()
            write.assert_not_called()

    def test_both_outputs_checked(self):
        result = self.comparison((10, 10, 3), (1000, 3001, 4))
        with self.assertRaises(ValueError):
            gui.validate_export_size(result, 3)

    def test_exact_limit_is_allowed_without_writing(self):
        gui.validate_export_size(self.comparison((1500, 4000, 3)), 2)

    def test_invalid_scale_is_rejected(self):
        for invalid in (True, 2.0, 0, 5, 9):
            with self.subTest(scale=invalid), self.assertRaises(ValueError):
                gui.validate_export_size(self.comparison((2, 3, 3)), invalid)


if __name__ == "__main__":
    unittest.main()
