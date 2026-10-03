"""Independent exact-grid fixtures and real-source rejection; no image writes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import unittest

import numpy as np
from PIL import Image

import uniform


ACTUAL_SOURCE = uniform.ROOT / "Tools/Building37/Source/sheet.png"
ACTUAL_FAILURE_DIR = None


def enlarge(native, step):
    return np.repeat(np.repeat(native, step, axis=0), step, axis=1)


class ExactLatticeTests(unittest.TestCase):
    def assert_lossless(self, source, expected, step):
        before = source.copy()
        output, report = uniform.process_array(source)
        np.testing.assert_array_equal(source, before, "Analysis must preserve source bytes")
        np.testing.assert_array_equal(output, expected, "Authored native content must survive")
        self.assertEqual(report["grid_status"], "verified_lossless")
        self.assertEqual(report["period_source_px"], step)
        self.assertEqual(report["source_dimensions"], [source.shape[1], source.shape[0]])
        self.assertEqual(report["output_dimensions"], [output.shape[1], output.shape[0]])
        self.assertEqual(report["reconstruction"]["changed_source_texels"], 0)
        self.assertNotIn("phase_coherence", report, "Exact evidence must not fabricate frequency confidence")
        # Decode the declared source-to-cell map independently of production sampling.
        map_x = np.asarray(report["grid"]["cell_x_indices"], dtype=np.int64)
        map_y = np.asarray(report["grid"]["cell_y_indices"], dtype=np.int64)
        self.assertEqual(map_x.shape, (source.shape[1],))
        self.assertEqual(map_y.shape, (source.shape[0],))
        self.assertGreaterEqual(int(map_x.min()), 0)
        self.assertGreaterEqual(int(map_y.min()), 0)
        self.assertLess(int(map_x.max()), output.shape[1])
        self.assertLess(int(map_y.max()), output.shape[0])
        reconstructed = output[map_y[:, None], map_x[None, :]]
        np.testing.assert_array_equal(reconstructed, before, "Entire source, including partial edge cells, must reconstruct")
        return output, report

    def assert_rejected(self, source):
        before = source.copy()
        with self.assertRaises(uniform.GridDetectionError) as raised:
            uniform.process_array(source)
        np.testing.assert_array_equal(source, before, "Rejection must preserve source bytes")
        report = getattr(raised.exception, "report", None)
        self.assertIsInstance(report, dict, "Rejected inputs need inspectable diagnostic evidence")
        self.assertNotEqual(report.get("grid_status"), "verified_lossless")
        return report

    def test_exact_rgba_blocks_scales_2_3_4_8(self):
        native = np.random.default_rng(871).integers(0, 256, (7, 9, 4), dtype=np.uint8)
        for step in (2, 3, 4, 8):
            with self.subTest(step=step):
                self.assert_lossless(enlarge(native, step), native, step)

    def test_native_one_pixel_line_and_eye_survive_scale_2(self):
        native = np.zeros((9, 11, 4), np.uint8)
        native[1:8, 1:10] = (50, 100, 150, 255)
        native[2:7, 3] = (5, 10, 15, 255)
        native[4, 6] = (240, 240, 120, 255)
        output, _ = self.assert_lossless(enlarge(native, 2), native, 2)
        np.testing.assert_array_equal(output[2:7, 3], np.tile((5, 10, 15, 255), (5, 1)))
        np.testing.assert_array_equal(output[4, 6], (240, 240, 120, 255))

    def test_harmonic_boundary_gaps_x6_y4_select_common_2(self):
        y, x = np.indices((9, 12))
        native = np.stack(((x // 3) * 45 + 10, (y // 2) * 35 + 20,
                           (x // 3 + y // 2) * 12 + 5, np.full_like(x, 255)), axis=2).astype(np.uint8)
        self.assert_lossless(enlarge(native, 2), native, 2)

    def test_cropped_offsets_and_partial_edges_reconstruct(self):
        native = np.random.default_rng(27).integers(0, 256, (7, 9, 4), dtype=np.uint8)
        for step in (2, 3, 4, 8):
            with self.subTest(step=step):
                expanded = enlarge(native, step)
                source = expanded[1:-1, step - 1:-1].copy()
                self.assert_lossless(source, native, step)

    def test_one_fine_pixel_inside_coarse_block_rejects(self):
        native = np.random.default_rng(109).integers(0, 256, (7, 9, 4), dtype=np.uint8)
        source = enlarge(native, 8)
        source[13, 17, 0] ^= np.uint8(1)
        self.assert_rejected(source)

    def test_unrelated_rgb_gradient_rejects(self):
        y, x = np.indices((31, 37))
        source = np.stack((x * 3, y * 4, x + y), axis=2).astype(np.uint8)
        self.assert_rejected(source)

    def test_alpha_only_boundaries_define_true_rgba_grid(self):
        y, x = np.indices((5, 7))
        native = np.empty((5, 7, 4), np.uint8)
        native[..., :3] = (12, 34, 56)
        native[..., 3] = (x * 23 + y * 31).astype(np.uint8)
        self.assert_lossless(enlarge(native, 3), native, 3)

    def test_single_flat_axis_uses_evidenced_axis_step(self):
        y, x = np.indices((5, 7))
        for axis in ("x", "y"):
            with self.subTest(changing_axis=axis):
                coordinate = x if axis == "x" else y
                native = np.stack((coordinate * 17 + 3, coordinate * 11 + 20,
                                   coordinate * 7 + 50, np.full_like(x, 255)), axis=2).astype(np.uint8)
                self.assert_lossless(enlarge(native, 2), native, 2)

    def test_constant_rgb_and_rgba_have_no_inferable_step(self):
        for channels in (3, 4):
            with self.subTest(channels=channels):
                self.assert_rejected(np.full((17, 19, channels), 120, dtype=np.uint8))

    def test_hidden_rgb_fine_detail_cannot_be_discarded(self):
        native = np.random.default_rng(125).integers(0, 256, (5, 7, 4), dtype=np.uint8)
        native[..., 3] = 0
        source = enlarge(native, 4)
        source[5, 5, 0] ^= np.uint8(1)
        self.assert_rejected(source)

    def test_actual_building37_source_rejects_with_report(self):
        self.assertTrue(ACTUAL_SOURCE.is_file(), "Requested real source must be present")
        before_hash = uniform.sha256(ACTUAL_SOURCE)
        with Image.open(ACTUAL_SOURCE) as image:
            source = np.array(image)
        report = self.assert_rejected(source)
        self.assertEqual(report["source_dimensions"], [source.shape[1], source.shape[0]])
        self.assertEqual(uniform.sha256(ACTUAL_SOURCE), before_hash)

    def test_actual_cli_rejection_produces_diagnosis_without_png(self):
        if ACTUAL_FAILURE_DIR is None:
            self.skipTest("CLI result not supplied")
        failure = json.loads((ACTUAL_FAILURE_DIR / "failure.json").read_text(encoding="utf-8"))
        self.assertEqual(failure["grid_status"], "rejected")
        self.assertEqual(failure["reason_code"], "NO_LOSSLESS_COARSER_LATTICE")
        self.assertEqual(failure["source_sha256"], uniform.sha256(ACTUAL_SOURCE))
        self.assertEqual(failure["producer_sha256"], uniform.sha256(Path(uniform.__file__)))
        self.assertFalse((ACTUAL_FAILURE_DIR / "output.png").exists())


def main():
    global ACTUAL_SOURCE, ACTUAL_FAILURE_DIR
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ACTUAL_SOURCE)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--failure-dir", type=Path)
    args = parser.parse_args()
    ACTUAL_SOURCE = args.source
    ACTUAL_FAILURE_DIR = args.failure_dir
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ExactLatticeTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"schema": "perfect-pixel-exact-lattice-tests/1", "tests_run": result.testsRun,
              "failures": [str(name) + "\n" + detail for name, detail in result.failures],
              "errors": [str(name) + "\n" + detail for name, detail in result.errors],
              "skipped": [str(name) + ": " + reason for name, reason in result.skipped],
              "passed": result.wasSuccessful(), "actual_source": str(ACTUAL_SOURCE),
              "scope": "authored RGBA fixtures, source-wide exact reconstruction, fine-detail rejection, real-source rejection; no image writes or artistic acceptance"}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
