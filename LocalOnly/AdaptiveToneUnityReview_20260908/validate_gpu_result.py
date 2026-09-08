"""Validate actual GPU artifacts against source ownership and an independent DP.

No Unity calls are made here. Stage-DP checks use the GPU's integer histogram as
input, then independently enumerate representative errors and partitions on CPU.
The separate resolve checks compare the actual readback with original seed data.
"""
import argparse
import json
import math
from pathlib import Path
import struct

from cpu_oracle import Bin, chroma_cell_key, solve_observed_bins


def lab(rgb):
    r, g, b = rgb[:3]
    l = max(.4122214708 * r + .5363325363 * g + .0514459929 * b, 0.) ** (1 / 3)
    m = max(.2119034982 * r + .6806995451 * g + .1073969566 * b, 0.) ** (1 / 3)
    s = max(.0883024619 * r + .2817188376 * g + .6299787005 * b, 0.) ** (1 / 3)
    return (.2104542553 * l + .7936177850 * m - .0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + .4505937099 * s,
            .0259040371 * l + .7827717662 * m - .8086757660 * s)


def subject(meta):
    return round(meta[0] * 255) + (round(meta[3] * 255) << 8)


def key(rgb, meta, error):
    lightness, a, b = lab(rgb)
    part, cx, cy = chroma_cell_key(round(meta[1] * 255),
                                  (a / max(lightness, .05), b / max(lightness, .05)), error)
    if not -128 <= cx <= 127 or not -128 <= cy <= 127:
        return None
    return ((part + 1) << 16) | ((cx + 128) << 8) | (cy + 128)


def close(left, right, tolerance=1e-7):
    return len(left) == len(right) and all(abs(a - b) <= tolerance for a, b in zip(left, right))


def float_bits(value):
    return struct.unpack('<f', struct.pack('<I', value))[0]


def pair(values, offset):
    return values[offset] + (values[offset + 1] << 32)


def normalize_float4_arrays(data):
    """Accept both the original row arrays and package-free JsonUtility DTOs."""
    if data.get('arrayLayout') != 'flat_float4_v1':
        return data
    normalized = dict(data)
    names = ('source_color_depth', 'source_meta', 'seed_color_depth', 'seed_meta',
             'outputColor', 'sourceColors', 'seedColors', 'sourceMetaBefore',
             'seedMetaBefore', 'sourceMeta', 'seedMeta', 'palette', 'solutions')
    for name in names:
        if name not in data:
            continue
        values = data[name]
        if not isinstance(values, list) or len(values) % 4:
            raise ValueError(name + ' must be a flat float array with length divisible by four')
        normalized[name] = [values[index:index + 4] for index in range(0, len(values), 4)]
    return normalized


