"""Behavior contracts for continuous color domains and adaptive tone coverage."""
import json
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from perfect_pixel.gradient_tones import prepare_gradient_tones
from perfect_pixel.palette import rgb_to_oklab


def warm_gradient(samples=32, rows=5, low=.03, high=.70):
    """One linear-light chromaticity, with luminance varying horizontally."""
    linear = np.linspace(low, high, samples)[:, None] * np.array([1., .55, .27])
    srgb = np.where(linear <= .0031308, 12.92 * linear,
                    1.055 * linear ** (1 / 2.4) - .055)
    row = np.rint(srgb * 255).astype(np.uint8)
    return np.repeat(row[None], rows, axis=0)


class GradientToneTests(unittest.TestCase):
    def assert_color_contract(self, source, result, color_error):
        flat = result['flat_image']
        labels = result['region_labels']
        tone_map = result['tone_map']
        palette = result['palette']
        visible = (source[..., 3] > 0 if source.shape[2] == 4
                   else np.ones(source.shape[:2], bool))
        self.assertEqual(flat.shape, source.shape)
        self.assertEqual(flat.dtype, np.uint8)
        self.assertEqual(labels.shape, source.shape[:2])
        self.assertEqual(tone_map.shape, source.shape[:2])
        self.assertTrue(np.all(labels[visible] >= 0))
        self.assertTrue(np.all(tone_map[visible] >= 0))
        np.testing.assert_array_equal(palette[tone_map[visible]], flat[..., :3][visible])
        source_lab = rgb_to_oklab(source[..., :3].astype(np.float32) / 255)
        output_lab = rgb_to_oklab(flat[..., :3].astype(np.float32) / 255)
        errors = np.linalg.norm(source_lab - output_lab, axis=2)
        self.assertLessEqual(float(errors[visible].max()), color_error + 1e-6)
        reported = {r['region_id']: r for r in result['metadata']['region_colors']['regions']}
        for identifier in np.unique(labels[visible]):
            selected = visible & (labels == identifier)
            allowed = set(map(tuple, source[..., :3][selected]))
            actual = set(map(tuple, flat[..., :3][selected]))
            self.assertTrue(actual <= allowed, f'region {identifier} borrowed another domain color')
            region = reported[int(identifier)]
            self.assertEqual(region['pixel_count'], int(selected.sum()))
            self.assertEqual(region['target_tone_count'], len(actual))
            self.assertAlmostEqual(region['max_color_error'], float(errors[selected].max()), delta=1e-6)
        if source.shape[2] == 4:
            np.testing.assert_array_equal(flat[..., 3], source[..., 3])
            np.testing.assert_array_equal(flat[~visible], source[~visible])
            self.assertTrue(np.all(labels[~visible] == -1))
            self.assertTrue(np.all(tone_map[~visible] == -1))
        json.dumps(result['metadata'], allow_nan=False)

    def test_flat_rgb_is_exactly_preserved(self):
        source = np.full((7, 13, 3), [163, 126, 95], np.uint8)
        before = source.copy()
        result = prepare_gradient_tones(source)
        np.testing.assert_array_equal(source, before)
        np.testing.assert_array_equal(result['flat_image'], source)
        self.assertEqual(result['metadata']['segmentation']['region_count'], 1)
        self.assertEqual(result['metadata']['region_colors']['regions'][0]['target_tone_count'], 1)
        self.assert_color_contract(source, result, .06)

    def test_warm_gradient_and_eightfold_stretch_share_one_domain_and_tones(self):
        source = warm_gradient()
        stretched = np.repeat(source, 8, axis=1)
        before, stretched_before = source.copy(), stretched.copy()
        small = prepare_gradient_tones(source, color_error=.06)
        large = prepare_gradient_tones(stretched, color_error=.06)
        self.assertEqual(small['metadata']['segmentation']['region_count'], 1)
        self.assertEqual(large['metadata']['segmentation']['region_count'], 1)
        np.testing.assert_array_equal(large['flat_image'], np.repeat(small['flat_image'], 8, axis=1))
        np.testing.assert_array_equal(source, before)
        np.testing.assert_array_equal(stretched, stretched_before)
        self.assert_color_contract(source, small, .06)
        self.assert_color_contract(stretched, large, .06)

    def test_weak_gradient_can_use_one_tone(self):
        values = np.arange(180, 193, dtype=np.uint8)
        source = np.repeat(np.repeat(values[None, :, None], 3, axis=2), 4, axis=0)
        result = prepare_gradient_tones(source, color_error=.06)
        self.assertEqual(result['metadata']['segmentation']['region_count'], 1)
        self.assertEqual(len(np.unique(result['flat_image'].reshape(-1, 3), axis=0)), 1)
        self.assert_color_contract(source, result, .06)

    def test_strong_gradient_can_exceed_three_tones_to_meet_error_bound(self):
        source = warm_gradient(samples=96, low=.008, high=.90)
        result = prepare_gradient_tones(source, color_error=.025)
        self.assertEqual(result['metadata']['segmentation']['region_count'], 1)
        self.assertGreater(len(np.unique(result['flat_image'].reshape(-1, 3), axis=0)), 3)
        self.assert_color_contract(source, result, .025)

    def test_tighter_color_error_preserves_coordinates_and_meets_each_bound(self):
        source = warm_gradient(samples=64)
        coarse = prepare_gradient_tones(source, color_error=.08)
        precise = prepare_gradient_tones(source, color_error=.02)
        np.testing.assert_array_equal(coarse['region_labels'], precise['region_labels'])
        self.assertGreater(len(precise['palette']), len(coarse['palette']))
        self.assert_color_contract(source, coarse, .08)
        self.assert_color_contract(source, precise, .02)

    def test_alpha_hole_wall_and_partial_alpha_are_preserved(self):
        source = np.full((7, 11, 4), [163, 126, 95, 255], np.uint8)
        source[:, 5] = [255, 0, 255, 0]
        source[2:4, 2:4] = [3, 220, 199, 0]
        source[1, 1, 3] = 128
        before = source.copy()
        result = prepare_gradient_tones(source)
        self.assertEqual(result['metadata']['segmentation']['region_count'], 2)
        self.assertNotEqual(result['region_labels'][0, 0], result['region_labels'][0, -1])
        np.testing.assert_array_equal(result['flat_image'], source)
        np.testing.assert_array_equal(source, before)
        self.assert_color_contract(source, result, .06)

    def test_sharp_different_hues_remain_separate_at_original_pixels(self):
        source = np.full((8, 20, 3), [190, 60, 35], np.uint8)
        source[:, 10:] = [40, 70, 200]
        result = prepare_gradient_tones(source)
        labels = result['region_labels']
        self.assertEqual(result['metadata']['segmentation']['region_count'], 2)
        self.assertEqual(len(np.unique(labels[:, :10])), 1)
        self.assertEqual(len(np.unique(labels[:, 10:])), 1)
        self.assertNotEqual(labels[0, 0], labels[0, -1])
        np.testing.assert_array_equal(result['flat_image'], source)
        self.assert_color_contract(source, result, .06)

    def test_small_nearly_equal_lightness_pink_blush_is_not_erased(self):
        skin = np.array([220., 180., 150.])
        pink = np.array([255., 157., 168.])
        yy, xx = np.mgrid[:17, :45]
        amount = np.exp(-((yy - 8) ** 2 + (xx - 22) ** 2) / (2 * 1.5 ** 2))
        source = np.rint(skin + amount[..., None] * (pink - skin)).astype(np.uint8)
        before = source.copy()
        original_lab = rgb_to_oklab(source.astype(np.float32) / 255)
        self.assertLess(abs(float(original_lab[8, 22, 0] - original_lab[0, 0, 0])), .002)
        self.assertGreater(float(np.linalg.norm(original_lab[8, 22, 1:] - original_lab[0, 0, 1:])), .08)
        result = prepare_gradient_tones(source, color_error=.025)
        result_lab = rgb_to_oklab(result['flat_image'].astype(np.float32) / 255)
        self.assertGreater(float(np.linalg.norm(result_lab[8, 22, 1:] - result_lab[0, 0, 1:])), .03)
        np.testing.assert_array_equal(source, before)
        self.assert_color_contract(source, result, .025)

    def test_boolean_and_nonfinite_options_are_rejected(self):
        source = np.full((3, 4, 3), [150, 100, 65], np.uint8)
        for name in ('color_error', 'edge_threshold', 'chroma_span'):
            for value in (True, np.bool_(True), np.bool_(False), float('nan'), float('inf'), -float('inf')):
                with self.subTest(option=name, value=value):
                    with self.assertRaises(ValueError):
                        prepare_gradient_tones(source, **{name: value})


if __name__ == '__main__':
    unittest.main()
