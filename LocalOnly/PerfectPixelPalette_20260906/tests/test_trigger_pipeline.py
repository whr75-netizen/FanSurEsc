import unittest
from unittest.mock import patch
import numpy as np
from perfect_pixel.trigger_pipeline import normalize_triggered, source_palette, sample_scoped, compose_lines, cleanup_mask


class TriggerPipelineTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(3)
        self.im = rng.integers(0, 256, (16, 20, 4), dtype=np.uint8)
        self.im[..., 3] = 255
        self.im[:3, :, 3] = 0
        self.rect = {'kind': 'rectangles', 'rectangles': [[5, 4, 15, 12]]}

    def test_all_off_is_exact_identity_including_hidden_rgb(self):
        with patch('perfect_pixel.trigger_pipeline.source_palette', side_effect=AssertionError):
            r = normalize_triggered(self.im, (20,16))
        np.testing.assert_array_equal(r['image'], self.im)

    def test_missing_scope_rejected(self):
        with self.assertRaises(ValueError):
            normalize_triggered(self.im, (20,16), features={'region_colors': {'enabled': True}})

    def test_scope_is_target_and_source_boundary(self):
        r = normalize_triggered(self.im, (20,16), features={'region_colors': {
            'enabled': True, 'scope': self.rect, 'options': {'colors': 4}}})
        mask = r['scopes']['region_colors']
        np.testing.assert_array_equal(r['image'][~mask], self.im[~mask])
        self.assertTrue(np.any(r['image'][mask] != self.im[mask]))

    def test_palette_colors_are_observed_opaque_colors(self):
        mask = np.ones(self.im.shape[:2], bool)
        r, meta = source_palette(self.im, mask, colors=8)
        observed = set(map(tuple, self.im[..., :3][self.im[..., 3] == 255]))
        self.assertTrue(set(map(tuple, meta['palette'])) <= observed)
        self.assertLessEqual(len(np.unique(r[..., :3][r[..., 3] == 255], axis=0)), 8)

    def test_hidden_rgb_has_no_palette_influence(self):
        im = self.im.copy()
        im[im[..., 3] == 0, :3] = 255 - im[im[..., 3] == 0, :3]
        cfg = {'region_colors': {'enabled': True, 'scope': {'kind':'all'}, 'options': {'colors':8}}}
        a = normalize_triggered(self.im, (20,16), features=cfg)
        b = normalize_triggered(im, (20,16), features=cfg)
        np.testing.assert_array_equal(a['image'], b['image'])

    def test_explicit_erase_only_erases_its_scope(self):
        r = normalize_triggered(self.im, (20,16), features={'mask_cleanup': {
            'enabled': True, 'scope': self.rect}})
        m = r['scopes']['mask_cleanup']
        self.assertFalse(r['image'][m].any())
        np.testing.assert_array_equal(r['image'][~m], self.im[~m])

    def test_alpha_not_implicitly_thresholded(self):
        self.im[5,5,3] = 127
        with self.assertRaises(ValueError):
            normalize_triggered(self.im, (20,16))

    def test_color_vote_ignores_hidden_rgb(self):
        im = np.zeros((2,2,4), np.uint8)
        im[0,0] = [220,50,20,255]
        im[0,1] = [220,50,20,255]
        im[1] = [0,255,255,0]
        r = sample_scoped(im, (1,1), np.ones((2,2), bool), coverage=.5)
        np.testing.assert_array_equal(r[0,0], [220,50,20,255])

    def test_scale_is_immutable_base_not_previous_output(self):
        a = normalize_triggered(self.im, (10,8), '1.2')['image']
        b = normalize_triggered(self.im, (10,8), '.9')['image']
        self.assertEqual(a.shape, (9,12,4))
        self.assertEqual(b.shape, (7,9,4))

    def test_unknown_feature_and_option_rejected(self):
        for cfg in [{'line':{}}, {'region_colors':{'enabled':True, 'scope':self.rect, 'options':{'random':3}}}]:
            with self.assertRaises(ValueError):
                normalize_triggered(self.im, (20,16), features=cfg)

    def test_no_upscaling_hidden_fallback(self):
        with self.assertRaises(ValueError):
            normalize_triggered(self.im, (40,32))

    def test_seeded_cleanup_restricts_color_and_connectivity(self):
        a = np.full((8,8,4), [80,120,240,255], np.uint8)
        a[1:3,1:3] = [190,150,120,255]
        a[5:7,5:7] = [190,150,120,255]
        scope = np.ones((8,8),bool)
        m = cleanup_mask(a, scope, mode='color_connected', seeds=[[1,1]])
        self.assertEqual(int(m.sum()),4)
        self.assertFalse(m[5,5])
        self.assertFalse(m[0,0])

    def test_seed_outside_scope_or_transparent_is_not_guessed(self):
        with self.assertRaises(ValueError):
            cleanup_mask(self.im, np.zeros((16,20),bool), mode='color_connected', seeds=[[5,5]])

    def test_explicit_delete_wins_over_coverage_vote(self):
        a = np.full((2,2,4), [100,100,100,255], np.uint8)
        cfg = {'mask_cleanup': {'enabled': True, 'scope': {'kind':'rectangles','rectangles':[[1,1,2,2]]}},
               'cell_sampling': {'enabled': True, 'scope': {'kind':'all'}}}
        r = normalize_triggered(a, (1,1), features=cfg)
        self.assertFalse(r['image'].any())

    def test_line_replaces_mixed_support_not_double_overlay(self):
        im = np.full((4,4,4), [200,200,200,255], np.uint8)
        im[0:2,0] = [30,30,30,255]
        base = np.full((2,2,4), [200,200,200,255], np.uint8)
        base[0,0] = [30,30,30,255]
        support = np.zeros((4,4), bool); support[:2,0:2] = True; support[0,1] = False
        data = {'target_mask':np.zeros((2,2),bool), 'collision_mask':np.zeros((2,2),bool),
                'source_candidate':support, 'source_xy':np.full((2,2,2),-1,int)}
        r, meta = compose_lines(base, im, data, np.ones((4,4),bool), (2,2))
        np.testing.assert_array_equal(r[0,0], [200,200,200,255])
        self.assertEqual(meta['replaced_mixed_support_cells'], 1)

    def test_line_cleanup_uses_vote_provenance_not_cell_center(self):
        im = np.full((2,2,4), [30,30,30,255], np.uint8)
        im[1,1] = [200,200,200,255]
        scope = np.ones((2,2),bool)
        support = scope.copy(); support[1,1] = False
        base, xy = sample_scoped(im, (1,1), scope, return_source_xy=True)
        data = {'target_mask':np.zeros((1,1),bool), 'collision_mask':np.zeros((1,1),bool),
                'source_candidate':support, 'source_xy':np.full((1,1,2),-1,int)}
        r, meta = compose_lines(base, im, data, scope, (1,1), xy)
        np.testing.assert_array_equal(r[0,0], [200,200,200,255])
        self.assertEqual(meta['replaced_mixed_support_cells'], 1)

    def test_line_mode_must_be_explicitly_known(self):
        with self.assertRaises(ValueError):
            normalize_triggered(self.im, (20,16), features={'line_normalization':{
                'enabled':True, 'scope':{'kind':'all'}, 'options':{'mode':'guess'}}})

    def test_line_first_geometry_precedes_palette_and_is_independent(self):
        a = np.full((40,40,4), [180,190,205,255], np.uint8)
        a[10:31,10:31] = [230,170,130,255]
        a[10:31,10:12] = a[10:31,29:31] = [30,40,50,255]
        a[10:12,10:31] = a[29:31,10:31] = [30,40,50,255]
        cfg = {'line_normalization':{'enabled':True, 'scope':{'kind':'all'},
                                    'options':{'mode':'line_first', 'min_component_pixels':2}}}
        raw = normalize_triggered(a,(20,20),features=cfg)
        cfg['region_colors'] = {'enabled':True,'scope':{'kind':'all'}, 'options':{'colors':2}}
        colored = normalize_triggered(a,(20,20),features=cfg)
        for key in ['fixed_line_mask','target_owners']:
            np.testing.assert_array_equal(raw['line_geometry'][key],colored['line_geometry'][key])
        original_colors = set(map(tuple,a[...,:3].reshape(-1,3)))
        final_colors = set(map(tuple,colored['image'][...,:3][colored['image'][...,3]==255]))
        self.assertTrue(final_colors <= original_colors)

    def test_sampling_option_cannot_change_another_scope_geometry(self):
        a = np.full((20,20,4),[130,180,220,255],np.uint8)
        a[:3,:,3] = 0
        cfg = {'cell_sampling':{'enabled':True,'scope':{'kind':'rectangles','rectangles':[[0,0,5,5]]},'options':{'coverage':.1}},
               'line_normalization':{'enabled':True,'scope':{'kind':'rectangles','rectangles':[[10,10,20,20]]},'options':{'mode':'line_first'}}}
        first = normalize_triggered(a,(10,10),features=cfg)
        cfg['cell_sampling']['options']['coverage'] = .9
        second = normalize_triggered(a,(10,10),features=cfg)
        np.testing.assert_array_equal(first['line_geometry']['target_foreground'],second['line_geometry']['target_foreground'])
        np.testing.assert_array_equal(first['line_geometry']['target_owners'],second['line_geometry']['target_owners'])


if __name__ == '__main__': unittest.main()
