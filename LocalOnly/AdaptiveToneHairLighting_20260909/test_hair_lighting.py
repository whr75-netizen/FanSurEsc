"""Mathematical contract checks, not a GPU or Unity execution test.

The tiny independent oracle exhaustively considers observed representatives;
it does not reproduce the compute shader's 32-bin DP, spatial guard or rounding.
Hair acceptance: RMSE(E) <= relative_error * max(mean(E), illumination_floor).
Only palette membership is normalized: emitted colors are source RGB samples.
"""

from itertools import combinations
from math import sqrt
import unittest


def observed_fit(values, tolerance):
    """Exact nearest observed palette for small, unguarded 1-D test cases."""
    candidates = tuple(sorted(set(values)))
    for count in range(1, len(candidates) + 1):
        best = None
        for palette in combinations(candidates, count):
            assigned = tuple(min(palette, key=lambda p: (abs(v - p), p)) for v in values)
            rmse = sqrt(sum((v - p) ** 2 for v, p in zip(values, assigned)) / len(values))
            candidate = (rmse, palette, assigned)
            if best is None or candidate < best:
                best = candidate
        if best[0] <= tolerance + 1e-12:
            return best[1], best[2], best[0]
    raise AssertionError("Observed samples must fit exactly at full palette size")


def hair_fit(illumination, relative_error=.10, illumination_floor=.02):
    scale = max(sum(illumination) / len(illumination), illumination_floor)
    return observed_fit(illumination, relative_error * scale)


def linear_oklab_l(rgb):
    l = sum(c * w for c, w in zip(rgb, (.4122214708, .5363325363, .0514459929))) ** (1 / 3)
    m = sum(c * w for c, w in zip(rgb, (.2119034982, .6806995451, .1073969566))) ** (1 / 3)
    s = sum(c * w for c, w in zip(rgb, (.0883024619, .2817188376, .6299787005))) ** (1 / 3)
    return .2104542553 * l + .7936177850 * m - .0040720468 * s


class HairIlluminationContractTests(unittest.TestCase):
    def test_dark_brown_can_pass_old_absolute_error_despite_distinct_illumination(self):
        illumination = (.4, .8, 1.2)
        brown = (.012, .004, .001)
        rendered_l = tuple(linear_oklab_l(tuple(c * e for c in brown)) for e in illumination)
        old_palette, _, _ = observed_fit(rendered_l, .06)
        new_palette, _, _ = hair_fit(illumination)
        self.assertEqual(len(old_palette), 1)
        self.assertEqual(len(new_palette), 3)

    def test_stage_count_is_not_forced_to_three(self):
        cases = (((1., 1., 1.), 1), ((.5, .5, 1., 1.), 2), ((.4, .8, 1.2), 3),
                 ((.25, .75, 1.25, 1.75), 4))
        for illumination, expected in cases:
            with self.subTest(illumination=illumination):
                self.assertEqual(len(hair_fit(illumination)[0]), expected)

    def test_day_night_exposure_scales_observed_output_without_auto_brightening(self):
        day = (.4, .8, 1.2)
        night = tuple(e * .1 for e in day)
        day_palette, day_assignment, _ = hair_fit(day)
        night_palette, night_assignment, _ = hair_fit(night)
        self.assertEqual(len(day_palette), len(night_palette))
        brown = (.012, .004, .001)
        day_rgb = tuple(tuple(c * e for c in brown) for e in day_assignment)
        night_rgb = tuple(tuple(c * e for c in brown) for e in night_assignment)
        for lit_day, lit_night in zip(day_rgb, night_rgb):
            for value_day, value_night in zip(lit_day, lit_night):
                self.assertAlmostEqual(value_night, .1 * value_day)

    def test_min_max_spread_alone_does_not_amplify_tiny_variation(self):
        illumination = (.99, 1., 1.01)
        self.assertEqual(len(hair_fit(illumination)[0]), 1)
        normalized = tuple((e - min(illumination)) / (max(illumination) - min(illumination))
                           for e in illumination)
        self.assertEqual(len(observed_fit(normalized, .10)[0]), 3)

    def test_darkness_floor_does_not_turn_near_zero_noise_into_extra_stages(self):
        palette, assigned, error = hair_fit((0., .001, .002))
        self.assertEqual(len(palette), 1)
        self.assertLessEqual(error, .10 * .02)
        self.assertTrue(all(value in (0., .001, .002) for value in assigned))

    def test_constant_black_is_finite_single_observed_tone(self):
        palette, assignment, error = hair_fit((0.,) * 9)
        self.assertEqual(palette, (0.,))
        self.assertEqual(assignment, (0.,) * 9)
        self.assertEqual(error, 0.)

    def test_rms_requires_extra_stage_without_spatial_guard(self):
        # This oracle has no image-space guard. Significant variation alone
        # must still stop a single representative from flattening the input.
        palette, _, error = hair_fit((1.,) * 20 + (1.6,))
        self.assertEqual(palette, (1., 1.6))
        self.assertEqual(error, 0.)

    def test_same_illumination_partitions_keep_each_materials_actual_rgb(self):
        illumination = (.4, .6, .8, 1.)
        _, assignment, _ = hair_fit(illumination, relative_error=.20)
        for albedo in ((.012, .004, .001), (.6, .4, .2)):
            source = tuple(tuple(e * c for c in albedo) for e in illumination)
            output = tuple(source[illumination.index(e)] for e in assignment)
            self.assertTrue(all(rgb in source for rgb in output))
            # Preserve the actual authored radiometric scale for both colors.
            self.assertLessEqual(max(rgb[0] for rgb in output), max(rgb[0] for rgb in source))

    def test_relative_guard_threshold_uses_same_illumination_units(self):
        for mean in (.08, .8, 8.):
            threshold = .025 * max(mean, .02)
            self.assertAlmostEqual(threshold / mean, .025)
        self.assertEqual(.025 * max(0., .02), .0005)


if __name__ == "__main__":
    unittest.main()
