"""Reproducible region-boundary palette processing, with no intermediate UI."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.deps'))
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from perfect_pixel.boundary_pipeline import BoundaryOptions, get_boundary_pixel
from perfect_pixel.palette import scaled_grid, detect_base_grid

SNAPSHOT_FILES = ['boundary_cli.py', 'boundary_review_config.json', 'requirements-boundary.txt',
                  'src/perfect_pixel/__init__.py', 'src/perfect_pixel/boundary_pipeline.py',
                  'src/perfect_pixel/boundary_regions.py', 'src/perfect_pixel/region_palette.py',
                  'src/perfect_pixel/gradient_tones.py',
                  'src/perfect_pixel/gradient_steps.py',
                  'src/perfect_pixel/palette.py', 'src/perfect_pixel/perfect_pixel_noCV2.py',
                  'src/perfect_pixel/perfect_pixel.py', 'src/perfect_pixel/reference_colors.py']

def read_image(path):
    with Image.open(path) as im:
        return np.array(im.convert('RGBA' if 'A' in im.getbands() or 'transparency' in im.info else 'RGB'))


def parse_grid(value):
    if isinstance(value, str):
        pieces = value.lower().split('x')
        if len(pieces) != 2 or any(not p.strip().isdigit() for p in pieces):
            raise ValueError('Grid must be two positive integer dimensions, e.g.70x73.')
        value = tuple(int(x) for x in pieces)
    grid = tuple(value)
    scaled_grid(grid)
    return grid


def sheet_dimensions(grid, zoom, reference_shape, previous_shape=None):
    if isinstance(zoom, bool) or not isinstance(zoom, int) or not 1 <= zoom <= 16:
        raise ValueError('Preview zoom must be an integer in [1,16].')
    sizes = [(grid[0] * zoom, grid[1] * zoom), (reference_shape[1], reference_shape[0])]
    if previous_shape is not None:
        sizes.append((previous_shape[1] * zoom, previous_shape[0] * zoom))
    if any(w * h > 24_000_000 for w, h in sizes):
        raise ValueError('A preview exceeds24MP; lower zoom. No files created.')
    width, height = max(w for w, _ in sizes), max(h for _, h in sizes)
    total = ((width + 16) * len(sizes) + 16, height + 84)
    if total[0] * total[1] > 72_000_000:
        raise ValueError('Comparison exceeds72MP. No files created.')
    return width, height, total


def create_comparison(result, reference, previous, zoom, target, previous_label='PREVIOUS'):
    def enlarge(array):
        im = Image.fromarray(array)
        return im.resize((im.width * zoom, im.height * zoom), Image.Resampling.NEAREST)
    width, height, size = sheet_dimensions((result.image.shape[1], result.image.shape[0]), zoom,
                                            reference.shape, None if previous is None else previous.shape)
    panels = []
    if previous is not None:
        panels.append((previous_label, enlarge(previous)))
    panels.extend([('STYLE REFERENCE', Image.fromarray(reference)),
                   ('NEW / REGION BOUNDARIES', enlarge(result.image))])
    sheet = Image.new('RGB', size, (242, 242, 247))
    draw = ImageDraw.Draw(sheet)
    font_path = Path('C:/Windows/Fonts/segoeui.ttf')
    font = ImageFont.truetype(str(font_path), 17) if font_path.exists() else ImageFont.load_default()
    for i, (name, im) in enumerate(panels):
        x = 16 + i * (width + 16)
        draw.text((x, 8), name, fill=(25, 25, 35), font=font)
        rgba = im.convert('RGBA')
        sheet.paste(rgba, (x + (width - im.width) // 2, 40 + (height - im.height) // 2), rgba)
    draw.text((16, height + 52), f'Native {result.image.shape[1]}x{result.image.shape[0]} | source regions + palette + fixed grid | no generative redraw',
              fill=(25, 25, 35), font=font)
    sheet.save(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', type=Path)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--reference-box')
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--base')
    parser.add_argument('--scale')
    parser.add_argument('--tones', type=int)
    parser.add_argument('--min-retained-tone-delta-l', type=float)
    parser.add_argument('--zoom', type=int)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    config = {} if args.config is None else json.loads(args.config.read_text(encoding='utf8'))
    config_root = Path.cwd() if args.config is None else args.config.resolve().parent
    def value(name, default=None):
        given = getattr(args, name, None)
        return given if given is not None else config.get(name, default)
    def path_value(name):
        given = getattr(args, name, None)
        if given is not None:
            return Path(given).resolve()
        found = config.get(name)
        return None if found is None else (config_root / found).resolve()
    source_path, ref_path = path_value('source'), path_value('reference')
    if source_path is None or ref_path is None:
        parser.error('source and reference are required, as arguments or in the JSON config.')
    previous_path = path_value('previous')
    source, reference = read_image(source_path), read_image(ref_path)
    previous = None if previous_path is None else read_image(previous_path)
    box = value('reference_box')
    if box is not None:
        box = tuple(int(x) for x in (box.split(',') if isinstance(box, str) else box))
        if len(box) != 4 or not (0 <= box[0] < box[2] <= reference.shape[1] and 0 <= box[1] < box[3] <= reference.shape[0]):
            parser.error('Invalid reference selection box.')
        reference = reference[box[1]:box[3], box[0]:box[2]].copy()
    base = detect_base_grid(source) if value('base') is None else parse_grid(value('base'))
    scale, zoom = str(value('scale', '1.0')), value('zoom', 6)
    grid = scaled_grid(base, scale)
    sheet_dimensions(grid, zoom, reference.shape, None if previous is None else previous.shape)
    output = args.output.resolve() if args.output is not None else ROOT / 'boundary_runs' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        parser.error('Output must be a new/empty directory. Existing reviews are preserved.')
    options = BoundaryOptions(tones=value('tones', 3),
        min_retained_tone_delta_l=value('min_retained_tone_delta_l', .025))
    code_snapshot = {rel:(ROOT / rel).read_bytes() for rel in SNAPSHOT_FILES}
    source_before = hashlib.sha256(source.tobytes()).hexdigest()
    ref_before = hashlib.sha256(reference.tobytes()).hexdigest()
    result = get_boundary_pixel(source, reference, base, scale, options)
    if any((ROOT / rel).read_bytes() != data for rel, data in code_snapshot.items()):
        raise RuntimeError('Implementation changed during processing; no result is saved with mismatched code.')
    if hashlib.sha256(source.tobytes()).hexdigest() != source_before or hashlib.sha256(reference.tobytes()).hexdigest() != ref_before:
        raise ValueError('A processing stage modified its input array.')
    if result.image.shape[:2] != (grid[1], grid[0]):
        raise ValueError('Native output does not match the requested grid.')
    emitted = result.image[..., :3] if result.image.shape[2] == 3 else result.image[..., :3][result.image[..., 3] > 0]
    allowed = set(map(tuple, result.palette.tolist()))
    if any(tuple(color) not in allowed for color in np.unique(emitted.reshape(-1, 3), axis=0)):
        raise ValueError('Output contains a color outside the discrete palette.')
    import scipy, skimage, PIL
    metadata = result.metadata
    metadata['profile'] = config.get('profile', 'unspecified')
    metadata['runtime'] = {'python':sys.version.split()[0], 'numpy':np.__version__,
                           'scipy':scipy.__version__, 'scikit_image':skimage.__version__, 'pillow':PIL.__version__}
    metadata['inputs'] = {'source':str(source_path), 'source_file_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),
                          'reference':str(ref_path), 'reference_file_sha256':hashlib.sha256(ref_path.read_bytes()).hexdigest(),
                          'reference_box':box, 'previous':None if previous_path is None else str(previous_path)}
    metadata['implementation_sha256'] = {rel:hashlib.sha256(data).hexdigest() for rel, data in code_snapshot.items()}
    metadata['technical_checks'] = {'inputs_unchanged':True, 'exact_grid':True, 'only_palette_rgb':True,
                                     'no_intermediate_user_questions':True, 'design_not_auto_approved':True}
    serialized = json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)
    output.mkdir(parents=True, exist_ok=True)
    Image.fromarray(result.image).save(output / 'pixel_native.png')
    Image.fromarray(result.image).resize((grid[0]*zoom, grid[1]*zoom), Image.Resampling.NEAREST).save(output / 'pixel_preview.png')
    Image.fromarray(result.flat_image).save(output / 'flat_reference_colors.png')
    np.savez_compressed(output / 'structure_maps.npz', regions=result.region_labels, edge_strength=result.edge_strength,
                        native_regions=result.native_regions, native_tones=result.native_tones)
    create_comparison(result, reference, previous, zoom, output / 'comparison.png',
        previous_label=config.get('previous_label', 'PREVIOUS'))
    (output / 'settings_and_result.json').write_text(serialized, encoding='utf8')
    snapshot_dir = output / 'code'
    snapshot_dir.mkdir()
    for rel, data in code_snapshot.items():
        target = snapshot_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(json.dumps({'output':str(output), 'native':list(grid), 'palette':len(result.palette),
                      'source_regions':metadata['sampling']['source_region_count'],
                      'represented_regions':metadata['sampling']['represented_region_count']}, ensure_ascii=False))


if __name__ == '__main__': main()
