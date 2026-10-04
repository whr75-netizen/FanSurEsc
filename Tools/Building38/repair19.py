"""Repair serialized cabinet material annotations; compare direct native densities."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image
import building16 as b
from geometry16 import build_asset
from night18 import caches, shade, FIXTURE

ROOT = b.ROOT
PREVIOUS = ROOT/'docs/artifacts/building39/run02'
IDS = ['empty_counter', 'island_body_template', 'utility_bench', 'cleaning_cabinet']


def calc(out):
    fine = out/'fine'; fine.mkdir()
    catalog = [x for x in b.read(PREVIOUS/'geometry-catalog.json') if x['id'] in IDS]
    if len(catalog) != 4 or not all(b.geometry_metadata(x).get('cabinet_design') for x in catalog):
        raise ValueError('Actual serialized cabinet designs required')
    for item in catalog:
        target = fine/item['id']; target.mkdir()
        for name in ['geometry.npz', 'geometry.json', 'mesh.json']:
            shutil.copyfile(PREVIOUS/item['id']/name, target/name)
    b.write(fine/'geometry-catalog.json', catalog)
    b.materials(fine); b.export(fine)
    if b.sha(fine/'palette.png') != b.sha(PREVIOUS/'palette.png'):
        raise ValueError('Observed palette changed')
    counts = []
    for item in catalog:
        ident = item['id']; data = b.load(fine, item)
        old = np.array(Image.open(PREVIOUS/ident/'material.png'))
        new = np.array(Image.open(fine/ident/'material.png'))
        if not np.array_equal(old[..., 2:], new[..., 2:]):
            raise ValueError('Edge/coverage changed: '+ident)
        for name in ['position.f32', 'normal.f32', 'mesh.json', 'geometry.npz']:
            if b.sha(fine/ident/name) != b.sha(PREVIOUS/ident/name):
                raise ValueError('Geometry changed: '+ident+'/'+name)
        body = (data['part'] == 0) & data['mask']
        added = int(np.count_nonzero(body & (new[..., 0] == 3) & (old[..., 0] != 3)))
        counts.append({'id':ident,'body_gold_added':added,'size':[new.shape[1],new.shape[0]]})
    if {x['id']:x['body_gold_added'] for x in counts} != {
            'empty_counter':1810,'island_body_template':414,'utility_bench':0,'cleaning_cabinet':0}:
        raise ValueError('Expected visible original inlay paths failed')
    palette = np.array(Image.open(fine/'palette.png').convert('RGB'))
    material = np.array(Image.open(fine/'empty_counter/material.png').convert('RGBA'))
    Image.fromarray(shade(material, palette, FIXTURE)).save(out/'cpu-fixture.png')
    coarse = out/'coarse'; coarse.mkdir(); coarse_catalog=[]
    asset = next(a for a in b.read(ROOT/'Tools/Building37/input-contract.json')['assets'] if a['id']=='empty_counter')
    ppu = b.PPU/2
    data = build_asset(asset, ppu=ppu)
    b.save_geometry(coarse, 'empty_counter', data, coarse_catalog, ppu=ppu)
    b.write(coarse/'geometry-catalog.json', coarse_catalog)
    b.materials(coarse); b.export(coarse)
    original = b.load(fine, next(x for x in catalog if x['id']=='empty_counter'))
    if not np.array_equal(data['mesh_vertices'], original['mesh_vertices']) or not np.array_equal(data['mesh_triangles'], original['mesh_triangles']):
        raise ValueError('Density comparison changed physical solids')
    handles = [int(np.count_nonzero(data['mask'] & (data['part']==i))) for i in [2,3,4]]
    if min(handles) < 4:
        raise ValueError('Coarser density discarded handle features')
    b.write(out/'cpu-observation.json', {'gold':counts,'coarse_ppu':ppu,
        'coarse_size':data['size'],'coarse_handle_pixels':handles,'physical_geometry_identical':True,
        'image_resize_in_production':0,'density_comparison_only':True})
    b.write(out/'frozen-caches.json', caches())
    print(json.dumps({'success':True,'gold':counts,'coarse_size':data['size'],'handles':handles}))


def gate(out, observation=None):
    observation=observation or out
    if b.read(out/'frozen-caches.json') != caches():
        raise ValueError('Existing geometry/cache files changed')
    cpu=np.array(Image.open(out/'cpu-fixture.png').convert('RGBA')).astype(np.int16)
    gpu=np.array(Image.open(observation/'gpu-fixture.png').convert('RGBA')).astype(np.int16)
    mask=cpu[...,3]>=128; mismatch=int(np.count_nonzero(mask!=(gpu[...,3]>=128)))
    error=int(np.abs(cpu[mask,:3]-gpu[mask,:3]).max(initial=0))
    if mismatch or error>2:raise ValueError('Repaired material GPU mismatch')
    coarse_material=np.array(Image.open(out/'coarse/empty_counter/material.png').convert('RGBA'))
    coarse_cpu=shade(coarse_material,np.array(Image.open(out/'coarse/palette.png').convert('RGB')),FIXTURE)
    coarse_gpu=np.array(Image.open(observation/'gpu-coarse-fixture.png').convert('RGBA')).astype(np.int16)
    coarse_mask=coarse_cpu[...,3]>=128
    coarse_mismatch=int(np.count_nonzero(coarse_mask!=(coarse_gpu[...,3]>=128)))
    coarse_error=int(np.abs(coarse_cpu.astype(np.int16)[coarse_mask,:3]-coarse_gpu[coarse_mask,:3]).max(initial=0))
    if coarse_mismatch or coarse_error>2:raise ValueError('Direct coarse GPU row/coverage mismatch')
    r=b.read(observation/'unity-observation.json')
    if r['mapBindings']!=4 or not r['existingGeometryPreserved'] or not r['sameComparisonCamera']:
        raise ValueError('Wrong binding or comparison camera')
    if abs(r['fineScreenPixel']-1)>.001 or abs(r['coarseScreenPixel']-2)>.001 or r['shaderErrors']:
        raise ValueError('Direct density display failed')
    game=b.read(out/'play/play-observation.json')
    if not game['isPlayMode'] or not game['sameMapsAndGeometry'] or not game['samePlayerAndCamera'] or game['shaderErrors']:
        raise ValueError('Actual unchanged gameplay observation required')
    if abs(game['pixelSpacing']-1)>.001 or abs(game['pitch']-30)>.001 or abs(game['yaw']-350)>.001:
        raise ValueError('Production camera/density changed')
    b.write(observation/'validation.json', {'success':True,'body_gold_restored':2224,'gpu_rgb_error':error,
        'coverage_mismatch':mismatch,'cache_files_unchanged':len(caches()),'production_density_changed':False,
        'coarse_gpu_rgb_error':coarse_error,'coarse_coverage_mismatch':coarse_mismatch,
        'comparison_screen_pixels':[r['fineScreenPixel'],r['coarseScreenPixel']],
        'art_approval':'not claimed; direct comparison provided'})
    print(json.dumps(b.read(observation/'validation.json')))


def reopen_comparison(out, observation):
    if not observation or observation.exists() or not observation.is_relative_to(out):
        raise ValueError('Fresh dependent observation folder required')
    graph=b.read(out/'graph.json')
    graph['entry']='unity';graph['max_steps']=2
    graph['goal']='Correct temporary float-map row direction; reuse unchanged material calculation and Play observation'
    graph['nodes']=[n for n in graph['nodes'] if n['id']!='material']
    unit=graph['nodes'][0]
    unit['inputs']={'source':{'literal':str(out)},'output':{'literal':str(observation)}}
    unit['parameters']['scope']='Recapture only the temporary native density comparator with PNG/float row alignment; preserve four repaired material bindings and reuse valid Play observation.'
    unit['question']=unit['parameters']['scope']
    final=graph['nodes'][1]
    final['parameters']['argv']+=['--observation-output',str(observation)]
    b.write(out/'comparison-reopen.json',{'cause':'temporary comparator raw float rows were not reversed like existing production importer',
        'preserved':'original graph, first images, material outputs, current production maps and prior Play observation',
        'allowed':'temporary float import, dependent comparator capture and final coarse CPU/GPU coverage check'})
    b.write(out/'comparison-graph.json',graph)
    for action,extra in [('init',[str(out/'comparison-graph.json')]),('run',[])]:
        r=subprocess.run([sys.executable,'-B',str(ROOT/'Tools/WorkLoop/work_loop.py'),action,
            str(out/'comparison-state.json'),*extra],cwd=ROOT,text=True,encoding='utf-8',capture_output=True,shell=False)
        print(r.stdout)
        if r.returncode:raise ValueError(r.stderr)


def start(out):
    if out.exists() or not out.is_relative_to(ROOT):raise ValueError('Fresh workspace output required')
    out.mkdir(parents=True)
    this=Path(__file__).resolve()
    code=[this,ROOT/'Tools/Building38/building16.py',ROOT/'Tools/Building38/geometry16.py',
          ROOT/'Assets/Editor/NativeCabinet19Repair.cs']
    def condition(node,op):return {'op':op,'args':[{'ref':node+'.exit_code'},{'literal':0}]}
    def command(node,action,phase,target):
        return {'id':node,'algorithm':'command.run','phase':phase,'inputs':{'stdin':{'literal':{'scope':'N19'}}},
            'parameters':{'argv':[sys.executable,'-B',str(this),action,'--output',str(out)],'cwd':str(ROOT),
                          'timeout':60,'code_files':[str(p) for p in code]},
            'reads':['native19:source' if action=='calc' else 'native19:unity'],
            'writes':['native19:material' if action=='calc' else 'native19:validation'],
            'edges':[{'when':condition(node,'eq'),'to':target},{'when':condition(node,'ne'),'to':'@blocked'}]}
    scope='Bind only four corrected material maps in the current building, preserve geometry/PPU/camera; capture direct 1px/2px density comparison without camera changes between cases and actual native night.'
    graph={'goal':'Restore existing cabinet gold design and isolate authoring density from camera zoom',
        'entry':'material','max_steps':3,'requirements':[{'id':'repair','source':'BUILDING16.md N19 and latest user feedback',
        'text':'Original inlay and fixed physical geometry/camera density comparison','predicate':condition('final','eq')}],
        'nodes':[command('material','calc','work','unity'),{'id':'unity','algorithm':'ai.work','phase':'work',
        'inputs':{'output':{'literal':str(out)}},'parameters':{'scope':scope},'question':scope,
        'output_schema':{'receiptFile':{'type':'string'}},'reads':['native19:material'],'writes':['native19:unity'],
        'edges':[{'when':{'op':'known','args':[{'ref':'unity.receiptFile'}]},'to':'final'}]},
        command('final','gate','validation','@complete')]}
    b.write(out/'graph.json',graph)
    for action,extra in [('init',[str(out/'graph.json')]),('run',[])]:
        r=subprocess.run([sys.executable,'-B',str(ROOT/'Tools/WorkLoop/work_loop.py'),action,str(out/'state.json'),*extra],
                         cwd=ROOT,text=True,encoding='utf-8',capture_output=True,shell=False)
        print(r.stdout)
        if r.returncode:raise ValueError(r.stderr)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['start','calc','gate','reopen_comparison']);p.add_argument('--output',required=True)
    p.add_argument('--observation-output')
    a=p.parse_args();sys.stdout.reconfigure(encoding='utf-8')
    out=Path(a.output).resolve();observation=Path(a.observation_output).resolve() if a.observation_output else None
    if a.action in ('gate','reopen_comparison'):globals()[a.action](out,observation)
    else:globals()[a.action](out)
