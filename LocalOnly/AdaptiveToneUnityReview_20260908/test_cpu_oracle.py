"""Synthetic numerical checks; passing these does not validate GPU dispatch."""
import unittest

from cpu_oracle import (Bin, adaptive_histogram, chroma_cell_key, observed_bins,
                        solve_observed_bins, supported_highlight)


class CpuOracleTests(unittest.TestCase):
    def test_constant_preserves_its_observed_representative(self):
        bins = observed_bins([.5] * 17, range(100, 117))
        result = solve_observed_bins(bins, tone_error=.001)
        self.assertEqual(result.status, 'ok')
        self.assertEqual(result.tone_count, 1)
        self.assertEqual(bins[result.representatives[0]].sample_index, 100)
        self.assertEqual(result.rmse, 0.)

    def test_tone_count_is_variable_and_not_forced_to_three(self):
        expected = (([.49, .5, .51], .03, 1),
                    ([.25, .75], .01, 2),
                    ([.125, .375, .625, .875], .01, 4))
        for values, error, count in expected:
            with self.subTest(values=values):
                result = solve_observed_bins(observed_bins(values), tone_error=error)
                self.assertEqual(result.status, 'ok')
                self.assertEqual(result.tone_count, count)

    def test_spatial_guard_can_require_more_tones_than_histogram_rmse(self):
        bins = (Bin(30, 30 * .25, 30 * .25 ** 2, .25, 0, low_count=30),
                Bin(40, 40 * .5, 40 * .5 ** 2, .5, 1),
                Bin(30, 30 * .75, 30 * .75 ** 2, .75, 2, high_count=30))
        histogram_only = solve_observed_bins(bins, tone_error=.3)
        protected = solve_observed_bins(bins, tone_error=.3, minimum_support_contrast=.325)
        self.assertEqual(histogram_only.tone_count, 1)
        self.assertGreater(protected.tone_count, 1)
        self.assertGreaterEqual(protected.support_contrast, .325)

    def test_sub_bin_source_variance_is_not_lost(self):
        # Both source values share one occupied bin; its representative is .25.
        # Replacing the entire bin by its representative has nonzero true SSE.
        bins = (Bin(2, .25 + .75, .25 ** 2 + .75 ** 2, .25, 8),)
        failed = solve_observed_bins(bins, tone_error=.01)
        passed = solve_observed_bins(bins, tone_error=.4)
        self.assertEqual(failed.status, 'no_feasible_candidate_within_tone_limit')
        self.assertEqual(failed.representatives, ())
        self.assertAlmostEqual(passed.rmse, (.5 ** 2 / 2) ** .5)

    def test_representatives_always_identify_actual_source_samples(self):
        colors = ((.12, .08, .03, 1.), (.27, .21, .08, 1.), (.55, .41, .19, 1.))
        bins = observed_bins([.25, .5, .75], [0, 1, 2])
        result = solve_observed_bins(bins, tone_error=.22)
        actual_indices = [bins[index].sample_index for index in result.representatives]
        palette = [colors[index] for index in actual_indices]
        self.assertTrue(all(color in colors for color in palette))
        self.assertNotIn((sum(c[0] for c in colors) / 3,
                          sum(c[1] for c in colors) / 3,
                          sum(c[2] for c in colors) / 3, 1.), palette)

    def test_frequency_affects_optimal_observed_representative(self):
        result = solve_observed_bins(observed_bins([.25] * 20 + [.75]), tone_error=.5)
        self.assertEqual(result.tone_count, 1)
        self.assertEqual(result.representatives, (0,))

    def test_bin_and_tone_limit_failures_are_explicit_and_have_no_palette(self):
        bins = observed_bins([.125, .375, .625, .875])
        limited_bins = solve_observed_bins(bins, max_bins=3)
        limited_tones = solve_observed_bins(bins, tone_error=.001, max_tones=2)
        self.assertEqual(limited_bins.status, 'bin_limit_exceeded')
        self.assertEqual(limited_tones.status, 'no_feasible_candidate_within_tone_limit')
        for result in (limited_bins, limited_tones):
            self.assertEqual(result.tone_count, 0)
            self.assertEqual(result.representatives, ())
            self.assertEqual(result.assignments, ())

    def test_same_lightness_groups_cannot_require_a_shared_rgb(self):
        # Group ownership is supplied externally. Solving each independently
        # must retain its own source representative even for identical L.
        groups = {(3, 1, 2): observed_bins([.5] * 5, [10] * 5),
                  (3, 2, 2): observed_bins([.5] * 5, [20] * 5),
                  (4, 1, 2): observed_bins([.5] * 5, [30] * 5),
                  (3, 1, 7): observed_bins([.5] * 5, [40] * 5)}
        selected = {}
        for key, bins in groups.items():
            result = solve_observed_bins(bins)
            selected[key] = bins[result.representatives[0]].sample_index
        self.assertEqual(set(selected.values()), {10, 20, 30, 40})

    def test_supported_highlight_is_positive_and_cannot_change_shadow_or_low_support(self):
        source = (.2, .4, .55, .7, .8)
        frozen = (.25, .25, .5, .5, .5)
        high = (True, False, False, True, True)
        result = supported_highlight(source, frozen, high)
        self.assertEqual(result.status, 'ok')
        self.assertTrue(set(result.changed_indices) <= {3, 4})
        self.assertGreater(source[result.source_index], max(frozen))
        self.assertGreater(result.sse_reduction, 0.)
        for index in result.changed_indices:
            self.assertLessEqual(abs(source[index] - source[result.source_index]),
                                 abs(source[index] - frozen[index]))

    def test_unsupported_or_nonpositive_highlight_is_not_invented(self):
        for source, frozen, high in (((.3, .5), (.3, .5), (True, True)),
                                      ((.3, .9), (.3, .5), (False, False)),
                                      ((.3, .51), (.3, .5), (False, True))):
            with self.subTest(source=source, high=high):
                result = supported_highlight(source, frozen, high)
                self.assertEqual(result.status, 'no_supported_positive_accent')
                self.assertEqual(result.changed_indices, ())
                self.assertIsNone(result.source_index)

    def test_adaptive_histogram_preserves_integer_source_moments_and_observed_rgb_index(self):
        values = [.1, .105, .107, .11, .5, .9]
        minimum, span, bins, assignment = adaptive_histogram(values)
        self.assertEqual(minimum, .1)
        self.assertAlmostEqual(span, .8)
        self.assertEqual(assignment[:4], (0, 0, 0, 0))
        self.assertEqual(bins[0].count, 4)
        self.assertGreater(bins[0].sum_l2, 0.)
        # The first bin's observed sample nearest its center is source index 3,
        # not an RGB invented at the bin center and not always the first sample.
        self.assertEqual(bins[0].sample_index, 3)
        self.assertAlmostEqual(bins[0].representative_l, (.11 - .1) / .8)
        for item in bins:
            self.assertAlmostEqual(item.representative_l, (values[item.sample_index] - minimum) / span)
        normalized_error = .01 / span
        result = solve_observed_bins(bins, tone_error=normalized_error)
        self.assertEqual(result.status, 'ok')
        self.assertGreater(result.tone_count, 1)

    def test_adaptive_histogram_remains_single_tone_for_constant(self):
        minimum, span, bins, assignments = adaptive_histogram([.37] * 10)
        self.assertEqual(minimum, .37)
        self.assertEqual(span, 0.)
        self.assertEqual(len(bins), 1)
        self.assertEqual(assignments, (0,) * 10)
        self.assertEqual(solve_observed_bins(bins).tone_count, 1)

    def test_chroma_and_part_keys_separate_equal_lightness_ownership(self):
        self.assertNotEqual(chroma_cell_key(1, (.1, .1)), chroma_cell_key(1, (-.1, .1)))
        self.assertNotEqual(chroma_cell_key(1, (.1, .1)), chroma_cell_key(2, (.1, .1)))
        # Same cell membership guarantees pairwise chroma distance no more than
        # chroma_error, but nearby colors crossing a cell edge remain separate.
        self.assertEqual(chroma_cell_key(1, (.01, .01)), chroma_cell_key(1, (.015, .015)))
        self.assertEqual(chroma_cell_key(1, (-.0000001, .01)), chroma_cell_key(1, (.0000001, .01)))
        self.assertNotEqual(chroma_cell_key(1, (.020, .01)), chroma_cell_key(1, (.023, .01)))


if __name__ == '__main__':
    unittest.main()
