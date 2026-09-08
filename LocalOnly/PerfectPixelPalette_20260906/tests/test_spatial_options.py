"""Adjustable source-support controls with unchanged default behavior."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from perfect_pixel import spatial_tones
from perfect_pixel.spatial_tones import build_spatial_constraints, validate_spatial_options


DEFAULTS = {'scale_fractions': [.02, .04, .08], 'minimum_coherence': .35,
            'minimum_support_overlap': .65, 'support_quantiles': [.2, .8]}


def arguments(image=None):
    if image is None:
        image = np.repeat(np.linspace(.3, .7, 80)[None], 64, axis=0)
    values = np.asarray(image, np.float64).ravel()
    colors, inverse = np.unique(values, return_inverse=True)
    positions = np.column_stack(np.nonzero(np.ones(image.shape, bool)))
    return values, inverse, positions, len(colors)


class SpatialOptionTests(unittest.TestCase):
    def test_defaults_are_complete_json_safe_and_fresh(self):
        first = validate_spatial_options()
        second = validate_spatial_options({})
        self.assertEqual(first, DEFAULTS)
        self.assertEqual(second, DEFAULTS)
        self.assertIsInstance(first['scale_fractions'], list)
        self.assertIsInstance(first['support_quantiles'], list)
        json.dumps(first, allow_nan=False)
        first['scale_fractions'][0] = .01
        first['support_quantiles'][0] = .1
        first['minimum_coherence'] = .7
        self.assertEqual(second, DEFAULTS)
        self.assertEqual(validate_spatial_options(), DEFAULTS)
        self.assertEqual(spatial_tones.SCALE_FRACTIONS, (.02, .04, .08))
        self.assertEqual(spatial_tones.SUPPORT_QUANTILES, (.2, .8))

    def test_explicit_defaults_match_original_default_constraints_and_supports(self):
        args = arguments()
        originals = tuple(a.copy() if isinstance(a, np.ndarray) else a for a in args)
        implicit = build_spatial_constraints(*args, return_supports=True)
        explicit = build_spatial_constraints(*args, return_supports=True, spatial_options=DEFAULTS)
        empty = build_spatial_constraints(*args, spatial_options={})
        self.assertEqual(len(implicit[0]), 1)
        self.assertEqual(implicit[1], explicit[1])
        self.assertEqual(implicit[1], empty[1])
        np.testing.assert_array_equal(implicit[0][0]['coefficients'], explicit[0][0]['coefficients'])
        np.testing.assert_array_equal(implicit[2]['low'], explicit[2]['low'])
        np.testing.assert_array_equal(implicit[2]['high'], explicit[2]['high'])
        for actual, original in zip(args, originals):
            np.testing.assert_array_equal(actual, original)
        self.assertEqual(DEFAULTS, validate_spatial_options())

    def test_scales_change_actual_filter_sigmas_without_changing_sampling_floor(self):
        supplied = {'scale_fractions': [.01, .025]}
        before = copy.deepcopy(supplied)
        constraints, metadata = build_spatial_constraints(*arguments(), spatial_options=supplied)
        self.assertEqual(len(constraints), 1)
        self.assertEqual(metadata['scale_fractions'], [.01, .025])
        self.assertEqual([scale['sigma'] for scale in metadata['scales']], [[.64, .8], [1.6, 2.]])
        self.assertEqual(metadata['selected_scale_fraction'], .025)
        self.assertEqual(metadata['sampling_sigma_floor'], .5)
        self.assertEqual(supplied, before)
        metadata['scale_fractions'][0] = .1
        self.assertEqual(supplied, before)
        json.dumps(metadata, allow_nan=False)

    def test_coherence_option_changes_acceptance_of_actual_ramp(self):
        default, _ = build_spatial_constraints(*arguments())
        strict, metadata = build_spatial_constraints(*arguments(), spatial_options={'minimum_coherence': 1.})
        self.assertEqual(len(default), 1)
        self.assertEqual(strict, [])
        self.assertEqual(metadata['minimum_coherence_ratio'], 1.)
        self.assertTrue(all(scale['bypass_reason'] == 'lightness_variance_does_not_survive_smoothing'
                            for scale in metadata['scales']))

    def test_support_quantiles_change_the_actual_source_masks(self):
        normal = build_spatial_constraints(*arguments(), return_supports=True)
        narrow = build_spatial_constraints(*arguments(), return_supports=True,
                                           spatial_options={'support_quantiles': [.1, .9]})
        self.assertEqual(len(narrow[0]), 1)
        self.assertLess(int(narrow[2]['high'].sum()), int(normal[2]['high'].sum()))
        self.assertLess(int(narrow[2]['low'].sum()), int(normal[2]['low'].sum()))
        self.assertTrue(np.all(~narrow[2]['high'] | normal[2]['high']))
        self.assertTrue(np.all(~narrow[2]['low'] | normal[2]['low']))
        self.assertGreater(narrow[1]['selected_source_contrast_l'], normal[1]['selected_source_contrast_l'])

    def test_overlap_option_changes_acceptance_of_actual_spatial_supports(self):
        yy, xx = np.mgrid[:64, :80]
        image = .5 + .1 * np.sin(xx / 9.) + .09 * np.cos(yy / 7.) + .035 * np.sin((xx + yy) / 2.)
        normal, normal_meta = build_spatial_constraints(*arguments(image))
        strict, strict_meta = build_spatial_constraints(*arguments(image),
                                                        spatial_options={'minimum_support_overlap': 1.})
        self.assertEqual(len(normal), 1)
        self.assertEqual(strict, [])
        self.assertEqual(strict_meta['minimum_support_overlap'], 1.)
        self.assertTrue(any('previous_scale_support_overlap' in scale for scale in normal_meta['scales']))

    def test_numpy_and_tuple_sequences_normalize_to_independent_float_lists(self):
        supplied = {'scale_fractions': np.array([.01, .03, .1], np.float32),
                    'minimum_coherence': np.float64(.4), 'support_quantiles': (.15, .85)}
        normalized = validate_spatial_options(supplied)
        self.assertTrue(all(type(value) is float for value in normalized['scale_fractions']))
        self.assertEqual(normalized['support_quantiles'], [.15, .85])
        normalized['scale_fractions'][0] = .4
        self.assertAlmostEqual(float(supplied['scale_fractions'][0]), .01)
        json.dumps(normalized, allow_nan=False)

    def test_invalid_options_reject_even_for_flat_source(self):
        bad_options = [True, False, [], 0, 'defaults', {'unknown': .2},
                       {'scale_fractions': .1}, {'scale_fractions': [.02]},
                       {'scale_fractions': [.01] * 7}, {'scale_fractions': [[.02], [.04]]},
                       {'scale_fractions': np.array(.02)}, {'scale_fractions': [.04, .02]},
                       {'scale_fractions': [.02, .02]}, {'scale_fractions': [.02, .51]},
                       {'support_quantiles': [.2]}, {'support_quantiles': [.2, .8, .9]},
                       {'support_quantiles': [[.2, .8]]}, {'support_quantiles': [.5, .8]},
                       {'support_quantiles': [.2, .5]}, {'support_quantiles': [.2, 1.]},
                       {'support_quantiles': [.8, .2]}]
        for bad in (True, np.bool_(True), 0, -.1, 1.1, np.nan, np.inf, '0.2', None):
            bad_options.extend([{'minimum_coherence': bad}, {'minimum_support_overlap': bad},
                                {'scale_fractions': [bad, .2]}, {'support_quantiles': [bad, .8]}])
        args = arguments(np.full((32, 40), .5))
        for bad in bad_options:
            with self.subTest(options=bad):
                with self.assertRaises(ValueError):
                    validate_spatial_options(bad)
                with self.assertRaises(ValueError):
                    build_spatial_constraints(*args, spatial_options=bad)

    def test_larger_option_scales_keep_the_existing_resource_limit(self):
        with mock.patch.object(spatial_tones, 'MAX_FILTER_PIXEL_TAPS', 1):
            with self.assertRaisesRegex(ValueError, 'filter resource bound'):
                build_spatial_constraints(*arguments(), spatial_options={'scale_fractions': [.25, .5]})


if __name__ == '__main__':
    unittest.main()
