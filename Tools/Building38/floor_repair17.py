"""Reopen only N17's incorrect inactive-floor binding; preserve the other caches.

The three-node graph calculates the corrected active floor, hands Unity GPU and
targeted binding to the existing writer, then checks pixels and the existing live
observation gate. It does not re-run or copy the other thirty-five surface caches.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

from floor17 import build_floor, assign_floor, SOURCE, CALIBRATION, BINDING_PATH
from geometry16 import R, U
from shade17 import shade_srgb, verify_contract

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREVIOUS = ROOT/'docs/artifacts/building39/run02'
DEFAULT_OUTPUT = ROOT/'docs/artifacts/building39/floor-fix01'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def files():
    return [SOURCE, CALIBRATION, PREVIOUS/'palette.png', HERE/'shading17.json',
            HERE/'floor17.py', HERE/'geometry16.py', HERE/'shade17.py',
            Path(__file__).resolve(), HERE/'unity_gate17.py',
            ROOT/'Assets/Shaders/World/NativeShade17.hlsl',
            *[PREVIOUS/asset/name for asset in ('empty_counter','stock_shelf')
              for name in ('preview.png','gpu-fixture.png')]]


def calculate(output):
    if output.exists() or not output.is_relative_to(ROOT):
        raise ValueError('Fresh workspace output required; previous outputs remain intact')
    verify_contract()
    shading = read(HERE/'shading17.json'); ppu = float(shading['ppu'])
    data = build_floor(ppu)
    if data['metadata']['bindingPath'] != BINDING_PATH or 'aligned native surfaces' not in BINDING_PATH:
        raise ValueError('Corrective target must be the actually active aligned Floor')
    palette_path = PREVIOUS/'palette.png'
    palette = np.asarray(Image.open(palette_path).convert('RGB'))
    ids, pattern, edge = assign_floor(data, palette)
    mask = data['mask']; height, width = mask.shape
    yy, xx = np.indices(mask.shape)
    positions = data['position'][mask]
    normals = data['normal'][mask]
    projected = np.stack([positions@R, -positions@U], -1)*ppu
    expected = np.stack([xx[mask]+.5+data['origin'][0],
                         yy[mask]+.5+data['origin'][1]], -1)
    roundtrip = float(np.max(np.abs(projected-expected)))
    lo, hi = np.asarray(data['bounds'])
    inside = bool(np.all(positions >= lo-1e-5) and np.all(positions <= hi+1e-5))
    normal_error = float(np.max(np.abs(np.linalg.norm(normals, axis=-1)-1)))
    material = np.stack([ids, pattern, edge, mask.astype(np.uint8)*255], -1)
    material[~mask] = 0
    preview = shade_srgb(material, palette, data['normal'], shading['reference_light_unity'])
    success = bool(mask.any() and roundtrip < 1e-4 and inside and normal_error < 1e-5
                   and np.allclose(normals, [0.,1.,0.], atol=1e-6)
                   and np.all(ids[mask] == 1) and np.all(pattern[mask] < 4)
                   and not np.any(edge) and np.array_equal(preview[...,3]>0, mask))
    if not success:
        raise ValueError('Corrected floor geometry/material invariant failed')
    output.mkdir(parents=True); folder = output/'floor_surface'; folder.mkdir()
    arrays = {k:v for k,v in data.items() if isinstance(v, np.ndarray)}
    np.savez_compressed(folder/'geometry.npz', **arrays)
    metadata = {k:v for k,v in data.items() if not isinstance(v, np.ndarray)}
    write(folder/'geometry.json', metadata)
    write(folder/'mesh.json', {'vertices':data['mesh_vertices'].tolist(),
                              'triangles':data['mesh_triangles'].reshape(-1).tolist()})
    for name in ('position','normal'):
        values = np.concatenate([data[name].astype(np.float32), mask[...,None].astype(np.float32)], -1)
        values[~mask] = 0
        values.astype('<f4').tofile(folder/(name+'.f32'))
    Image.fromarray(material, 'RGBA').save(folder/'material.png')
    Image.fromarray(preview, 'RGBA').save(folder/'preview.png')
    shutil.copyfile(palette_path, output/'palette.png')
    entry = {'id':'floor_surface', 'width':width, 'height':height,
             'origin':list(map(int,data['origin'])), 'ppu':ppu,
             'structurePath':BINDING_PATH, 'bindingPath':BINDING_PATH,
             'bounds':data['bounds'],
             **{name+'File':'floor_surface/'+name+suffix for name,suffix in
                [('position','.f32'),('normal','.f32'),('material','.png'),
                 ('preview','.png'),('mesh','.json')]}}
    write(output/'manifest.json', {'schema':'N17.metric.native.cache.v1',
                                  'paletteFile':'palette.png','assets':[entry],
                                  'physical_pixels_per_metre':ppu,
                                  'lighting_preview_only':True,'runtime_lighting_baked':False,
                                  'shade_contract_sha256':sha(HERE/'shading17.json'),
                                  'correction':'active Floor only; preserve the other 35 run02 surface caches'})
    write(output/'geometry-catalog.json', [{**entry,'metadata':data['metadata']}])
    result = {'success':success, 'shared_asset_count':1, 'asset':'floor_surface',
              'native_size':[width,height], 'covered_pixels':int(mask.sum()),
              'roundtrip_pixel_error':roundtrip,'unit_normal_error':normal_error,
              'inside_declared_bounds':inside,'bindingPath':BINDING_PATH,
              'source_sha256':sha(SOURCE),'source_dimensions':[125,132],
              'material_original_ppu':data['metadata']['material_original_ppu'],
              'ppu':ppu,'source_resize_count':0,'other_cache_regeneration_count':0,
              'palette_sha256':sha(output/'palette.png'),
              'palette_unchanged':sha(output/'palette.png')==sha(palette_path),
              'reused_fixture_directory':str(PREVIOUS)}
    write(output/'cpu-validation.json', result)
    write(output/'input-hashes.json', {p.relative_to(ROOT).as_posix():sha(p) for p in files()})
    print(json.dumps(result))


def compare_fixture(cpu_path, gpu_path, name):
    a=np.asarray(Image.open(cpu_path).convert('RGBA')).astype(np.int16)
    b=np.asarray(Image.open(gpu_path).convert('RGBA')).astype(np.int16)
    if a.shape != b.shape:
        raise ValueError(name+': GPU fixture domain mismatch')
    mask=a[...,3]>127; mismatch=int(np.count_nonzero(mask!=(b[...,3]>127)))
    error=int(np.max(np.abs(a[mask,:3]-b[mask,:3]))) if np.any(mask) else 0
    if mismatch or error>2:
        raise ValueError(name+': actual GPU parity failed; coverage='+str(mismatch)+', RGB='+str(error))
    return {'asset':name,'coverage_mismatch':mismatch,'max_rgb_error':error}


def gate(output):
    hashes=read(output/'input-hashes.json')
    changed=[name for name,value in hashes.items() if sha(ROOT/name)!=value]
    if changed:
        raise ValueError('Frozen floor repair input/code changed: '+repr(changed))
    cpu=read(output/'cpu-validation.json')
    if not cpu['success'] or cpu['shared_asset_count']!=1 or cpu['other_cache_regeneration_count']!=0:
        raise ValueError('Floor-only CPU receipt failed')
    comparisons=[compare_fixture(PREVIOUS/name/'preview.png',PREVIOUS/name/'gpu-fixture.png',name)
                 for name in ('empty_counter','stock_shelf')]
    comparisons.append(compare_fixture(output/'floor_surface/preview.png',
                                       output/'floor_surface/gpu-fixture.png','floor_surface'))
    receipt=read(output/'play-observation.json')
    if receipt.get('phase')!='play':
        raise ValueError('Actual new Play observation required, not a probe or reused completion')
    result=subprocess.run([sys.executable,'-B',str(HERE/'unity_gate17.py'),
                           str(output/'play-observation.json')],cwd=ROOT,capture_output=True,
                          text=True,encoding='utf-8',shell=False)
    print(result.stdout)
    if result.returncode:
        raise RuntimeError(result.stderr or 'Existing N17 actual Play gate failed')
    write(output/'final-validation.json', {'success':True,'comparisons':comparisons,
                                         'live_gate':'unity_gate17.py unchanged',
                                         'floor_only_repair':True})
    print(json.dumps({'success':True,'comparisons':comparisons}))


def condition(node,op):
    return {'op':op,'args':[{'ref':node+'.exit_code'},{'literal':0}]}


def start(output):
    state=output.parent/(output.name+'-workloop')
    if output.exists() or state.exists() or not output.is_relative_to(ROOT):
        raise ValueError('Fresh output/state required; genuine failed run02 stays preserved')
    tracked=files()
    code=[HERE/'floor17.py', HERE/'geometry16.py', HERE/'shade17.py',
          Path(__file__).resolve(), HERE/'unity_gate17.py']
    scope=('Import only the corrected floor using NativeBuilding17Importer floorOnly and '
           'Assets/Art/NativeBuilding39Floor40. Compare its actual neutral GPU fixture, bind '
           'the actually active aligned Floor only, retain the other 35 surface caches and '
           'original disabled floor, then record actual night, left/right motion and camera '
           'observations. Use the existing Unity writer; preserve the same Player/Camera.')
    graph={'goal':'Repair the actually active aligned floor binding; preserve run02 and other caches',
           'entry':'floorcalc','max_steps':3,
           'requirements':[{'id':'active_floor_live','source':'latest user correction; BUILDING16.md N17',
                            'text':'Actual active floor shares object native spacing and live quantized lighting',
                            'predicate':condition('final_gate','eq')}],
           'nodes':[
               {'id':'floorcalc','algorithm':'command.run','phase':'work',
                'inputs':{'stdin':{'literal':{'scope':'only corrected active floor','previous':str(PREVIOUS)}}},
                'parameters':{'argv':[sys.executable,'-B',str(Path(__file__).resolve()),'calc',
                                      '--output',str(output)],'cwd':str(ROOT),'timeout':60,
                              'code_files':[str(p) for p in code]},
                'reads':['file:'+p.as_posix() for p in tracked],
                'writes':['file:'+output.as_posix(),'native17:floor-repair'],
                'edges':[{'when':condition('floorcalc','eq'),'to':'unity_floor'},
                         {'when':condition('floorcalc','ne'),'to':'@blocked'}]},
               {'id':'unity_floor','algorithm':'ai.work','phase':'work',
                'inputs':{'output':{'literal':str(output)},'contract':{'literal':'BUILDING16.md N17'}},
                'parameters':{'scope':scope},
                'question':scope+' Write floor_surface/gpu-fixture.png and play-observation.json in '+str(output)+'.',
                'output_schema':{'receiptFile':{'type':'string'}},
                'reads':['native17:floor-repair'],
                'writes':['unity:native17-floor-integration','file:'+(output/'play-observation.json').as_posix(),
                          'file:'+(output/'floor_surface/gpu-fixture.png').as_posix()],
                'edges':[{'when':{'op':'known','args':[{'ref':'unity_floor.receiptFile'}]},'to':'final_gate'}]},
               {'id':'final_gate','algorithm':'command.run','phase':'validation',
                'inputs':{'stdin':{'literal':{'receipt':str(output/'play-observation.json')}}},
                'parameters':{'argv':[sys.executable,'-B',str(Path(__file__).resolve()),'gate',
                                      '--output',str(output)],'cwd':str(ROOT),'timeout':30,
                              'code_files':[str(p) for p in code]},
                'reads':['native17:floor-repair','unity:native17-floor-integration',
                         'file:'+(output/'play-observation.json').as_posix(),
                         'file:'+(output/'floor_surface/gpu-fixture.png').as_posix()],
                'writes':['file:'+(output/'final-validation.json').as_posix()],
                'edges':[{'when':condition('final_gate','eq'),'to':'@complete'},
                         {'when':condition('final_gate','ne'),'to':'@blocked'}]}]}
    state.mkdir(parents=True);write(state/'graph.json',graph)
    for action,extra in [('init',[str(state/'graph.json')]),('run',[])]:
        result=subprocess.run([sys.executable,'-B',str(ROOT/'Tools/WorkLoop/work_loop.py'),
                               action,str(state/'state.json'),*extra],cwd=ROOT,capture_output=True,
                              text=True,encoding='utf-8',shell=False)
        print(result.stdout)
        if result.returncode:
            raise RuntimeError(result.stderr or 'Corrective graph failed')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['start','calc','gate'])
    parser.add_argument('--output',default=str(DEFAULT_OUTPUT))
    args=parser.parse_args();sys.stdout.reconfigure(encoding='utf-8')
    path=Path(args.output).resolve()
    {'start':start,'calc':calculate,'gate':gate}[args.action](path)
