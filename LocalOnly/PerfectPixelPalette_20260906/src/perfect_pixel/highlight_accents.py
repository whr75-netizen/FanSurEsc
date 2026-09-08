"""Add an observed bright accent without fitting or replacing the frozen palette.

Only the original coarsest persistent high support of a chromaticity group may
receive an accent, and only where its frozen brightest retained RGB is present.
The Gaussian guide identifies source positions; it never supplies output RGB.
"""
import numpy as np

from .gradient_steps import MAX_INPUT_COLORS, _chroma_groups, _option
from .palette import rgb_to_oklab
from .spatial_tones import MAX_SOURCE_PIXELS, build_spatial_constraints, validate_spatial_options


MAX_DOMAINS = 65_536


def _rgba(value, name):
    if (not isinstance(value, np.ndarray) or value.dtype != np.uint8
            or value.ndim != 3 or value.shape[2] != 4 or min(value.shape[:2]) < 1):
        raise ValueError(name + ' must be a nonempty uint8 HxWx4 RGBA array')
    if value.shape[0] * value.shape[1] > MAX_SOURCE_PIXELS:
        raise ValueError('highlight source exceeds the 4MP pixel resource bound; no resize is performed')
    return value


def _best_tail(lightness, base_l, observed_l, observed_rgb, observed_counts, minimum_contrast):
    """Minimize frozen-base L SSE over ordered upper tails and observed accents.

    For each tail, its observed representative is nearest the weighted mean,
    subject to the minimum contrast and per-pixel non-increasing L error.
    Prefix sums and ordered searches avoid a quadratic pairwise cost array.
    """
    candidate = np.flatnonzero(observed_l >= base_l + minimum_contrast)
    if not len(candidate) or not len(lightness):
        return None
    # For exact equal-L ties prefer the most frequent actual source RGB, then
    # source RGB order. No channel-wise mean or generated RGB enters the output.
    order = np.lexsort((candidate, -observed_counts[candidate], observed_l[candidate]))
    candidate = candidate[order]
    _, first = np.unique(observed_l[candidate], return_index=True)
    candidate = candidate[first]
    candidate_l = observed_l[candidate]
    values, counts = np.unique(lightness, return_counts=True)
    weights = counts.astype(np.float64)
    tail_weight = np.cumsum(weights[::-1])[::-1]
    tail_sum = np.cumsum((weights * values)[::-1])[::-1]
    tail_square = np.cumsum((weights * values * values)[::-1])[::-1]
    means = tail_sum / tail_weight
    # h <= 2*min(tail)-b is equivalent to |L-h| <= |L-b| for every tail pixel.
    last = np.searchsorted(candidate_l, 2 * values - base_l, side='right') - 1
    valid = last >= 0
    if not np.any(valid):
        return None
    right = np.minimum(np.searchsorted(candidate_l, means), np.maximum(last, 0))
    left = np.maximum(right - 1, 0)
    chosen = np.where(abs(candidate_l[left] - means) <= abs(candidate_l[right] - means), left, right)
    accent_l = candidate_l[chosen]
    before = np.maximum(tail_square - 2 * base_l * tail_sum + base_l ** 2 * tail_weight, 0.)
    after = np.maximum(tail_square - 2 * accent_l * tail_sum + accent_l ** 2 * tail_weight, 0.)
    gain = np.where(valid, before - after, -np.inf)
    selected = int(np.argmax(gain))
    if not np.isfinite(gain[selected]) or gain[selected] <= 1e-12:
        return None
    representative = int(candidate[chosen[selected]])
    return {'rgb': observed_rgb[representative].copy(),
            'lightness': float(observed_l[representative]),
            'cutoff_lightness': float(values[selected]),
            'predicted_sse_reduction': float(gain[selected])}


