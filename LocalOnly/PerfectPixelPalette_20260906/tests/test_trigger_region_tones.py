"""Public pipeline contracts, not a character-specific appearance score."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / '.deps'))
sys.path.insert(0, str(root / 'src'))
import numpy as np
from perfect_pixel.boundary_pipeline import prepare_region_tones, get_boundary_pixel, BoundaryOptions
from perfect_pixel.region_palette import color_regions
from perfect_pixel.trigger_pipeline import normalize_triggered


def features(tones=3):
    return {'region_tones': {'enabled': True, 'scope': {'kind': 'all'},
                             'options': {'tones': tones, 'min_retained_tone_delta_l': .06}},
            'cell_sampling': {'enabled': True, 'scope': {'kind': 'all'},
                              'options': {'method': 'source_regions', 'coverage': .5,
                                          'color_edge_threshold': .08}}}


def gradient(width=32):
    image = np.full((8, width, 4), 255, np.uint8)
    ramp = np.linspace(30, 230, width).round().astype(np.uint8)
    image[..., :3] = ramp[None, :, None]
    return image


class RegionTonePipelineTests(unittest.TestCase):
    def test_both_entry_points_use_identical_source_shading(self):
        image = gradient()
        direct = get_boundary_pixel(image, image, (8, 2), options=BoundaryOptions(
            tones=3, min_retained_tone_delta_l=.06))
        scoped = normalize_triggered(image, (8, 2), features=features(), reference=image)
        np.testing.assert_array_equal(direct.flat_image, scoped['colors_source'])
        np.testing.assert_array_equal(direct.region_labels, scoped['region_tones_result']['region_labels'])
        np.testing.assert_array_equal(image, gradient())
        self.assertIsNone(scoped['metadata']['features']['region_tones']['fallback_algorithm'])

    def test_tone_changes_cannot_move_sample_coordinates(self):
        image = gradient()
        a = normalize_triggered(image, (8, 2), features=features(1), reference=image)
        b = normalize_triggered(image, (8, 2), features=features(3), reference=image)
        np.testing.assert_array_equal(a['sampling_source_xy'], b['sampling_source_xy'])
        np.testing.assert_array_equal(a['image'][..., 3], b['image'][..., 3])

    def test_unsupported_contracts_fail_before_processing(self):
        image = gradient()
        configurations = []
        both = features(); both['region_colors'] = {'enabled': True, 'scope': {'kind': 'all'}}
        configurations.append(both)
        wrong_sampler = features(); wrong_sampler['cell_sampling']['options']['method'] = 'rgb_vote'
        configurations.append(wrong_sampler)
        lines = features(); lines['line_normalization'] = {'enabled': True, 'scope': {'kind': 'all'}}
        configurations.append(lines)
        for cfg in configurations:
            with self.assertRaises(ValueError):
                normalize_triggered(image, (8, 2), features=cfg, reference=image)
        with self.assertRaisesRegex(ValueError, 'explicit reference'):
            normalize_triggered(image, (8, 2), features=features())

    def test_failure_propagates_without_palette_fallback(self):
        image = gradient()
        with patch('perfect_pixel.boundary_pipeline.prepare_region_tones', side_effect=ValueError('capacity failure')):
            with patch('perfect_pixel.trigger_pipeline.source_palette') as alternate:
                with self.assertRaisesRegex(ValueError, 'capacity failure'):
                    normalize_triggered(image, (8, 2), features=features(), reference=image)
                alternate.assert_not_called()

    def test_scope_and_alpha_remain_unchanged(self):
        image = gradient(); image[:, :2] = 0
        cfg = features()
        selected = {'kind': 'rectangles', 'rectangles': [[4, 0, 20, 8]]}
        cfg['region_tones']['scope'] = cfg['cell_sampling']['scope'] = selected
        result = normalize_triggered(image, (32, 8), features=cfg, reference=image)
        mask = result['scopes']['region_tones']
        np.testing.assert_array_equal(result['image'][~mask], image[~mask])
        np.testing.assert_array_equal(result['colors_source'][..., 3], image[..., 3])

    def test_stretching_one_gradient_does_not_invent_more_tones(self):
        original = gradient(32)
        stretched = np.repeat(original, 8, axis=1)
        outputs = []
        for image in (original, stretched):
            flat, _, _, meta = color_regions(image, np.zeros(image.shape[:2], np.int32),
                original, tones=3, min_retained_tone_delta_l=.06)
            self.assertLessEqual(meta['regions'][0]['target_tone_count'], 3)
            self.assertEqual(meta['regions'][0]['source_tone_count'], 3)
            outputs.append(flat)
        np.testing.assert_array_equal(np.repeat(outputs[0], 8, axis=1), outputs[1])

    def test_disabled_mode_stays_byte_identical(self):
        image = gradient()
        cfg = {'region_tones': {'enabled': False}}
        result = normalize_triggered(image, (32, 8), features=cfg)
        np.testing.assert_array_equal(result['image'], image)


if __name__ == '__main__':
    unittest.main()
