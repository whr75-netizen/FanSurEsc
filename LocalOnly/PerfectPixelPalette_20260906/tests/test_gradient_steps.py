import itertools
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from perfect_pixel import gradient_steps
from perfect_pixel.gradient_steps import select_step_palette
from perfect_pixel.palette import rgb_to_oklab


def gray(values):
    return np.repeat(np.asarray(values, np.uint8)[:, None], 3, axis=1)


class GradientStepTests(unittest.TestCase):
    def assert_contract(self, colors, counts, result, error, chroma_error=.04):
        ramp, assigned, meta = result
        self.assertEqual(ramp.dtype, np.uint8)
        self.assertEqual(assigned.shape, (len(colors),))
        self.assertTrue(set(map(tuple, ramp)) <= set(map(tuple, colors)))
        source_lab = rgb_to_oklab(colors.astype(np.float32) / 255)
        actual_lab = rgb_to_oklab(ramp[assigned].astype(np.float32) / 255)
        actual_rmse = np.sqrt(np.average((source_lab[:, 0] - actual_lab[:, 0]) ** 2, weights=counts))
        self.assertLessEqual(float(actual_rmse), error + 1e-7)
        self.assertAlmostEqual(float(actual_rmse), meta['weighted_rmse_l'], delta=1e-7)
        self.assertLessEqual(meta['max_chroma_error'], chroma_error + 1e-7)
        for group in meta['color_groups']:
            self.assertLessEqual(group['weighted_rmse_l'], error + 1e-10)
            if group['target_tone_count'] > 1:
                self.assertGreater(group['previous_k_weighted_rmse_l'], error)
        json.dumps(meta, allow_nan=False)

    def test_flat_exact_and_input_immutable(self):
        colors = np.array([[180, 135, 100], [180, 135, 100]], np.uint8)
        counts = np.array([3, 700])
        before, counts_before = colors.copy(), counts.copy()
        result = select_step_palette(colors, counts)
        np.testing.assert_array_equal(result[0][result[1]], colors)
        self.assertEqual(len(result[0]), 1)
        np.testing.assert_array_equal(colors, before)
        np.testing.assert_array_equal(counts, counts_before)
        self.assert_contract(colors, counts, result, .06)

    def test_weak_and_strong_gradients_choose_different_step_counts(self):
        weak, strong = gray(range(180, 193)), gray(np.linspace(25, 240, 96))
        weak_result = select_step_palette(weak, np.ones(len(weak)))
        strong_result = select_step_palette(strong, np.ones(len(strong)))
        self.assertEqual(len(weak_result[0]), 1)
        self.assertGreater(len(strong_result[0]), 1)
        precise = select_step_palette(strong, np.ones(len(strong)), tone_error=.01)
        self.assertGreater(len(precise[0]), 3)
        self.assert_contract(weak, np.ones(len(weak)), weak_result, .06)
        self.assert_contract(strong, np.ones(len(strong)), strong_result, .06)
        self.assert_contract(strong, np.ones(len(strong)), precise, .01)

    def test_eightfold_pixel_frequency_scaling_does_not_change_steps(self):
        colors = gray(np.linspace(50, 200, 32))
        counts = np.arange(1, 33)
        short = select_step_palette(colors, counts)
        long = select_step_palette(colors, counts * 8)
        np.testing.assert_array_equal(short[0], long[0])
        np.testing.assert_array_equal(short[1], long[1])
        self.assert_contract(colors, counts * 8, long, .06)

    def test_rare_lightness_outlier_does_not_force_an_extra_step(self):
        colors = gray([180, 190, 250])
        counts = np.array([1000, 1000, 1])
        result = select_step_palette(colors, counts)
        self.assertEqual(len(result[0]), 1)
        self.assertGreater(result[2]['max_lightness_error'], .06)
        self.assert_contract(colors, counts, result, .06)

    def test_rare_nearly_equal_lightness_pink_keeps_its_color_group(self):
        colors = np.array([[220, 180, 150], [255, 157, 168]], np.uint8)
        counts = np.array([10000, 1])
        result = select_step_palette(colors, counts)
        self.assertEqual(result[2]['color_group_count'], 2)
        self.assertNotEqual(result[1][0], result[1][1])
        np.testing.assert_array_equal(result[0][result[1]], colors)
        self.assert_contract(colors, counts, result, .06)

    def test_black_and_near_black_produce_finite_diagnostics(self):
        colors = np.array([[0, 0, 0], [1, 0, 0], [4, 4, 4], [12, 9, 8]], np.uint8)
        counts = np.array([5, 2, 8, 1])
        result = select_step_palette(colors, counts)
        self.assert_contract(colors, counts, result, .06)

    def test_tiny_one_dimensional_problem_matches_exhaustive_partitions(self):
        colors = gray([35, 80, 117, 157, 201, 239])
        counts = np.array([1, 4, 9, 5, 3, 1])
        error = .05
        result = select_step_palette(colors, counts, tone_error=error)
        values = rgb_to_oklab(colors.astype(np.float32) / 255)[:, 0].astype(float)
        best_k = None
        for k in range(1, len(colors) + 1):
            best = float('inf')
            for cuts in itertools.combinations(range(1, len(colors)), k - 1):
                bounds = (0,) + cuts + (len(colors),)
                cost = 0.
                for start, end in zip(bounds[:-1], bounds[1:]):
                    cost += min(float(np.sum(counts[start:end] * (values[start:end] - r) ** 2))
                                for r in values[start:end])
                best = min(best, cost)
            if np.sqrt(best / counts.sum()) <= error:
                best_k = k
                break
        self.assertEqual(len(result[0]), best_k)
        self.assert_contract(colors, counts, result, error)

    def test_explicit_resource_failure_does_not_return_a_clamped_palette(self):
        colors = gray([30, 70, 120, 160])
        with mock.patch.object(gradient_steps, 'MAX_UNIQUE_LIGHTNESS', 3):
            with self.assertRaisesRegex(ValueError, 'resource bound'):
                select_step_palette(colors, np.ones(4))
        with mock.patch.object(gradient_steps, 'MAX_DP_TRANSITIONS', 1):
            with self.assertRaisesRegex(ValueError, 'transition budget'):
                select_step_palette(colors, np.ones(4))

    def test_invalid_options_and_counts_are_rejected(self):
        colors = gray([100, 130])
        for option in ('tone_error', 'chroma_error'):
            for value in (True, np.bool_(True), 0, -.1, float('nan'), float('inf')):
                with self.subTest(option=option, value=value):
                    with self.assertRaises(ValueError):
                        select_step_palette(colors, [1, 1], **{option: value})
        for counts in ([1], [1, 0], [1, -1], [True, False], [1, float('nan')]):
            with self.assertRaises(ValueError):
                select_step_palette(colors, counts)


if __name__ == '__main__':
    unittest.main()
