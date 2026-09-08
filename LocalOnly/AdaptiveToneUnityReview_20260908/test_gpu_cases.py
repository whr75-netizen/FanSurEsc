"""Fixture integrity checks only; GPU output is checked by the parent task."""
import json
import unittest

from gpu_cases import CASE_NAMES, build_case, encode_meta, unity_flat_fixture
from cpu_oracle import chroma_cell_key


class GpuCaseIntegrityTests(unittest.TestCase):
    def test_fixtures_are_finite_json_with_exact_texture_shapes_and_sparse_seeds(self):
        for name in CASE_NAMES:
            case = build_case(name)
            with self.subTest(name=name):
                size = case['width'] * case['height']
                for key in ('source_color_depth', 'source_meta', 'seed_color_depth', 'seed_meta'):
                    self.assertEqual(len(case[key]), size)
                    self.assertTrue(all(len(sample) == 4 for sample in case[key]))
                expected_seeds = sum(x % 4 == 2 and y % 4 == 2
                                     for y in range(case['height']) for x in range(case['width']))
                self.assertEqual(sum(sample[0] != 0 for sample in case['seed_meta']), expected_seeds)
                self.assertTrue(all(0 <= channel <= 16 for sample in case['source_color_depth'] for channel in sample[:3]))
                json.dumps(case, allow_nan=False)

    def test_subject_encoding_uses_both_subject_bytes_and_does_not_treat_alpha_as_coverage(self):
        self.assertEqual(encode_meta(257, 2), (1 / 255., 2 / 255., 4 / 255., 1 / 255.))
        case = build_case('equal_l_chroma_part_subject')
        subjects = set(round(meta[0] * 255) + 256 * round(meta[3] * 255) for meta in case['source_meta'])
        self.assertEqual(subjects, {257, 258})
        self.assertEqual(case['settings']['subject_id'], 257)

    def test_capacity_fixture_contains_more_than_160_distinct_valid_keys(self):
        case = build_case('hash_capacity')
        keys = set()
        for color, meta in zip(case['source_color_depth'], case['source_meta']):
            r, g, b = color[:3]
            l = (.4122214708 * r + .5363325363 * g + .0514459929 * b) ** (1 / 3)
            m = (.2119034982 * r + .6806995451 * g + .1073969566 * b) ** (1 / 3)
            s = (.0883024619 * r + .2817188376 * g + .6299787005 * b) ** (1 / 3)
            lightness = .2104542553 * l + .7936177850 * m - .0040720468 * s
            a = (1.9779984951 * l - 2.4285922050 * m + .4505937099 * s) / max(lightness, .05)
            chroma_b = (.0259040371 * l + .7827717662 * m - .8086757660 * s) / max(lightness, .05)
            key = chroma_cell_key(round(meta[1] * 255), (a, chroma_b), case['settings']['chroma_error'])
            keys.add(key)
        self.assertEqual(len(keys), 165)
        self.assertTrue(all(-128 <= value <= 127 for key in keys for value in key[1:]))

    def test_unity_flat_fixture_is_lossless_without_mutating_original(self):
        for name in CASE_NAMES:
            original = build_case(name)
            before = json.dumps(original)
            flat = unity_flat_fixture(original)
            for field in ('source_color_depth', 'source_meta', 'seed_color_depth', 'seed_meta'):
                self.assertEqual(len(flat[field]), original['width'] * original['height'] * 4)
                self.assertEqual([flat[field][index:index + 4] for index in range(0, len(flat[field]), 4)],
                                 [list(pixel) for pixel in original[field]])
            self.assertEqual(flat['settings']['highlight_minimum_contrast'], .025)
            self.assertEqual(json.dumps(original), before)


if __name__ == '__main__':
    unittest.main()
