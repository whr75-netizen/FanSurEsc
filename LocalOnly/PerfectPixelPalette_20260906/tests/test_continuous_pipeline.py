"""Whole gradient path regressions: never supply artificial single-region labels."""
import unittest
from unittest.mock import patch
import numpy as np
from perfect_pixel.boundary_pipeline import prepare_region_tones, get_boundary_pixel, BoundaryOptions
from perfect_pixel.trigger_pipeline import normalize_triggered


def source():
    image = np.full((12, 64, 4), 255, np.uint8)
    image[..., :3] = np.linspace(40, 225, 64).round().astype(np.uint8)[None, :, None]
    return image


def features(error=.06):
    return {'region_tones': {'enabled': True, 'scope': {'kind': 'all'},
                            'options': {'mode': 'continuous', 'color_error': error}},
            'cell_sampling': {'enabled': True, 'scope': {'kind': 'all'},
                              'options': {'method': 'source_regions'}}}


class ContinuousIntegrationTests(unittest.TestCase):
    def test_output_grid_cannot_refit_source_domains_or_colors(self):
        image = source()
        results = []
        with patch('perfect_pixel.boundary_regions.segment_regions', side_effect=AssertionError('SLIC must not run')):
            for grid in ((8, 2), (16, 4), (32, 6)):
                results.append(normalize_triggered(image, grid, features=features(), reference=image))
        for result in results[1:]:
            np.testing.assert_array_equal(results[0]['colors_source'], result['colors_source'])
            for key in ('region_labels', 'tone_map', 'palette'):
                np.testing.assert_array_equal(results[0]['region_tones_result'][key],
                                              result['region_tones_result'][key])
        self.assertEqual(results[0]['region_tones_result']['metadata']['segmentation']['region_count'], 1)

    def test_stretching_full_pipeline_keeps_the_same_tones(self):
        image = source()
        larger = np.repeat(image, 8, axis=1)
        a = normalize_triggered(image, (16, 3), features=features(), reference=image)
        b = normalize_triggered(larger, (16, 3), features=features(), reference=larger)
        np.testing.assert_array_equal(np.repeat(a['colors_source'], 8, axis=1), b['colors_source'])
        np.testing.assert_array_equal(a['region_tones_result']['palette'], b['region_tones_result']['palette'])

    def test_shading_strength_never_changes_raw_sample_coordinates(self):
        image = source()
        a = normalize_triggered(image, (16, 3), features=features(.025), reference=image)
        b = normalize_triggered(image, (16, 3), features=features(.09), reference=image)
        raw = normalize_triggered(image, (16, 3), features={'cell_sampling': features()['cell_sampling']})
        for result in (b, raw):
            np.testing.assert_array_equal(a['sampling_source_xy'], result['sampling_source_xy'])
            np.testing.assert_array_equal(a['image'][..., 3], result['image'][..., 3])

    def test_public_entry_points_share_the_same_continuous_stage(self):
        image = source()
        direct = get_boundary_pixel(image, image, (16, 3),
                                    options=BoundaryOptions(shading_mode='continuous'))
        scoped = normalize_triggered(image, (16, 3), features=features(), reference=image)
        np.testing.assert_array_equal(direct.flat_image, scoped['colors_source'])
        np.testing.assert_array_equal(direct.region_labels, scoped['region_tones_result']['region_labels'])

    def test_explicit_scope_and_original_alpha_are_preserved(self):
        image = source(); image[0] = 0
        cfg = features()
        cfg['region_tones']['scope'] = {'kind': 'rectangles', 'rectangles': [[8, 0, 48, 12]]}
        before = image.copy()
        result = normalize_triggered(image, (64, 12), features=cfg, reference=image)
        mask = result['scopes']['region_tones']
        np.testing.assert_array_equal(result['colors_source'][~mask], image[~mask])
        np.testing.assert_array_equal(result['colors_source'][..., 3], image[..., 3])
        np.testing.assert_array_equal(image, before)

    def test_external_style_reference_is_not_silently_ignored(self):
        image = source(); reference = image.copy(); reference[..., :3] = [220, 130, 140]
        with self.assertRaisesRegex(ValueError, 'unmodified source'):
            prepare_region_tones(image, reference, (16, 3), mode='continuous')


if __name__ == '__main__': unittest.main()
