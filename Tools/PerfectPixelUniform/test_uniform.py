"""Known pixel fixtures, fractional-coordinate markers and saved real-sheet checks."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import unittest

import numpy as np
from PIL import Image
import uniform

ROOT = uniform.ROOT
ACTUAL = None


class UniformContractTests(unittest.TestCase):
    def test_known_blocks_auto_rgba(self):
        # Ground truth is authored before enlargement, not inferred from our result.
        native = np.random.default_rng(73).integers(0, 256, (32, 36, 4), dtype=np.uint8)
        source = np.repeat(np.repeat(native, 4, axis=0), 4, axis=1)
        before = source.copy()
        output, receipt = uniform.process_array(source)
        self.assertAlmostEqual(receipt["period_source_px"], 4, places=10)
        self.assertTrue(np.array_equal(source, before))
        self.assertTrue(np.array_equal(output, native), "Known full RGBA content must be reconstructed")

    def test_fractional_grid_coordinate_markers(self):
        height, width = 103, 1207
        y, x = np.indices((height, width))
        # Decode source X from two channels independently of the implementation.
        source = np.stack((x % 256, x // 256, y), axis=-1).astype(np.uint8)
        period, phase = 4.747232472324724, [1.25, 2.125]
        output, receipt = uniform.uniform_sample(source, period, phase)
        logical_x = (phase[0] + period / 2) % period + np.arange(output.shape[1]) * period
        logical_y = (phase[1] + period / 2) % period + np.arange(output.shape[0]) * period
        decoded_x = output[0, :, 0].astype(int) + 256 * output[0, :, 1].astype(int)
        decoded_y = output[:, 0, 2].astype(int)
        self.assertLessEqual(float(np.max(np.abs(decoded_x + 0.5 - logical_x))), 0.5)
        self.assertLessEqual(float(np.max(np.abs(decoded_y + 0.5 - logical_y))), 0.5)
        self.assertGreater(len(np.unique(np.diff(decoded_x))), 1, "Fractional spacing must not be rounded to one recursive step")
        self.assertLess(abs((logical_x[-1] - logical_x[0]) - (len(logical_x) - 1) * period), 1e-10)
        self.assertFalse(receipt["geometry"]["nonlinear_warp"])

    def test_global_phase_shifted_native_blocks(self):
        native = np.random.default_rng(91).integers(1, 256, (27, 31, 3), dtype=np.uint8)
        expanded = np.repeat(np.repeat(native, 5, axis=0), 5, axis=1)
        # Real known phase offset: prepend complete solid border, do not resize.
        source = np.pad(expanded, ((2, 0), (3, 0), (0, 0)), constant_values=0)
        px, _, known_x = uniform.global_phase(source, 5, 1)
        py, _, known_y = uniform.global_phase(source, 5, 0)
        self.assertTrue(known_x and known_y)
        self.assertAlmostEqual(px, 3, places=10)
        self.assertAlmostEqual(py, 2, places=10)
        output, _ = uniform.uniform_sample(source, 5, [px, py])
        # First output column is the half-cell border; remaining exact native cells.
        self.assertTrue(np.array_equal(output[:, 1:], native))

    def test_blank_detection_fails_without_fallback(self):
        with self.assertRaises(uniform.GridDetectionError):
            uniform.process_array(np.full((64, 64, 3), 120, np.uint8))

    def test_saved_sheet_geometry_and_provenance(self):
        if ACTUAL is None:
            self.skipTest("No actual saved result requested")
        receipt = json.loads((ACTUAL / "receipt.json").read_text(encoding="utf-8"))
        source_path = Path(receipt["source_path"])
        source = np.asarray(Image.open(source_path))
        output = np.asarray(Image.open(ACTUAL / "output.png"))
        self.assertEqual(uniform.sha256(source_path), receipt["source_sha256"])
        self.assertEqual(uniform.sha256(ACTUAL / "output.png"), receipt["output_sha256"])
        engine = receipt["automatic_detection"]["engine"]
        self.assertEqual(uniform.sha256(engine["path"]), engine["sha256"])
        self.assertEqual(uniform.sha256(engine["selector_path"]), engine["selector_sha256"])
        grid, period = receipt["grid"], receipt["period_source_px"]
        ix, iy = np.array(grid["sample_x_indices"]), np.array(grid["sample_y_indices"])
        self.assertTrue(np.array_equal(source[iy[:, None], ix[None, :]], output))
        old = json.loads((ROOT / "docs/artifacts/building37/native-final/receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(old["source_sha256"], receipt["source_sha256"])
        for axis, size in enumerate((output.shape[1], output.shape[0])):
            old_boundaries = old["refined_grid"][("x", "y")[axis] + "_source_boundaries"]
            self.assertGreater(len(np.unique(np.diff(old_boundaries))), 1)
            coords = grid["centre_origin_source_px"][axis] + np.arange(size) * period
            self.assertLess(float(np.max(np.abs(np.diff(coords) - period))), 1e-10)
        self.assertFalse(receipt["manual_size_fallback"])
        self.assertFalse(receipt["local_refinement"])


def main():
    global ACTUAL
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    ACTUAL = args.actual_dir
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(UniformContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"schema": "perfect-pixel-uniform-tests/1", "tests_run": result.testsRun,
              "failures": [str(name) + "\n" + detail for name, detail in result.failures],
              "errors": [str(name) + "\n" + detail for name, detail in result.errors],
              "skipped": [str(name) + ": " + reason for name, reason in result.skipped],
              "passed": result.wasSuccessful(), "actual_result": str(ACTUAL) if ACTUAL else None,
              "scope": "known full RGBA recovery, phase offset, bounded fractional coordinate error, no fallback, actual source provenance; no artistic or Unity acceptance"}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
