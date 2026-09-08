import unittest
from trigger_cli import comparison_size


class TriggerCliTests(unittest.TestCase):
    def test_four_panel_size_is_known_before_writes(self):
        self.assertEqual(comparison_size((866,385),(192,433),2,4),(1640,966))

    def test_combined_preview_limit_not_just_each_panel(self):
        with self.assertRaises(ValueError):
            comparison_size((1200,1200),(1200,1200),4,4)


if __name__=='__main__': unittest.main()
