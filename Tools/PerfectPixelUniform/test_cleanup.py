"""Independent colour-cleanup fixtures; creates no source or output images."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np
from PIL import Image

import cleanup

ROOT = Path(__file__).resolve().parents[2]
ACTUAL_SOURCE = ROOT / "Tools/PerfectPixelUniform/runs/20261003T092818576216Z-59a6e7b8655b4cf4a637cf98f68e32a7/source.png"
ACTUAL_RESULT = ROOT / "docs/artifacts/building37/Uniform03"


def noisy_flat(seed=143, shape=(64, 80)):
    """Known constant ground truth with independent bounded RGB noise."""
    flat = np.full((*shape, 3), (110, 130, 150), dtype=np.int16)
    noise = np.random.default_rng(seed).integers(-4, 5, flat.shape, dtype=np.int16)
    return (flat + noise).astype(np.uint8), flat.astype(np.uint8)


class CleanupContractTests(unittest.TestCase):
    def clean(self, source, strength=4, palette=64):
        before = source.copy()
        output, report = cleanup.process_cleanup(source, strength, palette)
        np.testing.assert_array_equal(source, before, "Input bytes must remain unchanged")
        self.assertEqual(output.shape, before.shape)
        self.assertEqual(output.dtype, np.uint8)
        self.assertEqual(report["source_dimensions"], [before.shape[1], before.shape[0]])
        self.assertEqual(report["output_dimensions"], [before.shape[1], before.shape[0]])
        if before.shape[2] == 4:
            np.testing.assert_array_equal(output[..., 3], before[..., 3])
            hidden = before[..., 3] == 0
            np.testing.assert_array_equal(output[hidden], before[hidden], "Hidden RGB is owned source data")
        return output, report

    def test_srgb_d65_lab_known_primaries(self):
        # Published D65 sRGB reference values, independent of cleanup's filter.
        colors = np.array([[0, 0, 0], [255, 255, 255], [255, 0, 0]], dtype=np.uint8)
        expected = np.array([[0, 0, 0], [100, 0, 0], [53.2408, 80.0925, 67.2032]])
        np.testing.assert_allclose(cleanup.rgb_lab(colors), expected, rtol=0, atol=.003)

    def test_one_pixel_line_eye_and_endpoints_are_exact(self):
        source, _ = noisy_flat(31)
        source[9:46, 23] = (4, 4, 4)
        source[37, 56] = (255, 20, 20)
        output, report = self.clean(source, strength=4, palette=64)
        self.assertGreater(report["colour_statistics"]["visible_rgb_colors_before"], 256)
        self.assertFalse(report["colour_statistics"]["already_limited_palette_noop"])
        self.assertGreater(report["colour_statistics"]["changed_visible_pixels"], 0)
        np.testing.assert_array_equal(output[9:46, 23], np.tile((4, 4, 4), (37, 1)))
        np.testing.assert_array_equal(output[37, 56], (255, 20, 20))
        np.testing.assert_array_equal(output[9, 23], source[9, 23])
        np.testing.assert_array_equal(output[45, 23], source[45, 23])

    def test_all_alpha_levels_and_hidden_rgb_are_exact(self):
        rgb, _ = noisy_flat(98)
        y, x = np.indices(rgb.shape[:2])
        alpha = np.array([0, 1, 128, 253, 255], dtype=np.uint8)[(x + y) % 5]
        source = np.dstack((rgb, alpha))
        # These hidden bytes deliberately do not resemble visible neighbours.
        source[alpha == 0, :3] = np.random.default_rng(47).integers(0, 256, (int((alpha == 0).sum()), 3), dtype=np.uint8)
        output, report = self.clean(source, strength=4, palette=64)
        self.assertGreater(report["colour_statistics"]["changed_visible_pixels"], 0)
        for value in (0, 1, 128, 253, 255):
            self.assertTrue(np.any(alpha == value))
            np.testing.assert_array_equal(output[..., 3][alpha == value], source[..., 3][alpha == value])
        np.testing.assert_array_equal(output[alpha == 0], source[alpha == 0])

    def test_final_quantized_bytes_obey_delta_e_2_4_8(self):
        rgb, _ = noisy_flat(57)
        alpha = np.random.default_rng(78).choice(np.array([0, 1, 128, 253, 255], np.uint8), rgb.shape[:2])
        source = np.dstack((rgb, alpha))
        original_lab = cleanup.rgb_lab(source[..., :3]).astype(np.float64)
        for strength in (2, 4, 8):
            with self.subTest(strength=strength):
                output, report = self.clean(source, strength=strength, palette=64)
                # Inspect final stored bytes, not an intermediate floating-point candidate.
                output_lab = cleanup.rgb_lab(output[..., :3]).astype(np.float64)
                measured = np.linalg.norm(output_lab - original_lab, axis=2)
                self.assertTrue(np.isfinite(measured).all())
                self.assertLessEqual(float(measured.max()), strength + .001)
                self.assertAlmostEqual(report["invariants"]["maximum_measured_delta_e76"], float(measured.max()), places=4)

    def test_already_limited_visible_palette_is_true_noop(self):
        y, x = np.indices((21, 24))
        colors = np.array([(12, 30, 50), (70, 90, 110), (150, 110, 40), (230, 210, 180)], dtype=np.uint8)
        rgb = colors[(x + y) % len(colors)]
        alpha = np.array([0, 1, 128, 253, 255], np.uint8)[x % 5]
        source = np.dstack((rgb, alpha))
        source[alpha == 0, :3] = np.random.default_rng(6).integers(0, 256, (int((alpha == 0).sum()), 3), dtype=np.uint8)
        for palette in (64, 128, 256):
            with self.subTest(palette=palette):
                output, report = self.clean(source, palette=palette)
                np.testing.assert_array_equal(output, source)
                self.assertTrue(report["colour_statistics"]["already_limited_palette_noop"])
                self.assertEqual(report["colour_statistics"]["changed_visible_pixels"], 0)

    def test_known_flat_noise_is_reduced_without_geometry_change(self):
        source, ground_truth = noisy_flat(143)
        output, report = self.clean(source, strength=4, palette=64)
        self.assertGreater(len(np.unique(source.reshape(-1, 3), axis=0)), 256)
        self.assertGreater(report["colour_statistics"]["changed_visible_pixels"], 0)
        before_error = np.mean((source.astype(float) - ground_truth.astype(float)) ** 2)
        after_error = np.mean((output.astype(float) - ground_truth.astype(float)) ** 2)
        self.assertLess(after_error, before_error * .8, "Known flat ground truth must become less noisy")
        # Independent RGB local-variation metric supplements the reported Lab metric.
        before_variation = sum(float(np.mean(np.diff(source.astype(float), axis=axis) ** 2)) for axis in (0, 1))
        after_variation = sum(float(np.mean(np.diff(output.astype(float), axis=axis) ** 2)) for axis in (0, 1))
        self.assertLess(after_variation, before_variation * .8)
        self.assertGreater(report["low_contrast_statistics"]["source_selected_pair_count"], 0)
        self.assertLess(report["low_contrast_statistics"]["energy_ratio"], 1)

    def test_invalid_strength_and_palette_are_rejected(self):
        source, _ = noisy_flat(shape=(8, 9))
        before = source.copy()
        for strength in (0, 1, 3, 16, True, None, "4", np.int64(4), float("nan"), float("inf")):
            with self.subTest(strength=repr(strength)):
                with self.assertRaises(ValueError):
                    cleanup.process_cleanup(source, strength=strength)
        for palette in (0, 32, 65, 512, 64.0, True, None, "128", np.int64(64)):
            with self.subTest(palette=repr(palette)):
                with self.assertRaises(ValueError):
                    cleanup.process_cleanup(source, palette_colors=palette)
        np.testing.assert_array_equal(source, before)

    def test_invalid_dtype_shape_and_non_array_are_rejected(self):
        invalid = [np.zeros((4, 5, 3), dtype=dtype) for dtype in (np.float32, np.int16, bool)]
        invalid.extend([np.zeros((4, 5), np.uint8), np.zeros((4, 5, 2), np.uint8),
                        np.zeros((4, 5, 5), np.uint8), np.zeros((0, 5, 3), np.uint8), [[1, 2, 3]]])
        for source in invalid:
            with self.subTest(source_type=type(source).__name__, shape=getattr(source, "shape", None)):
                with self.assertRaises(ValueError):
                    cleanup.process_cleanup(source)

    def test_saved_actual_artifact_preserves_source_contract(self):
        source_bytes = ACTUAL_SOURCE.read_bytes()
        report = json.loads((ACTUAL_RESULT / "receipt.json").read_text(encoding="utf-8"))
        with Image.open(ACTUAL_SOURCE) as image:
            source = np.array(image)
        with Image.open(ACTUAL_RESULT / "output.png") as image:
            output = np.array(image)
        self.assertEqual(Path(report["source_path"]).resolve(), ACTUAL_SOURCE.resolve())
        self.assertEqual(hashlib.sha256(source_bytes).hexdigest(), report["source_file_sha256"])
        self.assertEqual(hashlib.sha256(source.tobytes()).hexdigest(), report["source_array_sha256"])
        self.assertEqual(hashlib.sha256(output.tobytes()).hexdigest(), report["output_array_sha256"])
        self.assertEqual(output.shape, source.shape)
        self.assertEqual(output.dtype, source.dtype)
        np.testing.assert_array_equal(output[..., 3], source[..., 3])
        hidden = source[..., 3] == 0
        np.testing.assert_array_equal(output[hidden], source[hidden])
        visible = ~hidden
        actual_changed = int(np.count_nonzero(visible & np.any(output[..., :3] != source[..., :3], axis=2)))
        self.assertGreater(actual_changed, 0)
        self.assertEqual(actual_changed, report["colour_statistics"]["changed_visible_pixels"])
        # Reuses the separately reference-tested Lab conversion; this is not a
        # second independent implementation of colour science or an art judgement.
        original_lab = cleanup.rgb_lab(source[..., :3]).astype(np.float64)
        output_lab = cleanup.rgb_lab(output[..., :3]).astype(np.float64)
        measured = np.linalg.norm(output_lab - original_lab, axis=2)
        self.assertTrue(np.isfinite(measured).all())
        self.assertLessEqual(float(measured.max()), report["settings"]["maximum_delta_e76"] + .001)
        self.assertGreater(report["low_contrast_statistics"]["source_selected_pair_count"], 0)
        self.assertLess(report["low_contrast_statistics"]["energy_ratio"], 1)
        self.assertEqual(ACTUAL_SOURCE.read_bytes(), source_bytes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, nargs="?")
    args = parser.parse_args()
    if args.report and args.report.exists():
        parser.error("기존 검증 보고서를 덮어쓰지 않습니다.")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CleanupContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"schema": "perfect-pixel-colour-cleanup-tests/1", "tests_run": result.testsRun,
              "passed": result.wasSuccessful(),
              "failures": [str(name) + "\n" + detail for name, detail in result.failures],
              "errors": [str(name) + "\n" + detail for name, detail in result.errors],
              "skipped": [str(name) + ": " + reason for name, reason in result.skipped],
              "actual_source": str(ACTUAL_SOURCE), "actual_result": str(ACTUAL_RESULT),
              "scope": "known Lab references, native thin features, byte preservation, final-byte colour bounds, known flat noise and saved actual artifact; no actual-source generation or art acceptance"}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
