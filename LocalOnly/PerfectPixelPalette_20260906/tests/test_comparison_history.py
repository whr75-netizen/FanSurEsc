import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageFont

import trigger_cli


class ComparisonHistoryTests(unittest.TestCase):
    def write_inputs(self, directory):
        source = np.full((3,4,4),[100,130,160,255],np.uint8)
        Image.fromarray(source).save(directory/'source.png')
        history = []
        for name,color in [('continuous',[30,60,90,255]),('weighted',[60,90,120,255])]:
            array = np.full_like(source,color)
            Image.fromarray(array).save(directory/f'{name}.png')
            history.append({'path':f'{name}.png','label':name.upper()})
        config = {'source':'source.png','base_grid':[4,3],'preview_zoom':2,'features':{},
                  'comparison_history':history}
        return config,source

    def save_config(self, directory, config):
        path = directory/'config.json'
        path.write_text(json.dumps(config),encoding='utf8')
        return path

    def pipeline_result(self, source):
        yy,xx = np.indices(source.shape[:2])
        return {'image':source.copy(),'baseline':source.copy(),'cleaned_source':source.copy(),
                'colors_source':source.copy(),'before_lines':source.copy(),
                'scopes':{},'line_result':None,'line_geometry':None,'line_render':None,
                'sampling_source_xy':np.stack((xx,yy),axis=2),
                'erase_mask':np.zeros(source.shape[:2],bool),'metadata':{'features':{}}}

    def test_ordered_four_panel_board_preserves_inputs_and_portable_snapshots(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            config,source = self.write_inputs(directory)
            inputs = {name:(directory/name).read_bytes()
                      for name in ('source.png','continuous.png','weighted.png')}
            config_path = self.save_config(directory,config)
            output = directory/'result'
            font = ImageFont.load_default()
            with patch.object(trigger_cli,'normalize_triggered',return_value=self.pipeline_result(source)), \
                 patch.object(trigger_cli.ImageFont,'truetype',return_value=font), \
                 patch.object(trigger_cli.ImageDraw.ImageDraw,'text') as labels, patch('builtins.print'):
                trigger_cli.main(['--config',str(config_path),'--output',str(output)])
            self.assertEqual([call.args[1] for call in labels.call_args_list[:4]],
                             ['SOURCE','CONTINUOUS','WEIGHTED','NEW / SCOPED NORMALIZATION'])
            with Image.open(output/'comparison.png') as board:
                self.assertEqual(board.size,trigger_cli.comparison_size(source.shape[:2],(4,3),2,4))
                for index,color in enumerate(((100,130,160),(30,60,90),(60,90,120),(100,130,160))):
                    self.assertEqual(board.getpixel((20+index*28+4,51)),color)
            record = json.loads((output/'settings_and_result.json').read_text(encoding='utf8'))
            self.assertEqual(record['input_file_sha256'],trigger_cli.sha(inputs['source.png']))
            self.assertTrue(record['technical_checks']['comparison_history_unchanged'])
            rerun = json.loads((output/'rerun_config.json').read_text(encoding='utf8'))
            for index,entry in enumerate(config['comparison_history']):
                saved = record['comparison_history'][index]
                snapshot = output/rerun['comparison_history'][index]['path']
                self.assertEqual(saved['path'],str((directory/entry['path']).resolve()))
                self.assertEqual(saved['label'],entry['label'])
                self.assertEqual(saved['snapshot_path'],rerun['comparison_history'][index]['path'])
                self.assertEqual(snapshot.read_bytes(),inputs[entry['path']])
                self.assertEqual(saved['file_sha256'],trigger_cli.sha(inputs[entry['path']]))
                with Image.open(snapshot) as image:
                    self.assertEqual(saved['array_sha256'],trigger_cli.sha(np.array(image).tobytes()))
            for name,data in inputs.items():
                self.assertEqual((directory/name).read_bytes(),data)
            with patch.object(trigger_cli,'normalize_triggered',return_value=self.pipeline_result(source)), \
                 patch.object(trigger_cli,'compare_sheet') as compare, patch('builtins.print'):
                trigger_cli.main(['--config',str(output/'rerun_config.json'),
                                  '--output',str(directory/'rerun')])
            self.assertEqual([label for array,label in compare.call_args.kwargs['history']],
                             ['CONTINUOUS','WEIGHTED'])

    def test_invalid_history_configuration_rejected_before_processing_or_writes(self):
        valid = {'path':'continuous.png','label':'CONTINUOUS'}
        invalid = [None,True,{},'continuous.png',[valid]*5,[None],[{}],
                   [{'path':'continuous.png'}],[{'path':False,'label':'A'}],
                   [{'path':'  ','label':'A'}],[{'path':'continuous.png','label':1}],
                   [{'path':'continuous.png','label':''}],
                   [{'path':'continuous.png','label':'A\nB'}],
                   [dict(valid,extra=True)]]
        for history in invalid:
            with self.subTest(history=history), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                config,_ = self.write_inputs(directory)
                config['comparison_history'] = history
                path = self.save_config(directory,config)
                with patch.object(trigger_cli,'normalize_triggered') as pipeline, \
                     patch('sys.stderr'), self.assertRaises(SystemExit):
                    trigger_cli.main(['--config',str(path),'--output',str(directory/'result')])
                pipeline.assert_not_called()
                self.assertFalse((directory/'result').exists())

    def test_incompatible_inputs_rejected_before_processing_or_writes(self):
        for case in ('previous','line_first','rgb','grid','scale_override','missing'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                config,source = self.write_inputs(directory)
                extra_args = []
                if case=='previous':
                    config['comparison_previous'] = 'weighted.png'
                elif case=='line_first':
                    config['features']['line_normalization'] = {'enabled':True,'options':{'mode':'line_first'}}
                elif case=='rgb':
                    Image.fromarray(source[...,:3]).save(directory/'continuous.png')
                elif case=='grid':
                    Image.fromarray(source[:2]).save(directory/'continuous.png')
                elif case=='scale_override':
                    extra_args = ['--scale','2.0']
                else:
                    config['comparison_history'][0]['path'] = 'missing.png'
                path = self.save_config(directory,config)
                with patch.object(trigger_cli,'normalize_triggered') as pipeline, \
                     patch('sys.stderr'), self.assertRaises(SystemExit):
                    trigger_cli.main(['--config',str(path),'--output',str(directory/'result')]+extra_args)
                pipeline.assert_not_called()
                self.assertFalse((directory/'result').exists())

    def test_history_changed_during_processing_is_not_saved(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            config,source = self.write_inputs(directory)
            path = self.save_config(directory,config)
            def process(*args,**kwargs):
                Image.fromarray(source).save(directory/'continuous.png')
                return self.pipeline_result(source)
            with patch.object(trigger_cli,'normalize_triggered',side_effect=process), \
                 self.assertRaisesRegex(RuntimeError,'history input changed'):
                trigger_cli.main(['--config',str(path),'--output',str(directory/'result')])
            self.assertFalse((directory/'result').exists())

    def test_four_history_entries_supported_and_combined_size_checked_upfront(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            config,source = self.write_inputs(directory)
            config['comparison_history'] *= 2
            path = self.save_config(directory,config)
            with patch.object(trigger_cli,'normalize_triggered',return_value=self.pipeline_result(source)), \
                 patch.object(trigger_cli,'compare_sheet') as compare, \
                 patch.object(trigger_cli,'comparison_size',wraps=trigger_cli.comparison_size) as size, \
                 patch('builtins.print'):
                trigger_cli.main(['--config',str(path),'--output',str(directory/'result')])
            self.assertEqual(len(compare.call_args.kwargs['history']),4)
            self.assertEqual(size.call_args.args[-1],6)
            with patch.object(trigger_cli,'comparison_size',side_effect=ValueError('Full comparison exceeds 32MP.')), \
                 patch.object(trigger_cli,'normalize_triggered') as pipeline, \
                 self.assertRaisesRegex(ValueError,'32MP'):
                trigger_cli.main(['--config',str(path),'--output',str(directory/'oversized')])
            pipeline.assert_not_called()
            self.assertFalse((directory/'oversized').exists())

    def test_previous_scale_override_and_line_first_remain_usable_without_history(self):
        for line_first in (False,True):
            with self.subTest(line_first=line_first), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                config,source = self.write_inputs(directory)
                config.pop('comparison_history')
                config['comparison_previous'] = 'weighted.png'
                config['base_grid'] = [2,2]
                if line_first:
                    config['features']['line_normalization'] = {'enabled':True,'options':{'mode':'line_first'}}
                result = self.pipeline_result(np.full((4,4,4),source[0,0],np.uint8))
                if line_first:
                    result['line_geometry'] = {'fixed_line_mask':np.ones((4,4),bool)}
                    result['line_render'] = {}
                path = self.save_config(directory,config)
                with patch.object(trigger_cli,'normalize_triggered',return_value=result), \
                     patch.object(trigger_cli,'compare_sheet') as compare, patch('builtins.print'):
                    trigger_cli.main(['--config',str(path),'--output',str(directory/'result'),'--scale','2.0'])
                self.assertIsNone(compare.call_args.kwargs['previous'])
                self.assertEqual(compare.call_args.kwargs['history'],[])
                self.assertEqual(compare.call_args.kwargs['fixed_lines'] is not None,line_first)
                self.assertEqual((directory/'result'/'comparison_previous.png').read_bytes(),
                                 (directory/'weighted.png').read_bytes())


if __name__=='__main__':
    unittest.main()
