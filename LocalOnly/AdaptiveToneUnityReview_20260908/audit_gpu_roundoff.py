"""Bound float prefix/SSE cancellation without relaxing the GPU validator.

The bound uses binary32 unit roundoff and six scalar multiply/add operations in
the expanded SSE. Fused operations only reduce this conservative operation
count. GPU integer moments, candidates and the original evidence stay unchanged.
"""
import argparse
from decimal import Decimal, localcontext
import json
import math
from pathlib import Path
import struct

from validate_gpu_result import float_bits, normalize_float4_arrays, pair


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def pair_float(values, offset):
    return f32(f32(values[offset + 1] * 4294967296.) + f32(values[offset]))


def audit(evidence, fixture):
    data = normalize_float4_arrays(evidence)
    histogram, groups, palette, solutions = (data[name] for name in ('histogram', 'groups', 'palette', 'solutions'))
    unit = 2. ** -24
    gamma6 = 6 * unit / (1 - 6 * unit)
    result = []
    for group in range(160):
        if not data['status'][group] & 1:
            continue
        minimum, maximum = float_bits(groups[group * 8 + 6]), float_bits(groups[group * 8 + 7])
        span = f32(maximum - minimum)
        if span <= 1e-8:
            continue
        occupied = [b for b in range(32) if histogram[(group * 32 + b) * 6]]
        count_prefix, sum_prefix, square_prefix = [0], [0.], [0.]
        for bin_id in occupied:
            offset = (group * 32 + bin_id) * 6
            sum_value = f32(pair_float(histogram, offset + 1) / 65535.)
            square_value = f32(pair_float(histogram, offset + 3) / f32(65535. * 65535.))
            count_prefix.append(count_prefix[-1] + histogram[offset])
            sum_prefix.append(f32(sum_prefix[-1] + sum_value))
            square_prefix.append(f32(square_prefix[-1] + square_value))
        intervals = []
        start = 0
        for end in range(1, len(occupied) + 1):
            if end < len(occupied) and palette[group * 32 + occupied[end]] == palette[group * 32 + occupied[start]]:
                continue
            intervals.append((start, end))
            start = end
        reports, exact_total, lower_total, upper_total = [], 0., 0., 0.
        for start, end in intervals:
            count = count_prefix[end] - count_prefix[start]
            raw_sum = sum(pair(histogram, (group * 32 + bin_id) * 6 + 1) for bin_id in occupied[start:end])
            raw_square = sum(pair(histogram, (group * 32 + bin_id) * 6 + 3) for bin_id in occupied[start:end])
            gpu_sum = f32(sum_prefix[end] - sum_prefix[start])
            gpu_square = f32(square_prefix[end] - square_prefix[start])
            level = palette[group * 32 + occupied[start]][3]
            representative = f32(f32(level - minimum) / span)
            with localcontext() as context:
                context.prec = 60
                r = Decimal(representative)
                exact_sum = Decimal(raw_sum) / Decimal(65535)
                exact_square = Decimal(raw_square) / Decimal(65535 ** 2)
                exact = exact_square - 2 * r * exact_sum + r * r * count
                prepared = Decimal(gpu_square) - 2 * r * Decimal(gpu_sum) + r * r * count
            magnitude = abs(gpu_square) + 2 * abs(representative * gpu_sum) + representative ** 2 * count
            arithmetic_bound = gamma6 * magnitude
            lower = max(0., float(prepared) - arithmetic_bound)
            upper = max(0., float(prepared) + arithmetic_bound)
            exact_total += max(float(exact), 0.)
            lower_total += lower
            upper_total += upper
            reports.append({'occupied_bins': occupied[start:end], 'population': count,
                            'representative_u_float32': representative,
                            'exact_source_sum_u': float(exact_sum), 'gpu_prefix_interval_sum_u': gpu_sum,
                            'exact_source_sum_u2': float(exact_square), 'gpu_prefix_interval_sum_u2': gpu_square,
                            'exact_moment_sse': float(exact), 'sse_before_final_float_operations': float(prepared),
                            'moment_prefix_sse_error': float(prepared - exact),
                            'six_operation_roundoff_bound': arithmetic_bound,
                            'expanded_sse_interval': [lower, upper]})
        additions = max(len(intervals) - 1, 0)
        gamma_add = additions * unit / (1 - additions * unit)
        lower_total *= max(0., 1 - gamma_add)
        upper_total *= 1 + gamma_add
        count = count_prefix[-1]
        reported_rmse = solutions[group * 3][1]
        reported_sse = (reported_rmse / span) ** 2 * count
        # Divide, sqrt and final multiplication can each round once more.
        final_relative = 3 * unit / (1 - 3 * unit)
        minimum_rmse = span * math.sqrt(lower_total / count) * (1 - final_relative)
        maximum_rmse = span * math.sqrt(upper_total / count) * (1 + final_relative)
        result.append({'group': group, 'gpu_tone_count': solutions[group * 3][0],
                       'fixture_tone_error': fixture['settings']['tone_error'],
                       'gpu_reported_rmse_l': reported_rmse,
                       'exact_moments_rmse_using_gpu_float_representatives_l': span * math.sqrt(exact_total / count),
                       'reported_normalized_sse': reported_sse,
                       'binary32_operation_error_envelope_rmse_l': [minimum_rmse, maximum_rmse],
                       'reported_error_is_inside_operation_envelope': minimum_rmse <= reported_rmse <= maximum_rmse,
                       'fixture_rmse_acceptance_unchanged': reported_rmse <= fixture['settings']['tone_error'],
                       'reported_error_below_inspector_minimum_1e_4': reported_rmse <= .0001,
                       'intervals': reports})
    return {'case': fixture['name'], 'stage': 'binary32_prefix_sse_roundoff_audit',
            'binary32_unit_roundoff': unit, 'gamma_6': gamma6, 'groups': result,
            'changes_to_gpu_or_validator': 'none; original failing strict-tolerance summary preserved',
            'interpretation': 'An operation-derived enclosure explains the residual; it does not prove exact RMSE reporting at arbitrarily small tolerances.',
            'low_tolerance_limit': 'If a requested tolerance is below the reported numerical residual, a visually exact observed palette can be rejected. Current fixture acceptance is checked separately.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', required=True, type=Path)
    parser.add_argument('--result', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to(Path(__file__).resolve().parent) or target.exists():
        parser.error('Output must be a new file inside this review folder.')
    summary = audit(json.loads(args.result.read_text(encoding='utf-8-sig')),
                    json.loads(args.fixture.read_text(encoding='utf-8-sig')))
    with target.open('x', encoding='utf-8') as stream:
        json.dump(summary, stream, indent=2, allow_nan=False)
    print(json.dumps({'summary': str(target), 'groups': [
        {name: group[name] for name in ('group', 'gpu_reported_rmse_l',
            'exact_moments_rmse_using_gpu_float_representatives_l',
            'binary32_operation_error_envelope_rmse_l', 'reported_error_is_inside_operation_envelope',
            'fixture_rmse_acceptance_unchanged', 'reported_error_below_inspector_minimum_1e_4')}
        for group in summary['groups']]}))
