import json
from pathlib import Path
import sys
import unittest
from unittest import mock

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / '.deps'))
sys.path.insert(0, str(root / 'src'))
import numpy as np
from perfect_pixel.boundary_regions import segment_regions


class BoundaryRegionTests(unittest.TestCase):
    def test_uniform_region_merges_and_inputs_are_unchanged(self):
        source = np.full((36, 42, 3), (140, 170, 190), np.uint8)
        before = source.copy()
        labels, edge, meta = segment_regions(source, (7, 6))
        np.testing.assert_array_equal(source, before)
        self.assertEqual(labels.dtype, np.int32)
        self.assertEqual(edge.dtype, np.float32)
        self.assertEqual(labels.shape, source.shape[:2])
        self.assertEqual(meta['region_count'], 1)
        self.assertEqual(float(edge.max()), 0)
        json.dumps(meta, allow_nan=False)

    def test_deterministic(self):
        source = np.full((32, 35, 3), (180, 170, 160), np.uint8)
        source[7:19, 13:23] = (60, 80, 130)
        a, ea, ma = segment_regions(source, (6, 6))
        b, eb, mb = segment_regions(source, (6, 6))
        np.testing.assert_array_equal(a, b)
        np.testing.assert_array_equal(ea, eb)
        self.assertEqual(ma, mb)

    def test_alpha_and_disconnected_identical_colors(self):
        source = np.full((24, 32, 4), (130, 170, 190, 255), np.uint8)
        source[:, 14:18, 3] = 0
        source[0, 0, 3] = 1
        source[0, 1, 3] = 128
        before = source.copy()
        labels, edge, meta = segment_regions(source, (6, 4))
        self.assertTrue(np.all(labels[:, 14:18] == -1))
        self.assertTrue(np.all(edge[:, 14:18] == 0))
        self.assertNotEqual(labels[10, 5], labels[10, 25])
        self.assertGreaterEqual(labels[0, 0], 0)
        np.testing.assert_array_equal(source, before)
        changed_hidden = source.copy()
        changed_hidden[:, 14:18, :3] = (255, 0, 230)
        again, _, _ = segment_regions(changed_hidden, (6, 4))
        np.testing.assert_array_equal(labels, again)

    def test_isoluminant_chromatic_boundary_is_present(self):
        from skimage.color import lab2rgb, rgb2lab
        rgb = np.rint(lab2rgb(np.array([[[60, 30, 0], [60, -30, 0]]], float)) * 255).astype(np.uint8)
        self.assertLess(abs(float(rgb2lab(rgb)[0, 0, 0] - rgb2lab(rgb)[0, 1, 0])), 1)
        source = np.empty((30, 30, 3), np.uint8)
        source[:, :15] = rgb[0, 0]
        source[:, 15:] = rgb[0, 1]
        labels, edge, _ = segment_regions(source, (5, 5))
        self.assertGreater(float(edge[:, 14:16].mean()), .8)
        self.assertNotEqual(labels[15, 5], labels[15, 25])

    def test_one_and_two_pixel_high_contrast_features_survive(self):
        for side in (1, 2):
            source = np.full((32, 32, 3), (190, 190, 190), np.uint8)
            source[15:15 + side, 15:15 + side] = (20, 40, 100)
            labels, edge, meta = segment_regions(source, (2, 2))
            feature = labels[15, 15]
            self.assertNotEqual(feature, labels[10, 10])
            self.assertEqual(int(np.sum(labels == feature)), side * side)
            self.assertFalse(meta['minimum_area_pruning'])

    def test_every_label_is_four_connected(self):
        from scipy.ndimage import label
        source = np.full((30, 30, 3), (130, 160, 180), np.uint8)
        source[4:9, 4:9] = (220, 120, 80)
        source[20:25, 20:25] = (220, 120, 80)
        labels, _, _ = segment_regions(source, (5, 5))
        for region in np.unique(labels):
            self.assertEqual(label(labels == region)[1], 1)

    def test_empty_visibility_tiny_shapes_and_validation(self):
        source = np.zeros((2, 3, 4), np.uint8)
        labels, edge, meta = segment_regions(source)
        self.assertTrue(np.all(labels == -1))
        self.assertEqual(meta['region_count'], 0)
        for shape in ((1, 1, 3), (1, 8, 3), (8, 1, 3)):
            labels, _, meta = segment_regions(np.full(shape, 120, np.uint8), (1, 1))
            self.assertEqual(meta['region_count'], 1)
        for grid in ((0, 2), (True, 2), (2.5, 2), (4096, 4096), (1,)):
            with self.assertRaises(ValueError): segment_regions(source, grid)
        with self.assertRaises(ValueError): segment_regions(source.astype(float))

    def test_pixel_and_region_bounds_fail_without_pruning(self):
        huge = np.broadcast_to(np.zeros((1, 1, 3), np.uint8), (2049, 2048, 3))
        with self.assertRaisesRegex(ValueError, 'no hidden resize'):
            segment_regions(huge)
        # Truly disconnected alpha islands cannot be merged, unlike texture.
        source = np.zeros((513, 513, 4), np.uint8)
        source[::2, ::2] = (120, 120, 120, 255)
        with self.assertRaisesRegex(ValueError, 'no small-region pruning'):
            segment_regions(source, (1, 1))
        source = np.zeros((129, 129, 4), np.uint8)
        source[::2, ::2] = (120, 120, 120, 255)
        with self.assertRaisesRegex(ValueError, 'downstream 4096-region bound'):
            segment_regions(source, (1, 1))

    def test_dense_high_frequency_texture_is_not_permanent_regions(self):
        stripes = np.tile((np.arange(48) % 2 * 255).astype(np.uint8), (48, 1))
        source = np.repeat(stripes[..., None], 3, axis=2)
        labels, edge, meta = segment_regions(source, (6, 6))
        self.assertLess(meta['region_count'], 48)
        self.assertEqual(meta['microfeature_pixel_count'], 0)
        self.assertFalse(meta['minimum_area_pruning'])

    def test_missing_dependency_is_an_explicit_failure(self):
        original_import = __import__
        def missing(name, *args, **kwargs):
            if name == 'skimage':
                raise ImportError('synthetic dependency absence')
            return original_import(name, *args, **kwargs)
        source = np.full((4, 4, 3), 120, np.uint8)
        with mock.patch('builtins.__import__', side_effect=missing):
            with self.assertRaisesRegex(ImportError, 'no alternate segmentation'):
                segment_regions(source)


if __name__ == '__main__':
    unittest.main()
