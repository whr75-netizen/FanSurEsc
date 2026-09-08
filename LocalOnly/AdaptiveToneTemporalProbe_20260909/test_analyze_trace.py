"""Deterministic parser/math fixtures, not Unity execution or visual approval."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

import analyze_trace as trace


def store_pair(array, offset, value):
    array[offset] = value & 0xffffffff
    array[offset + 1] = value >> 32


def histogram(values, bins=None):
    result = np.zeros((32, 6), dtype="<u4")
    bins = np.minimum((np.asarray(values) * 32).astype(int), 31) if bins is None else bins
    for value, bin_id in zip(values, bins):
        q = int(np.rint(value * trace.Q))
        result[bin_id, 0] += 1
        for offset, increment in ((1, q), (3, q * q)):
            current = int(result[bin_id, offset]) | (int(result[bin_id, offset + 1]) << 32)
            store_pair(result[bin_id], offset, current + increment)
    return result


def empty_capture(folder):
    folder.mkdir(parents=True, exist_ok=True)
    meta = dict(width=4, height=4, frame=100, subjectId=257, captureId="fixture-empty", settingsJson=json.dumps(trace.DEFAULTS))
    (folder / "capture.json").write_text(json.dumps(meta), encoding="utf-8")
    for name, (dtype, shape) in trace.LAYOUTS.items():
        array = np.zeros(shape, dtype=dtype)
        if name == "palette":
            array[..., 3] = -1
        array.tofile(folder / (name + ".bin"))
    for name in ("nativeColor", "cellColor", "output", "nativeLighting", "nativeMeta", "cellMeta"):
        np.zeros((4, 4, 4), dtype="u1" if name.endswith("Meta") else "<f2").tofile(folder / (name + ".bin"))


class TraceTests(unittest.TestCase):
    def test_exact_size_and_little_endian(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "values.bin"
            path.write_bytes(bytes((4, 3, 2, 1)))
            self.assertEqual(int(trace.read_array(path, "<u4", (1,))[0]), 0x01020304)
            with self.assertRaisesRegex(ValueError, "expected 8 bytes"):
                trace.read_array(path, "<u4", (2,))

    def test_moment_pair_carry_and_square(self):
        h = histogram([1.] * 4)
        count, total, square = trace.moments(h)
        self.assertEqual(count[31], 4)
        self.assertEqual(total[31], 4)
        self.assertEqual(square[31], 4)
        self.assertGreater(h[31, 4], 0)

    def test_single_bin_keeps_internal_variance(self):
        h = histogram([.25, .75], [7, 7])
        candidates = np.zeros(32)
        candidates[7] = .25
        result = trace.reconstruct_k1(h, candidates, 0, 1)
        self.assertAlmostEqual(result["rmse"], 2 ** -.5 / 2, places=5)

    def test_k1_is_observed_candidate_and_tie_uses_first_bin(self):
        h = histogram([0., 1.])
        candidate = np.zeros(32)
        candidate[31] = 1
        result = trace.reconstruct_k1(h, candidate, 0, 1)
        self.assertEqual(result["representative_bin"], 0)
        self.assertEqual(result["representative_metric"], 0)
        self.assertAlmostEqual(result["rmse"], 2 ** -.5)

    def test_empty_capture_and_cli_reports(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            empty_capture(root / "capture")
            (root / "sample.json").write_text('{"index": 3, "phase": "fixture"}', encoding="utf-8")
            capture = trace.load_capture(root / "capture", root)
            report = trace.analyze_capture(capture)
            self.assertEqual(report["sample"]["index"], 3)
            self.assertEqual(report["groups"], [])
            self.assertEqual(report["coverage"]["changed_outside_target_seeds"], 0)
            self.assertEqual(trace.main([str(root), "--out", str(root / "report")]), 0)
            summary = trace.read_json(root / "report" / "summary.json")
            self.assertEqual(summary["capture_count"], 1)
            self.assertEqual(summary["capture_errors"], [])

    def test_metadata_subject_and_neutral_chroma(self):
        meta = np.zeros((2, 4), dtype=np.uint8)
        meta[:, 0], meta[:, 3], meta[:, 1] = 1, 1, 4
        colors = np.array([[.05, .05, .05, 2], [.5, .5, .5, 2]], dtype=np.float16)
        self.assertTrue(np.all(trace.subject_ids(meta) == 257))
        self.assertTrue(np.all(trace.color_keys(colors, meta, .06) == ((5 << 16) | 0x8080)))

    def test_nonempty_skin_capture_and_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            empty_capture(folder)
            capture = trace.load_capture(folder)
            a = capture["arrays"]
            for name in ("nativeMeta", "cellMeta"):
                a[name][..., 0], a[name][..., 3], a[name][..., 1] = 1, 1, 4
            color = a["nativeColor"]
            color[..., :3], color[..., 3] = .04, 2
            color[:, 2:, :3] = .08
            a["cellColor"][:] = color
            a["output"][:] = color
            a["output"][..., :3] = color[0, 0, :3]
            a["nativeLighting"][..., 0], a["nativeLighting"][..., 3] = .15, 1
            metric = trace.oklab(color[..., :3])[..., 0]
            minimum, maximum = float(metric.min()), float(metric.max())
            u = ((metric - minimum) / (maximum - minimum)).flatten()
            key, slot = (5 << 16) | 0x8080, 77
            group = a["groups"][slot]
            group[:6] = (key, 16, 0, 0, 3, 3)
            group[6:8] = np.asarray([minimum, maximum], dtype="<f4").view("<u4")
            h = histogram(u)
            h[0, 5], h[31, 5] = 0, 2
            a["histogram"][slot] = h
            for t, value in enumerate(u):
                a["tiles"][slot, t, 0] = 1
                store_pair(a["tiles"][slot, t], 1, int(np.rint(float(value) * trace.Q)))
                a["tileHistogram"][slot, t, min(int(value * 32), 31)] = 1
            a["status"][slot] = 1
            a["solutions"][slot, 0] = (1, .06, 0, 0)
            for bin_id in (0, 31):
                a["palette"][slot, bin_id] = (*color[0, 0, :3], minimum)
            report = trace.analyze_capture(capture)
            g = report["groups"][0]
            self.assertEqual(g["slot"], 77)
            self.assertEqual(g["metric"], "Oklab_L")
            self.assertEqual(g["cpu_source_group_count"], 16)
            self.assertEqual(g["source_colors"], 2)
            self.assertEqual(g["output_colors"], 1)
            self.assertAlmostEqual(g["E"]["mean"], .15, places=3)
            self.assertEqual(report["coverage"]["depth_bit_changes"], 0)
            self.assertEqual(report["parts"][0]["K1_source_population"], 16)
            self.assertIn("CPU64_guard_differs_from_GPU", g["warnings"])

    def test_guard_broad_gradient_and_hair_relative_limit(self):
        values = [0., 0., 1., 1.] * 4
        h = histogram(values)
        tiles = np.zeros((16, 3), dtype=np.uint32)
        for i, value in enumerate(values):
            tiles[i, 0] = 1
            store_pair(tiles[i], 1, int(value * trace.Q))
        for precision in ("float64", "float32"):
            guard = trace.reconstruct_guard(h, tiles, .02, .08, trace.DEFAULTS, True, precision)
            self.assertTrue(guard["guard"])
            self.assertAlmostEqual(guard["metric_mean"], .06, places=6)
            self.assertAlmostEqual(guard["error_limit"], .006, places=6)
            self.assertAlmostEqual(guard["required_contrast"], .08 * .65, places=6)

    def test_old_skin_only_hair_only_metric_selection(self):
        legacy = {k: v for k, v in trace.DEFAULTS.items() if not k.startswith("skin")}
        variants = ((legacy, None, None),
                    ({**trace.DEFAULTS, "skinLighting": True}, None, "skin"),
                    ({**trace.DEFAULTS, "hairLighting": True}, "hair", None),
                    ({**trace.DEFAULTS, "hairLighting": True, "skinLighting": True}, "hair", "skin"))
        for settings, hair_expected, skin_expected in variants:
            with self.subTest(settings=settings):
                self.assertEqual(trace.lighting_prefix(settings, 3), hair_expected)
                self.assertEqual(trace.lighting_prefix(settings, 4), skin_expected)
                self.assertIsNone(trace.lighting_prefix(settings, 1))

    def test_skin_and_hair_use_separate_relative_error_and_floor(self):
        settings = {**trace.DEFAULTS, "hairRelativeError": .12, "hairIlluminationFloor": .02,
                    "skinRelativeError": .03, "skinIlluminationFloor": .09}
        h = histogram([0., 1.])
        tiles = np.zeros((16, 3), dtype=np.uint32)
        for precision in ("float64", "float32"):
            hair = trace.reconstruct_guard(h, tiles, .02, .08, settings, True, precision)
            skin = trace.reconstruct_guard(h, tiles, .02, .08, settings, False, precision, skin=True)
            legacy = trace.reconstruct_guard(h, tiles, .02, .08, settings, False, precision)
            self.assertAlmostEqual(hair["metric_scale"], .06, places=6)
            self.assertAlmostEqual(hair["error_limit"], .0072, places=6)
            self.assertAlmostEqual(skin["metric_scale"], .09, places=6)
            self.assertAlmostEqual(skin["error_limit"], .0027, places=6)
            self.assertAlmostEqual(skin["minimum_contrast"], .025 * .09, places=6)
            self.assertAlmostEqual(skin["highlight_minimum_contrast"], .025 * .09, places=6)
            self.assertAlmostEqual(legacy["error_limit"], .06, places=6)

    def test_legacy_capture_defaults_skin_off(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            empty_capture(folder)
            metadata = trace.read_json(folder / "capture.json")
            metadata["settingsJson"] = json.dumps({k: v for k, v in trace.DEFAULTS.items() if not k.startswith("skin")})
            (folder / "capture.json").write_text(json.dumps(metadata), encoding="utf-8")
            capture = trace.load_capture(folder)
            self.assertFalse(capture["settings"]["skinLighting"])
            self.assertIn("skinLighting", capture["settings_defaulted"])
            self.assertIsNone(trace.lighting_prefix(capture["settings"], 4))

    def test_coarse_average_can_reject_fine_contrast(self):
        values = [0., 1., 0., 1.] * 4
        h = histogram(values)
        tiles = np.zeros((16, 3), dtype=np.uint32)
        for i, value in enumerate(values):
            tiles[i, 0] = 1
            store_pair(tiles[i], 1, int(value * trace.Q))
        guard = trace.reconstruct_guard(h, tiles, 0., 1., trace.DEFAULTS, False)
        self.assertFalse(guard["guard"])
        self.assertEqual(guard["reason"], "coarse_coherence_below_.35")
        self.assertEqual(guard["fine_coherence"], 1)
        self.assertEqual(guard["coarse_coherence"], 0)

    def test_flat_guard_rejected_and_error_limit_present(self):
        guard = trace.reconstruct_guard(histogram([0.] * 4), np.zeros((16, 3), dtype=np.uint32), .2, 0., trace.DEFAULTS, False)
        self.assertEqual(guard["reason"], "variance_at_or_below_1e-12")
        self.assertEqual(guard["error_limit"], .06)

    def test_adjacent_uses_key_not_slot(self):
        gpu = dict(K=2, guard=True, highlight=False, status=3, palette=[[.1, .1, .1, .4]])
        group = dict(identity="257:327808", slot=2, part=4, metric="Oklab_L", count=10, range=.1, gpu=gpu,
                     cpu_reconstructed={"float64": {"guard": {"error_limit": .06, "reason": "passed"}}})
        first = dict(metadata={"captureId": "a", "frame": 100}, sample={"index": 0}, settings=trace.DEFAULTS, groups=[group])
        second = copy.deepcopy(first)
        second["metadata"]["captureId"] = "b"
        second["groups"][0]["slot"] = 99
        self.assertEqual(trace.adjacent_jumps([first, second]), [])
        second["groups"][0]["gpu"].update(K=1, guard=False, status=1)
        changes = trace.adjacent_jumps([first, second])
        self.assertEqual(len(changes), 1)
        self.assertIn("collapsed_to_K1", changes[0]["reasons"])
        self.assertIn("guard_changed", changes[0]["reasons"])
        second["groups"][0]["metric"] = "illumination_Y"
        changes = trace.adjacent_jumps([first, second])
        self.assertIn("metric_changed_not_comparable", changes[0]["reasons"])
        self.assertNotIn("collapsed_to_K1", changes[0]["reasons"])
        self.assertIsNone(changes[0]["range_delta"])
        self.assertIsNone(changes[0]["palette_metric_hausdorff"])
        second["metadata"]["cameraId"] = 2
        self.assertEqual(trace.adjacent_jumps([first, second]), [])


if __name__ == "__main__":
    unittest.main()
