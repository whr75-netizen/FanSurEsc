import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reference_style_cli import verify_palette_only


class PaletteOnlyContractTests(unittest.TestCase):
    def test_accepts_global_lookup_and_reports_merges(self):
        source = np.array([[[20, 30, 40], [60, 70, 80], [20, 30, 40]]], np.uint8)
        output = np.full_like(source, 100)
        result = verify_palette_only(source, output)
        self.assertEqual(result['split_source_colors'], 0)
        self.assertEqual(result['merged_source_colors'], 1)

    def test_rejects_spatial_relabeling(self):
        source = np.full((2, 2, 3), 30, np.uint8)
        output = np.full_like(source, 60)
        output[1, 1] = 90
        with self.assertRaisesRegex(ValueError, 'multiple targets'):
            verify_palette_only(source, output)

    def test_rejects_alpha_changes(self):
        source = np.full((1, 1, 4), 255, np.uint8)
        output = source.copy()
        output[..., 3] = 128
        with self.assertRaisesRegex(ValueError, 'alpha'):
            verify_palette_only(source, output)

    def test_empty_transparent_image(self):
        source = np.zeros((2, 2, 4), np.uint8)
        self.assertEqual(verify_palette_only(source, source)['source_colors'], 0)


if __name__ == '__main__':
    unittest.main()
