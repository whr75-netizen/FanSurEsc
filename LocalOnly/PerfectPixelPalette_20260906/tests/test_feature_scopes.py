"""Technical scope checks. File-mask fixtures stay in memory; no image is saved."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from perfect_pixel.feature_scopes import build_scope, validate_feature


class FeatureScopeTests(unittest.TestCase):
    def test_no_scope_default(self):
        for value in (None, [], 'all', {}, {'kind': 'foreground'}, {'kind': 'edges'}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_scope((3, 4), value)

    def test_explicit_all_only(self):
        result = build_scope((3, 4), {'kind': 'all'})
        self.assertEqual(result.dtype, np.bool_)
        self.assertEqual(result.shape, (3, 4))
        self.assertTrue(result.all())
        with self.assertRaises(ValueError):
            build_scope((3, 4), {'kind': 'all', 'threshold': 1})

    def test_rectangles_exclusive_union_and_empty(self):
        spec = {'kind': 'rectangles', 'rectangles': [[0, 1, 2, 3], [1, 0, 4, 2]]}
        result = build_scope((3, 4), spec)
        expected = np.array([[0, 1, 1, 1], [1, 1, 1, 1], [1, 1, 0, 0]], bool)
        np.testing.assert_array_equal(result, expected)
        self.assertFalse(build_scope((3, 4), {'kind': 'rectangles', 'rectangles': []}).any())
        self.assertEqual(spec['rectangles'], [[0, 1, 2, 3], [1, 0, 4, 2]])

    def test_bad_rectangles(self):
        for rectangle in ([2, 0, 1, 2], [0, 2, 2, 1], [-1, 0, 1, 1],
                          [0, 0, 5, 1], [0, 0, 1, 4], [0, 0, 0, 1],
                          [0, 0, 1, 0], [0.0, 0, 1, 1], [False, 0, 1, 1],
                          [0, 0, 1], '0,0,1,1', None):
            with self.subTest(rectangle=rectangle), self.assertRaises(ValueError):
                build_scope((3, 4), {'kind': 'rectangles', 'rectangles': [rectangle]})
        for spec in ({'kind': 'rectangles'}, {'kind': 'rectangles', 'rectangles': None},
                     {'kind': 'rectangles', 'rectangles': [], 'infer': True}):
            with self.assertRaises(ValueError):
                build_scope((3, 4), spec)

    def test_invalid_shape(self):
        for shape in ((0, 3), (-1, 3), (3,), (2, 3, 4), (True, 2), (2.0, 3), None):
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                build_scope(shape, {'kind': 'all'})

    def _file_scope(self, fixture, shape=(2, 3)):
        with patch('perfect_pixel.feature_scopes.Image.open', return_value=fixture):
            return build_scope(shape, {'kind': 'mask', 'path': 'fixture.png'})

    def test_l_and_rgb_binary_masks(self):
        values = np.array([[0, 255, 0], [255, 255, 0]], np.uint8)
        for array in (values, np.repeat(values[..., None], 3, axis=2)):
            with self.subTest(channels=array.ndim):
                np.testing.assert_array_equal(self._file_scope(Image.fromarray(array)), values == 255)

    def test_mask_rejects_ambiguous_modes(self):
        for mode in ('RGBA', 'LA', 'P', '1', 'I'):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self._file_scope(Image.new(mode, (3, 2)))

    def test_mask_rejects_size_gray_values_and_colored_rgb(self):
        fixtures = [Image.new('L', (2, 3)), Image.new('L', (3, 2), 128),
                    Image.new('RGB', (3, 2), (255, 0, 255)),
                    Image.new('RGB', (3, 2), (128, 128, 128))]
        for fixture in fixtures:
            with self.assertRaises(ValueError):
                self._file_scope(fixture)

    def test_mask_path_and_no_file_fallback(self):
        fixture = Image.new('L', (3, 2), 255)
        with patch('perfect_pixel.feature_scopes.Image.open', return_value=fixture) as opened:
            result = build_scope((2, 3), {'kind': 'mask', 'path': 'scopes/a.png'}, base_dir=Path('project'))
            opened.assert_called_once_with(Path('project') / 'scopes/a.png')
            self.assertTrue(result.all())
        with patch('perfect_pixel.feature_scopes.Image.open', side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                build_scope((2, 3), {'kind': 'mask', 'path': 'missing.png'})
        for spec in ({'kind': 'mask'}, {'kind': 'mask', 'path': ''},
                     {'kind': 'mask', 'path': None}, {'kind': 'mask', 'path': 'x', 'alpha': True}):
            with self.assertRaises(ValueError):
                build_scope((2, 3), spec)

    def test_disabled_ignores_content_but_not_top_level_schema(self):
        self.assertEqual(validate_feature({}, []), (False, None, {}))
        self.assertEqual(validate_feature({'enabled': False, 'scope': None, 'options': ['invalid']}, []),
                         (False, None, {}))
        for feature in (None, [], {'enable': False}, {'enabled': False, 'global': True}):
            with self.assertRaises(ValueError):
                validate_feature(feature, [])

    def test_enabled_exact_bool_and_required_scope(self):
        for value in (0, 1, 'true', None, np.bool_(True)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_feature({'enabled': value}, [])
        for feature in ({'enabled': True}, {'enabled': True, 'scope': None},
                        {'enabled': True, 'scope': 'all'}):
            with self.assertRaises(ValueError):
                validate_feature(feature, [])

    def test_options_whitelist_and_owner_value_validation(self):
        feature = {'enabled': True, 'scope': {'kind': 'all'}, 'options': {'width': 'parent-validates'}}
        enabled, scope, options = validate_feature(feature, {'width'})
        self.assertTrue(enabled)
        self.assertEqual(options, feature['options'])
        self.assertIsNot(scope, feature['scope'])
        self.assertIsNot(options, feature['options'])
        with self.assertRaises(ValueError):
            validate_feature(feature, [])
        with self.assertRaises(ValueError):
            validate_feature({'enabled': True, 'scope': {'kind': 'all'}, 'options': None}, [])
        self.assertEqual(validate_feature({'enabled': True, 'scope': {'kind': 'all'}}, []),
                         (True, {'kind': 'all'}, {}))


if __name__ == '__main__':
    unittest.main()
