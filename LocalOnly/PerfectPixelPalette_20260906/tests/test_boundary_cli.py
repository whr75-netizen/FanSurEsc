import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from boundary_cli import parse_grid, sheet_dimensions


class BoundaryCliTests(unittest.TestCase):
    def test_grid_parsing_uses_core(self):
        self.assertEqual(parse_grid('70x73'), (70, 73))
        self.assertEqual(parse_grid([70, 73]), (70, 73))
        for value in ('0x3', '100000x3', '2x3x4', '2.5x3', [True, 3], [2.5, 3]):
            with self.assertRaises(ValueError): parse_grid(value)

    def test_limits_before_any_files(self):
        with self.assertRaises(ValueError): sheet_dimensions((4096, 4096), 6, (100, 100, 3))
        with self.assertRaises(ValueError): sheet_dimensions((70, 73), 20, (100, 100, 3))
        with self.assertRaises(ValueError): sheet_dimensions((70, 73), True, (100, 100, 3))
        width, height, size = sheet_dimensions((70, 73), 6, (482, 425, 3), (73, 70, 3))
        self.assertEqual((width, height), (425, 482))
        self.assertEqual(size, (1339, 566))


if __name__ == '__main__': unittest.main()
