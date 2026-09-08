"""Grid-independent connected gradient domains and error-bounded source colors.

No SLIC seeds, image-size kernel, material names, reference hue bins or fixed K.
Domain growth uses source adjacency and bounded chromaticity, not output cells.
Farthest-first covering is deterministic and bounds color error; it is NOT a
claim to find the globally smallest palette or recover intrinsic materials.
"""
import numpy as np
from numbers import Real

from .palette import _image, rgb_to_oklab

MAX_PIXELS = 4_194_304
MAX_DOMAINS = 65_536
MAX_COLORS_PER_DOMAIN = 512  # computational guard, never a silent tone clamp


def validate_options(color_error, edge_threshold, chroma_span):
    for name, value in (('color_error', color_error), ('edge_threshold', edge_threshold),
                        ('chroma_span', chroma_span)):
        if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real) or
                not np.isfinite(value) or not 0 < value <= 1):
            raise ValueError(name + ' must be finite in (0,1].')


def _domains(lab, visible, edge_threshold, chroma_span):
    """4-connected components with abrupt-edge and component-wide color bounds.

    Oklab is homogeneous in the cube root of a linear-RGB intensity multiplier:
    (a/L,b/L) removes that multiplier except numerical noise near black. A whole
    component's chromaticity bounding-box diagonal is limited to prevent an
    arbitrarily long chain of small hue changes joining a rainbow into one ramp.
    This bound has color units, no spatial radius/area/minimum region size.
    """
    h, w = visible.shape
    n = h * w
    chroma = lab[..., 1:] / np.maximum(lab[..., :1], .05)
    low = chroma.reshape(-1, 2).copy()
    high = low.copy()
    parent = np.arange(n, dtype=np.int32)
    rank = np.zeros(n, np.uint8)
    ids = parent.reshape(h, w)
    edge = np.zeros((h, w), np.float32)
    starts, ends, costs = [], [], []
    candidate_count = 0
    for axis in (0, 1):
        if lab.shape[axis] < 2:
            continue
        first = (slice(None, -1), slice(None)) if axis == 0 else (slice(None), slice(None, -1))
        second = (slice(1, None), slice(None)) if axis == 0 else (slice(None), slice(1, None))
        delta = lab[second] - lab[first]
        distance = np.linalg.norm(delta, axis=2)
        active = visible[first] & visible[second]
        previous, following = np.zeros_like(delta), np.zeros_like(delta)
        prev_active, next_active = np.zeros_like(active), np.zeros_like(active)
        if axis == 0:
            previous[1:] = delta[:-1]; following[:-1] = delta[1:]
            prev_active[1:] = active[:-1]; next_active[:-1] = active[1:]
        else:
            previous[:, 1:] = delta[:, :-1]; following[:, :-1] = delta[:, 1:]
            prev_active[:, 1:] = active[:, :-1]; next_active[:, :-1] = active[:, 1:]
        residual = np.maximum(np.linalg.norm(delta - previous, axis=2),
                              np.linalg.norm(delta - following, axis=2))
        # A large but smoothly continuing slope is not a material boundary.
        smooth = (prev_active & next_active & (residual <= edge_threshold * .5) &
                  ((delta * previous).sum(axis=2) > 0) &
                  ((delta * following).sum(axis=2) > 0))
        allowed = active & ((distance <= edge_threshold) | smooth)
        candidate_count += int(active.sum())
        starts.append(ids[first][allowed]); ends.append(ids[second][allowed])
        costs.append(distance[allowed])
        strength = np.where(active, np.clip(distance / edge_threshold, 0, 1), 0)
        np.maximum(edge[first], strength, out=edge[first])
        np.maximum(edge[second], strength, out=edge[second])
    if starts:
        aa, bb, dd = np.concatenate(starts), np.concatenate(ends), np.concatenate(costs)
    else:
        aa = bb = np.empty(0, np.int32); dd = np.empty(0, np.float32)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = int(parent[a])
        return a

    rejected_chroma = 0
    span_sq = float(chroma_span) ** 2
    for index in np.argsort(dd, kind='stable'):
        a, b = find(int(aa[index])), find(int(bb[index]))
        if a == b:
            continue
        lo, hi = np.minimum(low[a], low[b]), np.maximum(high[a], high[b])
        if float(np.sum((hi - lo) ** 2)) > span_sq + 1e-10:
            rejected_chroma += 1
            continue
        if rank[a] < rank[b]:
            a, b = b, a
        parent[b] = a
        low[a], high[a] = lo, hi
        if rank[a] == rank[b]:
            rank[a] += 1
    indices = np.flatnonzero(visible)
    roots = parent[indices]
    while len(roots) and np.any(parent[roots] != roots):
        roots = parent[roots]
    _, inverse = np.unique(roots, return_inverse=True)
    count = int(inverse.max()) + 1 if len(inverse) else 0
    if count > MAX_DOMAINS:
        raise ValueError(f'{count} gradient domains exceed the {MAX_DOMAINS} resource bound; no pruning or resize.')
    labels = np.full(n, -1, np.int32)
    labels[indices] = inverse
    return labels.reshape(h, w), edge, {
        'method': 'source-continuity-bounded-chromaticity/1', 'region_count': count,
        'source_size': [w, h], 'connectivity': 4,
        'output_grid_used': False, 'spatial_size_threshold': None,
        'minimum_area_pruning': False, 'slic_used': False,
        'edge_threshold_oklab': float(edge_threshold),
        'maximum_chromaticity_box_diagonal': float(chroma_span),
        'black_chromaticity_denominator_floor': .05,
        'candidate_adjacencies': candidate_count,
        'locally_continuous_adjacencies': len(dd),
        'component_chromaticity_rejections': rejected_chroma,
    }


