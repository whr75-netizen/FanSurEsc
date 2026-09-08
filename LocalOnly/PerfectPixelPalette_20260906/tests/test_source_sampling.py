import unittest

import numpy as np

from perfect_pixel.trigger_pipeline import center_sample, sample_scoped


class SourceSamplingTests(unittest.TestCase):
    def split_cell(self):
        guide = np.array([
            [[35, 45, 55, 255], [220, 200, 175, 255]],
            [[36, 46, 56, 255], [222, 201, 176, 255]],
        ], dtype=np.uint8)
        first = guide.copy()
        first[:, 0] = [40, 50, 60, 255]
        first[0, 1] = [210, 190, 160, 255]
        first[1, 1] = [230, 210, 180, 255]
        second = guide.copy()
        second[0, 0] = [30, 40, 50, 255]
        second[1, 0] = [50, 60, 70, 255]
        second[:, 1] = [220, 200, 170, 255]
        return guide, first, second

    def test_palette_color_fragmentation_cannot_move_source_region_sample(self):
        guide, first, second = self.split_cell()
        scope = np.ones((2, 2), bool)
        samples = []
        for palette in (first, second):
            image, xy = sample_scoped(
                palette, (1, 1), scope, method='source_regions',
                source_guide=guide, color_edge_threshold=.08,
                return_source_xy=True)
            # Both raw regions cover half the cell. Equal spatial phases use
            # the bottom/right source pixel consistently, despite RGB counts.
            np.testing.assert_array_equal(xy[0, 0], [1, 1])
            np.testing.assert_array_equal(image[0, 0], palette[1, 1])
            samples.append(xy)
        np.testing.assert_array_equal(samples[0], samples[1])

    def test_legacy_default_keeps_exact_rgb_vote_and_tie_behavior(self):
        _, first, second = self.split_cell()
        scope = np.ones((2, 2), bool)
        for palette, expected in ((first, [0, 0]), (second, [1, 0])):
            default, default_xy = sample_scoped(
                palette, (1, 1), scope, return_source_xy=True)
            explicit, explicit_xy = sample_scoped(
                palette, (1, 1), scope, method='rgb_vote',
                return_source_xy=True)
            np.testing.assert_array_equal(default_xy[0, 0], expected)
            np.testing.assert_array_equal(default, explicit)
            np.testing.assert_array_equal(default_xy, explicit_xy)

    def test_noninteger_grid_uses_true_cell_center_on_both_grid_phases(self):
        guide = np.full((2, 385, 4), [225, 205, 180, 255], np.uint8)
        guide[:, [140, 241]] = [35, 45, 55, 255]
        out, xy = sample_scoped(
            guide, (192, 1), np.ones((2, 385), bool),
            method='source_regions', source_guide=guide,
            return_source_xy=True)
        # Target 70 owns source columns 140,141; its center is about 140.867.
        # Target 120 owns 241,242; its center is about 241.128. A block-midpoint
        # tie always choosing the right pixel would get the second case wrong.
        np.testing.assert_array_equal(xy[0, 70], [141, 1])
        np.testing.assert_array_equal(xy[0, 120], [241, 1])
        np.testing.assert_array_equal(out[0, 70], guide[1, 141])
        np.testing.assert_array_equal(out[0, 120], guide[1, 241])

    def test_one_source_pixel_per_cell_preserves_palette_image(self):
        rng = np.random.default_rng(18)
        guide = rng.integers(0, 256, (3, 4, 4), dtype=np.uint8)
        guide[..., 3] = 255
        palette = guide.copy()
        palette[..., :3] = 255 - palette[..., :3]
        out, xy = sample_scoped(
            palette, (4, 3), np.ones((3, 4), bool),
            method='source_regions', source_guide=guide,
            return_source_xy=True)
        np.testing.assert_array_equal(out, palette)
        yy, xx = np.indices((3, 4))
        np.testing.assert_array_equal(xy, np.stack((xx, yy), axis=2))

    def test_scope_limits_source_choices_and_preserves_outside_target_bytes(self):
        guide = np.full((4, 6, 4), [210, 190, 160, 255], np.uint8)
        palette = np.full((4, 6, 4), [180, 160, 130, 255], np.uint8)
        scope = np.zeros((4, 6), bool)
        scope[:2, 2:4] = True
        scope[0, 2] = False
        palette[0, 2] = [0, 255, 255, 255]
        guide[1, 2, 3] = palette[1, 2, 3] = 0
        # Unselected transparent target centers retain even their hidden RGB.
        guide[3, 5, 3] = palette[3, 5, 3] = 0
        baseline = center_sample(palette, (3, 2))
        out, xy = sample_scoped(
            palette, (3, 2), scope, method='source_regions',
            source_guide=guide, coverage=.5, return_source_xy=True)
        target_scope = center_sample(scope, (3, 2))
        np.testing.assert_array_equal(out[~target_scope], baseline[~target_scope])
        sx, sy = xy[0, 1]
        self.assertTrue(scope[sy, sx])
        self.assertEqual(int(palette[sy, sx, 3]), 255)
        np.testing.assert_array_equal(out[0, 1], palette[sy, sx])

    def test_alpha_coverage_and_hidden_rgb_do_not_enter_region_ballots(self):
        guide = np.full((2, 4, 4), [255, 0, 255, 0], np.uint8)
        guide[0, 0] = [45, 60, 80, 255]
        guide[:, 3] = [200, 180, 150, 255]
        changed_hidden = guide.copy()
        changed_hidden[changed_hidden[..., 3] == 0, :3] = [0, 255, 0]
        scope = np.ones((2, 4), bool)
        images = []
        for source in (guide, changed_hidden):
            out, xy = sample_scoped(
                source, (2, 1), scope, method='source_regions',
                source_guide=source, coverage=.5, return_source_xy=True)
            np.testing.assert_array_equal(out[0, 0], [0, 0, 0, 0])
            np.testing.assert_array_equal(xy[0, 0], [-1, -1])
            np.testing.assert_array_equal(out[0, 1], [200, 180, 150, 255])
            images.append(out)
        np.testing.assert_array_equal(images[0], images[1])

    def test_invalid_method_and_incompatible_source_guides_are_rejected(self):
        guide, palette, _ = self.split_cell()
        scope = np.ones((2, 2), bool)
        with self.assertRaises(ValueError):
            sample_scoped(palette, (1, 1), scope, method='unknown')
        wrong_alpha = guide.copy()
        wrong_alpha[0, 0, 3] = 0
        for invalid in (guide[:, :1], guide[..., :3], wrong_alpha):
            with self.subTest(shape=invalid.shape, alpha_mismatch=invalid is wrong_alpha):
                with self.assertRaises(ValueError):
                    sample_scoped(
                        palette, (1, 1), scope, method='source_regions',
                        source_guide=invalid)

    def test_samples_are_actual_palette_pixels_and_inputs_are_unchanged(self):
        rng = np.random.default_rng(42)
        guide = rng.integers(0, 256, (6, 6, 4), dtype=np.uint8)
        palette = rng.integers(0, 256, (6, 6, 4), dtype=np.uint8)
        guide[..., 3] = palette[..., 3] = 255
        guide_before, palette_before = guide.copy(), palette.copy()
        out, xy = sample_scoped(
            palette, (3, 3), np.ones((6, 6), bool),
            method='source_regions', source_guide=guide,
            return_source_xy=True)
        np.testing.assert_array_equal(out, palette[xy[..., 1], xy[..., 0]])
        observed = set(map(tuple, palette.reshape(-1, 4)))
        self.assertTrue(set(map(tuple, out.reshape(-1, 4))) <= observed)
        np.testing.assert_array_equal(guide, guide_before)
        np.testing.assert_array_equal(palette, palette_before)


if __name__ == '__main__':
    unittest.main()
