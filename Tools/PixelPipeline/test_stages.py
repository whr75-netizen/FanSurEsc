"""Small regressions for the actual numeric contract and artifact boundaries."""
import json
import math
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np

from common import ROOT,basis,gap_coefficient,gap_aperture,read,write,receipt,verify_receipt,consistent_edges,parallel_double_strokes,surface_boundaries
from stages import execute,reuse_stage

class StageTests(unittest.TestCase):
    def setUp(self):self.contract=read(Path(__file__).with_name('desk_contract.json'))

    def test_2_to_1_camera_and_gap_perpendicular_width(self):
        r,u,d=basis(self.contract['camera'])
        np.testing.assert_allclose(np.stack([r,u,d])@np.stack([r,u,d]).T,np.eye(3),atol=1e-12)
        self.assertAlmostEqual(abs(u[0]/r[0]),.5)
        k=gap_coefficient(self.contract['camera']);self.assertAlmostEqual(k,96/math.sqrt(2))
        target=2/k
        self.assertAlmostEqual(target*k,2)
        self.assertLess((target-1e-6)*k,2)

    def test_finite_depth_blocks_a_two_pixel_front_gap(self):
        camera=self.contract['camera'];front_only=2/gap_coefficient(camera)
        initial=gap_aperture(front_only,.036,camera,2)
        self.assertEqual(initial['clear_width_pixels'],0)
        corrected=gap_aperture(initial['required_gap_m'],.036,camera,2)
        self.assertAlmostEqual(corrected['clear_width_pixels'],2)
        self.assertAlmostEqual(corrected['probe_x'],.018)

    def test_modified_file_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';source.write_text('original');out=root/'output';out.write_text('result')
            receipt(root,'example',[source],[out],{})
            verify_receipt(root/'stage_receipt.json')
            out.write_text('different result')
            with self.assertRaisesRegex(ValueError,'STALE_ARTIFACT'):verify_receipt(root/'stage_receipt.json')

    def test_object_render_cannot_replace_approved_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c=self.contract.copy();c['source_wood']='LocalOnly/DeskReference20/reference.png'
            path=root/'contract.json';write(path,c)
            result=execute('inputs',0,root/'run',path)
            self.assertEqual(result['state'],'blocked')
            self.assertEqual(result['diagnosis']['code'],'UNAPPROVED_MATERIAL_SOURCE')
            self.assertFalse((root/'run').exists())

    def test_repair_bound_stops_instead_of_changing_ppu(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c=json.loads(json.dumps(self.contract));c['pixel']['minimum_gap_pixels']=100
            path=root/'contract.json';write(path,c)
            write(root/'run/pass-0/settings.json',{'drawer_gap_override':None,'repair_history':[]})
            write(root/'run/pass-0/diagnose/diagnosis.json',{'issues':[{'code':'DRAWER_GAP_UNDERSAMPLED'}]})
            write(root/'run/geometry/geometry.json',{'drawer_span':1.3,'drawer_gap':.011,'parts':[{'name':'Drawer_-1','dimensions':[.64,.036,.19]}]})
            with self.assertRaisesRegex(ValueError,'exceeds declared style bound'):execute('repair',1,root/'run',path)
            self.assertFalse((root/'run/pass-1/settings.json').exists())

    def test_real_diagnosis_is_json_serializable_and_localized(self):
        actual=ROOT/'LocalOnly/PixelPipeline21/run01/pass-0/diagnose/diagnosis.json'
        if not actual.exists():self.skipTest('Actual pipeline diagnosis has not run yet')
        d=read(actual);json.dumps(d,allow_nan=False)
        self.assertEqual(d['state'],'repairable')
        self.assertEqual([i['code'] for i in d['issues']],['DRAWER_GAP_UNDERSAMPLED','DRAWER_GAP_OCCLUDED'])
        self.assertLess(d['drawer_gap_pixels'],1)

    def test_actual_double_seam_is_removed_without_traversal_order_dependency(self):
        actual=ROOT/'LocalOnly/PixelPipeline21/run01/pass-1/raster/buffers.npz'
        if not actual.exists():self.skipTest('Actual pipeline evidence has not run yet')
        b=np.load(actual)
        self.assertGreater(sum(q['count'] for q in parallel_double_strokes(b,b['edges'])),0)
        edge,records,_=consistent_edges(b,self.contract['camera'])
        self.assertEqual(parallel_double_strokes(b,edge),[])
        self.assertFalse(np.any(edge&~b['mask']))
        self.assertTrue(all(int(b['part'][y,x])==p and int(b['face'][y,x])==f for y,x,p,f in records))
        groups,silhouette=surface_boundaries(b)
        reverse={key:list(reversed(value)) for key,value in reversed(list(groups.items()))}
        with patch('common.surface_boundaries',return_value=(reverse,silhouette.copy())):
            opposite,_,_=consistent_edges(b,self.contract['camera'])
        np.testing.assert_array_equal(opposite,edge)

    def test_pixel_repair_cannot_reuse_geometry_after_gap_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp)
            write(run/'pass-0/settings.json',{'drawer_gap_override':.04})
            write(run/'pass-1/settings.json',{'drawer_gap_override':.06,'reuse_pass':0})
            with self.assertRaisesRegex(ValueError,'Geometry changed'):
                reuse_stage('raster',1,run,Path(__file__).with_name('desk_contract.json'))
            self.assertFalse((run/'pass-1/raster').exists())

if __name__=='__main__':unittest.main()
