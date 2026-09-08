"""Frozen-palette highlight contracts on synthetic arrays only."""
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from perfect_pixel import highlight_accents
from perfect_pixel.highlight_accents import add_highlight_accents, _best_tail
from perfect_pixel.palette import rgb_to_oklab
from perfect_pixel.spatial_tones import build_spatial_constraints


def scene():
    gray = np.round(np.linspace(80, 220, 80)).astype(np.uint8)
    source = np.full((64, 80, 4), 255, np.uint8)
    source[..., :3] = gray[None, :, None]
    base = np.full_like(source, 255)
    base[..., :3] = 140
    base[:, :32, :3] = 90
    return source, base, np.zeros(source.shape[:2], np.int32), np.ones(source.shape[:2], bool)


class HighlightAccentTests(unittest.TestCase):
    def test_coherent_highlight_keeps_frozen_shadow_and_base(self):
        source, base, labels, scope = scene()
        before = tuple(a.copy() for a in (source, base, labels, scope))
        result = add_highlight_accents(source, base, labels, scope)
        changed = result['overlay'][..., 3] == 255
        self.assertGreater(int(changed.sum()), 0)
        self.assertEqual(len(np.unique(result['overlay'][changed, :3], axis=0)), 1)
        self.assertTrue(np.all(base[changed, :3] == 140))
        np.testing.assert_array_equal(result['image'][~changed], base[~changed])
        np.testing.assert_array_equal(result['image'][changed], result['overlay'][changed])
        np.testing.assert_array_equal(result['image'][..., 3], base[..., 3])
        self.assertTrue(np.all(result['overlay'][~changed] == 0))
        source_rgb = set(map(tuple, source[..., :3].reshape(-1, 3)))
        self.assertTrue(set(map(tuple, result['overlay'][changed, :3])) <= source_rgb)
        for actual, original in zip((source, base, labels, scope), before):
            np.testing.assert_array_equal(actual, original)
        report = next(g for g in result['metadata']['groups'] if g['changed_source_pixels'])
        self.assertGreaterEqual(report['accent_lightness'] - report['frozen_brightest_lightness'], .025)
        self.assertLess(report['source_lightness_sse_after'], report['source_lightness_sse_before'])
        self.assertGreaterEqual(report['retained_support_contrast_after'], report['retained_support_contrast_before'])
        raw_l = rgb_to_oklab(source[..., :3].astype(np.float32) / 255)[..., 0]
        base_l = rgb_to_oklab(base[..., :3].astype(np.float32) / 255)[..., 0]
        output_l = rgb_to_oklab(result['image'][..., :3].astype(np.float32) / 255)[..., 0]
        self.assertTrue(np.all(abs(raw_l[changed] - output_l[changed]) <= abs(raw_l[changed] - base_l[changed]) + 1e-7))
        json.dumps(result['metadata'], allow_nan=False)

    def test_scoping_keeps_supports_and_changes_only_opaque_selected_pixels(self):
        source, base, labels, scope = scene()
        source[:2, :, 3] = 0
        base[:2] = [1, 2, 3, 0]
        source[2:4, :, 3] = 120
        base[2:4, :, 3] = 120
        all_result = add_highlight_accents(source, base, labels, scope)
        scope[:32] = False
        limited = add_highlight_accents(source, base, labels, scope)
        self.assertGreater(limited['metadata']['changed_source_pixels'], 0)
        self.assertEqual(all_result['metadata']['groups'][0]['spatial_support'],
                         limited['metadata']['groups'][0]['spatial_support'])
        np.testing.assert_array_equal(limited['image'][~scope], base[~scope])
        np.testing.assert_array_equal(limited['image'][:4], base[:4])
        self.assertTrue(np.all(limited['overlay'][:4] == 0))
        np.testing.assert_array_equal(limited['image'][..., 3], base[..., 3])

    def test_flat_noise_and_already_bright_sources_do_not_force_accents(self):
        source, base, labels, scope = scene()
        flat = np.full_like(source, [140, 140, 140, 255])
        noise = source.copy()
        noise[..., :3] = np.random.default_rng(827).permutation(source[..., :3].reshape(-1, 3)).reshape(source.shape[0], source.shape[1], 3)
        for raw, frozen in ((flat, flat), (noise, base), (source, source)):
            with self.subTest(raw_range=int(np.ptp(raw[..., 0])), frozen_equal=np.array_equal(raw, frozen)):
                result = add_highlight_accents(raw, frozen, labels, scope)
                np.testing.assert_array_equal(result['image'], frozen)
                self.assertEqual(result['metadata']['changed_source_pixels'], 0)
                self.assertTrue(np.all(result['overlay'] == 0))

    def test_unlabelled_and_transparent_pixels_never_receive_overlay(self):
        source, base, labels, scope = scene()
        labels[:32] = -1
        base[40, 70, 3] = 0
        result = add_highlight_accents(source, base, labels, scope)
        self.assertGreater(result['metadata']['changed_source_pixels'], 0)
        np.testing.assert_array_equal(result['image'][labels < 0], base[labels < 0])
        np.testing.assert_array_equal(result['image'][40, 70], base[40, 70])
        self.assertEqual(int(result['overlay'][40, 70, 3]), 0)

    def test_domain_rgb_provenance_and_independent_frozen_top_tones(self):
        source, base, labels, scope = scene()
        # A separate actual-color ramp must never borrow the first domain's gray.
        source[32:, :, 0] = 230
        base[32:, :, 0] = 230
        labels[32:] = 4
        result = add_highlight_accents(source, base, labels, scope, chroma_error=.2)
        changed = result['overlay'][..., 3] != 0
        self.assertGreater(int(changed[:32].sum()), 0)
        self.assertGreater(int(changed[32:].sum()), 0)
        for identifier in (0, 4):
            observed = set(map(tuple, source[labels == identifier, :3]))
            accents = set(map(tuple, result['overlay'][changed & (labels == identifier), :3]))
            self.assertTrue(accents <= observed)

    def test_tail_choice_matches_exhaustive_frozen_base_minimum(self):
        rng = np.random.default_rng(40)
        for _ in range(20):
            observed_l = np.sort(rng.choice(np.linspace(.25, .9, 100), 12, replace=False))
            observed_rgb = np.arange(36, dtype=np.uint8).reshape(12, 3)
            observed_counts = rng.integers(1, 30, 12)
            lightness = rng.choice(observed_l, 60)
            base_l = .44
            selected = _best_tail(lightness, base_l, observed_l, observed_rgb, observed_counts, .025)
            brute_gain = 0.
            for cutoff in np.unique(lightness):
                tail = lightness[lightness >= cutoff]
                for accent_l in observed_l:
                    if accent_l < base_l + .025 or accent_l > 2 * cutoff - base_l:
                        continue
                    gain = float(np.sum((tail - base_l) ** 2 - (tail - accent_l) ** 2))
                    brute_gain = max(brute_gain, gain)
            if selected is None:
                self.assertLessEqual(brute_gain, 1e-12)
            else:
                self.assertAlmostEqual(selected['predicted_sse_reduction'], brute_gain, delta=1e-12)

    def test_optional_support_return_keeps_existing_api_and_metadata(self):
        values = np.repeat(np.linspace(.3, .7, 80)[None], 64, axis=0)
        positions = np.column_stack(np.nonzero(np.ones(values.shape, bool)))
        colors, inverse = np.unique(values.ravel(), return_inverse=True)
        old = build_spatial_constraints(values.ravel(), inverse, positions, len(colors))
        new = build_spatial_constraints(values.ravel(), inverse, positions, len(colors), return_supports=True)
        self.assertEqual(len(old), 2)
        self.assertEqual(len(new), 3)
        self.assertEqual(old[1], new[1])
        np.testing.assert_array_equal(old[0][0]['coefficients'], new[0][0]['coefficients'])
        supports = new[2]
        self.assertEqual(supports['high'].shape, (values.size,))
        self.assertEqual(supports['high'].dtype, np.bool_)
        self.assertFalse(np.any(supports['high'] & supports['low']))
        contrast = float(values.ravel()[supports['high']].mean() - values.ravel()[supports['low']].mean())
        self.assertAlmostEqual(contrast, new[1]['selected_source_contrast_l'])
        json.dumps(new[1], allow_nan=False)
        flat = build_spatial_constraints(np.ones(values.size) * .5, inverse, positions, len(colors), return_supports=True)
        self.assertEqual(flat[0], [])
        self.assertIsNone(flat[2])
        with self.assertRaises(ValueError):
            build_spatial_constraints(values.ravel(), inverse, positions, len(colors), return_supports='yes')

    def test_invalid_options_shapes_and_resource_bounds_fail_without_changes(self):
        source, base, labels, scope = scene()
        source[..., 3] = 0
        for name in ('chroma_error', 'minimum_contrast'):
            for value in (0, -1, True, np.bool_(True), float('nan'), float('inf'), 1.1):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        add_highlight_accents(source, base, labels, scope, **{name: value})
        for args in ((source.astype(float), base, labels, scope),
                     (source, base[:, :-1], labels, scope),
                     (source, base, labels.astype(float), scope),
                     (source, base, labels - 2, scope),
                     (source, base, labels, scope.astype(np.uint8))):
            with self.assertRaises(ValueError):
                add_highlight_accents(*args)
        with mock.patch.object(highlight_accents, 'MAX_SOURCE_PIXELS', 1):
            with self.assertRaisesRegex(ValueError, '4MP pixel resource bound'):
                add_highlight_accents(source, base, labels, scope)


if __name__ == '__main__':
    unittest.main()
