import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image
import trigger_cli
from trigger_cli import comparison_size


class TriggerCliTests(unittest.TestCase):
    def test_four_panel_size_is_known_before_writes(self):
        self.assertEqual(comparison_size((866,385),(192,433),2,4),(1640,966))

    def test_combined_preview_limit_not_just_each_panel(self):
        with self.assertRaises(ValueError):
            comparison_size((1200,1200),(1200,1200),4,4)

    def write_inputs(self, directory, *, enabled=True, rgba_reference=False):
        source = np.full((2,2,4),[160,130,100,255],np.uint8)
        reference = np.full((2,2,3),[80,100,130],np.uint8)
        if rgba_reference:
            reference = np.dstack((reference,np.full((2,2),255,np.uint8)))
            reference[0,0] = [17,19,23,0]
        Image.fromarray(source).save(directory/'source.png')
        Image.fromarray(reference).save(directory/'reference.png')
        config = {'source':'source.png','reference':'reference.png','base_grid':[2,2],
                  'preview_zoom':1,'features':{
                      'region_tones':{'enabled':enabled,'scope':{'kind':'all'},'options':{'tones':3}},
                      'cell_sampling':{'enabled':True,'scope':{'kind':'all'},
                                       'options':{'method':'source_regions'}}}}
        config_path = directory/'config.json'
        config_path.write_text(json.dumps(config),encoding='utf8')
        return config_path,source,reference

    def pipeline_result(self, source, rgb):
        native = source.copy()
        native[...,:3] = rgb
        yy,xx = np.indices(source.shape[:2])
        return {'image':native,'baseline':source.copy(),'cleaned_source':source.copy(),
                'colors_source':native.copy(),'before_lines':native.copy(),
                'scopes':{},'line_result':None,'line_geometry':None,'line_render':None,
                'sampling_source_xy':np.stack((xx,yy),axis=2),
                'erase_mask':np.zeros(source.shape[:2],bool),'metadata':{'features':{}}}

    def test_region_reference_is_passed_allowed_snapshotted_and_rerun_portably(self):
        for rgba in (False,True):
            with self.subTest(rgba=rgba), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                config_path,source,reference = self.write_inputs(directory,rgba_reference=rgba)
                reference_bytes = (directory/'reference.png').read_bytes()
                output = directory/'result'
                result = self.pipeline_result(source,reference[1,1,:3])
                with patch.object(trigger_cli,'normalize_triggered',return_value=result) as pipeline, \
                     patch.object(trigger_cli,'compare_sheet') as comparison, patch('builtins.print'):
                    trigger_cli.main(['--config',str(config_path),'--output',str(output)])
                np.testing.assert_array_equal(pipeline.call_args.kwargs['reference'],reference)
                self.assertTrue(comparison.call_args.kwargs['reference_used'])
                record = json.loads((output/'settings_and_result.json').read_text(encoding='utf8'))
                self.assertEqual(record['reference_file_sha256'],trigger_cli.sha(reference_bytes))
                self.assertEqual(record['reference_array_sha256'],trigger_cli.sha(reference.tobytes()))
                self.assertTrue(record['technical_checks']['reference_unchanged'])
                self.assertTrue(record['technical_checks']['opaque_rgb_from_source_or_reference'])
                self.assertFalse(record['technical_checks']['opaque_rgb_from_original'])
                rerun = json.loads((output/'rerun_config.json').read_text(encoding='utf8'))
                self.assertEqual((output/rerun['reference']).read_bytes(),reference_bytes)
                for module in ('boundary_pipeline.py','boundary_regions.py','region_palette.py'):
                    relative = 'src/perfect_pixel/'+module
                    self.assertIn(relative,record['code_sha256'])
                    self.assertEqual(trigger_cli.sha((output/'code'/relative).read_bytes()),
                                     record['code_sha256'][relative])
                with patch.object(trigger_cli,'normalize_triggered',return_value=result) as pipeline, \
                     patch.object(trigger_cli,'compare_sheet'), patch('builtins.print'):
                    trigger_cli.main(['--config',str(output/'rerun_config.json'),
                                      '--output',str(directory/'rerun')])
                np.testing.assert_array_equal(pipeline.call_args.kwargs['reference'],reference)

    def test_invalid_reference_provenance_and_processing_failure_create_no_output(self):
        for failure in ('hidden_reference_rgb','unknown_rgb','reference_mutation','algorithm_failure'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                config_path,source,reference = self.write_inputs(directory,rgba_reference=True)
                output = directory/'result'
                def process(*args,**kwargs):
                    if failure=='algorithm_failure':
                        raise RuntimeError('Unsupported region tone operation.')
                    if failure=='reference_mutation':
                        kwargs['reference'][1,1,0] ^= 1
                    rgb = reference[0,0,:3] if failure=='hidden_reference_rgb' else [1,2,3]
                    return self.pipeline_result(source,rgb)
                with patch.object(trigger_cli,'normalize_triggered',side_effect=process), \
                     patch('builtins.print'), self.assertRaises(RuntimeError):
                    trigger_cli.main(['--config',str(config_path),'--output',str(output)])
                self.assertFalse(output.exists())

    def test_active_reference_is_required_but_disabled_legacy_reference_is_not_loaded(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            config_path,source,_ = self.write_inputs(directory)
            config = json.loads(config_path.read_text(encoding='utf8'))
            config.pop('reference')
            config_path.write_text(json.dumps(config),encoding='utf8')
            with patch.object(trigger_cli,'normalize_triggered') as pipeline, \
                 patch('sys.stderr'), self.assertRaises(SystemExit):
                trigger_cli.main(['--config',str(config_path),'--output',str(directory/'missing')])
            pipeline.assert_not_called()
            self.assertFalse((directory/'missing').exists())
            config['reference'] = 'old-unused-reference-does-not-exist.png'
            config['features']['region_tones']['enabled'] = False
            config_path.write_text(json.dumps(config),encoding='utf8')
            with patch.object(trigger_cli,'normalize_triggered',return_value=self.pipeline_result(source,source[0,0,:3])) as pipeline, \
                 patch.object(trigger_cli,'compare_sheet'), patch('builtins.print'):
                trigger_cli.main(['--config',str(config_path),'--output',str(directory/'legacy')])
            self.assertNotIn('reference',pipeline.call_args.kwargs)
            record = json.loads((directory/'legacy'/'settings_and_result.json').read_text(encoding='utf8'))
            self.assertNotIn('reference_file_sha256',record)
            self.assertTrue(record['technical_checks']['opaque_rgb_from_original'])

    def test_large_diagnostics_are_saved_but_not_repeated_on_stdout(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            config_path,source,reference = self.write_inputs(directory)
            result = self.pipeline_result(source,reference[0,0,:3])
            result['metadata']['features']['region_tones'] = {
                'enabled':True, 'tones':3, 'region_colors':{'regions':[{'id':i} for i in range(500)]}}
            with patch.object(trigger_cli,'normalize_triggered',return_value=result), \
                 patch.object(trigger_cli,'compare_sheet'), patch('builtins.print') as printed:
                trigger_cli.main(['--config',str(config_path),'--output',str(directory/'result')])
            brief = json.loads(printed.call_args.args[0])
            self.assertNotIn('region_colors',brief['features']['region_tones'])
            record = json.loads((directory/'result'/'settings_and_result.json').read_text(encoding='utf8'))
            self.assertEqual(len(record['result']['features']['region_tones']['region_colors']['regions']),500)


if __name__=='__main__': unittest.main()
