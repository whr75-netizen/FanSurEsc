"""Timeline and geometry counterexamples; no cloud calls or art quality tests."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from postprocess import common_crop, select_frames


class TimelineTests(unittest.TestCase):
    def test_variable_rate_uses_displayed_frame_and_excludes_endpoint(self):
        self.assertEqual(select_frames([0, .08, .31, .48, .6, .77], 1.0, 4), [0, 1, 3, 4])

    def test_too_few_distinct_displayed_frames_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "distinct"):
            select_frames([0, .9], 1.0, 4)

    def test_one_frame_uses_start(self):
        self.assertEqual(select_frames([0, .2, .4], .6, 1), [0])

    def test_duplicate_pts_choose_last_frame_at_that_instant(self):
        self.assertEqual(select_frames([0, .25, .25, .75], 1.0, 2), [0, 2])


class CropTests(unittest.TestCase):
    def test_shared_crop_covers_displaced_frames_with_exact_uniform_scale(self):
        crop, grid, scale, union = common_crop([(200, 100, 650, 890), (180, 120, 710, 880)], 960)
        self.assertEqual(union, (180, 100, 710, 890))
        self.assertTrue(all(value % scale.denominator == 0 for value in crop))
        self.assertEqual(grid[0], (crop[2] - crop[0]) * scale)
        self.assertEqual(grid[1], (crop[3] - crop[1]) * scale)
        self.assertLessEqual(crop[0], union[0])
        self.assertGreaterEqual(crop[2], union[2])

    def test_padding_at_canvas_edge_clamps_without_changing_scale(self):
        crop, grid, scale, _ = common_crop([(0, 0, 960, 960)], 960)
        self.assertEqual(crop, (0, 0, 960, 960))
        self.assertEqual(grid, (512, 512))


if __name__ == "__main__":
    unittest.main()