def _cover(colors, counts, error):
    """Add observed representatives until EVERY source color is within error.

    No area-quantile exemption: a tiny distinct eye/accent is not averaged away.
    Frequency chooses the first medoid only, not permission to exceed the bound.
    Labels use full Oklab distance so equal-lightness hue changes survive too.
    """
    lab = rgb_to_oklab(colors.astype(np.float32) / 255)
    weights = counts.astype(np.float64) / counts.sum()
    mean = np.sum(lab.astype(np.float64) * weights[:, None], axis=0)
    first = int(np.argmin(np.sum((lab - mean) ** 2, axis=1)))
    chosen = [first]
    distances = np.sum((lab - lab[first]) ** 2, axis=1)
    assigned = np.zeros(len(colors), np.int32)
    limit = float(error) ** 2
    while float(distances.max()) > limit + 1e-14:
        if len(chosen) >= MAX_COLORS_PER_DOMAIN:
            raise ValueError('Gradient palette exceeds the explicit resource bound; increase color_error. No forced K clamp.')
        candidate = int(np.argmax(distances))
        next_distance = np.sum((lab - lab[candidate]) ** 2, axis=1)
        better = next_distance < distances
        assigned[better] = len(chosen)
        distances[better] = next_distance[better]
        chosen.append(candidate)
    return colors[chosen], assigned, {
        'target_tone_count': len(chosen),
        'max_color_error': float(np.sqrt(distances.max())),
        'weighted_rms_color_error': float(np.sqrt(np.sum(distances * weights))),
        'source_lightness_span': float(np.ptp(lab[:, 0])),
    }


