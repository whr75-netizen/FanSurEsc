import json
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from perfect_pixel.reference_colors import transfer_reference_colors
from perfect_pixel.palette import rgb_to_oklab


class ReferenceColorTests(unittest.TestCase):
    def test_geometry_alpha_hidden_rgb_and_inputs_are_preserved(self):
        source = np.array([[[40, 80, 120, 0], [40, 80, 120, 1]],
                           [[70, 90, 110, 128], [70, 90, 110, 255]]], np.uint8)
        reference = np.array([[[80, 140, 200, 255], [130, 180, 230, 255],
                               [255, 0, 255, 0]]], np.uint8)
        before = source.copy(), reference.copy()
        result, metadata = transfer_reference_colors(source, reference)
        self.assertEqual(result.shape, source.shape)
        np.testing.assert_array_equal(result[..., 3], source[..., 3])
        np.testing.assert_array_equal(result[0, 0], source[0, 0])
        np.testing.assert_array_equal(source, before[0])
        np.testing.assert_array_equal(reference, before[1])
        self.assertNotIn([255, 0, 255], metadata['reference_palette'])
        json.dumps(metadata, allow_nan=False)

    def test_actual_reference_provenance_palette_bounds_and_mapping(self):
        rng = np.random.default_rng(4)
        source = rng.integers(0, 256, (13, 9, 3), dtype=np.uint8)
        reference = rng.integers(0, 256, (25, 17, 3), dtype=np.uint8)
        result, meta = transfer_reference_colors(source, reference, 2)
        actual = set(map(tuple, reference.reshape(-1, 3)))
        self.assertTrue(set(map(tuple, result.reshape(-1, 3))) <= actual | set(map(tuple, source.reshape(-1, 3))))
        self.assertTrue(set(map(tuple, meta['reference_palette'])) <= actual)
        self.assertLessEqual(len(meta['reference_palette']), 50)
        self.assertEqual(len(meta['mappings']), len(np.unique(source.reshape(-1, 3), axis=0)))
        mapping = {tuple(m['source_rgb']): m for m in meta['mappings']}
        for s, t in zip(source.reshape(-1, 3), result.reshape(-1, 3)):
            self.assertEqual(mapping[tuple(s)]['target_rgb'], t.tolist())
            self.assertLessEqual(len(mapping[tuple(s)]['target_ramp']), 2)
            if tuple(t) not in actual:
                self.assertTrue(mapping[tuple(s)]['retained_source_for_brightness_floor'])
                np.testing.assert_array_equal(s, t)
        self.assertTrue(np.all(rgb_to_oklab(result / 255)[..., 0] >= rgb_to_oklab(source / 255)[..., 0] - .020001))

    def test_rare_hues_are_not_removed_by_reference_area(self):
        source = np.array([[[120, 30, 35], [25, 110, 35], [25, 35, 120]]], np.uint8)
        reference = np.full((30, 30, 3), (210, 55, 60), np.uint8)
        reference[0, 0] = (45, 205, 65)
        reference[0, 1] = (45, 65, 210)
        result, _ = transfer_reference_colors(source, reference)
        np.testing.assert_array_equal(np.argmax(result[0], axis=1), [0, 1, 2])

    def test_rare_tone_does_not_collapse_and_order_moves_brighter(self):
        source = np.array([[[60, 120, 180], [90, 150, 210], [150, 200, 250]]], np.uint8)
        reference = np.full((10, 10, 3), (90, 150, 210), np.uint8)
        reference[0, 0] = (60, 120, 180)
        reference[0, 1] = (150, 200, 250)
        result, meta = transfer_reference_colors(source, reference)
        self.assertEqual(len(np.unique(result.reshape(-1, 3), axis=0)), 3)
        lightness = rgb_to_oklab(result[0] / 255)[:, 0]
        self.assertTrue(np.all(np.diff(lightness) > 0))
        np.testing.assert_array_equal(result, source)
        self.assertTrue(all(len(m['target_ramp']) <= 3 for m in meta['mappings']))

    def test_pixel_order_and_duplicate_area_do_not_change_mapping(self):
        source = np.array([[[30, 60, 90], [45, 90, 135], [60, 120, 180]]], np.uint8)
        reference = np.array([[[60, 120, 180], [90, 150, 210], [150, 200, 250]]], np.uint8)
        a, _ = transfer_reference_colors(source, reference)
        b, _ = transfer_reference_colors(source[:, ::-1], reference[:, ::-1])
        np.testing.assert_array_equal(a, b[:, ::-1])
        expanded = np.concatenate([reference, np.repeat(reference[:, 1:2], 100, axis=1)], axis=1)
        c, _ = transfer_reference_colors(source, expanded)
        np.testing.assert_array_equal(a, c)

    def test_dictionary_chunk_boundary_keeps_one_pixel_color(self):
        reference = np.full((1, 131073, 3), (210, 55, 60), np.uint8)
        reference[0, -1] = (45, 65, 210)
        source = np.array([[[25, 35, 120]]], np.uint8)
        result, meta = transfer_reference_colors(source, reference)
        np.testing.assert_array_equal(result[0, 0], reference[0, -1])
        self.assertIn(reference[0, -1].tolist(), meta['reference_palette'])

    def test_flat_near_white_anchor_is_not_middle_gray(self):
        bright = np.array([242, 243, 254], np.uint8)
        dark = np.array([10, 11, 22], np.uint8)
        intermediates = np.array([[v, v + 1, v + 12] for v in range(30, 220)], np.uint8)
        reference = np.concatenate([np.tile(bright, (1000, 1)), np.tile(dark, (1000, 1)), intermediates])[None]
        source = np.array([[bright, [230, 232, 247]]], np.uint8)
        result, meta = transfer_reference_colors(source, reference)
        np.testing.assert_array_equal(result[0, 0], bright)
        self.assertIn(bright.tolist(), meta['reference_palette'])
        self.assertTrue(np.all(rgb_to_oklab(result / 255)[..., 0] >= rgb_to_oklab(source / 255)[..., 0] - .020001))

    def test_no_bright_reference_retains_source_and_reports_it(self):
        source = np.array([[[230, 235, 240]]], np.uint8)
        reference = np.array([[[10, 15, 20], [25, 30, 35]]], np.uint8)
        result, meta = transfer_reference_colors(source, reference)
        np.testing.assert_array_equal(result, source)
        self.assertEqual(meta['source_colors_retained_for_brightness_floor'], 1)

    def test_tone_collapse_is_reported_not_hidden(self):
        source = np.array([[[20, 45, 70], [30, 60, 90], [40, 75, 110]]], np.uint8)
        reference = np.array([[[90, 150, 210]]], np.uint8)
        result, meta = transfer_reference_colors(source, reference)
        self.assertEqual(meta['collapsed_source_color_count'], 2)
        self.assertEqual(meta['range_tone_counts'][0]['source_lightness_level_count'], 3)
        self.assertEqual(meta['range_tone_counts'][0]['target_color_count'], 1)

    def test_lookup_is_monotone_inside_each_reference_range(self):
        rng = np.random.default_rng(17)
        source = rng.integers(10, 246, (20, 10, 3), dtype=np.uint8)
        reference = rng.integers(10, 246, (30, 10, 3), dtype=np.uint8)
        result, meta = transfer_reference_colors(source, reference)
        palette_groups = {tuple(c): i for i, ramp in enumerate(meta['reference_ramps']) for c in ramp}
        records = {}
        for mapping in meta['mappings']:
            if mapping['retained_source_for_brightness_floor']:
                continue
            group = palette_groups[tuple(mapping['target_rgb'])]
            lightness = rgb_to_oklab(np.array([mapping['source_rgb'], mapping['target_rgb']]) / 255)[:, 0]
            records.setdefault(group, []).append(lightness)
        for values in records.values():
            pairs = np.array(values)
            ordered = pairs[np.argsort(pairs[:, 0], kind='stable')]
            self.assertTrue(np.all(np.diff(ordered[:, 1]) >= -1e-6))
        self.assertTrue(meta['monotone_lightness_within_matched_reference_range'])

    def test_degenerate_and_validation(self):
        pixel = np.full((1, 1, 3), 128, np.uint8)
        result, meta = transfer_reference_colors(pixel, pixel, 1)
        np.testing.assert_array_equal(result, pixel)
        self.assertEqual(len(meta['reference_palette']), 1)
        transparent = np.zeros((1, 1, 4), np.uint8)
        result, meta = transfer_reference_colors(transparent, pixel)
        np.testing.assert_array_equal(result, transparent)
        self.assertEqual(meta['mappings'][0]['target_ramp'], [])
        with self.assertRaises(ValueError): transfer_reference_colors(pixel, transparent)
        for bad in (True, 0, 4, 2.5, '3'):
            with self.assertRaises(ValueError): transfer_reference_colors(pixel, pixel, bad)
        for bad in (pixel.astype(float), np.zeros((0, 1, 3), np.uint8), np.zeros((2, 2), np.uint8)):
            with self.assertRaises(ValueError): transfer_reference_colors(bad, pixel)


if __name__ == '__main__':
    unittest.main()
