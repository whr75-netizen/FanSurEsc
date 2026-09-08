"""Highlight-only integration must preserve the previously rendered base."""
import json
import unittest

import numpy as np

from perfect_pixel.palette import rgb_to_oklab
from perfect_pixel.trigger_pipeline import normalize_triggered


def source():
    image = np.full((64, 80, 4), 255, np.uint8)
    image[..., :3] = np.round(np.linspace(70, 175, 80)).astype(np.uint8)[None, :, None]
    return image


def features(highlight=True):
    cfg = {'region_tones': {'enabled': True, 'scope': {'kind': 'all'},
                            'options': {'mode': 'continuous', 'tone_policy': 'spatial_steps'}},
           'cell_sampling': {'enabled': True, 'scope': {'kind': 'all'},
                             'options': {'method': 'source_regions'}}}
    if highlight:
        cfg['highlight_accents'] = {'enabled': True, 'scope': {'kind': 'all'},
                                    'options': {'minimum_contrast': .025}}
    return cfg


class HighlightPipelineTests(unittest.TestCase):
    def test_overlay_only_frozen_base_coordinates_alpha_and_observed_colors(self):
        image = source(); original = image.copy()
        old = normalize_triggered(image, (20, 16), features=features(False), reference=image)
        new = normalize_triggered(image, (20, 16), features=features(), reference=image)
        np.testing.assert_array_equal(image, original)
        np.testing.assert_array_equal(new['layer_base'], old['image'])
        np.testing.assert_array_equal(new['sampling_source_xy'], old['sampling_source_xy'])
        np.testing.assert_array_equal(new['base_colors_source'], old['colors_source'])
        np.testing.assert_array_equal(new['image'][..., 3], old['image'][..., 3])
        active = new['highlight_overlay'][..., 3] == 255
        self.assertGreater(int(active.sum()), 0)
        np.testing.assert_array_equal(new['image'][~active], old['image'][~active])
        assembled = old['image'].copy(); assembled[active] = new['highlight_overlay'][active]
        np.testing.assert_array_equal(assembled, new['image'])
        old_l = rgb_to_oklab(old['image'][..., :3].astype(np.float32) / 255)[..., 0]
        new_l = rgb_to_oklab(new['image'][..., :3].astype(np.float32) / 255)[..., 0]
        self.assertTrue(np.all(new_l[active] > old_l[active]))
        self.assertTrue(set(map(tuple, new['image'][active, :3])) <=
                        set(map(tuple, image[..., :3].reshape(-1, 3))))
        json.dumps(new['metadata'], allow_nan=False)

    def test_overlay_source_is_independent_of_native_grid(self):
        image = source()
        a = normalize_triggered(image, (10, 8), features=features(), reference=image)
        b = normalize_triggered(image, (20, 16), features=features(), reference=image)
        np.testing.assert_array_equal(a['colors_source'], b['colors_source'])
        np.testing.assert_array_equal(a['highlight_result']['overlay'], b['highlight_result']['overlay'])

    def test_flat_and_white_are_not_given_invented_highlights(self):
        for rgb in ([255, 255, 255], [120, 90, 70]):
            image = np.full((32, 40, 4), [*rgb, 255], np.uint8)
            new = normalize_triggered(image, (40, 32), features=features(), reference=image)
            np.testing.assert_array_equal(new['image'], image)
            self.assertFalse(new['highlight_overlay'].any())

    def test_explicit_highlight_scope_and_erased_alpha_are_preserved(self):
        image = source(); image[:4] = 0
        cfg = features()
        cfg['highlight_accents']['scope'] = {'kind': 'rectangles', 'rectangles': [[60, 16, 80, 40]]}
        cfg['mask_cleanup'] = {'enabled': True, 'scope': {'kind': 'rectangles', 'rectangles': [[75, 16, 80, 40]]},
                               'options': {'mode': 'erase'}}
        old_cfg = json.loads(json.dumps(cfg)); del old_cfg['highlight_accents']
        old = normalize_triggered(image, (80, 64), features=old_cfg, reference=image)
        new = normalize_triggered(image, (80, 64), features=cfg, reference=image)
        scope = new['scopes']['highlight_accents']
        np.testing.assert_array_equal(old['image'][~scope], new['image'][~scope])
        np.testing.assert_array_equal(new['layer_base'], old['image'])
        np.testing.assert_array_equal(old['image'][..., 3], new['image'][..., 3])
        self.assertFalse(new['highlight_overlay'][:4].any())

    def test_wrong_base_or_different_color_group_contract_is_rejected(self):
        image = source()
        invalid = []
        cfg = features(); cfg['region_tones']['options']['tone_policy'] = 'weighted_steps'; invalid.append(cfg)
        cfg = features(); cfg['highlight_accents']['options']['chroma_error'] = .1; invalid.append(cfg)
        cfg = features(); cfg['region_tones']['scope'] = {'kind': 'rectangles', 'rectangles': [[1, 1, 20, 20]]}; invalid.append(cfg)
        for cfg in invalid:
            with self.assertRaises(ValueError):
                normalize_triggered(image, (20, 16), features=cfg, reference=image)


if __name__ == '__main__': unittest.main()
