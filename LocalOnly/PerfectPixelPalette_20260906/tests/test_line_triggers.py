import builtins
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / '.deps'))
sys.path.insert(0, str(root / 'src'))
import numpy as np
from perfect_pixel.line_triggers import normalize_lines


def image(bg=220):
    return np.full((48, 48, 4), (bg, bg, bg, 255), np.uint8)


class LineTriggerTests(unittest.TestCase):
    def test_off_does_not_import_optional_dependencies(self):
        a = image()
        real_import = builtins.__import__
        def guarded(name, *args, **kwargs):
            if name.startswith(('scipy', 'skimage')):
                raise AssertionError('Optional dependency touched in OFF mode')
            return real_import(name, *args, **kwargs)
        with mock.patch('builtins.__import__', side_effect=guarded):
            r = normalize_lines(a, (12, 12), None)
        for key in ('source_candidate', 'source_skeleton', 'target_mask', 'target_rgba', 'collision_mask'):
            self.assertFalse(r[key].any())
        self.assertTrue(np.all(r['source_xy'] == -1))

    def test_dark_and_bright_lines_and_source_provenance(self):
        for bg, fg in ((220, (32, 42, 67)), (25, (224, 238, 245))):
            a = image(bg)
            a[6:42, 23:25, :3] = fg
            before = a.copy()
            scope = np.ones(a.shape[:2], bool)
            r = normalize_lines(a, (12, 12), scope, enabled=True)
            self.assertGreater(r['target_mask'].sum(), 6)
            self.assertLessEqual(np.count_nonzero(r['target_mask'], axis=1).max(), 1)
            xy = r['source_xy'][r['target_mask']]
            np.testing.assert_array_equal(r['target_rgba'][r['target_mask']], a[xy[:, 1], xy[:, 0]])
            self.assertTrue(np.all(r['target_rgba'][r['target_mask'], 3] == 255))
            np.testing.assert_array_equal(a, before)
            again = normalize_lines(a, (12, 12), scope, enabled=True)
            np.testing.assert_array_equal(r['target_rgba'], again['target_rgba'])
            json.dumps(r['metadata'], allow_nan=False)

    def test_flat_step_and_uniform_images_are_not_lines(self):
        a = image()
        scope = np.ones(a.shape[:2], bool)
        self.assertFalse(normalize_lines(a, (12, 12), scope, enabled=True)['target_mask'].any())
        a[:, :24, :3] = 30
        r = normalize_lines(a, (12, 12), scope, enabled=True)
        self.assertFalse(r['source_candidate'].any())

    def test_scope_both_source_and_target_center(self):
        a = image()
        a[6:42, 23:25, :3] = 30
        scope = np.ones(a.shape[:2], bool)
        scope[24:] = False
        r = normalize_lines(a, (12, 12), scope, enabled=True)
        self.assertFalse(r['source_skeleton'][24:].any())
        self.assertFalse(r['target_mask'][6:].any())
        # Source line lies inside a narrow scope, target-cell center does not.
        scope[:] = False
        scope[:, 23:25] = True
        r = normalize_lines(a, (12, 12), scope, enabled=True)
        self.assertTrue(r['source_skeleton'].any())
        self.assertFalse(r['target_mask'].any())

    def test_alpha_and_hidden_rgb_do_not_create_lines(self):
        a = image()
        a[:, 20:28, 3] = 0
        scope = np.ones(a.shape[:2], bool)
        b = a.copy()
        b[:, 20:28, :3] = (0, 255, 0)
        ra = normalize_lines(a, (12, 12), scope, enabled=True)
        rb = normalize_lines(b, (12, 12), scope, enabled=True)
        np.testing.assert_array_equal(ra['target_rgba'], rb['target_rgba'])
        self.assertFalse(ra['target_mask'].any())
        a = image()
        a[6:42, 23:25] = (20, 30, 40, 254)
        r = normalize_lines(a, (12, 12), scope, enabled=True)
        self.assertFalse(r['target_mask'].any())

    def test_disconnected_line_segments_are_not_bridged(self):
        a = image()
        a[3:16, 23:25, :3] = 30
        a[32:45, 23:25, :3] = 30
        r = normalize_lines(a, (12, 12), np.ones((48, 48), bool), enabled=True)
        self.assertTrue(r['target_mask'][:4].any())
        self.assertTrue(r['target_mask'][8:].any())
        self.assertFalse(r['target_mask'][5:7].any())

    def test_bent_line_keeps_eight_connected_projection(self):
        from scipy.ndimage import label
        a = image()
        for y in range(6, 42):
            x = 16 + abs(y - 24) // 3
            a[y, x:x + 2, :3] = (35, 50, 65)
        r = normalize_lines(a, (16, 16), np.ones((48, 48), bool), enabled=True)
        self.assertGreater(r['target_mask'].sum(), 8)
        self.assertEqual(label(r['target_mask'], structure=np.ones((3, 3), bool))[1], 1)
        xy = r['source_xy'][r['target_mask']]
        ty, tx = np.nonzero(r['target_mask'])
        np.testing.assert_array_equal((2 * xy[:, 0] + 1) * 16 // 96, tx)
        np.testing.assert_array_equal((2 * xy[:, 1] + 1) * 16 // 96, ty)

    def test_distinct_source_lines_colliding_in_a_cell_are_reported(self):
        a = image()
        a[6:42, 21, :3] = (20, 30, 40)
        a[6:42, 23, :3] = (30, 40, 50)
        r = normalize_lines(a, (12, 12), np.ones((48, 48), bool), enabled=True)
        self.assertTrue(r['collision_mask'].any())
        self.assertEqual(r['metadata']['collision_cells'], int(r['collision_mask'].sum()))

    def test_width_bound_and_component_filter(self):
        a = image()
        a[6:42, 18:30, :3] = 30
        r = normalize_lines(a, (12, 12), np.ones((48, 48), bool), enabled=True)
        self.assertFalse(r['source_candidate'][16:32].any())
        a = image()
        a[24, 24, :3] = 0
        r = normalize_lines(a, (12, 12), np.ones((48, 48), bool), enabled=True)
        self.assertFalse(r['target_mask'].any())

    def test_empty_and_all_transparent(self):
        a = image()
        r = normalize_lines(a, (12, 12), np.zeros((48, 48), bool), enabled=True)
        self.assertFalse(r['source_candidate'].any())
        a[..., 3] = 0
        r = normalize_lines(a, (12, 12), np.ones((48, 48), bool), enabled=True)
        self.assertFalse(r['target_mask'].any())

    def test_validation(self):
        a = image()
        scope = np.ones((48, 48), bool)
        with self.assertRaises(ValueError): normalize_lines(a, (12, 12), None, enabled=True)
        for grid in ((49, 12), (0, 12), (True, 12), (12.0, 12)):
            with self.assertRaises(ValueError): normalize_lines(a, grid, scope)
        for opt in ({'unknown': 1}, {'min_response': float('nan')}, {'min_contrast': 0},
                    {'max_width_source_px': 33}, {'min_component_pixels': True}):
            with self.assertRaises(ValueError): normalize_lines(a, (12, 12), scope, options=opt)
        with self.assertRaises(ValueError): normalize_lines(a.astype(float), (12, 12), scope)
        with self.assertRaises(ValueError): normalize_lines(a, (12, 12), scope.astype(np.uint8))


if __name__ == '__main__':
    unittest.main()
