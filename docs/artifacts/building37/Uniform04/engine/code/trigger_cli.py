"""Run a reproducible opt-in/scoped normalization experiment, without UI questions."""
import argparse
from datetime import datetime
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.deps'))
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
CODE_FILES = ['trigger_cli.py', 'requirements-boundary.txt',
              'src/perfect_pixel/trigger_pipeline.py', 'src/perfect_pixel/line_triggers.py',
              'src/perfect_pixel/line_first.py',
              'src/perfect_pixel/source_sampling.py',
              'src/perfect_pixel/boundary_pipeline.py',
              'src/perfect_pixel/boundary_regions.py', 'src/perfect_pixel/region_palette.py',
              'src/perfect_pixel/gradient_tones.py',
              'src/perfect_pixel/gradient_steps.py',
              'src/perfect_pixel/spatial_tones.py',
              'src/perfect_pixel/highlight_accents.py',
              'src/perfect_pixel/color_layers.py',
              'src/perfect_pixel/tone_controls.py',
              'src/perfect_pixel/feature_scopes.py', 'src/perfect_pixel/palette.py',
              'src/perfect_pixel/__init__.py', 'src/perfect_pixel/perfect_pixel_noCV2.py',
              'src/perfect_pixel/perfect_pixel.py']
# Capture BEFORE importing implementation, then reject any in-flight changes.
BOOT_CODE = {rel:(ROOT/rel).read_bytes() for rel in CODE_FILES}
from perfect_pixel.trigger_pipeline import normalize_triggered, FEATURES
from perfect_pixel.palette import scaled_grid
from perfect_pixel.tone_controls import resolve_tone_controls


def sha(data):
    return hashlib.sha256(data).hexdigest()


def comparison_size(source_shape, grid, zoom, panels):
    w = max(source_shape[1],grid[0]*zoom)
    h = max(source_shape[0],grid[1]*zoom)
    size = (panels*(w+20)+20,h+100)
    if size[0]*size[1] > 32_000_000:
        raise ValueError('Full comparison exceeds 32MP. Lower preview_zoom; no files created.')
    return size