def prepare_gradient_tones(image, *, color_error=.06, edge_threshold=.06, chroma_span=.12,
                           tone_policy='max_error', tone_error=.06, chroma_error=.06):
    image = _image(image)
    if image.shape[0] * image.shape[1] > MAX_PIXELS:
        raise ValueError('Gradient processing exceeds the explicit 4MP resource bound; no hidden resize.')
    validate_options(color_error, edge_threshold, chroma_span)
    if tone_policy not in ('max_error', 'weighted_steps'):
        raise ValueError('tone_policy must be max_error or weighted_steps.')
    if tone_policy == 'weighted_steps':
        from .gradient_steps import select_step_palette, _option
        _option(tone_error, 'tone_error'); _option(chroma_error, 'chroma_error')
    visible = np.ones(image.shape[:2], bool) if image.shape[2] == 3 else image[..., 3] > 0
    rgb = image[..., :3]
    lab = rgb_to_oklab(rgb.astype(np.float32) / 255)
    labels, edge, segmentation = _domains(lab, visible, edge_threshold, chroma_span)
    output = image.copy()
    valid = np.flatnonzero(visible)
    order = np.argsort(labels.ravel()[valid], kind='stable')
    sorted_indices = valid[order]
    identifiers, counts = np.unique(labels.ravel()[sorted_indices], return_counts=True)
    begin, regions = 0, []
    for identifier, count in zip(identifiers, counts):
        indices = sorted_indices[begin:begin + count]; begin += count
        colors, inverse, weights = np.unique(rgb.reshape(-1, 3)[indices], axis=0,
                                             return_inverse=True, return_counts=True)
        if tone_policy == 'weighted_steps':
            ramp, choice, meta = select_step_palette(colors, weights,
                tone_error=tone_error, chroma_error=chroma_error)
        else:
            ramp, choice, meta = _cover(colors, weights, color_error)
        output.reshape(-1, image.shape[2])[indices, :3] = ramp[choice[inverse]]
        regions.append({'region_id': int(identifier), 'pixel_count': int(count),
                        'source_color_count': len(colors), 'target_ramp': ramp.tolist(), **meta})
    tone_map = np.full(visible.shape, -1, np.int32)
    palette, inverse = np.unique(output[..., :3][visible], axis=0, return_inverse=True)
    tone_map[visible] = inverse
    colors_metadata = {
        'method': ('shared-domain-weighted-lightness-steps/1' if tone_policy == 'weighted_steps'
                   else 'shared-domain-error-bounded-observed-color-cover/1'),
        'tone_policy': tone_policy,
        'region_count': len(regions), 'regions': regions,
        'color_error_limit_oklab': float(color_error) if tone_policy == 'max_error' else None,
        'weighted_lightness_error_limit': float(tone_error) if tone_policy == 'weighted_steps' else None,
        'chromaticity_error_limit': float(chroma_error) if tone_policy == 'weighted_steps' else None,
        'fixed_tone_count': None, 'max_observed_color_error': max(
            (r['max_color_error'] for r in regions), default=0.),
        'palette_size': len(palette), 'reference_palette_transfer': False,
        'rgb_provenance': 'actual source colors from the same connected gradient domain',
        'lightness_rescaled': False, 'rgb_averaging': False,
        'limits': {'max_pixels': MAX_PIXELS, 'max_domains': MAX_DOMAINS,
                   'max_colors_per_domain': MAX_COLORS_PER_DOMAIN if tone_policy == 'max_error' else None},
        'limitations': ['Not intrinsic material recognition; smoothly blended materials can be ambiguous.',
                       'Error bound is not artistic approval or globally minimal palette size.',
                       'Source enlargement invariance is not guaranteed for arbitrary resampling, noise or compression.',
                       'Disconnected gradient domains do not yet share a cross-domain style palette.',
                       'weighted_steps limits weighted lightness error, NOT worst per-pixel RGB error.'],
    }
    return {'flat_image': output, 'region_labels': labels, 'edge_strength': edge,
            'tone_map': tone_map, 'palette': palette,
            'metadata': {'method': 'continuous-gradient-tones/2', 'tone_policy': tone_policy,
                         'tone_error': tone_error if tone_policy == 'weighted_steps' else None,
                         'chroma_error': chroma_error if tone_policy == 'weighted_steps' else None,
                         'segmentation': segmentation,
                         'region_colors': colors_metadata, 'output_sampling_performed': False,
                         'fallback_algorithm': None}}
