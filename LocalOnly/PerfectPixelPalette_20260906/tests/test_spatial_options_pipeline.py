"""Spatial controls share one source-support contract across public entry points."""
import copy
import json
import unittest

import numpy as np

from perfect_pixel.boundary_pipeline import BoundaryOptions, get_boundary_pixel
from perfect_pixel.gradient_steps import select_step_palette
from perfect_pixel.gradient_tones import prepare_gradient_tones
from perfect_pixel.highlight_accents import add_highlight_accents
from perfect_pixel.spatial_tones import validate_spatial_options
from perfect_pixel.trigger_pipeline import normalize_triggered


def source():
    image = np.full((48, 64, 4), 255, np.uint8)
    image[..., :3] = np.round(np.linspace(70, 175, 64)).astype(np.uint8)[None, :, None]
    return image


def features():
    return {
        'region_tones': {'enabled': True, 'scope': {'kind': 'all'},
                         'options': {'mode': 'continuous', 'tone_policy': 'spatial_steps'}},
        'highlight_accents': {'enabled': True, 'scope': {'kind': 'all'}, 'options': {}},
        'cell_sampling': {'enabled': True, 'scope': {'kind': 'all'},
                          'options': {'method': 'source_regions'}},
    }


class SpatialOptionsPipelineTests(unittest.TestCase):
    def test_omitted_empty_and_explicit_defaults_are_identical(self):
        image = source()
        baseline = normalize_triggered(image, (16, 12), features=features(), reference=image)
        for options in ({}, validate_spatial_options()):
            config = features()
            config['region_tones']['options']['spatial_options'] = options
            configured = normalize_triggered(image, (16, 12), features=config, reference=image)
            for key in ('image', 'colors_source', 'base_colors_source', 'layer_base',
                        'sampling_source_xy', 'highlight_overlay'):
                np.testing.assert_array_equal(configured[key], baseline[key])
            self.assertEqual(configured['metadata'], baseline['metadata'])

    def test_controls_reach_both_tones_and_highlights_and_boundary_entry(self):
        image = source()
        options = {'scale_fractions': [.02, .05, .1], 'minimum_coherence': .4,
                   'minimum_support_overlap': .75, 'support_quantiles': [.15, .85]}
        original_options = copy.deepcopy(options)
        config = features()
        config['region_tones']['options']['spatial_options'] = options
        result = normalize_triggered(image, (16, 12), features=config, reference=image)
        regions = result['metadata']['features']['region_tones']['region_colors']['regions']
        tone_supports = [group['spatial_support'] for region in regions
                         for group in region['color_groups']]
        highlight_supports = [group['spatial_support'] for group in
                              result['metadata']['features']['highlight_accents']['groups']]
        self.assertTrue(tone_supports)
        self.assertTrue(highlight_supports)
        for support in tone_supports + highlight_supports:
            self.assertEqual(support['scale_fractions'], options['scale_fractions'])
            self.assertEqual(support['minimum_coherence_ratio'], options['minimum_coherence'])
            self.assertEqual(support['minimum_support_overlap'], options['minimum_support_overlap'])
            self.assertEqual(support['support_quantiles'], options['support_quantiles'])
        direct = get_boundary_pixel(image, image, (16, 12), options=BoundaryOptions(
            shading_mode='continuous', tone_policy='spatial_steps', spatial_options=options))
        np.testing.assert_array_equal(direct.flat_image, result['base_colors_source'])
        self.assertEqual(options, original_options)
        json.dumps(result['metadata'], allow_nan=False)

    def test_unknown_and_invalid_controls_reject_before_flat_or_empty_bypass(self):
        image = np.full((4, 4, 4), [120, 120, 120, 0], np.uint8)
        colors = np.array([[120, 120, 120]], np.uint8)
        context = {'positions': np.array([[0, 0]]), 'color_indices': np.array([0])}
        labels = np.full(image.shape[:2], -1, np.int32)
        scope = np.ones(image.shape[:2], bool)
        for options in ({'unknown_control': .5}, {'minimum_coherence': 0}, []):
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    select_step_palette(colors, [1], spatial_context=context, spatial_options=options)
                with self.assertRaises(ValueError):
                    prepare_gradient_tones(image, tone_policy='spatial_steps', spatial_options=options)
                with self.assertRaises(ValueError):
                    add_highlight_accents(image, image, labels, scope, spatial_options=options)
                config = features()
                config['region_tones']['options']['spatial_options'] = options
                with self.assertRaises(ValueError):
                    normalize_triggered(image, (4, 4), features=config, reference=image)

    def test_explicit_controls_require_a_spatial_policy(self):
        image = source()
        colors = np.array([[120, 120, 120]], np.uint8)
        with self.assertRaisesRegex(ValueError, 'spatial_context'):
            select_step_palette(colors, [1], spatial_options={})
        for policy in ('max_error', 'weighted_steps'):
            with self.assertRaisesRegex(ValueError, 'spatial_steps'):
                prepare_gradient_tones(image, tone_policy=policy, spatial_options={})
            with self.assertRaisesRegex(ValueError, 'spatial_steps'):
                BoundaryOptions(shading_mode='continuous', tone_policy=policy,
                                spatial_options={}).validate()
            config = features()
            del config['highlight_accents']
            config['region_tones']['options'].update(tone_policy=policy, spatial_options={})
            with self.assertRaisesRegex(ValueError, 'spatial_steps'):
                normalize_triggered(image, (16, 12), features=config, reference=image)
        with self.assertRaisesRegex(ValueError, 'continuous spatial_steps'):
            BoundaryOptions(spatial_options={}).validate()

    def test_highlight_configuration_cannot_override_shared_spatial_controls(self):
        image = source()
        config = features()
        config['highlight_accents']['options']['spatial_options'] = {}
        with self.assertRaises(ValueError):
            normalize_triggered(image, (16, 12), features=config, reference=image)


if __name__ == '__main__':
    unittest.main()
