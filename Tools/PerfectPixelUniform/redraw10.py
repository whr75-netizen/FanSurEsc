"""R10: explicit line/region/ramp reconstruction, not authored-grid recovery."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

from cleanup import rgb_lab, colour_count
from uniform import process_array, GridDetectionError
from redraw_tones import build_tones

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MAX_PIXELS = 4_000_000


def save_json(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def neighbourhood(array):
    a = np.pad(array, 1, mode='constant')
    return [a[:-2, 1:-1], a[:-2, 2:], a[1:-1, 2:], a[2:, 2:],
            a[2:, 1:-1], a[2:, :-2], a[1:-1, :-2], a[:-2, :-2]]


def thin(mask):
    """Zhang-Suen topology thinning; no RGB or coordinate interpolation."""
    image = mask.copy()
    iterations = 0
    for iterations in range(1, 33):
        changed = False
        for phase in (0, 1):
            n = neighbourhood(image)
            count = sum(x.astype(np.uint8) for x in n)
            transitions = sum((~n[i] & n[(i+1) % 8]).astype(np.uint8) for i in range(8))
            if phase == 0:
                protected = (n[0] & n[2] & n[4]) | (n[2] & n[4] & n[6])
            else:
                protected = (n[0] & n[2] & n[6]) | (n[0] & n[4] & n[6])
            remove = image & (count >= 2) & (count <= 6) & (transitions == 1) & ~protected
            if np.any(remove):
                image[remove] = False
                changed = True
        if not changed:
            break
    return image, iterations


def dark_ridges(rgb, visible, material):
    """Propose valleys, abstain on neutral reflection bands and material seams."""
    lab = rgb_lab(rgb).astype(np.float32)
    lightness = lab[..., 0]
    candidate = np.zeros(visible.shape, bool)
    accepted = np.zeros(visible.shape, bool)
    reflection_uncertain = np.zeros(visible.shape, bool)
    # Symmetric opposite neighbours distinguish a valley from a monotone edge.
    # These are image hypotheses, NOT semantic groove/metal classifiers.
    for radius in (1, 2, 3):
        lpad = np.pad(lightness, radius, mode='edge')
        cpad = np.pad(lab[..., 1:], ((radius,radius),(radius,radius),(0,0)), mode='edge')
        vpad = np.pad(visible, radius, mode='constant')
        mpad = np.pad(material, radius, mode='constant', constant_values=-1)
        h, w = visible.shape
        for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
            a = lpad[radius + dy*radius:radius + dy*radius+h,
                     radius + dx*radius:radius + dx*radius+w]
            b = lpad[radius - dy*radius:radius - dy*radius+h,
                     radius - dx*radius:radius - dx*radius+w]
            va = vpad[radius + dy*radius:radius + dy*radius+h,
                      radius + dx*radius:radius + dx*radius+w]
            vb = vpad[radius - dy*radius:radius - dy*radius+h,
                      radius - dx*radius:radius - dx*radius+w]
            sa = (slice(radius + dy*radius, radius + dy*radius+h),
                  slice(radius + dx*radius, radius + dx*radius+w))
            sb = (slice(radius - dy*radius, radius - dy*radius+h),
                  slice(radius - dx*radius, radius - dx*radius+w))
            valley = visible & va & vb & (np.minimum(a, b) - lightness >= 12.0)
            candidate |= valley
            same_region = mpad[sa] == mpad[sb]
            ca, cb = cpad[sa], cpad[sb]
            side_chroma = np.sqrt(np.sum(((ca+cb)*.5)**2, axis=-1))
            chroma_delta = np.sqrt(np.sum((ca-cb)**2, axis=-1))
            reflection_uncertain |= valley & (side_chroma < 8.0)
            accepted |= valley & same_region & (chroma_delta <= 8.0) & (side_chroma >= 8.0)
    # Any neutral-reflection ambiguity wins over a different probe direction.
    accepted &= ~reflection_uncertain
    skeleton, iterations = thin(accepted)
    return accepted, skeleton, {'candidate_pixels': int(candidate.sum()),
                                'accepted_candidate_pixels': int(accepted.sum()),
                                'ambiguous_candidates_preserved': int((candidate & ~accepted).sum()),
                                'neutral_reflection_candidates_preserved': int((candidate & reflection_uncertain).sum()),
                                'skeleton_pixels': int(skeleton.sum()),
                                'thinning_iterations': iterations,
                                'semantic_classification': False,
                                'bright_ridges_promoted': False,
                                'maximum_probe_radius_source_px': 3}


def fill_line_halo(material, tone, palette, visible, candidate, line):
    """Assign removed ridge pixels to nearest non-ridge region, then lock 1px line."""
    owners = material.copy()
    levels = tone.copy()
    pending = candidate & ~line
    known = visible & ~candidate
    h, w = visible.shape
    repaired = 0
    # Synchronous Manhattan breadth expansion. Ties use lowest neighbour index.
    # Original source RGB is never used as an unbounded colour fallback.
    for _ in range(8):
        if not pending.any():
            break
        mask_pad = np.pad(known, 1, constant_values=False)
        m_pad = np.pad(owners, 1, constant_values=-1)
        t_pad = np.pad(levels, 1, constant_values=0)
        assigned = np.zeros((h, w), bool)
        for sy, sx in ((0, 1), (1, 0), (1, 2), (2, 1)):
            active = pending & ~assigned & mask_pad[sy:sy+h, sx:sx+w]
            owners[active] = m_pad[sy:sy+h, sx:sx+w][active]
            levels[active] = t_pad[sy:sy+h, sx:sx+w][active]
            assigned |= active
        if not assigned.any():
            break
        repaired += int(assigned.sum())
        pending[assigned] = False
        known |= assigned
    # Outline uses the candidate region's darkest ramp tone, not new black RGB.
    levels[line] = 0
    return owners, levels, {'halo_reassigned_pixels': repaired,
                            'unresolved_halo_pixels': int(pending.sum()),
                            'tie_policy': 'north, west, east, south at same BFS distance'}


def prepare_array(pixels):
    if not isinstance(pixels, np.ndarray) or pixels.dtype != np.uint8 or pixels.ndim != 3 or pixels.shape[2] not in (3, 4):
        raise ValueError('R10 input must be RGB/RGBA uint8.')
    if min(pixels.shape[:2]) < 2 or pixels.shape[0]*pixels.shape[1] > MAX_PIXELS:
        raise ValueError('R10 input limit: 2px per axis, 4MP.')
    start = time.perf_counter()
    grid_report = None
    try:
        working, grid_report = process_array(pixels)
        status = 'certified_repeated_rgba'
    except GridDetectionError as error:
        working = pixels.copy()
        status = 'uncertified_source_lattice'
        grid_report = getattr(error, 'report', {})
    alpha_before = working[..., 3] if working.shape[2] == 4 else np.full(working.shape[:2], 255, np.uint8)
    alpha = np.where(alpha_before >= 128, 255, 0).astype(np.uint8)
    if not np.any(alpha):
        raise ValueError('No covered pixels at explicit alpha128 threshold.')
    pitch = int(grid_report.get('period_source_px', 1)) if status == 'certified_repeated_rgba' else 1
    return working, alpha, {
        'schema': 'pixel-structure-redraw/10', 'grid_status': status,
        'grid_recovered': status == 'certified_repeated_rgba',
        'source_dimensions': [pixels.shape[1], pixels.shape[0]],
        'source_visible_rgb_colors': colour_count(pixels[..., :3], pixels[..., 3] > 0 if pixels.shape[2] == 4 else np.ones(pixels.shape[:2], bool)),
        'output_dimensions': [working.shape[1], working.shape[0]],
        'transform': {'uniform_pitch': pitch,
                      'source_origin': grid_report.get('geometry', {}).get('source_offset', [0, 0]),
                      'nonlinear_warp': False},
        'grid_evidence': grid_report,
        'alpha_policy': 'coverage >=128; explicit lossy antialias removal',
        'alpha_changed_pixels_working_lattice': int(np.count_nonzero(alpha != alpha_before)),
        'alpha_discarded_nonzero_pixels_working_lattice': int(np.count_nonzero((alpha_before > 0) & (alpha == 0))),
        'timings_seconds': {'analysis': time.perf_counter()-start},
    }


def render_array(working, alpha, report, levels=4):
    start = time.perf_counter()
    visible = alpha > 0
    original_colours = np.unique(working[visible, :3], axis=0)
    # Already-native finite palette is not a reason to reinterpret or thin it.
    binary_alpha = working.shape[2] == 3 or np.all((working[..., 3] == 0) | (working[..., 3] == 255))
    if len(original_colours) <= 12*levels and binary_alpha:
        _, inverse = np.unique(working[visible, :3], axis=0, return_inverse=True)
        count = len(original_colours)
        padded = np.repeat(original_colours[-1:], (-count) % levels, axis=0)
        palette = np.concatenate((original_colours, padded)).reshape(-1, levels, 3)
        material = np.full(visible.shape, -1, np.int16)
        material[visible] = inverse//levels
        tones = np.zeros(visible.shape, np.uint8)
        tones[visible] = inverse % levels
        line = np.zeros(visible.shape, bool)
        line_report = {'bypass': 'already binary/native finite palette', 'skeleton_pixels': 0}
        tone_report = {'bypass': True, 'source_observed_palette': True,
                       'lighting_semantics_available': False}
    else:
        tone_result = build_tones(working[..., :3], visible, levels=levels, materials=12)
        material, tones, palette = tone_result['material_id'], tone_result['tone_id'], tone_result['palette']
        tone_report = tone_result['report']
        report['timings_seconds']['tones'] = time.perf_counter()-start
        line_start = time.perf_counter()
        candidate, line, line_report = dark_ridges(working[..., :3], visible, material)
        material, tones, fill_report = fill_line_halo(material, tones, palette, visible, candidate, line)
        line_report.update(fill_report)
        report['timings_seconds']['lines'] = time.perf_counter()-line_start
    rgb = working[..., :3].copy()
    rgb[visible] = palette[material[visible], tones[visible]]
    output = np.dstack((rgb, alpha)) if working.shape[2] == 4 else rgb
    report['timings_seconds']['render_total'] = time.perf_counter()-start
    report['settings'] = {'levels': levels, 'material_candidates': 12, 'alpha_threshold': 128,
                          'manual_target_resolution': None, 'rgb_interpolation': False, 'dithering': False}
    report['tone_analysis'] = tone_report
    report['line_analysis'] = line_report
    report['colour_statistics'] = {
        'visible_rgb_colors_before': report['source_visible_rgb_colors'],
        'working_covered_rgb_colors_before': int(len(original_colours)),
        'visible_rgb_colors_after': int(len(np.unique(rgb[visible], axis=0))),
        'palette_limit': 12*levels,
    }
    report['warnings'] = [
        '원본의 선/재질은 통계적 후보입니다. 의미·디자인의 완벽한 복구를 증명하지 않습니다.',
        '원화의 명암을 단계로 보존했습니다. albedo/normal 복구나 baked 조명 제거는 아닙니다.',
        '어두운 금속 반사대와 구조선은 단일 RGB에서 모호할 수 있습니다.',
    ]
    if report['grid_status'] == 'uncertified_source_lattice':
        report['warnings'].insert(0, '원래 logical 격자의 증거가 없어 원본1px 좌표에서 재작성했습니다. 공통 logical 픽셀 크기 정규화는 미확정입니다.')
    return output, report, {'material_id': material, 'tone_id': tones, 'line_mask': line,
                            'alpha': alpha, 'palette': palette}


def process_redraw(pixels, levels=4):
    if levels not in (3, 4):
        raise ValueError('R10 levels must be 3 or 4.')
    working, alpha, report = prepare_array(pixels)
    output, report, maps = render_array(working, alpha, report, levels)
    return output, report, maps


def stage(command, source, output, levels):
    from redraw_checks import verify, palette_lookup
    source, output = Path(source).resolve(), Path(output).resolve()
    if not output.is_relative_to(ROOT):
        raise ValueError('R10 outputs must stay in workspace.')
    if command == 'prepare':
        output.mkdir(parents=True, exist_ok=False)
        raw = source.read_bytes()
        with Image.open(source) as im:
            if im.mode not in ('RGB', 'RGBA'):
                raise ValueError('No implicit image mode conversion.')
            pixels = np.array(im)
        working, alpha, report = prepare_array(pixels)
        report['source_path'] = str(source)
        report['source_sha256'] = digest(raw)
        report['source_array_sha256'] = digest(pixels.tobytes())
        report['levels'] = levels
        (output/'source.png').write_bytes(raw)
        np.savez_compressed(output/'prepared.npz', working=working, alpha=alpha)
        save_json(output/'analysis.json', report)
        return {'phase': 'prepare', 'grid_status': report['grid_status']}
    report = read_json(output/'analysis.json')
    if digest(source.read_bytes()) != report['source_sha256']:
        raise ValueError('R10 original source changed.')
    if command == 'render':
        with np.load(output/'prepared.npz', allow_pickle=False) as values:
            result, report, maps = render_array(values['working'], values['alpha'], report, report['levels'])
        Image.fromarray(result).save(output/'native.png')
        Image.fromarray(maps['line_mask'].astype(np.uint8)*255).save(output/'line-mask.png')
        Image.fromarray(maps['tone_id']*(255//max(1,report['levels']-1))).save(output/'tone-map.png')
        np.savez_compressed(output/'maps.npz', **maps)
        for delta, label in ((-1,'dim'), (1,'bright')):
            shifts = np.where(maps['line_mask'], 0, delta)
            if report['tone_analysis'].get('bypass'):
                shifts.fill(0)
            rgb = palette_lookup(maps['material_id'], maps['tone_id'], maps['palette'], shifts)
            shifted = result.copy()
            shifted[maps['alpha'] > 0, :3] = rgb[maps['alpha'] > 0]
            Image.fromarray(shifted).save(output/f'band-{label}.png')
        report['native_sha256'] = digest((output/'native.png').read_bytes())
        save_json(output/'receipt.json', report)
        return {'phase': 'render', 'colours': report['colour_statistics'], 'timings': report['timings_seconds']}
    if command == 'validate':
        with Image.open(output/'source.png') as im:
            original = np.array(im)
        with Image.open(output/'native.png') as im:
            native = np.array(im)
        with np.load(output/'maps.npz', allow_pickle=False) as data:
            maps = {key: data[key] for key in data.files}
        report = read_json(output/'receipt.json')
        checks = verify(original, native, report, maps)
        checks['files_sha256'] = {str(path): digest(path.read_bytes()) for path in output.iterdir() if path.is_file()}
        checks['art_approved'] = False
        checks['repeated_lattice_recovered'] = report['grid_recovered']
        checks['whole_normalization_certified'] = False
        save_json(output/'validation.json', checks)
        return {'phase': 'validate', **checks}
    raise ValueError('Unknown R10 stage.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare','render','validate'])
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--levels', type=int, choices=[3,4], default=4)
    args = parser.parse_args()
    result = stage(args.phase, args.source, args.output, args.levels)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result.get('passed', True) else 1


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(json.dumps({'phase': 'error', 'error': str(error)}, ensure_ascii=False))
        raise SystemExit(2)