def add_highlight_accents(source_rgba, frozen_base_rgba, region_labels, scope, *,
                          chroma_error=.06, minimum_contrast=.025, spatial_options=None):
    """Return corrected source-sized image, transparent overlay and JSON metadata.

    Analyze all visible source pixels within each supplied domain, so restricting
    scope does not refit chromaticity groups or move their spatial supports.
    Writes require both source and frozen alpha 255, scope, and a domain >= 0.
    The returned image preserves every frozen RGBA byte outside the overlay.
    This source-space result does not select or alter output sampling positions.
    """
    source = _rgba(source_rgba, 'source_rgba')
    base = _rgba(frozen_base_rgba, 'frozen_base_rgba')
    if source.shape != base.shape:
        raise ValueError('source_rgba and frozen_base_rgba must have the same shape')
    chroma_error = _option(chroma_error, 'chroma_error')
    minimum_contrast = _option(minimum_contrast, 'minimum_contrast')
    validate_spatial_options(spatial_options)
    if (not isinstance(region_labels, np.ndarray) or region_labels.shape != source.shape[:2]
            or region_labels.dtype.kind not in 'iu' or np.any(region_labels < -1)):
        raise ValueError('region_labels must be an integer HxW array with domain IDs or -1')
    if (not isinstance(scope, np.ndarray) or scope.dtype != np.bool_
            or scope.shape != source.shape[:2]):
        raise ValueError('scope must be a boolean HxW array')

    output, overlay = base.copy(), np.zeros_like(base)
    source_flat, base_flat = source.reshape(-1, 4), base.reshape(-1, 4)
    output_flat, overlay_flat = output.reshape(-1, 4), overlay.reshape(-1, 4)
    scope_flat = scope.ravel()
    valid = np.flatnonzero((source[..., 3] > 0) & (region_labels >= 0))
    order = np.argsort(region_labels.ravel()[valid], kind='stable')
    sorted_pixels = valid[order]
    domains, domain_counts = np.unique(region_labels.ravel()[sorted_pixels], return_counts=True)
    if len(domains) > MAX_DOMAINS:
        raise ValueError('highlight domain resource bound exceeded; no domains are merged or discarded')
    metadata = {
        'method': 'frozen-palette-source-support-observed-highlight/1',
        'chroma_error': chroma_error, 'minimum_contrast': minimum_contrast,
        'domain_count': len(domains), 'groups': [], 'changed_source_pixels': 0,
        'accent_group_count': 0, 'frozen_palette_refitted': False,
        'rgb_provenance': 'actual source RGB from the same fixed chromaticity group',
        'placement': 'original persistent high support, scoped frozen brightest retained tone only',
        'output_sampling_performed': False,
        'resource_limits': {'source_pixels': MAX_SOURCE_PIXELS,
                            'domains': MAX_DOMAINS, 'source_colors_per_domain': MAX_INPUT_COLORS},
        'limitations': ['Spatial coherence is heuristic, not material recognition or artistic approval.',
                       'A source highlight can disappear at an unchanged output sampling coordinate.',
                       'At most one accent RGB is selected per group; no accent is forced.'],
    }
    begin = 0
    for domain, count in zip(domains, domain_counts):
        pixels = sorted_pixels[begin:begin + count]
        begin += count
        colors, inverse, counts = np.unique(source_flat[pixels, :3], axis=0,
                                             return_inverse=True, return_counts=True)
        if len(colors) > MAX_INPUT_COLORS:
            raise ValueError('highlight source color resource bound exceeded; no colors are discarded')
        # This matches select_step_palette's unique-RGB order and normalization.
        weights = counts.astype(np.float64) / float(counts.max())
        weights /= weights.sum()
        lab = rgb_to_oklab(colors.astype(np.float32) / 255).astype(np.float64)
        chroma = lab[:, 1:] / np.maximum(lab[:, :1], .05)
        groups, _ = _chroma_groups(chroma, weights, chroma_error)
        pixel_groups = groups[inverse]
        for group in range(int(groups.max()) + 1):
            members = np.flatnonzero(groups == group)
            included = pixel_groups == group
            group_pixels = pixels[included]
            local_lookup = np.full(len(colors), -1, np.int32)
            local_lookup[members] = np.arange(len(members))
            pixel_local = local_lookup[inverse[included]]
            source_l = lab[members, 0][pixel_local]
            positions = np.column_stack(np.unravel_index(group_pixels, source.shape[:2]))
            _, support_meta, supports = build_spatial_constraints(
                source_l, pixel_local, positions, len(members),
                minimum_contrast=minimum_contrast, return_supports=True,
                spatial_options=spatial_options)
            report = {'domain_id': int(domain), 'group_id': group,
                      'source_pixel_count': len(group_pixels), 'changed_source_pixels': 0,
                      'spatial_support': support_meta, 'bypass_reason': None}
            metadata['groups'].append(report)
            if supports is None:
                report['bypass_reason'] = 'no_persistent_source_support'
                continue
            retained, retained_inverse = np.unique(base_flat[group_pixels, :3], axis=0,
                                                   return_inverse=True)
            retained_l = rgb_to_oklab(retained.astype(np.float32) / 255).astype(np.float64)[:, 0]
            visible_retained = np.bincount(retained_inverse,
                weights=(base_flat[group_pixels, 3] > 0), minlength=len(retained)) > 0
            if not np.any(visible_retained):
                report['bypass_reason'] = 'no_visible_frozen_tone'
                continue
            top = int(np.argmax(np.where(visible_retained, retained_l, -np.inf)))
            base_l = float(retained_l[top])
            base_pixel_l = retained_l[retained_inverse]
            eligible = (supports['high'] & (retained_inverse == top) & scope_flat[group_pixels]
                        & (source_flat[group_pixels, 3] == 255) & (base_flat[group_pixels, 3] == 255))
            report.update(frozen_brightest_rgb=retained[top].tolist(),
                          frozen_brightest_lightness=base_l,
                          eligible_source_pixels=int(eligible.sum()))
            selected = _best_tail(source_l[eligible], base_l, lab[members, 0],
                                  colors[members], counts[members], minimum_contrast)
            if selected is None:
                report['bypass_reason'] = 'no_supported_observed_bright_accent_improves_error'
                continue
            accent_l = selected['lightness']
            change = (eligible & (source_l >= selected['cutoff_lightness'])
                      & (source_l >= (base_l + accent_l) * .5))
            before_error = (source_l[change] - base_l) ** 2
            after_error = (source_l[change] - accent_l) ** 2
            gain = float(np.sum(before_error - after_error))
            if not np.any(change) or gain <= 1e-12 or np.any(after_error > before_error + 1e-14):
                report['bypass_reason'] = 'final_source_mask_does_not_improve_error'
                continue
            corrected_l = base_pixel_l.copy()
            corrected_l[change] = accent_l
            low, high = supports['low'], supports['high']
            contrast_before = float(np.mean(base_pixel_l[high]) - np.mean(base_pixel_l[low]))
            contrast_after = float(np.mean(corrected_l[high]) - np.mean(corrected_l[low]))
            if (np.any(change & low) or np.any(change & (retained_inverse != top))
                    or contrast_after + 1e-12 < contrast_before):
                raise RuntimeError('highlight violated the frozen shadow or original source-support contrast')
            changed_pixels = group_pixels[change]
            output_flat[changed_pixels, :3] = selected['rgb']
            overlay_flat[changed_pixels, :3] = selected['rgb']
            overlay_flat[changed_pixels, 3] = 255
            report.update(accent_rgb=selected['rgb'].tolist(), accent_lightness=accent_l,
                          cutoff_lightness=selected['cutoff_lightness'],
                          changed_source_pixels=len(changed_pixels),
                          source_lightness_sse_before=float(before_error.sum()),
                          source_lightness_sse_after=float(after_error.sum()),
                          source_lightness_sse_reduction=gain,
                          retained_support_contrast_before=contrast_before,
                          retained_support_contrast_after=contrast_after)
            metadata['changed_source_pixels'] += len(changed_pixels)
            metadata['accent_group_count'] += 1
    changed = overlay[..., 3] != 0
    if (not np.array_equal(output[~changed], base[~changed])
            or not np.array_equal(output[..., 3], base[..., 3])
            or np.any(changed & ~scope)):
        raise RuntimeError('highlight escaped its frozen RGBA or scope contract')
    return {'image': output, 'overlay': overlay, 'metadata': metadata}
