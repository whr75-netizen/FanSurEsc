"""Observed-color steps with bounded chromaticity and weighted lightness error.

The minimum-K claim for the unguarded weighted policy applies only to fixed
chromaticity groups and ordered one-dimensional observed-lightness quantization.
Spatial guards test one SSE-optimal candidate per K, NOT all feasible partitions.
Neither policy is material recognition or a per-pixel RGB error guarantee.
"""
from numbers import Real

import numpy as np

from .palette import rgb_to_oklab


MAX_UNIQUE_LIGHTNESS = 2048
MAX_COST_ARRAY_BYTES = 64 * 1024 * 1024
MAX_DP_TRANSITIONS = 64_000_000
MAX_CHROMA_DISTANCE_EVALUATIONS = 16_000_000
MAX_INPUT_COLORS = 65_536


def _option(value, name):
    if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
            or not np.isfinite(value) or not 0 < value <= 1):
        raise ValueError(name + ' must be finite in (0,1].')
    return float(value)


def _chroma_groups(chroma, weights, error):
    """Actual-center covering at half the allowed diameter, including rare hues."""
    mean = np.average(chroma, weights=weights, axis=0)
    first = int(np.argmin(np.sum((chroma - mean) ** 2, axis=1)))
    centers = [first]
    nearest = np.sum((chroma - chroma[first]) ** 2, axis=1)
    assigned = np.zeros(len(chroma), np.int32)
    evaluations = len(chroma)
    radius_squared = (error * .5) ** 2
    while float(nearest.max()) > radius_squared + 1e-14:
        if evaluations + len(chroma) > MAX_CHROMA_DISTANCE_EVALUATIONS:
            raise ValueError('chromaticity distance budget exceeded; no forced group merge is performed')
        selected = int(np.argmax(nearest))
        distances = np.sum((chroma - chroma[selected]) ** 2, axis=1)
        closer = distances < nearest
        assigned[closer] = len(centers)
        nearest[closer] = distances[closer]
        centers.append(selected)
        evaluations += len(chroma)
    return assigned, evaluations


def _lightness_steps(lightness, weights, error, *, constraints=()):
    """Try the SSE-optimal partition at each K, with optional spatial guards.

    With guards this is NOT the globally minimum feasible K: a different,
    non-SSE-optimal partition at the same K could satisfy the spatial guards.
    """
    values, inverse = np.unique(lightness, return_inverse=True)
    n = len(values)
    cost_bytes = (n + 1) ** 2 * (np.dtype(np.float64).itemsize + np.dtype(np.int32).itemsize)
    # The bound covers the two quadratic arrays; linear arrays add O(n) storage.
    if n > MAX_UNIQUE_LIGHTNESS or cost_bytes > MAX_COST_ARRAY_BYTES:
        raise ValueError('observed-lightness DP resource bound exceeded; no resize or tone clamp is performed')
    weights = weights / weights.sum()
    frequency = np.bincount(inverse, weights=weights, minlength=n)
    pw = np.r_[0., np.cumsum(frequency)]
    px = np.r_[0., np.cumsum(frequency * values)]
    pq = np.r_[0., np.cumsum(frequency * values * values)]

    def representatives(start, ends):
        weight = pw[ends] - pw[start]
        mean = (px[ends] - px[start]) / weight
        right = np.minimum(np.maximum(np.searchsorted(values, mean), start), ends - 1)
        left = np.maximum(start, right - 1)
        # An observed value nearest the weighted mean minimizes squared error.
        return np.where(abs(values[left] - mean) <= abs(values[right] - mean), left, right)

    costs = np.full((n + 1, n + 1), np.inf, np.float64)
    for start in range(n):
        ends = np.arange(start + 1, n + 1)
        representative = values[representatives(start, ends)]
        total = pq[ends] - pq[start]
        total -= 2 * representative * (px[ends] - px[start])
        total += representative ** 2 * (pw[ends] - pw[start])
        costs[start, ends] = np.maximum(total, 0.)
        # A single observed L has mathematically zero error. Prefix subtraction
        # can otherwise invent ~1e-16 SSE and reject an exact palette at tiny tolerances.
        costs[start, start + 1] = 0.
    back = np.full((n + 1, n + 1), -1, np.int32)
    previous = np.full(n + 1, np.inf)
    previous[0] = 0.
    transitions = 0
    previous_rmse = None
    spatial_rejections = 0

    def reconstruct(k):
        intervals = []
        end = n
        for level in range(k, 0, -1):
            start = int(back[level, end])
            representative = int(representatives(start, np.array([end]))[0])
            intervals.append((start, end, representative))
            end = start
        intervals.reverse()
        assigned_values = np.empty(n, np.int32)
        selected = []
        for tone, (start, end, representative) in enumerate(intervals):
            assigned_values[start:end] = tone
            candidates = np.flatnonzero(inverse == representative)
            selected.append(int(candidates[np.argmax(weights[candidates])]))
        return np.asarray(selected, np.int32), assigned_values[inverse]

    for k in range(1, n + 1):
        width = n - k + 1
        required = width * (width + 1) // 2
        if transitions + required > MAX_DP_TRANSITIONS:
            raise ValueError('weighted-lightness DP transition budget exceeded; no forced tone cap is performed')
        transitions += required
        current = np.full(n + 1, np.inf)
        for end in range(k, n + 1):
            candidates = previous[k - 1:end] + costs[k - 1:end, end]
            start = k - 1 + int(np.argmin(candidates))
            current[end] = previous[start] + costs[start, end]
            back[k, end] = start
        rmse = float(np.sqrt(max(current[n], 0.)))
        if rmse <= error + 1e-12:
            selected, assigned = reconstruct(k)
            target = lightness[selected][assigned]
            contrasts = [float(np.dot(c['coefficients'], target)) for c in constraints]
            if all(actual + 1e-10 >= c['minimum_contrast']
                   for actual, c in zip(contrasts, constraints)):
                break
            spatial_rejections += 1
        previous_rmse = rmse
        previous = current
    else:
        raise ValueError('No candidate satisfied the spatial contrast guards; no fallback palette returned')
    return selected, assigned, {
        'unique_lightness_count': n, 'target_tone_count': k,
        'weighted_rmse_l': rmse, 'previous_k_weighted_rmse_l': previous_rmse,
        'dp_transitions': transitions, 'quadratic_array_bytes': cost_bytes,
        'spatially_rejected_candidates': spatial_rejections,
        'retained_support_contrasts': contrasts,
        'required_support_contrasts': [float(c['minimum_contrast']) for c in constraints],
        'signed_mean_lightness_error': float(np.dot(weights, target - lightness)),
        'minimum_k_scope': ('first passing SSE-optimal candidate in increasing K; NOT global constrained minimum'
                            if constraints else
                            'fixed chromaticity group; contiguous observed-L representatives; weighted squared error')}