def compare_sheet(source, baseline, result, zoom, target, *, fixed_lines=None, previous=None,
                  reference_used=False, history=None):
    def enlarge(a):
        im = Image.fromarray(a)
        return im.resize((im.width * zoom, im.height * zoom), Image.Resampling.NEAREST)
    images = [Image.fromarray(source), enlarge(baseline), enlarge(result)]
    names = ['SOURCE', 'CENTER SAMPLE / FEATURES OFF', 'SCOPED NORMALIZATION / FEATURES ON']
    if previous is not None:
        images[1] = enlarge(previous)
        names[1] = 'PREVIOUS / SAVED RESULT'
    if fixed_lines is not None:
        images = [Image.fromarray(source), enlarge(fixed_lines),
                  enlarge(previous if previous is not None else baseline), enlarge(result)]
        names = ['SOURCE', 'LINES FIXED BEFORE COLOR FILL',
                 'PREVIOUS / SAVED RESULT' if previous is not None else 'CENTER SAMPLE',
                 'NEW / SCOPED NORMALIZATION']
    if history:
        if previous is not None or fixed_lines is not None:
            raise ValueError('comparison_history cannot be combined with comparison_previous or line_first.')
        images = [Image.fromarray(source)] + [enlarge(array) for array,label in history] + [enlarge(result)]
        names = ['SOURCE'] + [label for array,label in history] + ['NEW / SCOPED NORMALIZATION']
    w, h = max(im.width for im in images), max(im.height for im in images)
    size = comparison_size(source.shape[:2],(result.shape[1],result.shape[0]),zoom,len(images))
    sheet = Image.new('RGB', size, (239,241,247))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 14)
    for index, (im, name) in enumerate(zip(images, names)):
        x, y = 20+index*(w+20), 48
        draw.text((x,12), name, font=font, fill=(32,40,58))
        for cy in range(y,y+h,12):
            for cx in range(x,x+w,12):
                c = (226,230,240) if ((cx-x)//12+(cy-y)//12)%2 else (247,248,251)
                draw.rectangle((cx,cy,min(cx+11,x+w-1),min(cy+11,y+h-1)), fill=c)
        sheet.paste(im, (x+(w-im.width)//2, y+(h-im.height)//2), im)
    colors = 'source + reference RGB representatives' if reference_used else 'original RGB representatives'
    draw.text((20,h+66), f'Native {result.shape[1]} x {result.shape[0]} | nearest preview {zoom}x | {colors} | no generative redraw', font=font, fill=(32,40,58))
    sheet.save(target)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--scale')
    parser.add_argument('--disable', action='append', choices=list(FEATURES), default=[])
    args = parser.parse_args(argv)
    config_bytes = args.config.read_bytes()
    config = json.loads(config_bytes.decode('utf8'))
    if not isinstance(config, dict) or set(config)-{'source','reference','comparison_previous','comparison_history','base_grid','scale','preview_zoom','features','notes','export_color_layers','tone_controls'}:
        parser.error('Unknown configuration keys.')
    if not isinstance(config.get('export_color_layers', False), bool):
        parser.error('export_color_layers must be a boolean.')
    for key in ['source','base_grid','features']:
        if key not in config:
            parser.error(f'Missing {key}.')
    try:
        effective_features = (resolve_tone_controls(config['features'], config['tone_controls'])
                              if 'tone_controls' in config else json.loads(json.dumps(config['features'])))
    except ValueError as exc:
        parser.error(str(exc))
    base_dir = args.config.resolve().parent
    source_path = (base_dir / config['source']).resolve()
    source_bytes = source_path.read_bytes()
    with Image.open(source_path) as im:
        if im.mode != 'RGBA':
            parser.error('Input must already be RGBA; no hidden background removal/conversion.')
        source = np.array(im)
    config['scale'] = str(args.scale if args.scale is not None else config.get('scale','1.0'))
    zoom = config.get('preview_zoom',2)
    if isinstance(zoom,bool) or not isinstance(zoom,int) or not 1 <= zoom <= 8:
        parser.error('preview_zoom must be 1..8.')
    for feature in args.disable:
        config['features'].setdefault(feature,{})['enabled'] = False
        effective_features.setdefault(feature,{})['enabled'] = False
    reference, reference_bytes, reference_path, reference_before = None, None, None, None
    if config['features'].get('region_tones',{}).get('enabled',False):
        if not isinstance(config.get('reference'),str) or not config['reference'].strip():
            parser.error('Enabled region_tones requires an explicit reference image path.')
        reference_path = (base_dir/config['reference']).resolve()
        reference_bytes = reference_path.read_bytes()
        with Image.open(reference_path) as im:
            if im.mode not in ('RGB','RGBA'):
                parser.error('Reference must already be RGB or RGBA; no implicit conversion.')
            reference = np.array(im)
        reference_before = sha(reference.tobytes())
    if source.shape[0]*source.shape[1]*zoom*zoom > 24_000_000:
        parser.error('Preview size exceeds the 24MP input-based safety bound.')
    f = config['features'].get('line_normalization',{})
    line_first = f.get('enabled',False) and f.get('options',{}).get('mode')=='line_first'
    history_spec = config.get('comparison_history',[])
    if not isinstance(history_spec,list) or len(history_spec)>4:
        parser.error('comparison_history must be an array of at most 4 {path, label} entries.')
    for index,entry in enumerate(history_spec):
        if not isinstance(entry,dict) or set(entry)!={'path','label'} or any(
                not isinstance(entry[key],str) or not entry[key].strip() for key in ('path','label')):
            parser.error(f'comparison_history[{index}] requires exactly nonempty path and label strings.')
        if not entry['label'].isprintable():
            parser.error(f'comparison_history[{index}].label must be a printable single line.')
    if history_spec and (config.get('comparison_previous') or line_first):
        parser.error('comparison_history cannot be combined with comparison_previous or line_first.')
    panels = len(history_spec)+2 if history_spec else (4 if line_first else 3)
    grid = scaled_grid(config['base_grid'],config['scale'])
    comparison_size(source.shape[:2],grid,zoom,panels)
    history_inputs = []
    for index,entry in enumerate(history_spec):
        path = (base_dir/entry['path']).resolve()
        try:
            data = path.read_bytes()
            with Image.open(BytesIO(data)) as im:
                if im.mode != 'RGBA':
                    parser.error(f'comparison_history[{index}] must already be RGBA; no implicit conversion.')
                if im.size != tuple(grid):
                    parser.error(f'comparison_history[{index}] grid {im.size} must match output grid {tuple(grid)}.')
                array = np.array(im)
        except (OSError,ValueError) as exc:
            parser.error(f'Cannot read comparison_history[{index}]: {exc}')
        snapshot = f'comparison_history/{index+1:02d}' + (path.suffix.lower() or '.image')
        history_inputs.append({'path':path, 'bytes':data, 'image':array, 'label':entry['label'],
                               'array_sha256':sha(array.tobytes()), 'snapshot_path':snapshot})
    output = (args.output if args.output is not None else ROOT/'trigger_runs'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')).resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        parser.error('Output must be new/empty. Previous results are never overwritten.')
    code = dict(BOOT_CODE)
    if any((ROOT/rel).read_bytes() != data for rel,data in code.items()):
        raise RuntimeError('Code changed since import; launch a fresh run before saving.')
    mask_sources = {}
    for name, feature in config['features'].items():
        spec = feature.get('scope') if feature.get('enabled',False) else None
        if isinstance(spec,dict) and spec.get('kind')=='mask':
            path = (base_dir/spec['path']).resolve()
            mask_sources[name] = (path,path.read_bytes())
    source_before = sha(source.tobytes())
    pipeline_options = {'base_dir':base_dir}
    if reference is not None:
        pipeline_options['reference'] = reference
    result = normalize_triggered(source, config['base_grid'], config['scale'], effective_features, **pipeline_options)
    if sha(source.tobytes()) != source_before or source_path.read_bytes() != source_bytes:
        raise RuntimeError('Original input changed during processing.')
    if reference is not None and (sha(reference.tobytes()) != reference_before or
                                  reference_path.read_bytes() != reference_bytes):
        raise RuntimeError('Reference input changed during processing; no mismatched run is saved.')
    if any((ROOT/rel).read_bytes() != data for rel,data in code.items()):
        raise RuntimeError('Code changed during processing; no mismatched run is saved.')
    if any(path.read_bytes() != data for path,data in mask_sources.values()):
        raise RuntimeError('A scope mask changed during processing; no mismatched run is saved.')
    if any(item['path'].read_bytes()!=item['bytes'] or sha(item['image'].tobytes())!=item['array_sha256']
           for item in history_inputs):
        raise RuntimeError('A comparison history input changed during processing; no mismatched run is saved.')
    # Mandatory technical checks only, not an aesthetic approval score.
    native = result['image']
    if any(item['image'].shape != native.shape for item in history_inputs):
        raise RuntimeError('comparison_history grid must match the actual native output grid.')
    if not np.isin(native[...,3], [0,255]).all():
        raise RuntimeError('Nonbinary alpha in final output.')
    source_allowed = set(map(tuple, source[...,:3][source[...,3]==255]))
    allowed = source_allowed.copy()
    if reference is not None:
        visible_reference = (reference[...,:3][reference[...,3]>0] if reference.shape[2]==4
                             else reference.reshape(-1,3))
        allowed.update(map(tuple,visible_reference))
    observed = set(map(tuple, native[...,:3][native[...,3]==255]))
    if not observed <= allowed:
        origin = 'opaque source and visible reference' if reference is not None else 'opaque source'
        raise RuntimeError(f'Final RGB contains a color absent from the {origin}.')
    previous, previous_bytes, previous_path = None, None, None
    if config.get('comparison_previous'):
        previous_path = (base_dir/config['comparison_previous']).resolve()
        previous_bytes = previous_path.read_bytes()
        with Image.open(previous_path) as im:
            previous = np.array(im.convert('RGBA'))
        if previous.shape != native.shape:
            # Compare only like-for-like grids. A scale override remains usable.
            previous = None
    output.mkdir(parents=True, exist_ok=True)
    for filename, array in [('source_input.png',source), ('center_baseline_native.png',result['baseline']),
                            ('cleaned_source.png',result['cleaned_source']), ('colors_source.png',result['colors_source']),
                            ('before_lines_native.png',result['before_lines']), ('pixel_native.png',native)]:
        Image.fromarray(array).save(output/filename)
    Image.fromarray(native).resize((native.shape[1]*zoom,native.shape[0]*zoom), Image.Resampling.NEAREST).save(output/'pixel_preview.png')
    if result['highlight_result'] is not None:
        for filename, array in [('base_native.png', result['layer_base']),
                                ('highlight_native.png', result['highlight_overlay']),
                                ('base_colors_source.png', result['base_colors_source']),
                                ('highlight_source.png', result['highlight_result']['overlay'])]:
            Image.fromarray(array).save(output/filename)
    layer_export = None
    if config.get('export_color_layers', False):
        from perfect_pixel.color_layers import export_color_layers
        recomposed = result['layer_base'].copy()
        active = result['highlight_overlay'][..., 3] == 255
        recomposed[active] = result['highlight_overlay'][active]
        np.testing.assert_array_equal(recomposed, native)
        layer_export = export_color_layers(result['layer_base'], result['highlight_overlay'],
                                           output/'color_layers')
    fixed_lines = None
    if result['line_geometry'] is not None:
        fixed_lines = np.zeros_like(native)
        locked = result['line_geometry']['fixed_line_mask']
        fixed_lines[locked] = native[locked]
        Image.fromarray(fixed_lines).save(output/'locked_lines_native.png')
    compare_sheet(source,result['baseline'],native,zoom,output/'comparison.png',fixed_lines=fixed_lines,
                  previous=previous,reference_used=reference is not None,
                  history=[(item['image'],item['label']) for item in history_inputs])
    diagnostics = {'sampling_source_xy':result['sampling_source_xy'], 'erase_mask':result['erase_mask']}
    if result.get('region_tones_result') is not None:
        for name in ('region_labels','edge_strength','tone_map'):
            diagnostics['region_tones_'+name] = result['region_tones_result'][name]
    for name,mask in result['scopes'].items():
        Image.fromarray(mask.astype(np.uint8)*255).save(output/f'scope_{name}.png')
        diagnostics['scope_'+name] = mask
    Image.fromarray(result['erase_mask'].astype(np.uint8)*255).save(output/'erased_source_mask.png')
    if result['line_result'] is not None:
        for name,array in result['line_result'].items():
            if isinstance(array,np.ndarray):
                diagnostics['line_'+name] = array
                if array.ndim==2:
                    Image.fromarray(array.astype(np.uint8)*255).save(output/f'line_{name}.png')
        Image.fromarray(result['line_result']['target_rgba']).save(output/'line_source_rgb_overlay_native.png')
    if result['line_geometry'] is not None:
        for name,array in result['line_geometry'].items():
            if isinstance(array,np.ndarray):
                diagnostics['geometry_'+name] = array
        for name,array in result['line_render'].items():
            if isinstance(array,np.ndarray):
                diagnostics['render_'+name] = array
    np.savez_compressed(output/'processing_maps.npz', **diagnostics)
    for rel,data in code.items():
        path = output/'code'/rel
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    input_masks = []
    for name,(path,data) in mask_sources.items():
        dest = output/'config_masks'/f'{name}.png'
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data)
        input_masks.append({'feature':name,'path':str(path),'sha256':sha(data)})
    record = {'configuration':config, 'configuration_path':str(args.config.resolve()),
              'input_file_sha256':sha(source_bytes), 'input_array_sha256':source_before,
              'configuration_file_sha256':sha(config_bytes), 'input_masks':input_masks,
              'comparison_previous_sha256':None if previous_bytes is None else sha(previous_bytes),
              'code_sha256':{rel:sha(data) for rel,data in code.items()},
              'result':result['metadata'], 'technical_checks':{
                  'source_unchanged':True, 'binary_alpha':True,
                  'native_grid':list(native.shape[1::-1]),'unique_opaque_rgb':len(observed),
                  'opaque_rgb_from_original':observed <= source_allowed, 'design_approval':'user review pending'}}
    if layer_export is not None:
        record['color_layers'] = layer_export
        record['technical_checks']['layer_recomposition_matches_native'] = True
    if 'tone_controls' in config:
        record['effective_features'] = effective_features
    if reference is not None:
        record.update(reference_path=str(reference_path), reference_file_sha256=sha(reference_bytes),
                      reference_array_sha256=reference_before)
        record['technical_checks'].update(reference_unchanged=True,
                                          opaque_rgb_from_source_or_reference=True)
    if history_inputs:
        record['comparison_history'] = [
            {'path':str(item['path']), 'label':item['label'], 'snapshot_path':item['snapshot_path'],
             'file_sha256':sha(item['bytes']), 'array_sha256':item['array_sha256']}
            for item in history_inputs]
        record['technical_checks']['comparison_history_unchanged'] = True
    (output/'settings_and_result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
    # The portable rerun config uses input/scope copies saved alongside it.
    rerun = json.loads(json.dumps(config))
    rerun['source'] = 'source_input.png'
    if reference is not None:
        reference_name = 'reference_input' + (reference_path.suffix.lower() or '.image')
        (output/reference_name).write_bytes(reference_bytes)
        rerun['reference'] = reference_name
    if previous_bytes is not None:
        (output/'comparison_previous.png').write_bytes(previous_bytes)
        rerun['comparison_previous'] = 'comparison_previous.png'
    for index,item in enumerate(history_inputs):
        snapshot = output/item['snapshot_path']
        snapshot.parent.mkdir(parents=True,exist_ok=True)
        snapshot.write_bytes(item['bytes'])
        rerun['comparison_history'][index]['path'] = item['snapshot_path']
    for mask in input_masks:
        rerun['features'][mask['feature']]['scope']['path'] = 'config_masks/'+mask['feature']+'.png'
    (output/'rerun_config.json').write_text(json.dumps(rerun,ensure_ascii=False,indent=2),encoding='utf8')
    with Image.open(output/'pixel_native.png') as check:
        np.testing.assert_array_equal(np.array(check),native)
    # Region/graph diagnostics can be megabytes: keep them in the saved record,
    # not duplicated into the agent's stdout/context on every successful run.
    summary_keys = ('enabled','method','mode','tone_policy','tone_error','chroma_error','contrast_retention','minimum_contrast','color_error','tones','min_retained_tone_delta_l','scope_pixels')
    feature_summary = {name:{key:meta[key] for key in summary_keys if key in meta}
                       for name,meta in result['metadata']['features'].items()}
    print(json.dumps({'output':str(output), 'technical_checks':record['technical_checks'],
                      'features':feature_summary,
                      'details':'settings_and_result.json'}, ensure_ascii=False))


if __name__=='__main__': main()
