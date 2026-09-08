import json
from pathlib import Path
import sys
import unittest
from unittest import mock
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from perfect_pixel.region_palette import color_regions
from perfect_pixel.palette import rgb_to_oklab


class RegionPaletteTests(unittest.TestCase):
    def test_immutability_alpha_exclusion_and_roundtrip(self):
        source = np.array([[[20, 30, 40, 0], [170, 130, 100, 128]],
                           [[120, 80, 50, 255], [90, 60, 40, 255]]], np.uint8)
        labels = np.array([[0, 0], [1, -1]], np.int32)
        ref = np.array([[[210, 175, 140, 255], [255, 0, 255, 0]]], np.uint8)
        copies = source.copy(), labels.copy(), ref.copy()
        out, ids, palette, meta = color_regions(source, labels, ref)
        np.testing.assert_array_equal(source, copies[0])
        np.testing.assert_array_equal(labels, copies[1])
        np.testing.assert_array_equal(ref, copies[2])
        np.testing.assert_array_equal(out[..., 3], source[..., 3])
        np.testing.assert_array_equal(out[0, 0], source[0, 0])
        np.testing.assert_array_equal(out[1, 1], source[1, 1])
        self.assertEqual(ids[0, 0], -1)
        self.assertEqual(ids[1, 1], -1)
        np.testing.assert_array_equal(palette[ids[ids >= 0]], out[..., :3][ids >= 0])
        self.assertNotIn([255, 0, 255], palette.tolist())
        json.dumps(meta, allow_nan=False)

    def test_flat_exact_reference_anchor(self):
        source = np.full((3, 4, 3), [163, 126, 95], np.uint8)
        ref = np.array([[[163, 126, 95], [240, 220, 190]]], np.uint8)
        out, _, _, meta = color_regions(source, np.zeros((3, 4), np.int32), ref)
        np.testing.assert_array_equal(out, source)
        self.assertTrue(meta['regions'][0]['exact_flat_anchor'])

    def test_black_is_not_warmed(self):
        source = np.full((2, 2, 3), [9, 8, 7], np.uint8)
        ref = np.array([[[100, 25, 18], [190, 130, 100]]], np.uint8)
        out, _, _, _ = color_regions(source, np.zeros((2, 2), np.int32), ref)
        np.testing.assert_array_equal(out, source)

    def test_visible_provenance_and_tone_limits(self):
        rng = np.random.default_rng(7)
        source = rng.integers(0, 256, (9, 12, 3), dtype=np.uint8)
        labels = np.repeat(np.arange(3, dtype=np.int32), 4)[None].repeat(9, axis=0)
        ref = rng.integers(0, 256, (12, 12, 3), dtype=np.uint8)
        out, _, palette, meta = color_regions(source, labels, ref)
        allowed = set(map(tuple, source.reshape(-1, 3))) | set(map(tuple, ref.reshape(-1, 3)))
        self.assertTrue(set(map(tuple, palette)) <= allowed)
        for region in meta['regions']:
            self.assertLessEqual(region['source_tone_count'], 3)
            self.assertLessEqual(region['target_tone_count'], 3)
        self.assertEqual(out.shape, source.shape)

    def test_insufficient_reference_tones_do_not_collapse_source(self):
        source = np.array([[[90, 60, 35], [150, 100, 65], [205, 160, 120]]], np.uint8)
        ref = np.array([[[155, 105, 75]]], np.uint8)
        out, _, _, meta = color_regions(source, np.zeros((1, 3), np.int32), ref)
        self.assertEqual(len(np.unique(out.reshape(-1, 3), axis=0)), 3)
        self.assertTrue(np.all(np.diff(rgb_to_oklab(out.astype(float) / 255)[0, :, 0]) > 0))
        self.assertIsNotNone(meta['regions'][0]['fallback_reason'])

    def test_adjacent_distinct_flat_regions_do_not_merge(self):
        source = np.array([[[140, 100, 70], [170, 125, 90]]], np.uint8)
        ref = np.array([[[170, 120, 85]]], np.uint8)
        out, _, _, meta = color_regions(source, np.array([[0, 1]], np.int32), ref)
        self.assertFalse(np.array_equal(out[0, 0], out[0, 1]))
        # Contract v3: do NOT restore arbitrary original-region colors. Repair
        # only within the predeclared fixed bank, or explicitly report failure.
        self.assertEqual(meta['boundary_fallback_regions'], [])
        self.assertTrue(meta['candidate_palette_fixed_before_optimization'])
        self.assertEqual(meta['unresolved_quantized_boundary_pairs'], [])

    def test_pale_region_uses_bright_low_chroma_reference(self):
        source = np.full((8, 8, 3), [215, 195, 165], np.uint8)
        ref = np.array([[[255, 165, 125], [250, 240, 211], [230, 215, 185]]], np.uint8)
        out, _, _, _ = color_regions(source, np.zeros((8, 8), np.int32), ref)
        sl = rgb_to_oklab(source[0, 0].astype(float) / 255)
        tl = rgb_to_oklab(out[0, 0].astype(float) / 255)
        self.assertGreater(tl[0], sl[0])
        self.assertLess(np.linalg.norm(tl[1:]), .075)

    def test_invalid_arguments(self):
        source = np.zeros((2, 2, 3), np.uint8)
        for labels in [np.zeros((1, 2), np.int32), np.zeros((2, 2), float), np.full((2, 2), -2, np.int32)]:
            with self.assertRaises(ValueError):
                color_regions(source, labels, source)
        for tones in [0, 4, True, 2.5]:
            with self.assertRaises(ValueError):
                color_regions(source, np.zeros((2, 2), np.int32), source, tones)
        for value in [-.1, 1.1, True, '.06', float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                color_regions(source, np.zeros((2, 2), np.int32), source,
                              min_retained_tone_delta_l=value)

    def test_design_setting_allows_weak_shading_to_share_a_color(self):
        # Broad min/max caused two representative tones despite a subtle central
        # gradient. Retaining every such pair invented an unwanted color band.
        source = np.array([[[183, 160, 130]] + [[198, 176, 147]] * 49 +
                           [[206, 185, 157]] * 49 + [[224, 206, 184]]], np.uint8)
        reference = np.array([[[233, 200, 160], [245, 226, 193], [244, 237, 211]]], np.uint8)
        labels = np.zeros((1, 100), np.int32)
        before = source.copy()
        old, _, _, old_meta = color_regions(source, labels, reference)
        new, _, _, new_meta = color_regions(source, labels, reference,
                                            min_retained_tone_delta_l=.06)
        self.assertEqual(len(np.unique(old.reshape(-1, 3), axis=0)), 2)
        self.assertEqual(len(np.unique(new.reshape(-1, 3), axis=0)), 1)
        self.assertEqual(old_meta['candidate_palette'], new_meta['candidate_palette'])
        self.assertEqual(new_meta['within_region_tone_order_constraints'], 0)
        self.assertEqual(new_meta['mergeable_weak_tone_pairs'], 1)
        self.assertEqual(new_meta['min_retained_tone_delta_l'], .06)
        np.testing.assert_array_equal(source, before)

    def test_soft_shading_setting_keeps_observed_strong_boundaries(self):
        source = np.array([[[140, 100, 70], [170, 125, 90]]], np.uint8)
        reference = np.array([[[170, 120, 85]]], np.uint8)
        labels = np.array([[0, 1]], np.int32)
        old, _, _, old_meta = color_regions(source, labels, reference)
        new, _, _, new_meta = color_regions(source, labels, reference,
                                            min_retained_tone_delta_l=.06)
        np.testing.assert_array_equal(old, new)
        self.assertFalse(np.array_equal(new[0, 0], new[0, 1]))
        self.assertEqual(old_meta['protected_boundary_count'], new_meta['protected_boundary_count'])

    def test_missing_color_family_retains_source(self):
        source = np.full((3, 4, 3), [40, 100, 180], np.uint8)
        ref = np.array([[[170, 80, 30], [230, 160, 100]]], np.uint8)
        out, _, _, meta = color_regions(source, np.zeros((3, 4), np.int32), ref)
        np.testing.assert_array_equal(out, source)
        self.assertIsNotNone(meta['regions'][0]['fallback_reason'])

    def test_rare_extreme_tones_and_input_label_ids(self):
        source = np.full((1, 100, 3), [140, 90, 55], np.uint8)
        source[0, 0] = [70, 40, 25]
        source[0, -1] = [210, 170, 125]
        ref = np.array([[[160, 100, 60]]], np.uint8)
        out, _, _, meta = color_regions(source, np.full((1, 100), 5000, np.int32), ref)
        self.assertEqual(meta['regions'][0]['region_id'], 5000)
        self.assertEqual(len(np.unique(out.reshape(-1, 3), axis=0)), 3)

    def test_narrow_local_noise_does_not_get_three_tones(self):
        source = np.array([[[210, 195, 165], [212, 197, 167], [214, 199, 169]],
                           [[214, 199, 169], [216, 201, 171], [218, 203, 173]]], np.uint8)
        ref = np.array([[[220, 200, 170], [240, 223, 190], [251, 242, 217]]], np.uint8)
        labels = np.array([[0, 0, 0], [1, 1, 1]], np.int32)
        out, _, _, meta = color_regions(source, labels, ref)
        self.assertEqual([r['source_tone_count'] for r in meta['regions']], [1, 1])
        self.assertEqual(meta['regions'][0]['reference_family'], meta['regions'][1]['reference_family'])
        self.assertEqual(meta['regions'][0]['shared_family_lightness_shift'],
                         meta['regions'][1]['shared_family_lightness_shift'])
        # The repeated common family brightness rule, not local endpoint rank,
        # controls the output. Minor SLIC variation can correctly share a color.
        self.assertLessEqual(len(np.unique(out.reshape(-1, 3), axis=0)), 2)

    def test_rgba_visible_rgb_is_written_after_flattening(self):
        source = np.full((3, 4, 4), [215, 195, 165, 128], np.uint8)
        ref = np.array([[[250, 240, 211]]], np.uint8)
        out, ids, palette, _ = color_regions(source, np.zeros((3, 4), np.int32), ref)
        self.assertFalse(np.array_equal(out[..., :3], source[..., :3]))
        np.testing.assert_array_equal(out[..., 3], source[..., 3])
        np.testing.assert_array_equal(palette[ids], out[..., :3])

    def test_many_regions_cannot_restore_thousands_of_source_colors(self):
        rng = np.random.default_rng(71)
        source = np.clip(rng.normal([175, 135, 95], 18, (25, 32, 3)), 0, 255).astype(np.uint8)
        labels = np.arange(800, dtype=np.int32).reshape(25, 32)
        ref = np.array([[[75, 45, 25], [160, 110, 70], [235, 210, 165]]], np.uint8)
        out, _, palette, meta = color_regions(source, labels, ref)
        fixed = set(map(tuple, meta['candidate_palette']))
        self.assertTrue(set(map(tuple, palette)) <= fixed)
        self.assertLessEqual(len(palette), 150)
        self.assertLessEqual(meta['candidate_palette_count'], meta['total_palette_limit'])
        self.assertFalse(meta['region_original_color_restoration'])
        self.assertTrue(all(len(f['ramp']) <= 3 for f in meta['source_families']))
        self.assertEqual(len(palette), len(np.unique(out.reshape(-1, 3), axis=0)))

    def test_more_than_4096_single_pixel_regions_keep_their_labels(self):
        source = np.full((65, 65, 3), [163, 126, 95], np.uint8)
        labels = np.arange(4225, dtype=np.int32).reshape(65, 65)
        before = source.copy(), labels.copy()
        reference = source[:1, :1].copy()
        out, tone_labels, palette, meta = color_regions(source, labels, reference)
        np.testing.assert_array_equal(source, before[0])
        np.testing.assert_array_equal(labels, before[1])
        np.testing.assert_array_equal(out, source)
        np.testing.assert_array_equal(palette[tone_labels], out)
        self.assertEqual(meta['region_count'], 4225)
        self.assertEqual([r['region_id'] for r in meta['regions']], list(range(4225)))
        self.assertTrue(all(r['source_tone_count'] == 1 for r in meta['regions']))
        self.assertEqual(meta['maximum_regions'], 65536)
        self.assertEqual(meta['tone_node_upper_bound'], 4225)
        self.assertEqual(meta['tone_node_count'], 4225)
        self.assertEqual(meta['cost_array_upper_bound_bytes'], 4225 * 12)
        self.assertEqual(meta['cost_array_peak_storage_bytes'], 4225 * 12)
        self.assertEqual(meta['cost_array_budget_bytes'], 64 * 1024 * 1024)
        self.assertIn('not total working memory', meta['cost_array_budget_scope'])

    def test_cost_budget_fails_before_allocating_region_costs(self):
        source = np.full((1, 2, 3), [163, 126, 95], np.uint8)
        labels = np.array([[0, 1]], np.int32)
        before = source.copy(), labels.copy()
        with mock.patch('perfect_pixel.region_palette._MAX_COST_ARRAY_BYTES', 23):
            with mock.patch('perfect_pixel.region_palette._family_score') as scoring:
                with self.assertRaisesRegex(ValueError, '24 bytes exceeds the 23-byte cost-array budget'):
                    color_regions(source, labels, source)
                scoring.assert_not_called()
        np.testing.assert_array_equal(source, before[0])
        np.testing.assert_array_equal(labels, before[1])

    def test_palette_region_capacity_matches_the_connected_partition(self):
        source = np.full((1, 65537, 3), 120, np.uint8)
        labels = np.arange(65537, dtype=np.int32).reshape(1, 65537)
        with self.assertRaisesRegex(ValueError, '65536 regions exceeds the connected-partition bound'):
            color_regions(source, labels, source[:1, :1])

    def test_incidental_reference_rgb_does_not_anchor_every_pixel(self):
        rng = np.random.default_rng(8)
        ref = np.clip(rng.normal([180, 140, 100], 5, (20, 20, 3)), 0, 255).astype(np.uint8)
        # All original colors occur in the reference; only selected reference
        # representatives may be anchors under the fixed-palette contract.
        labels = np.arange(400, dtype=np.int32).reshape(20, 20)
        _, _, palette, meta = color_regions(ref, labels, ref)
        self.assertLess(len(palette), len(np.unique(ref.reshape(-1, 3), axis=0)))
        anchors = sum(r['exact_flat_anchor'] for r in meta['regions'])
        self.assertLess(anchors, 400)


if __name__ == '__main__':
    unittest.main()
