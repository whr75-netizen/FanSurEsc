"""Spatial tone regressions on synthetic images, without any character coordinates."""
import json
import unittest
from unittest.mock import patch

import numpy as np

from perfect_pixel.boundary_pipeline import BoundaryOptions, get_boundary_pixel
from perfect_pixel.gradient_steps import _lightness_steps, select_step_palette
from perfect_pixel.trigger_pipeline import normalize_triggered


def source():
    gray = np.round(120 + 20 * np.cos(np.linspace(0, 2 * np.pi, 80))).astype(np.uint8)
    image = np.full((64, 80, 4), 255, np.uint8)
    image[..., :3] = gray[None, :, None]
    return image


def features(policy='spatial_steps'):
    return {'region_tones': {'enabled': True, 'scope': {'kind': 'all'},
                            'options': {'mode': 'continuous', 'tone_policy': policy,
                                        'tone_error': .06, 'chroma_error': .06,
                                        'contrast_retention': .65, 'minimum_contrast': .025}},
            'cell_sampling': {'enabled': True, 'scope': {'kind': 'all'},
                              'options': {'method': 'source_regions'}}}


class SpatialPipelineTests(unittest.TestCase):
    def test_structure_lost_by_histogram_error_now_survives(self):
        image = source(); before = image.copy()
        old = normalize_triggered(image, (20, 16), features=features('weighted_steps'), reference=image)
        new = normalize_triggered(image, (20, 16), features=features(), reference=image)
        self.assertEqual(len(np.unique(old['colors_source'][..., :3].reshape(-1, 3), axis=0)), 1)
        self.assertGreater(len(np.unique(new['colors_source'][..., :3].reshape(-1, 3), axis=0)), 1)
        np.testing.assert_array_equal(old['sampling_source_xy'], new['sampling_source_xy'])
        np.testing.assert_array_equal(old['region_tones_result']['region_labels'],
                                      new['region_tones_result']['region_labels'])
        np.testing.assert_array_equal(old['image'][..., 3], new['image'][..., 3])
        np.testing.assert_array_equal(image, before)
        regions = new['metadata']['features']['region_tones']['region_colors']['regions']
        self.assertTrue(any(g['spatially_rejected_candidates'] for r in regions for g in r['color_groups']))
        for region in regions:
            self.assertLessEqual(region['weighted_rmse_l'], .06 + 1e-7)
            for group in region['color_groups']:
                for actual, required in zip(group['retained_support_contrasts'], group['required_support_contrasts']):
                    self.assertGreaterEqual(actual + 1e-9, required)
        json.dumps(new['metadata'], allow_nan=False)
        self.assertTrue(set(map(tuple, new['colors_source'][..., :3].reshape(-1, 3))) <=
                        set(map(tuple, image[..., :3].reshape(-1, 3))))

    def test_output_grid_does_not_change_source_structure_or_palette(self):
        image = source()
        a = normalize_triggered(image, (10, 8), features=features(), reference=image)
        b = normalize_triggered(image, (20, 16), features=features(), reference=image)
        np.testing.assert_array_equal(a['colors_source'], b['colors_source'])
        np.testing.assert_array_equal(a['region_tones_result']['palette'], b['region_tones_result']['palette'])

    def test_shared_public_entry_points_use_same_shading(self):
        image = source()
        direct = get_boundary_pixel(image, image, (20, 16),
                                    options=BoundaryOptions(shading_mode='continuous', tone_policy='spatial_steps'))
        scoped = normalize_triggered(image, (20, 16), features=features(), reference=image)
        np.testing.assert_array_equal(direct.flat_image, scoped['colors_source'])

    def test_source_2x_repeat_keeps_synthetic_step_count(self):
        image = source(); larger = np.repeat(np.repeat(image, 2, axis=0), 2, axis=1)
        a = normalize_triggered(image, (20, 16), features=features(), reference=image)
        b = normalize_triggered(larger, (20, 16), features=features(), reference=larger)
        self.assertEqual(len(a['region_tones_result']['palette']), len(b['region_tones_result']['palette']))

    def test_flat_color_tiny_accent_alpha_and_scope_survive(self):
        image = np.full((24, 32, 4), [210, 180, 140, 255], np.uint8)
        image[:2] = [70, 80, 90, 0]
        image[8, 11] = [5, 7, 3, 255]
        cfg = features()
        cfg['region_tones']['scope'] = {'kind': 'rectangles', 'rectangles': [[2, 2, 25, 20]]}
        result = normalize_triggered(image, (32, 24), features=cfg, reference=image)
        np.testing.assert_array_equal(result['colors_source'], image)
        np.testing.assert_array_equal(result['image'][8, 11], image[8, 11])

    def test_bad_options_reject_even_when_no_visible_pixels(self):
        image = source(); image[..., 3] = 0
        for name in ('contrast_retention', 'minimum_contrast'):
            for bad in (0, -1, True, np.bool_(True), float('nan'), 1.1):
                cfg = features(); cfg['region_tones']['options'][name] = bad
                with self.assertRaises(ValueError):
                    normalize_triggered(image, (20, 16), features=cfg, reference=image)

    def test_dp_rejects_flat_candidate_and_measures_actual_fixed_support(self):
        values = np.array([.2, .3, .4]); weights = np.array([50., 1., 50.])
        guard = {'coefficients': np.array([-1., 0., 1.]), 'minimum_contrast': .13}
        selected, labels, meta = _lightness_steps(values, weights, .2, constraints=[guard])
        self.assertEqual(len(selected), 2)
        self.assertEqual(meta['spatially_rejected_candidates'], 1)
        self.assertGreaterEqual(float(guard['coefficients'] @ values[selected][labels]), .13)
        self.assertIn('NOT global', meta['minimum_k_scope'])
        with patch('perfect_pixel.gradient_steps.MAX_DP_TRANSITIONS', 6):
            with self.assertRaisesRegex(ValueError, 'transition budget'):
                _lightness_steps(values, weights, .2, constraints=[guard])

    def test_inconsistent_spatial_context_cannot_change_histogram_or_duplicate_pixel(self):
        colors = np.array([[100, 100, 100], [130, 130, 130]], np.uint8)
        for context in (
            {'positions': [[0, 0], [0, 0]], 'color_indices': [0, 1]},
            {'positions': [[0, 0], [1, 0]], 'color_indices': [0, 0]},
            {'positions': [[0, 0], [1, 0]], 'color_indices': [0, 2]},
        ):
            with self.assertRaises(ValueError):
                select_step_palette(colors, [1, 1], spatial_context=context)


if __name__ == '__main__': unittest.main()
