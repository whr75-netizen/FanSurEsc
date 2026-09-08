import json
from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / '.deps'))
sys.path.insert(0, str(root / 'src'))
import numpy as np
from perfect_pixel.line_first import prepare_line_geometry, render_line_geometry


def line_data(source, grid, candidate=None, locked=None):
    sh, sw = source.shape[:2]
    w, h = grid
    candidate = np.zeros((sh, sw), bool) if candidate is None else candidate
    mask = np.zeros((h, w), bool) if locked is None else locked
    xy = np.full((h, w, 2), -1, np.int32)
    for y, x in zip(*np.nonzero(candidate)):
        tx, ty = (2 * x + 1) * w // (2 * sw), (2 * y + 1) * h // (2 * sh)
        if mask[ty, tx]: xy[ty, tx] = [x, y]
    return dict(source_candidate=candidate, target_mask=mask,
                collision_mask=np.zeros((h, w), bool), source_xy=xy)


def box():
    a = np.full((15, 15, 4), (210, 190, 120, 255), np.uint8)
    a[5:10, 5:10, :3] = (100, 170, 220)
    candidate = np.zeros((15, 15), bool)
    candidate[4, 4:11] = candidate[10, 4:11] = True
    candidate[4:11, 4] = candidate[4:11, 10] = True
    a[candidate] = (25, 30, 45, 255)
    return a, candidate


