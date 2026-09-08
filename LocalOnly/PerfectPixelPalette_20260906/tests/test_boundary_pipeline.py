import sys
from pathlib import Path
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from perfect_pixel.boundary_pipeline import BoundaryOptions, sample_region_grid, get_boundary_pixel


class BoundarySamplerTests(unittest.TestCase):
    def test_selects_region_before_tones_and_does_not_mix_rgb(self):
        image = np.full((2, 5, 3), 100, np.uint8)
        labels = np.array([[0, 0, 0, 1, 1], [0, 0, 0, 1, 1]], np.int32)
        tones = np.array([[0, 1, 2, 3, 3], [0, 1, 2, 3, 3]], np.int32)
        palette = np.array([[20, 30, 40], [30, 40, 50], [40, 50, 60], [240, 0, 30]], np.uint8)
        out, regions, picked, meta = sample_region_grid(image, labels, tones, palette,
            (np.array([0., 5.]), np.array([0., 2.])), (1, 1), 0)
        self.assertEqual(regions[0, 0], 0)
        self.assertIn(picked[0, 0], [0, 1, 2])
        np.testing.assert_array_equal(out[0, 0, :3], palette[picked[0, 0]])
        self.assertEqual(meta['mixed_region_cells'], 1)

    def test_alpha_coverage_independent_of_feature_preference(self):
        image = np.zeros((4, 4, 4), np.uint8)
        image[0, 0] = [255, 255, 255, 255]
        labels = np.full((4, 4), -1, np.int32); labels[0, 0] = 0
        tones = labels.copy()
        palette = np.array([[255, 255, 255]], np.uint8)
        out, regions, _, _ = sample_region_grid(image, labels, tones, palette,
            (np.array([0., 4.]), np.array([0., 4.])), (1, 1), 3)
        self.assertEqual(out[0, 0, 3], 0)
        self.assertEqual(regions[0, 0], -1)

    def test_disjoint_regions_sharing_same_rgb_remain_labeled(self):
        image = np.full((2, 4, 3), 80, np.uint8)
        labels = np.array([[0, 0, 1, 1], [0, 0, 1, 1]], np.int32)
        palette = np.array([[80, 80, 80]], np.uint8)
        out, regions, _, _ = sample_region_grid(image, labels, np.zeros_like(labels), palette,
            (np.array([0., 2., 4.]), np.array([0., 2.])), (2, 1), 0)
        np.testing.assert_array_equal(regions, [[0, 1]])
        np.testing.assert_array_equal(out[..., :3], np.full((1, 2, 3), 80, np.uint8))

    def test_subelement_grid_keeps_exact_dimensions(self):
        image = np.array([[[20, 60, 80, 255]]], np.uint8)
        palette = image[0, :, :3]
        zeros = np.zeros((1, 1), np.int32)
        out, _, _, _ = sample_region_grid(image, zeros, zeros, palette,
            (np.linspace(0, 1, 4), np.linspace(0, 1, 5)), (1, 1), 0)
        self.assertEqual(out.shape, (4, 3, 4))
        self.assertTrue(np.all(out[..., 3] == 255))

    def test_invalid_labels_and_options_are_rejected(self):
        image = np.ones((1, 1, 3), np.uint8)
        with self.assertRaises(ValueError):
            sample_region_grid(image, np.array([[-1]]), np.array([[0]]), image[0],
                               (np.array([0., 1.]), np.array([0., 1.])), (1, 1))
        for options in (BoundaryOptions(tones=0), BoundaryOptions(feature_strength=float('nan')),
                        BoundaryOptions(refine_intensity=True),
                        BoundaryOptions(min_retained_tone_delta_l=True),
                        BoundaryOptions(min_retained_tone_delta_l=1.1)):
            with self.assertRaises(ValueError): options.validate()

    def test_structure_gates_bonus_not_coverage_or_palette(self):
        image = np.full((8, 8, 3), 160, np.uint8)
        image[2:5, 2:5] = 15
        labels = np.zeros((8, 8), np.int32)
        labels[2:5, 2:5] = 1
        palette = np.array([[160, 160, 160], [15, 15, 15]], np.uint8)
        edges = (np.array([0., 4., 8.]), np.array([0., 4., 8.]))
        args = (image, labels, labels, palette, edges, (2, 2))
        ordinary = sample_region_grid(*args, feature_strength=0)
        gated_off = sample_region_grid(*args, feature_strength=3,
                                      structure_strength=np.zeros((8, 8), np.float32))
        raw = sample_region_grid(*args, feature_strength=3)
        gated_on = sample_region_grid(*args, feature_strength=3,
                                     structure_strength=np.ones((8, 8), np.float32))
        for index in (0, 1, 2):
            np.testing.assert_array_equal(ordinary[index], gated_off[index])
            np.testing.assert_array_equal(raw[index], gated_on[index])
        self.assertTrue(gated_on[3]['structure_confidence_used'])
        self.assertFalse(gated_on[3]['small_component_deletion'])
        for invalid in (np.full((8, 8), np.nan), np.full((8, 8), 2.), np.zeros((1, 1))):
            with self.assertRaises(ValueError): sample_region_grid(*args, structure_strength=invalid)


class BoundaryIntegrationTests(unittest.TestCase):
    def test_end_to_end_keeps_original_and_scale_does_not_refit_regions(self):
        image = np.full((16, 20, 4), [215, 195, 165, 255], np.uint8)
        image[:, 10:, :3] = [140, 100, 70]
        image[0, 0] = [10, 250, 30, 0]
        reference = np.array([[[250, 240, 211], [230, 215, 185], [175, 125, 85]]], np.uint8)
        before = image.copy()
        result = get_boundary_pixel(image, reference, (5, 4))
        bigger = get_boundary_pixel(image, reference, (5, 4), '1.2')
        self.assertEqual(result.image.shape, (4, 5, 4))
        self.assertEqual(bigger.image.shape, (4, 6, 4))
        np.testing.assert_array_equal(image, before)
        np.testing.assert_array_equal(result.region_labels, bigger.region_labels)
        np.testing.assert_array_equal(result.flat_image, bigger.flat_image)
        np.testing.assert_array_equal(result.palette, bigger.palette)
        np.testing.assert_array_equal(result.flat_image[..., 3], before[..., 3])
        self.assertFalse(result.metadata['generative_redraw'])
        self.assertTrue(result.metadata['sampling']['structure_confidence_used'])


if __name__ == '__main__': unittest.main()