def select_step_palette(colors, counts, *, tone_error=.06, chroma_error=.04,
                        spatial_context=None, contrast_retention=.65, minimum_contrast=.025):
    """Return actual input representatives, input-row assignments, diagnostics.

    A rare lightness extreme may exceed tone_error at that pixel: tone_error
    bounds pixel-frequency-weighted lightness RMSE, not maximum pixel error.
    Chromaticity is grouped independently so a rare distinct hue is retained.
    """
    tone_error, chroma_error = _option(tone_error, 'tone_error'), _option(chroma_error, 'chroma_error')
    if (not isinstance(colors, np.ndarray) or colors.dtype != np.uint8
            or colors.ndim != 2 or colors.shape[1] != 3 or not 1 <= len(colors) <= MAX_INPUT_COLORS):
        raise ValueError('colors must be nonempty uint8 Nx3 within the input-color resource bound')
    counts = np.asarray(counts)
    if (counts.shape != (len(colors),) or counts.dtype.kind not in 'iuf'
            or not np.all(np.isfinite(counts)) or np.any(counts <= 0)):
        raise ValueError('counts must be finite positive numeric values, one per input color')
    if spatial_context is not None:
        contrast_retention = _option(contrast_retention, 'contrast_retention')
        minimum_contrast = _option(minimum_contrast, 'minimum_contrast')
        if not isinstance(spatial_context, dict) or set(spatial_context) != {'positions', 'color_indices'}:
            raise ValueError('spatial_context must contain positions and color_indices')
        positions = np.asarray(spatial_context['positions'])
        pixel_colors = np.asarray(spatial_context['color_indices'])
        if (positions.ndim != 2 or positions.shape[1] != 2 or positions.dtype.kind not in 'iu'
                or pixel_colors.shape != (len(positions),) or pixel_colors.dtype.kind not in 'iu'
                or len(pixel_colors) == 0 or np.any(positions < 0)
                or np.any(pixel_colors < 0) or np.any(pixel_colors >= len(colors))):
            raise ValueError('invalid spatial pixel positions or color indices')
        if len(positions) > 4_194_304:
            raise ValueError('spatial context exceeds the 4MP source-pixel resource bound')
        if len(np.unique(positions, axis=0)) != len(positions):
            raise ValueError('spatial context must not contain duplicate positions')
        if not np.array_equal(np.bincount(pixel_colors.astype(np.int64), minlength=len(colors)), counts):
            raise ValueError('spatial pixel histogram must match source counts')
    unique, original_to_unique = np.unique(colors, axis=0, return_inverse=True)
    # Normalize before summing to avoid overflow and make uniform frequency
    # scaling immaterial. Aggregate duplicate RGB rows without changing inputs.
    scaled = counts.astype(np.float64) / float(counts.max())
    weights = np.bincount(original_to_unique, weights=scaled, minlength=len(unique))
    if not np.all(np.isfinite(weights)) or np.any(weights <= 0):
        raise ValueError('count dynamic range exceeds numeric capacity; no rare color is discarded')
    weights /= weights.sum()
    if np.any(weights <= 0):
        raise ValueError('normalized counts exceed numeric capacity; no rare color is discarded')
    lab = rgb_to_oklab(unique.astype(np.float32) / 255).astype(np.float64)
    chroma = lab[:, 1:] / np.maximum(lab[:, :1], .05)
    groups, chroma_evaluations = _chroma_groups(chroma, weights, chroma_error)
    if spatial_context is not None:
        from .spatial_tones import build_spatial_constraints
        pixel_unique = original_to_unique[pixel_colors]
        pixel_groups = groups[pixel_unique]
    assignment = np.empty(len(unique), np.int32)
    ramp, group_metadata = [], []
    for identifier in range(int(groups.max()) + 1):
        members = np.flatnonzero(groups == identifier)
        constraints, spatial_metadata = [], None
        if spatial_context is not None:
            included = pixel_groups == identifier
            local_lookup = np.full(len(unique), -1, np.int32)
            local_lookup[members] = np.arange(len(members))
            pixel_local = local_lookup[pixel_unique[included]]
            constraints, spatial_metadata = build_spatial_constraints(
                lab[members, 0][pixel_local], pixel_local, positions[included], len(members),
                contrast_retention=contrast_retention, minimum_contrast=minimum_contrast)
        selected, local, info = _lightness_steps(lab[members, 0], weights[members], tone_error,
                                                constraints=constraints)
        assignment[members] = local + len(ramp)
        representatives = members[selected]
        ramp.extend(unique[representatives].tolist())
        info.update(group_id=identifier, source_color_count=len(members),
                    pixel_weight=float(weights[members].sum()))
        if spatial_metadata is not None:
            info['spatial_support'] = spatial_metadata
        group_metadata.append(info)
    ramp = np.asarray(ramp, np.uint8)
    target_lab = rgb_to_oklab(ramp.astype(np.float32) / 255).astype(np.float64)[assignment]
    target_chroma = target_lab[:, 1:] / np.maximum(target_lab[:, :1], .05)
    delta_l = lab[:, 0] - target_lab[:, 0]
    metadata = {
        'method': ('spatial-contrast-guarded-observed-lightness-dp/1' if spatial_context is not None
                   else 'fixed-chromaticity-groups-weighted-observed-lightness-dp/1'),
        'tone_error': tone_error, 'chroma_error': chroma_error,
        'source_color_count': len(unique), 'target_tone_count': len(ramp),
        'color_group_count': len(group_metadata), 'color_groups': group_metadata,
        'weighted_rmse_l': float(np.sqrt(np.sum(weights * delta_l ** 2))),
        'max_lightness_error': float(np.max(abs(delta_l))),
        'max_chroma_error': float(np.linalg.norm(chroma - target_chroma, axis=1).max()),
        'max_color_error': float(np.linalg.norm(lab - target_lab, axis=1).max()),
        'chromaticity_distance_evaluations': chroma_evaluations,
        'rgb_provenance': 'actual source RGB from the same fixed chromaticity group',
        'minimum_k_scope': ('first passing SSE-optimal candidate per group; NOT global constrained minimum'
                            if spatial_context is not None else
                            'each fixed chromaticity group, observed-L representatives and weighted squared error only'),
        'spatial_contrast_used': spatial_context is not None,
        'maximum_error_per_pixel_guaranteed': False,
        'resource_limits': {'unique_lightness_per_group': MAX_UNIQUE_LIGHTNESS,
                            'quadratic_array_bytes_per_group': MAX_COST_ARRAY_BYTES,
                            'dp_transitions_per_group': MAX_DP_TRANSITIONS,
                            'chromaticity_distance_evaluations': MAX_CHROMA_DISTANCE_EVALUATIONS},
    }
    return ramp, assignment[original_to_unique], metadata
