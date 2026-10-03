"""Run the unchanged old color-range quantizer at source resolution, without grid sampling."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'Tools/PerfectPixelUniform/runs/20261003T092818576216Z-59a6e7b8655b4cf4a637cf98f68e32a7/source.png'
SOURCE_SHA = 'e4eb81a6bb53708a807e7eb182bfaa10bc39e37a5ed337c7913384323172d1ae'
ENGINE = ROOT / 'LocalOnly/PerfectPixelPalette_20260906'
OUT = ROOT / 'docs/artifacts/building37/Legacy11'
CODE_FILES = ['__init__.py', 'perfect_pixel_noCV2.py', 'perfect_pixel.py',
              'palette.py', 'boundary_pipeline.py', 'regions.py', 'color_ranges.py']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def source():
    if sha(SOURCE.read_bytes()) != SOURCE_SHA:
        raise ValueError('Agreed source changed; do not substitute it.')
    with Image.open(SOURCE) as im:
        if im.mode != 'RGBA' or im.size != (1489, 1056):
            raise ValueError('Expected the actual 1489x1056 RGBA source.')
        return np.array(im)


def code_hashes():
    return {name: sha((ENGINE / 'src/perfect_pixel' / name).read_bytes()) for name in CODE_FILES}


def prepare():
    a = source()
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / 'code').mkdir()
    hashes = code_hashes()
    for name in CODE_FILES:
        data = (ENGINE / 'src/perfect_pixel' / name).read_bytes()
        if sha(data) != hashes[name]:
            raise ValueError('Legacy code changed while snapshotting.')
        (OUT / 'code' / name).write_bytes(data)
    write(OUT / 'contract.json', {
        'source_path': str(SOURCE), 'source_sha256': SOURCE_SHA,
        'source_array_sha256': sha(a.tobytes()), 'source_size': [1489, 1056],
        'source_visible_rgb_count': len(np.unique(a[a[..., 3] > 0, :3], axis=0)),
        'alpha_policy': 'preserve every alpha value; quantify all alpha>0 pixels',
        'engine': str(ENGINE), 'engine_code_sha256': hashes,
        'api': 'perfect_pixel.color_ranges.build_color_ranges',
        'tones_cases': [3, 4], 'hue_width_degrees': 15,
        'coordinate_transform': 'identity', 'resize': False, 'line_redraw': False,
        'old_full_wrapper_used': False, 'whole_grid_recovery': False,
        'excluded_stages': ['clean_tone_labels', 'grid_sampling', 'alpha128', 'line_first'],
    })
    print(json.dumps({'prepared': True, 'output': str(OUT)}))


def quantize():
    contract = json.loads((OUT / 'contract.json').read_text(encoding='utf-8'))
    if code_hashes() != contract['engine_code_sha256']:
        raise ValueError('Legacy code changed before execution.')
    sys.path.insert(0, str(ENGINE / 'src'))
    from perfect_pixel.palette import PaletteOptions, rgb_to_oklab
    from perfect_pixel.color_ranges import build_color_ranges
    import perfect_pixel.color_ranges as actual
    if Path(actual.__file__).resolve() != (ENGINE / 'src/perfect_pixel/color_ranges.py').resolve():
        raise ValueError('Wrong old engine module imported.')
    a = source()
    visible = a[..., 3] > 0
    lab = rgb_to_oklab(a[..., :3].astype(np.float32) / 255)
    reports = []
    for levels in contract['tones_cases']:
        options = PaletteOptions(tones_per_family=levels, palette_method='color_ranges')
        options.validate()
        started = time.perf_counter()
        palette, families, family_map, tone_labels, details = build_color_ranges(
            a[..., :3], lab, visible, options)
        out = a.copy()
        out[visible, :3] = palette[tone_labels[visible]]
        elapsed = time.perf_counter() - started
        Image.fromarray(out).save(OUT / f'native-{levels}.png')
        np.savez_compressed(OUT / f'maps-{levels}.npz', palette=palette,
                            family_map=family_map, tone_labels=tone_labels)
        report = {'levels_maximum_per_color_range': levels,
                  'elapsed_quantizer_and_lookup_seconds': elapsed,
                  'palette': palette.tolist(), 'family_palette_indices': families,
                  'visible_rgb_count': len(np.unique(out[visible, :3], axis=0)),
                  'visible_rgb_changed_pixels': int(np.count_nonzero(np.any(a[visible, :3] != out[visible, :3], axis=1))),
                  'details': details, 'array_sha256': sha(out.tobytes()),
                  'png_sha256': sha((OUT / f'native-{levels}.png').read_bytes())}
        write(OUT / f'receipt-{levels}.json', report)
        reports.append({k: report[k] for k in ('levels_maximum_per_color_range',
                       'elapsed_quantizer_and_lookup_seconds', 'visible_rgb_count',
                       'visible_rgb_changed_pixels')})
    if code_hashes() != contract['engine_code_sha256']:
        raise ValueError('Legacy code changed during execution.')
    print(json.dumps({'executed': True, 'cases': reports}))


def previews(a, outputs):
    # Same source ROI for all panels. Enlargement is display only, never a processing step.
    box = (4, 2, 328, 294)
    for levels, out in outputs:
        panel = Image.new('RGB', (1312, 624), (29, 33, 37))
        draw = ImageDraw.Draw(panel)
        draw.text((8, 7), 'SOURCE | same 324 x 292 crop | nearest display 2x', fill='white')
        draw.text((664, 7), f'OLD MODIFIED | max {levels} tones per hue range | display 2x', fill='white')
        for x, array in ((8, a), (664, out)):
            im = Image.fromarray(array).crop(box).resize((648, 584), Image.Resampling.NEAREST)
            panel.paste(im, (x, 32), im)
        panel.save(OUT / f'comparison-{levels}-x2.png')


def validate():
    a = source()
    contract = json.loads((OUT / 'contract.json').read_text(encoding='utf-8'))
    checks = {'source_array_preserved': sha(a.tobytes()) == contract['source_array_sha256'],
              'legacy_engine_unchanged': code_hashes() == contract['engine_code_sha256']}
    visible = a[..., 3] > 0
    source_colors = set(map(tuple, np.unique(a[visible, :3], axis=0)))
    outputs = []
    summaries = []
    for levels in contract['tones_cases']:
        with Image.open(OUT / f'native-{levels}.png') as im:
            out = np.array(im)
        receipt = json.loads((OUT / f'receipt-{levels}.json').read_text(encoding='utf-8'))
        with np.load(OUT / f'maps-{levels}.npz') as maps:
            palette, families, labels = maps['palette'], maps['family_map'], maps['tone_labels']
            checks[f'{levels}_same_size'] = out.shape == a.shape
            checks[f'{levels}_alpha_exact'] = np.array_equal(out[..., 3], a[..., 3])
            checks[f'{levels}_hidden_rgb_preserved'] = np.array_equal(out[~visible], a[~visible])
            checks[f'{levels}_exact_palette_lookup'] = np.array_equal(out[visible, :3], palette[labels[visible]])
            checks[f'{levels}_observed_source_rgb_only'] = all(tuple(p) in source_colors for p in palette)
            checks[f'{levels}_per_range_tone_limit'] = all(
                len(np.unique(labels[families == f])) <= levels for f in np.unique(families[visible]))
            checks[f'{levels}_same_range_representatives'] = all(
                all(np.any(np.all(a[(families == f) & visible, :3] == palette[t], axis=1))
                    for t in np.unique(labels[families == f])) for f in np.unique(families[visible]))
        checks[f'{levels}_saved_array_sha'] = sha(out.tobytes()) == receipt['array_sha256']
        checks[f'{levels}_saved_png_sha'] = sha((OUT / f'native-{levels}.png').read_bytes()) == receipt['png_sha256']
        outputs.append((levels, out))
        summaries.append({k: receipt[k] for k in ('levels_maximum_per_color_range',
                        'elapsed_quantizer_and_lookup_seconds', 'visible_rgb_count')})
    previews(a, outputs)
    result = {'checks': checks, 'passed': all(checks.values()), 'cases': summaries,
              'source_visible_rgb_count': contract['source_visible_rgb_count'],
              'source_size': contract['source_size'], 'alpha_changed_pixels': 0,
              'grid_recovered': False, 'line_geometry_redrawn': False,
              'art_approved': False, 'unity_or_web_engine_changed': False,
              'limitations': ['Hue ranges are not semantic or connected material regions.',
                              'Original fractional-alpha edges remain unchanged.',
                              'No regular line reconstruction or authored-grid recovery.']}
    write(OUT / 'validation.json', result)
    print(json.dumps(result))
    if not result['passed']:
        raise SystemExit(1)


def run():
    graph_path = ROOT / 'LocalOnly/PerfectPixelUniform/legacy11-graph.json'
    state_path = ROOT / 'LocalOnly/PerfectPixelUniform/legacy11-state.json'
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    code = [str(Path(__file__).resolve())] + [str(ENGINE / 'src/perfect_pixel' / n) for n in CODE_FILES]
    nodes = []
    for stage, after in (('prepare', 'quantize'), ('quantize', 'validate'), ('validate', '@complete')):
        test = lambda op: {'op': op, 'args': [{'ref': stage + '.exit_code'}, {'literal': 0}]}
        nodes.append({'id': stage, 'algorithm': 'command.run',
                      'phase': 'validation' if stage == 'validate' else 'work',
                      'inputs': {'stdin': {'literal': {'contract': 'LEGACY11.md: unchanged old quantizer, native identity coordinates'}}},
                      'parameters': {'argv': [sys.executable, '-B', str(Path(__file__).resolve()), stage],
                                     'cwd': str(ROOT), 'timeout': 60, 'code_files': code},
                      'reads': ['file:' + SOURCE.as_posix()] + ['file:' + p.replace('\\', '/') for p in code],
                      'writes': ['file:' + OUT.as_posix()],
                      'edges': [{'when': test('eq'), 'to': after}, {'when': test('ne'), 'to': '@blocked'}]})
    graph = {'goal': 'Execute the unchanged old 3/4-tone quantizer; not complete pixel reconstruction',
             'entry': 'prepare', 'max_steps': 3, 'nodes': nodes,
             'requirements': [{'id': 'actual_old_quantizer', 'text': 'Observed RGB ramps, exact coordinates and alpha',
                               'source': 'LEGACY11.md', 'predicate': {'op': 'eq', 'args': [
                                   {'ref': 'validate.exit_code'}, {'literal': 0}]}}]}
    write(graph_path, graph)
    engine = ROOT / 'Tools/WorkLoop/work_loop.py'
    for command, extra in (('init', [str(graph_path)]), ('run', [])):
        p = subprocess.run([sys.executable, '-B', str(engine), command, str(state_path), *extra],
                           cwd=ROOT, capture_output=True, encoding='utf-8')
        if p.returncode:
            raise RuntimeError(p.stdout + p.stderr)
        result = json.loads(p.stdout)
    if OUT.exists():
        (OUT / 'workloop-graph.json').write_bytes(graph_path.read_bytes())
        (OUT / 'workloop-state.json').write_bytes(state_path.read_bytes())
    print(json.dumps(result))
    if result.get('action') != 'graph_complete':
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare', 'quantize', 'validate', 'run'])
    args = parser.parse_args()
    globals()[args.phase]()