class LineFirstTests(unittest.TestCase):
    def test_supported_flood_accepts_later_lower_cost_route_of_same_owner(self):
        from perfect_pixel.line_first import _supported_expand
        markers = np.zeros((3, 3), np.int32)
        markers[0, 1] = markers[2, 1] = 1
        markers[1, 0] = 2
        labels = markers - 1
        mask = markers > 0
        mask[1, 1] = True
        energy = np.zeros((3, 3))
        energy[0, 1], energy[1, 0], energy[2, 1] = 9, 4, 1
        lab = np.full((3, 3, 3), .5)
        lab[1, 0, 0] = .53
        expanded, _ = _supported_expand(markers, energy, mask, lab,
            np.ones((3, 3), bool), labels, np.arange(4), np.arange(4), (3, 3), .08)
        self.assertEqual(expanded[1, 1], 1)

    def test_fill_guard_blocks_dark_owner_expansion_into_raw_skin(self):
        a = np.full((6, 6, 4), (230, 160, 125, 255), np.uint8)
        a[4:] = (35, 12, 5, 255)
        candidate = np.zeros((6, 6), bool)
        candidate[:4] = True  # False-positive line candidates erased all skin seeds.
        data = line_data(a, (3, 3), candidate)
        old = prepare_line_geometry(a, (3, 3), np.ones((6, 6), bool), data)
        guarded = prepare_line_geometry(a, (3, 3), np.ones((6, 6), bool), data,
                                        fill_source_guard=True)
        self.assertTrue(np.all(old['target_owners'][:2] >= 0))
        self.assertTrue(np.all(guarded['target_owners'][:2] == -1))
        self.assertGreater(guarded['metadata']['unsupported_owner_proposals'], 0)
        np.testing.assert_array_equal(render_line_geometry(guarded, a)['image'], a[1::2, 1::2])

    def test_fill_guard_still_expands_compatible_raw_color(self):
        a = np.full((6, 6, 4), (230, 160, 125, 255), np.uint8)
        candidate = np.zeros((6, 6), bool)
        candidate[:4] = True
        g = prepare_line_geometry(a, (3, 3), np.ones((6, 6), bool),
                                  line_data(a, (3, 3), candidate), fill_source_guard=True)
        self.assertTrue(np.all(g['target_owners'] >= 0))
        self.assertEqual(g['metadata']['unsupported_owner_proposals'], 0)

    def test_fill_guard_does_not_move_locked_lines(self):
        a, candidate = box()
        data = line_data(a, (15, 15), candidate, candidate.copy())
        g = prepare_line_geometry(a, (15, 15), np.ones((15, 15), bool), data,
                                  fill_source_guard=True)
        np.testing.assert_array_equal(g['fixed_line_mask'], candidate)
        np.testing.assert_array_equal(render_line_geometry(g, a)['image'], a)

    def test_closed_box_owners_do_not_cross_locked_line(self):
        a, candidate = box()
        data = line_data(a, (15, 15), candidate, candidate.copy())
        g = prepare_line_geometry(a, (15, 15), np.ones((15, 15), bool), data)
        self.assertNotEqual(g['source_labels'][7, 7], g['source_labels'][1, 1])
        self.assertEqual(g['target_owners'][7, 7], g['source_labels'][7, 7])
        self.assertTrue(np.all(g['target_owners'][candidate] == -1))
        r = render_line_geometry(g, a)
        np.testing.assert_array_equal(r['image'], a)

    def test_downscaled_closed_box_keeps_distinct_interior_and_exterior(self):
        native, locked = box()
        a = np.repeat(np.repeat(native, 2, axis=0), 2, axis=1)
        candidate = np.repeat(np.repeat(locked, 2, axis=0), 2, axis=1)
        data = line_data(a, (15, 15), candidate, locked)
        g = prepare_line_geometry(a, (15, 15), np.ones((30, 30), bool), data)
        r = render_line_geometry(g, a)
        np.testing.assert_array_equal(r['image'], native)
        self.assertNotEqual(g['target_owners'][7, 7], g['target_owners'][1, 1])

    def test_palette_changes_do_not_change_geometry_or_line_locations(self):
        a, candidate = box()
        g = prepare_line_geometry(a, (15, 15), np.ones((15, 15), bool), line_data(a, (15, 15), candidate, candidate))
        owners, fixed = g['target_owners'].copy(), g['fixed_line_mask'].copy()
        palette = a.copy()
        palette[5:10, 5:10, :3] = (140, 200, 235)
        palette[candidate, :3] = (50, 55, 70)
        r = render_line_geometry(g, palette)
        np.testing.assert_array_equal(g['target_owners'], owners)
        np.testing.assert_array_equal(g['fixed_line_mask'], fixed)
        np.testing.assert_array_equal(r['image'][candidate], palette[candidate])
        self.assertTrue(set(map(tuple, r['image'].reshape(-1, 4))) <= set(map(tuple, palette.reshape(-1, 4))))
        json.dumps(r['metadata'], allow_nan=False)

    def test_open_line_is_not_closed(self):
        a, candidate = box()
        candidate[4, 7] = False
        a[4, 7] = a[1, 1]
        g = prepare_line_geometry(a, (15, 15), np.ones((15, 15), bool), line_data(a, (15, 15), candidate, candidate))
        np.testing.assert_array_equal(g['fixed_line_mask'], candidate)
        self.assertFalse(g['fixed_line_mask'][4, 7])
        r = render_line_geometry(g, a)
        np.testing.assert_array_equal(r['image'][4, 7], a[4, 7])

    def test_scope_exclusion_preserves_raw_center(self):
        a, candidate = box()
        scope = np.zeros((15, 15), bool); scope[5:10, 5:10] = True
        g = prepare_line_geometry(a, (15, 15), scope, line_data(a, (15, 15)))
        palette = a.copy(); palette[..., :3] = (120, 180, 240)
        out = render_line_geometry(g, palette)['image']
        np.testing.assert_array_equal(out[~scope], a[~scope])

    def test_hidden_rgb_has_no_geometry_or_visible_fill_influence(self):
        a = np.full((8, 8, 4), (180, 150, 100, 255), np.uint8)
        a[:2, :, 3] = 0
        b = a.copy(); b[:2, :, :3] = (0, 255, 240)
        scope = np.ones((8, 8), bool)
        ga = prepare_line_geometry(a, (4, 4), scope, line_data(a, (4, 4)))
        gb = prepare_line_geometry(b, (4, 4), scope, line_data(b, (4, 4)))
        for key in ('source_labels', 'target_owners', 'target_energy', 'target_foreground'):
            np.testing.assert_array_equal(ga[key], gb[key])
        np.testing.assert_array_equal(render_line_geometry(ga, a)['image'], render_line_geometry(gb, b)['image'])

    def test_deleted_center_stays_deleted_after_fill_and_lines(self):
        a, candidate = box()
        deleted = np.zeros((15, 15), bool); deleted[7, 7] = deleted[4, 7] = True
        g = prepare_line_geometry(a, (15, 15), np.ones((15, 15), bool), line_data(a, (15, 15), candidate, candidate), deleted_mask=deleted)
        out = render_line_geometry(g, a)['image']
        self.assertFalse(out[deleted].any())
        self.assertFalse(g['fixed_line_mask'][4, 7])

    def test_markerless_fallback_is_raw_center_and_explicit(self):
        a = np.full((6, 6, 4), (45, 60, 80, 255), np.uint8)
        candidate = np.ones((6, 6), bool)
        g = prepare_line_geometry(a, (3, 3), candidate, line_data(a, (3, 3), candidate))
        self.assertEqual(g['metadata']['unresolved_cells'], 9)
        self.assertEqual(g['metadata']['unresolved_components'], 1)
        palette = a.copy(); palette[..., :3] = 200
        np.testing.assert_array_equal(render_line_geometry(g, palette)['image'], a[1::2, 1::2])

    def test_empty_marker_cell_uses_only_its_assigned_source_region(self):
        a = np.full((9, 9, 4), (80, 130, 190, 255), np.uint8)
        candidate = np.zeros((9, 9), bool); candidate[3:6, 3:6] = True
        a[candidate, :3] = (20, 30, 50)
        g = prepare_line_geometry(a, (3, 3), np.ones((9, 9), bool), line_data(a, (3, 3), candidate))
        self.assertEqual(g['metadata']['expanded_unseeded_cells'], 1)
        r = render_line_geometry(g, a)
        self.assertEqual(r['metadata']['same_region_nearest_samples'], 1)
        xy = r['source_xy'][1, 1]
        self.assertEqual(g['source_labels'][xy[1], xy[0]], g['target_owners'][1, 1])
        np.testing.assert_array_equal(r['image'][1, 1], [80, 130, 190, 255])

    def test_collision_cell_preserves_raw_center(self):
        a, candidate = box()
        data = line_data(a, (5, 5), candidate, np.zeros((5, 5), bool))
        data['collision_mask'][2, 2] = True
        g = prepare_line_geometry(a, (5, 5), np.ones((15, 15), bool), data)
        palette = a.copy(); palette[..., :3] = 180
        r = render_line_geometry(g, palette)
        np.testing.assert_array_equal(r['image'][2, 2], a[7, 7])
        self.assertEqual(g['metadata']['collision_cells'], 1)

    def test_validation_and_input_immutability(self):
        a, candidate = box()
        before = a.copy(); scope = np.ones((15, 15), bool)
        data = line_data(a, (15, 15))
        g = prepare_line_geometry(a, (15, 15), scope, data)
        render_line_geometry(g, a)
        np.testing.assert_array_equal(a, before)
        for grid in ((16, 15), (0, 3), (True, 3), (3.5, 3)):
            with self.assertRaises(ValueError): prepare_line_geometry(a, grid, scope, data)
        for kw in ({'coverage':float('nan')}, {'coverage':0}, {'color_edge_threshold':0}, {'deleted_mask':scope.astype(int)}):
            with self.assertRaises(ValueError): prepare_line_geometry(a, (15, 15), scope, data, **kw)
        with self.assertRaises(ValueError): prepare_line_geometry(a, (15, 15), scope.astype(int), data)
        wrong = a.copy(); wrong[0, 0, 3] = 0
        with self.assertRaises(ValueError): render_line_geometry(g, wrong)
        wrong = a.copy(); wrong[0, 0, 3] = 127
        with self.assertRaises(ValueError): prepare_line_geometry(wrong, (15, 15), scope, data)

    def test_size_limit_and_invalid_line_provenance_fail_explicitly(self):
        # Read-only broadcast view reaches the size validator without allocating
        # or filtering a real 4 MP image.
        big = np.broadcast_to(np.array([1, 2, 3, 255], np.uint8), (2049, 2049, 4))
        with self.assertRaises(ValueError): prepare_line_geometry(big, (1, 1), None, {})
        a, candidate = box()
        data = line_data(a, (15, 15), candidate, candidate)
        data['source_xy'][4, 4] = [100, 100]
        with self.assertRaises(ValueError):
            prepare_line_geometry(a, (15, 15), np.ones((15, 15), bool), data)
        data = line_data(a, (15, 15), candidate, candidate)
        data['source_xy'][4, 4] = [5, 4]
        with self.assertRaises(ValueError):
            prepare_line_geometry(a, (15, 15), np.ones((15, 15), bool), data)


if __name__ == '__main__': unittest.main()
