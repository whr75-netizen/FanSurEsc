import json
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

import trigger_cli
from perfect_pixel.tone_controls import resolve_tone_controls, validate_tone_controls
from perfect_pixel.trigger_pipeline import normalize_triggered


def features():
    return {'region_tones': {'enabled': True, 'scope': {'kind': 'all'},
                             'options': {'mode': 'continuous', 'tone_policy': 'spatial_steps'}},
            'highlight_accents': {'enabled': True, 'scope': {'kind': 'all'}},
            'cell_sampling': {'enabled': True, 'scope': {'kind': 'all'},
                              'options': {'method': 'source_regions'}}}


class ToneControlsTests(unittest.TestCase):
    def test_defaults_match_legacy_pipeline_without_mutating_inputs(self):
        source = np.full((32, 48, 4), 255, np.uint8)
        source[..., :3] = np.round(np.linspace(70, 175, 48)).astype(np.uint8)[None, :, None]
        original_features = features(); before = deepcopy(original_features)
        expanded = resolve_tone_controls(original_features, {})
        old = normalize_triggered(source, (24, 16), features=original_features, reference=source)
        new = normalize_triggered(source, (24, 16), features=expanded, reference=source)
        for key in ('image', 'layer_base', 'highlight_overlay', 'sampling_source_xy', 'colors_source'):
            np.testing.assert_array_equal(old[key], new[key])
        self.assertEqual(original_features, before)

    def test_editable_values_route_once_and_preserve_feature_switches(self):
        cfg = features(); cfg['highlight_accents']['enabled'] = False
        controls = {'tone_error': .09, 'minimum_contrast': .04,
                    'highlight_minimum_contrast': .08,
                    'spatial_options': {'minimum_coherence': .6}}
        before = deepcopy(controls)
        expanded = resolve_tone_controls(cfg, controls)
        self.assertEqual(expanded['region_tones']['options']['tone_error'], .09)
        self.assertEqual(expanded['region_tones']['options']['minimum_contrast'], .04)
        self.assertEqual(expanded['region_tones']['options']['spatial_options']['minimum_coherence'], .6)
        self.assertEqual(expanded['highlight_accents']['options'], {'minimum_contrast': .08})
        self.assertFalse(expanded['highlight_accents']['enabled'])
        self.assertEqual(controls, before)
        expanded['region_tones']['options']['spatial_options']['scale_fractions'][0] = .01
        self.assertEqual(validate_tone_controls({})['spatial_options']['scale_fractions'][0], .02)
        del cfg['highlight_accents']
        self.assertNotIn('highlight_accents', resolve_tone_controls(cfg, {}))

    def test_duplicate_owners_and_wrong_policy_are_rejected(self):
        for name, options in [('region_tones', {'tone_error': .06}),
                              ('highlight_accents', {'minimum_contrast': .025}),
                              ('highlight_accents', {'chroma_error': .06})]:
            cfg = features(); cfg[name].setdefault('options', {}).update(options)
            with self.subTest(name=name, options=options), self.assertRaises(ValueError):
                resolve_tone_controls(cfg, {})
        cfg = features(); cfg['region_tones']['options']['tone_policy'] = 'weighted_steps'
        with self.assertRaises(ValueError): resolve_tone_controls(cfg, {})

    def test_invalid_values_are_not_silently_clamped(self):
        for controls in (None, [], {'unknown': .2}, {'tone_error': True}, {'tone_error': 0},
                         {'tone_error': 1.1}, {'tone_error': float('nan')},
                         {'highlight_minimum_contrast': '0.05'}, {'spatial_options': None},
                         {'spatial_options': {'minimum_coherence': False}}):
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                validate_tone_controls(controls)

    def test_cli_preserves_editable_controls_and_records_effective_values(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = np.full((12, 12, 4), [120, 90, 75, 255], np.uint8)
            Image.fromarray(source).save(directory / 'source.png')
            cfg = {'source': 'source.png', 'reference': 'source.png', 'base_grid': [12, 12],
                   'preview_zoom': 1, 'features': features(),
                   'tone_controls': {'tone_error': .09, 'highlight_minimum_contrast': .04}}
            path = directory / 'config.json'; path.write_text(json.dumps(cfg), encoding='utf8')
            with patch.object(trigger_cli, 'compare_sheet'), patch('builtins.print'):
                trigger_cli.main(['--config', str(path), '--output', str(directory / 'first')])
                trigger_cli.main(['--config', str(directory / 'first' / 'rerun_config.json'),
                                  '--output', str(directory / 'second'), '--disable', 'highlight_accents'])
            record = json.loads((directory / 'first' / 'settings_and_result.json').read_text(encoding='utf8'))
            self.assertEqual(record['configuration']['tone_controls'], cfg['tone_controls'])
            self.assertEqual(record['effective_features']['region_tones']['options']['tone_error'], .09)
            self.assertEqual(record['result']['features']['region_tones']['tone_error'], .09)
            self.assertEqual(record['result']['features']['highlight_accents']['minimum_contrast'], .04)
            self.assertIn('src/perfect_pixel/tone_controls.py', record['code_sha256'])
            rerun = json.loads((directory / 'first' / 'rerun_config.json').read_text(encoding='utf8'))
            self.assertEqual(rerun['tone_controls'], cfg['tone_controls'])
            self.assertEqual(rerun['features'], cfg['features'])
            second = json.loads((directory / 'second' / 'settings_and_result.json').read_text(encoding='utf8'))
            self.assertFalse(second['result']['features']['highlight_accents']['enabled'])
            with Image.open(directory / 'first' / 'pixel_native.png') as actual:
                np.testing.assert_array_equal(np.array(actual), source)

    def test_cli_rejects_controls_before_reading_or_processing_image(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            cfg = {'source': 'absent.png', 'base_grid': [12, 12], 'features': features(),
                   'tone_controls': {'minimum_contrast': -1}}
            path = directory / 'config.json'; path.write_text(json.dumps(cfg), encoding='utf8')
            with patch('sys.stderr'), patch.object(trigger_cli, 'normalize_triggered') as pipeline, \
                 self.assertRaises(SystemExit):
                trigger_cli.main(['--config', str(path), '--output', str(directory / 'out')])
            pipeline.assert_not_called()
            self.assertFalse((directory / 'out').exists())


if __name__ == '__main__': unittest.main()