def validate(fixture, evidence):
    checks, dp_groups = [], []

    def check(name, passed, details=None, stage='resolve_and_preservation'):
        checks.append({'stage': stage, 'check': name, 'passed': bool(passed), 'details': details})

    try:
        fixture, evidence = normalize_float4_arrays(fixture), normalize_float4_arrays(evidence)
    except ValueError as error:
        check('flat_float4_shape', False, str(error), 'artifact_integrity')
        return {'case': fixture.get('name'), 'status': 'failed', 'checks': checks,
                'stage_dp': {'status': 'not_run'}}
    width, height = fixture['width'], fixture['height']
    size = width * height
    lengths = {'outputColor': size, 'sourceColors': size, 'seedColors': size,
               'sourceMeta': size, 'seedMeta': size, 'sourceMetaBefore': size, 'seedMetaBefore': size,
               'status': 161, 'groups': 160 * 8, 'histogram': 160 * 32 * 6,
               'tiles': 160 * 16 * 3, 'tileHistogram': 160 * 16 * 32,
               'supports': 160 * 2, 'palette': 160 * 32, 'solutions': 160 * 3}
    malformed = {name: len(evidence.get(name, [])) for name, count in lengths.items()
                 if len(evidence.get(name, [])) != count}
    check('result_buffer_shapes', not malformed, malformed, 'artifact_integrity')
    if malformed:
        return {'case': fixture['name'], 'status': 'failed', 'checks': checks, 'stage_dp': {'status': 'not_run'}}
    output, source, seed = evidence['outputColor'], evidence['sourceColors'], evidence['seedColors']
    status, groups, histogram = evidence['status'], evidence['groups'], evidence['histogram']
    palettes, solutions = evidence['palette'], evidence['solutions']
    global_status = status[160]
    expected, settings = fixture['expected'], fixture['settings']
    target_subject = settings['subject_id']
    error = settings['chroma_error']
    check('eye_depth_and_empty_seed_values_preserved',
          all(output[index][3] == seed[index][3] for index in range(size))
          and all(close(output[index], seed[index]) for index in range(size)
                  if subject(evidence['seedMeta'][index]) == 0))
    check('source_and_seed_metadata_unchanged', evidence['sourceMeta'] == evidence['sourceMetaBefore']
          and evidence['seedMeta'] == evidence['seedMetaBefore'])
    check('other_subjects_unchanged', all(close(output[index], seed[index]) for index in range(size)
                                       if subject(evidence['seedMeta'][index]) != target_subject))
    if 'global_status' in expected:
        check('global_status', global_status == expected['global_status'], global_status)
    if 'global_status_bits_required' in expected:
        bits = expected['global_status_bits_required']
        check('required_failure_status_bits', global_status & bits == bits, global_status)
    if expected.get('exact_seed_color_depth'):
        check('exact_original_seed_color_depth', all(close(a, b) for a, b in zip(output, seed)))
    active = [group for group in range(160) if groups[group * 8] != 0]
    ready = [group for group in active if status[group] & 1]
    if 'active_group_count' in expected:
        check('active_owner_group_count', len(active) == expected['active_group_count'], len(active), 'stage_dp')
    if global_status & 31:
        check('global_failure_preserves_original', all(close(a, b) for a, b in zip(output, seed)))
        check('global_failure_is_not_marked_ready', not ready, ready, 'stage_dp')
    else:
        check('all_active_groups_have_ready_solution', len(ready) == len(active),
              {'active': len(active), 'ready': len(ready)}, 'stage_dp')
        actual_counts = sorted(round(solutions[group * 3][0]) for group in ready)
        if 'group_tone_counts' in expected:
            check('expected_variable_tone_counts', actual_counts == sorted(expected['group_tone_counts']),
                  actual_counts, 'stage_dp')
        if 'minimum_group_tone_count' in expected:
            check('broad_gradient_uses_multiple_tones', all(count >= expected['minimum_group_tone_count']
                                                          for count in actual_counts), actual_counts, 'stage_dp')
        if expected.get('require_guard_present'):
            check('broad_source_guard_present', bool(ready) and all(status[group] & 2 for group in ready), stage='stage_dp')
    by_key = {groups[group * 8]: group for group in active}
    ranges = {}
    for group in ready:
        minimum, maximum = float_bits(groups[group * 8 + 6]), float_bits(groups[group * 8 + 7])
        span = max(maximum - minimum, 0.)
        ranges[group] = minimum, span
        active_bins, bins, candidate_rgbs = [], [], []
        low_mask, high_mask = evidence['supports'][group * 2:group * 2 + 2]
        for bin_id in range(32):
            offset = (group * 32 + bin_id) * 6
            count = histogram[offset]
            if not count:
                continue
            sample_index = histogram[offset + 5] & 4194303
            if sample_index >= size:
                check('candidate_source_index_in_bounds', False, {'group': group, 'index': sample_index}, 'stage_dp')
                continue
            color = source[sample_index][:3]
            candidate_rgbs.append(color)
            candidate_l = lab(color)[0]
            normalized = max(0., min(1., (candidate_l - minimum) / span)) if span > 1e-8 else 0.
            low_count, high_count = 0, 0
            for tile in range(16):
                population = evidence['tileHistogram'][(group * 16 + tile) * 32 + bin_id]
                low_count += population if low_mask & (1 << tile) else 0
                high_count += population if high_mask & (1 << tile) else 0
            bins.append(Bin(count, pair(histogram, offset + 1) / 65535,
                            pair(histogram, offset + 3) / 65535 ** 2,
                            normalized, sample_index, low_count, high_count))
            active_bins.append(bin_id)
        required = solutions[group * 3][2]
        # Float GPU comparisons permit 1e-6 in absolute L units. The CPU still
        # computes its interval errors independently using direct double sums.
        oracle = solve_observed_bins(bins, tone_error=(settings['tone_error'] + 1e-6) / span if span > 1e-8 else 1.,
            minimum_support_contrast=max(0., required - 1e-6) / span if required > 0 and span > 1e-8 else None)
        dp_groups.append({'group': group, 'gpu_tones': round(solutions[group * 3][0]),
                          'oracle_tones': oracle.tone_count, 'oracle_status': oracle.status,
                          'gpu_rmse_l': solutions[group * 3][1],
                          'oracle_rmse_l': oracle.rmse * span if oracle.rmse is not None else None})
        check('independent_dp_minimum_candidate_count', oracle.status == 'ok'
              and oracle.tone_count == round(solutions[group * 3][0]), dp_groups[-1], 'stage_dp')
        target_levels = [palettes[group * 32 + bin_id][3] for bin_id in active_bins]
        count = sum(item.count for item in bins)
        normalized_levels = [(value - minimum) / span if span > 1e-8 else 0. for value in target_levels]
        true_sse = sum(max(item.sum_l2 - 2 * value * item.sum_l + value * value * item.count, 0.)
                       for item, value in zip(bins, normalized_levels))
        measured_rmse = math.sqrt(true_sse / count) * span if count else 0.
        check('palette_error_matches_reported_rmse', abs(measured_rmse - solutions[group * 3][1]) <= 3e-5,
              {'group': group, 'measured_rmse_l': measured_rmse, 'reported_rmse_l': solutions[group * 3][1]}, 'stage_dp')
        check('ready_palette_meets_requested_rmse', measured_rmse <= settings['tone_error'] + 3e-5,
              {'group': group, 'rmse_l': measured_rmse}, 'stage_dp')
        check('palette_rgb_is_actual_group_candidate', all(any(close(palettes[group * 32 + bin_id][:3], color)
                                                             for color in candidate_rgbs) for bin_id in active_bins),
              {'group': group}, 'stage_dp')
        if required > 0:
            low_count, high_count = sum(item.low_count for item in bins), sum(item.high_count for item in bins)
            actual = (sum(item.high_count * value for item, value in zip(bins, target_levels)) / high_count
                      - sum(item.low_count * value for item, value in zip(bins, target_levels)) / low_count)
            check('original_support_contrast_preserved', actual + 2e-6 >= required,
                  {'group': group, 'required': required, 'actual': actual}, 'stage_dp')
        accent = solutions[group * 3 + 1]
        if accent[3] > .5:
            check('supported_highlight_positive_and_observed', accent[1] >= accent[0]
                  + settings.get('highlight_minimum_contrast', .025) - 2e-6
                  and any(close(solutions[group * 3 + 2][:3], color) for color in candidate_rgbs),
                  {'group': group, 'base_l': accent[0], 'accent_l': accent[1]}, 'highlight')
    mismatches = []
    if not global_status & 31:
        for index, (original, meta) in enumerate(zip(seed, evidence['seedMeta'])):
            if subject(meta) != target_subject or original[3] <= 0:
                continue
            try:
                logical_key = key(original, meta, error)
            except ValueError:
                logical_key = None
            group = by_key.get(logical_key)
            expected_color = original[:3]
            if group in ready:
                minimum, span = ranges[group]
                lightness = lab(original)[0]
                normalized = max(0., min(1., (lightness - minimum) / span)) if span > 1e-8 else 0.
                bin_id = min(31, int(normalized * 32))
                base = palettes[group * 32 + bin_id]
                expected_color = base[:3]
                x, y = index % width, index // width
                ox, oy, mx, my = groups[group * 8 + 2:group * 8 + 6]
                tile = min((y - oy) * 4 // (my - oy + 1), 3) * 4 + min((x - ox) * 4 // (mx - ox + 1), 3)
                accent = solutions[group * 3 + 1]
                high = evidence['supports'][group * 2 + 1] & (1 << tile)
                if accent[3] > .5 and high and base[3] == accent[0] and lightness >= accent[2] and lightness >= (accent[0] + accent[1]) * .5:
                    expected_color = solutions[group * 3 + 2][:3]
            if not close(output[index][:3], expected_color):
                mismatches.append({'index': index, 'group': group, 'actual': output[index][:3], 'expected': expected_color})
        check('resolve_matches_frozen_palette_and_supported_accent', not mismatches, mismatches[:8])
    failed = [entry for entry in checks if not entry['passed']]
    dp_failed = [entry for entry in failed if entry['stage'] == 'stage_dp']
    return {'case': fixture['name'], 'status': 'failed' if failed else 'passed',
            'global_status': global_status, 'checks': checks,
            'stage_dp': {'status': ('not_run_expected_global_failure' if global_status & 31
                                     else 'failed' if dp_failed else 'passed'), 'groups': dp_groups},
            'evidence': 'Actual GPU readback plus independent CPU interval-DP oracle; no art evaluation.',
            'float_error_tolerance_l': 3e-5}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture-dir', required=True, type=Path)
    parser.add_argument('--result-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--case', action='append')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    target = args.output.resolve()
    if not target.is_relative_to(root) or target.exists():
        parser.error('Output must be a new file within this review folder; no existing evidence is overwritten.')
    paths = [args.result_dir / (name + '.json') for name in args.case] if args.case else sorted(args.result_dir.glob('*.json'))
    if not paths:
        parser.error('No GPU result artifacts were found.')
    results = []
    for path in paths:
        evidence = json.loads(path.read_text(encoding='utf-8-sig'))
        fixture = json.loads((args.fixture_dir / (evidence['case'] + '.json')).read_text(encoding='utf-8-sig'))
        results.append(validate(fixture, evidence))
    summary = {'stage': 'gpu_readback_with_independent_stage_dp_oracle',
               'status': 'passed' if all(result['status'] == 'passed' for result in results) else 'failed',
               'case_count': len(results), 'cases': results,
               'visual_design_validation': 'not_performed', 'runtime_performance_validation': 'not_performed'}
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8') as stream:
        json.dump(summary, stream, indent=2, allow_nan=False)
    print(json.dumps({'summary': str(target), 'status': summary['status'],
                      'cases': [{'case': result['case'], 'status': result['status'],
                                 'failed_checks': [check['check'] for check in result['checks'] if not check['passed']]}
                                for result in results]}))
    raise SystemExit(0 if summary['status'] == 'passed' else 1)
