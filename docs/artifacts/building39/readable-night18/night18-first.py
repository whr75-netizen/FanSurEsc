"""Readable-night colour only: frozen caches -> CPU fixture -> Unity -> final gate."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
from shade17 import srgb_to_linear, linear_to_srgb, LUMINANCE

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIXTURE = np.array([.03, .045, .085], np.float32)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def caches():
    roots = [ROOT / 'Assets/Art/NativeBuilding39', ROOT / 'Assets/Art/NativeBuilding39Floor40']
    return {p.relative_to(ROOT).as_posix(): sha(p) for root in roots for p in sorted(root.rglob('*'))
            if p.is_file() and p.suffix in {'.asset', '.png'}}


def shade(material, palette, incident):
    light = np.maximum(np.asarray(incident, np.float32), 0)
    peak = np.max(light, axis=-1, keepdims=True)
    normalized = light / np.maximum(peak, np.float32(1e-6))
    tint = np.where(peak > 1e-6, np.floor(np.clip(normalized, 0, 1) * 3 + .5) / 3, 1)
    band = (np.sum(light * LUMINANCE, axis=-1) >= .12).astype(np.int32)
    band += np.sum(light * LUMINANCE, axis=-1) >= .4
    cool = (light[..., 2] > light[..., 0]) & (light[..., 2] > light[..., 1])
    strength = np.where(cool, .3 * (1 - band * .5), .3)
    tint = 1 + (tint - 1) * strength[..., None]
    ids = material[..., 0].astype(np.int32)
    row = np.clip(ids - 1, 0, 9)
    column = np.where(ids == 1, material[..., 1], 2)
    column = np.minimum(column, np.where(ids == 3, 2, 3))
    column = np.where(material[..., 2] == 3, 0, column)
    base = srgb_to_linear(palette[row, column] / 255)
    brightness = np.array([.55, .78, 1], np.float32)[band]
    color = base * brightness[..., None] * tint
    color[(material[..., 2] == 1) | (material[..., 2] == 2)] = 0
    covered = (material[..., 3] >= 128) & (ids >= 1) & (ids <= 10)
    color[~covered] = 0
    rgba = np.concatenate((linear_to_srgb(color), np.where(covered, material[..., 3] / 255, 0)[..., None]), -1)
    return np.floor(rgba * 255 + .5).astype(np.uint8)


def calculate(output):
    material = np.array(Image.open(ROOT / 'Assets/Art/NativeBuilding39/stock_shelf/material.png').convert('RGBA'))
    palette = np.array(Image.open(ROOT / 'Assets/Art/NativeBuilding39/palette.png').convert('RGB'))
    Image.fromarray(shade(material, palette, FIXTURE)).save(output / 'cpu-fixture.png')
    sample = np.zeros((1, 4, 4), np.uint8)
    sample[..., 0] = 1; sample[..., 1] = np.arange(4); sample[..., 3] = 255
    tests = {}
    for name, light in [('zero', [0, 0, 0]), ('blue', FIXTURE), ('neutral', [1, 1, 1]), ('green', [.4, 1, .1])]:
        colors = shade(sample, palette, light)
        if len(np.unique(colors[..., :3].reshape(-1, 3), axis=0)) != 4:
            raise ValueError('Material rank merged: ' + name)
        tests[name] = colors.tolist()
    write(output / 'frozen-caches.json', caches())
    write(output / 'cpu-observation.json', {'wood_rank_count': 4, 'fixtures': tests,
          'fixture_irradiance': FIXTURE.tolist(), 'production_regeneration_count': 0})
    print(json.dumps({'success': True, 'wood_rank_count': 4, 'production_regeneration_count': 0}))


def gate(output):
    frozen = json.loads((output / 'frozen-caches.json').read_text(encoding='utf-8'))
    if frozen != caches():
        raise ValueError('Geometry/material/position/normal/palette cache changed')
    cpu = np.array(Image.open(output / 'cpu-fixture.png').convert('RGBA')).astype(np.int16)
    gpu = np.array(Image.open(output / 'gpu-fixture.png').convert('RGBA')).astype(np.int16)
    if cpu.shape != gpu.shape:
        raise ValueError('Fixture dimensions changed')
    covered = cpu[..., 3] >= 128
    mismatch = int(np.count_nonzero(covered != (gpu[..., 3] >= 128)))
    error = int(np.abs(cpu[covered, :3] - gpu[covered, :3]).max(initial=0))
    if mismatch or error > 2:
        raise ValueError(f'GPU mismatch: coverage={mismatch}, RGB={error}')
    receipt = json.loads((output / 'play-observation.json').read_text(encoding='utf-8'))
    if not receipt['isPlayMode'] or not receipt['sameMapsAndGeometry'] or not receipt['samePlayerAndCamera']:
        raise ValueError('Actual unchanged Play instances/maps/geometry required')
    if receipt['shaderErrors'] or receipt['readableMaterials'] != 36 or abs(receipt['hour']-21) > .001:
        raise ValueError('Actual shader/material/night state failed')
    if abs(receipt['pixelSpacing']-round(receipt['pixelSpacing'])) > .001 or receipt['pixelSpacing'] < .999:
        raise ValueError('Native display spacing failed')
    if abs(receipt['pitch']-30) > .001 or abs(receipt['yaw']-350) > .001:
        raise ValueError('Actual camera angle changed')
    images = {name: np.array(Image.open(output / (name+'.png')).convert('RGBA'))
              for name in ['legacy-off', 'readable-off', 'readable-on']}
    changed = int(np.any(images['legacy-off'][..., :3] != images['readable-off'][..., :3], -1).sum())
    lit_changed = int(np.any(images['readable-on'][..., :3] != images['readable-off'][..., :3], -1).sum())
    if not changed or not lit_changed:
        raise ValueError('No actual presentation/light response')
    result = {'success': True, 'cache_files_unchanged': len(frozen), 'coverage_mismatch': mismatch,
              'gpu_rgb_error': error, 'presentation_changed_pixels': changed,
              'local_light_changed_pixels': lit_changed, 'production_regeneration_count': 0,
              'art_approval': 'not claimed; actual preview provided'}
    write(output / 'validation.json', result)
    print(json.dumps(result))


def start(output):
    if output.exists() or not output.is_relative_to(ROOT):
        raise ValueError('Fresh workspace output required')
    output.mkdir(parents=True)
    this = str(Path(__file__).resolve())
    code = [this, str(ROOT/'Assets/Shaders/World/NativePaletteSurface16.shader'),
            str(ROOT/'Assets/Shaders/World/NativeReadable18.hlsl'), str(ROOT/'Assets/Editor/NativeNight18Observation.cs')]
    def condition(node, op):
        return {'op':op,'args':[{'ref':node+'.exit_code'},{'literal':0}]}
    def command(node, action, phase, target):
        return {'id':node, 'algorithm':'command.run', 'phase':phase,
            'inputs':{'stdin':{'literal':{'scope':'colour only'}}},
            'parameters':{'argv':[sys.executable,'-B',this,action,'--output',str(output)],
                          'cwd':str(ROOT),'timeout':60,'code_files':code},
            'reads':['native18:cache' if action=='calculate' else 'native18:observation'],
            'writes':['native18:cpu' if action=='calculate' else 'native18:validation'],
            'edges':[{'when':condition(node,'eq'),'to':target},{'when':condition(node,'ne'),'to':'@blocked'}]}
    graph = {'goal':'Readable native night, preserve all existing geometry and pixel caches',
             'entry':'colour', 'max_steps':3,
             'requirements':[{'id':'readable_night','text':'Rank preservation, actual GPU/Play and unchanged caches',
                              'source':'BUILDING16.md N18 and latest user correction','predicate':condition('final','eq')}],
             'nodes':[command('colour','calculate','work','unity'),
                {'id':'unity','algorithm':'ai.work','phase':'work','inputs':{'output':{'literal':str(output)}},
                 'parameters':{'scope':'Only active existing native material ReadableNight setting and actual observations; no geometry/cache/camera/lighting owner changes.'},
                 'question':'Configure existing 36 active materials, capture fixed GPU fixture and actual 21:00 legacy/readable/light-off/on; preserve instances and maps.',
                 'output_schema':{'receiptFile':{'type':'string'}},'reads':['native18:cpu'],
                 'writes':['native18:observation'],
                 'edges':[{'when':{'op':'known','args':[{'ref':'unity.receiptFile'}]},'to':'final'}]},
                command('final','gate','validation','@complete')]}
    write(output/'graph.json',graph)
    for action, more in [('init',[str(output/'graph.json')]),('run',[])]:
        run = subprocess.run([sys.executable,'-B',str(ROOT/'Tools/WorkLoop/work_loop.py'),action,str(output/'state.json'),*more],
                             cwd=ROOT,capture_output=True,text=True,encoding='utf-8',shell=False)
        print(run.stdout)
        if run.returncode: raise ValueError(run.stderr)


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['start','calculate','gate']);p.add_argument('--output',required=True)
    a=p.parse_args();sys.stdout.reconfigure(encoding='utf-8');globals()[a.action](Path(a.output).resolve())
