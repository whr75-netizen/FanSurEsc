import json
from pathlib import Path
import sys
import unittest
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from perfect_pixel import spatial_tones
from perfect_pixel.spatial_tones import build_spatial_constraints


def samples(values, mask=None):
    values = np.asarray(values, float)
    if mask is None:
        mask = np.ones(values.shape, bool)
    positions = np.column_stack(np.nonzero(mask))
    lightness = values[mask]
    colors, inverse = np.unique(lightness, return_inverse=True)
    return lightness, inverse, positions, len(colors), colors


class SpatialToneTests(unittest.TestCase):
    def call(self, values, mask=None, **kwargs):
        lightness, inverse, positions, count, colors = samples(values, mask)
        result = build_spatial_constraints(lightness, inverse, positions, count, **kwargs)
        json.dumps(result[1], allow_nan=False)
        for constraint in result[0]:
            self.assertEqual(constraint['coefficients'].shape, (count,))
            self.assertTrue(np.all(np.isfinite(constraint['coefficients'])))
            self.assertAlmostEqual(float(constraint['coefficients'].sum()), 0., delta=1e-12)
            source_contrast = float(constraint['coefficients'] @ colors)
            self.assertAlmostEqual(constraint['minimum_contrast'], source_contrast * .65, delta=1e-12)
        return result

    def test_flat_group_does_not_force_contrast(self):
        constraints, meta = self.call(np.full((40, 60), .7))
        self.assertEqual(constraints, [])
        self.assertEqual(meta['bypass_reason'], 'insufficient_source_lightness_contrast')

    def test_coherent_ramp_and_shuffled_same_histogram_are_distinguished(self):
        ramp = np.repeat(np.linspace(.4, .65, 80)[None], 64, axis=0)
        noise = np.random.default_rng(921).permutation(ramp.ravel()).reshape(ramp.shape)
        np.testing.assert_array_equal(np.sort(ramp.ravel()), np.sort(noise.ravel()))
        coherent, coherent_meta = self.call(ramp)
        random, random_meta = self.call(noise)
        self.assertEqual(len(coherent), 1)
        self.assertEqual(random, [])
        self.assertGreater(coherent_meta['selected_source_contrast_l'], .15)
        self.assertIn('two_scales', random_meta['bypass_reason'])
        # A constant candidate cannot pass, but the original color vector can.
        self.assertLess(float(coherent[0]['coefficients'] @ np.full(80, .525)),
                        coherent[0]['minimum_contrast'])

    def test_coherent_patch_and_shuffled_patch_histogram_are_distinguished(self):
        patch = np.full((64, 80), .5)
        patch[8:56, 48:72] = .68
        noise = np.random.default_rng(470).permutation(patch.ravel()).reshape(patch.shape)
        coherent, _ = self.call(patch)
        random, _ = self.call(noise)
        self.assertEqual(len(coherent), 1)
        self.assertEqual(random, [])

    def test_values_outside_group_mask_cannot_change_supports(self):
        image = np.repeat(np.linspace(.3, .65, 80)[None], 64, axis=0)
        mask = np.zeros_like(image, bool)
        mask[8:56, 8:72] = True
        mask[23:32, 25:34] = False
        dark_outside, white_outside = image.copy(), image.copy()
        dark_outside[~mask] = 0.
        white_outside[~mask] = 1.
        first, first_meta = self.call(dark_outside, mask)
        second, second_meta = self.call(white_outside, mask)
        self.assertEqual(first_meta, second_meta)
        self.assertEqual(len(first), 1)
        np.testing.assert_array_equal(first[0]['coefficients'], second[0]['coefficients'])

    def test_translation_and_input_permutation_do_not_change_constraint(self):
        image = np.repeat(np.linspace(.3, .7, 60)[None], 48, axis=0)
        lightness, inverse, positions, count, _ = samples(image)
        before = (lightness.copy(), inverse.copy(), positions.copy())
        first, first_meta = build_spatial_constraints(lightness, inverse, positions, count)
        order = np.random.default_rng(320).permutation(len(lightness))
        second, second_meta = build_spatial_constraints(
            lightness[order], inverse[order], positions[order] + [1_000_000, -2_000_000], count)
        np.testing.assert_allclose(first[0]['coefficients'], second[0]['coefficients'], atol=1e-14)
        self.assertAlmostEqual(first[0]['minimum_contrast'], second[0]['minimum_contrast'], delta=1e-14)
        self.assertEqual(first_meta['selected_scale_fraction'], second_meta['selected_scale_fraction'])
        for actual, original in zip((lightness, inverse, positions), before):
            np.testing.assert_array_equal(actual, original)

    def test_sampling_floor_does_not_count_three_identical_scales(self):
        constraints, meta = self.call(np.array([[.3, .7], [.3, .7]]))
        self.assertEqual(constraints, [])
        self.assertEqual(meta['bypass_reason'], 'fewer_than_two_distinct_source_scales')

    def test_invalid_shapes_nonfinite_options_and_duplicate_positions(self):
        args = [np.array([.3, .7]), np.array([0, 1]), np.array([[0, 0], [0, 1]]), 2]
        invalid = [
            (0, np.array([.3, np.nan])), (0, np.array([.3, np.inf])),
            (0, np.array([False, True])), (0, np.array([-.1, .7])),
            (1, np.array([0., 1.])), (1, np.array([0, 2])),
            (2, np.array([[0., 0.], [0., 1.]])), (2, np.array([[0, 0], [0, 0]])),
            (2, np.array([0, 1])), (3, True), (3, 0),
        ]
        for index, value in invalid:
            with self.subTest(index=index, value=value):
                replaced = args.copy()
                replaced[index] = value
                with self.assertRaises(ValueError):
                    build_spatial_constraints(*replaced)
        for name in ('contrast_retention', 'minimum_contrast'):
            for value in (True, 0, -.1, float('nan'), float('inf')):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        build_spatial_constraints(*args, **{name: value})

    def test_resource_bounds_fail_explicitly_without_resizing(self):
        args = [np.array([.3, .7]), np.array([0, 1]), np.array([[0, 0], [0, 100]]), 2]
        with mock.patch.object(spatial_tones, 'MAX_BOUNDING_BOX_PIXELS', 100):
            with self.assertRaisesRegex(ValueError, 'bounding-box resource bound'):
                build_spatial_constraints(*args)
        with mock.patch.object(spatial_tones, 'MAX_FILTER_PIXEL_TAPS', 1):
            with self.assertRaisesRegex(ValueError, 'filter resource bound'):
                build_spatial_constraints(*args)


if __name__ == '__main__':
    unittest.main()
