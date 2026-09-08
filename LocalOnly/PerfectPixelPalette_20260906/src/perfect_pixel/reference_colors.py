"""Deterministic, geometry-preserving transfer to actual reference RGB ramps.

This is a bounded color-space heuristic, not semantic correspondence or matting.
No object coordinates, named colors, learned profiles, or generated RGB are used.
"""
import numpy as np

from .palette import rgb_to_oklab


_MAX_PIXELS = 16_777_216
_MAX_SOURCE_COLORS = 262_144
_HUE_BINS = 24


def _validate_image(image, name):
    if (not isinstance(image, np.ndarray) or image.dtype != np.uint8 or
            image.ndim != 3 or image.shape[2] not in (3, 4) or
            not image.shape[0] or not image.shape[1]):
        raise ValueError(name + ' must be a nonempty uint8 RGB/RGBA array')
    if image.shape[0] * image.shape[1] > _MAX_PIXELS:
        raise ValueError(name + ' exceeds the 16-megapixel processing bound')


def _packed(rgb):
    c = rgb.astype(np.uint32)
    return (c[:, 0] << 16) | (c[:, 1] << 8) | c[:, 2]


def _unpacked(codes):
    return np.stack(((codes >> 16) & 255, (codes >> 8) & 255,
                     codes & 255), axis=1).astype(np.uint8)


def _dictionary(reference):
    """At most 32^3 occupied RGB cells, each represented by an actual pixel.

    Keep exact-color counts: flat colors must not have the same influence as
    thousands of distinct antialiased colors. Every occupied cell survives, but
    its representative is its most frequent actual RGB, with a stable tie-break.
    """
    flat = reference.reshape(-1, reference.shape[2])
    chunks = []
    for start in range(0, len(flat), 131072):
        block = flat[start:start + 131072]
        rgb = block[:, :3] if block.shape[1] == 3 else block[block[:, 3] > 0, :3]
        if len(rgb):
            chunks.append(_packed(rgb))
    if not chunks:
        raise ValueError('reference has no pixels with nonzero alpha')
    packed = np.concatenate(chunks)
    del chunks
    codes, counts = np.unique(packed, return_counts=True)
    del packed
    colors = _unpacked(codes)
    q = colors.astype(np.uint16) >> 3
    bins = (q[:, 0] << 10) | (q[:, 1] << 5) | q[:, 2]
    order = np.lexsort((codes, -counts, bins))
    _, first = np.unique(bins[order], return_index=True)
    chosen = order[first]
    return colors[chosen], counts[chosen].astype(np.float64)


def _color_features(rgb):
    lab = rgb_to_oklab(rgb.astype(np.float32) / 255)
    chroma = np.linalg.norm(lab[:, 1:], axis=1)
    hue = np.arctan2(lab[:, 2], lab[:, 1])
    # Channel equality, not broad perceptual-chroma rejection: pale colors keep
    # their hue family. Very dark colors have numerically unreliable hue.
    neutral = (np.ptp(rgb.astype(np.int16), axis=1) <= 6) | (rgb.max(axis=1) <= 8)
    return lab, chroma, hue, neutral


def _weighted_median(values, weights):
    order = np.argsort(values, kind='stable')
    index = np.searchsorted(np.cumsum(weights[order]), weights.sum() * .5)
    return float(values[order[min(index, len(order) - 1)]])


def _make_ramps(colors, weights, tones):
    lab, chroma, hue, neutral = _color_features(colors)
    labels = np.floor(((hue + np.pi / _HUE_BINS) % (2 * np.pi)) /
                      (2 * np.pi / _HUE_BINS)).astype(np.int16)
    labels[neutral] = _HUE_BINS
    ramps, ramp_weights = [], []
    for label in np.unique(labels):
        members = np.flatnonzero(labels == label)
        values = lab[members, 0]
        unique_l = np.unique(values)
        count = min(tones, len(unique_l))
        # Distinct-value initialization cannot collapse because a tone occupies
        # less than 5% of the pixels. Refinement uses actual exact-color counts.
        centers = unique_l[np.rint(np.linspace(0, len(unique_l) - 1, count)).astype(int)]
        for _ in range(12):
            assignment = np.argmin(abs(values[:, None] - centers), axis=1)
            updated = np.array([_weighted_median(values[assignment == k], weights[members[assignment == k]])
                                for k in range(len(centers))])
            if np.max(abs(updated - centers)) < 1e-7:
                break
            centers = updated
        assignment = np.argmin(abs(values[:, None] - centers), axis=1)
        indices = []
        for k in range(len(centers)):
            candidates = members[assignment == k]
            # A flat actual RGB wins over individually rare interpolation colors.
            indices.append(int(candidates[np.argmax(weights[candidates])]))
        indices.sort(key=lambda i: float(lab[i, 0]))
        ramps.append(colors[indices])
        ramp_weights.append(weights[indices])
    return ramps, ramp_weights


def transfer_reference_colors(source_native, reference, tones=3):
    """Return recolored native pixels and JSON metadata; never resample geometry.

    ``tones`` is 1..3 per bounded reference hue range, not a total palette size.
    Nonzero-alpha pixels participate in transfer. Zero-alpha RGB and every alpha
    byte remain unchanged. Both inputs are read-only. Missing/ambiguous reference
    hue matches are reported, not claimed to be recovered semantic colors.
    """
    _validate_image(source_native, 'source_native')
    _validate_image(reference, 'reference')
    if isinstance(tones, (bool, np.bool_)) or not isinstance(tones, (int, np.integer)) or not 1 <= tones <= 3:
        raise ValueError('tones must be an integer from 1 to 3')
    tones = int(tones)
    dictionary, dictionary_weights = _dictionary(reference)
    ramps, ramp_weights = _make_ramps(dictionary, dictionary_weights, tones)
    palette_rgb = np.concatenate(ramps)
    palette_group = np.concatenate([np.full(len(ramp), i, np.int32) for i, ramp in enumerate(ramps)])
    palette_lab, palette_chroma, palette_hue, palette_neutral = _color_features(palette_rgb)
    relative_weight = np.concatenate([w / w.max() for w in ramp_weights])
    source_rgb = source_native[..., :3].reshape(-1, 3)
    codes, inverse = np.unique(_packed(source_rgb), return_inverse=True)
    if len(codes) > _MAX_SOURCE_COLORS:
        raise ValueError('source_native exceeds the 262144-color metadata bound')
    colors = _unpacked(codes)
    lab, chroma, hue, neutral = _color_features(colors)
    visible = (np.ones(source_native.shape[:2], dtype=bool) if source_native.shape[2] == 3
               else source_native[..., 3] > 0).reshape(-1)
    visible_colors = np.zeros(len(colors), dtype=bool)
    visible_colors[inverse[visible]] = True
    choice = np.zeros(len(colors), dtype=np.int32)
    hue_error = np.zeros(len(colors), dtype=np.float64)
    ambiguous = np.zeros(len(colors), dtype=bool)
    retained = np.zeros(len(colors), dtype=bool)
    targets = colors.copy()
    for start in range(0, len(colors), 4096):
        end = min(start + 4096, len(colors))
        angle = abs((hue[start:end, None] - palette_hue[None, :] + np.pi) %
                    (2 * np.pi) - np.pi)
        reliability = np.minimum(chroma[start:end, None], palette_chroma[None, :]) / .03
        reliability = np.clip(reliability, 0, 1)
        cost = 6 * (1 - np.cos(angle)) * reliability
        cost += .35 * np.log((chroma[start:end, None] + .02) /
                            (palette_chroma[None, :] + .02)) ** 2
        # Absolute lightness role, not image-specific rank expansion. The hard
        # floor prevents a near-white input from becoming a middle gray.
        cost += ((lab[start:end, None, 0] - palette_lab[None, :, 0]) / .1) ** 2
        cost += 4 * (neutral[start:end, None] != palette_neutral[None, :])
        cost += .15 * -np.log(np.maximum(relative_weight[None, :], 1e-12))
        allowed = palette_lab[None, :, 0] >= lab[start:end, None, 0] - .02
        cost[~allowed] = np.inf
        exact = np.all(colors[start:end, None, :] == palette_rgb[None, :, :], axis=2)
        cost[exact] = -1
        unavailable = ~np.any(allowed, axis=1)
        local = np.argmin(cost, axis=1)
        choice[start:end] = palette_group[local]
        targets[start:end] = palette_rgb[local]
        targets[start:end][unavailable] = colors[start:end][unavailable]
        retained[start:end] = unavailable
        hue_error[start:end] = angle[np.arange(end - start), local]
        if cost.shape[1] > 1:
            best_two = np.partition(cost, 1, axis=1)[:, :2]
            finite = np.isfinite(best_two[:, 1])
            ambiguous[start:end][finite] = best_two[finite, 1] - best_two[finite, 0] < .05
    # Enforce nondecreasing target L ONLY inside an already matched reference
    # range. This is a lookup over RGB values, never a spatial/label operation.
    for group, ramp in enumerate(ramps):
        members = np.flatnonzero((choice == group) & visible_colors & ~retained)
        if len(members) < 2 or len(ramp) < 2:
            continue
        members = members[np.argsort(lab[members, 0], kind='stable')]
        rl, rc, rh, rn = _color_features(ramp)
        angle = abs((hue[members, None] - rh[None, :] + np.pi) % (2 * np.pi) - np.pi)
        reliability = np.clip(np.minimum(chroma[members, None], rc[None, :]) / .03, 0, 1)
        cost = 6 * (1 - np.cos(angle)) * reliability
        cost += .35 * np.log((chroma[members, None] + .02) / (rc[None, :] + .02)) ** 2
        cost += ((lab[members, None, 0] - rl[None, :, 0]) / .1) ** 2
        cost += 4 * (neutral[members, None] != rn[None, :])
        cost += .15 * -np.log(ramp_weights[group][None, :] / ramp_weights[group].max())
        cost[rl[None, :, 0] < lab[members, None, 0] - .02] = np.inf
        exact = np.all(colors[members, None, :] == ramp[None, :, :], axis=2)
        cost[np.any(exact, axis=1)] = np.inf
        cost[exact] = -1
        previous = np.zeros(cost.shape, dtype=np.int8)
        cumulative = cost[0].copy()
        for row in range(1, len(members)):
            predecessor = np.array([np.argmin(cumulative[:k + 1]) for k in range(len(ramp))])
            previous[row] = predecessor
            cumulative = cost[row] + cumulative[predecessor]
        if not np.any(np.isfinite(cumulative)):
            raise RuntimeError('no monotone reference lookup satisfies the brightness and exact-anchor constraints')
        selected = int(np.argmin(cumulative))
        for row in range(len(members) - 1, -1, -1):
            targets[members[row]] = ramp[selected]
            hue_error[members[row]] = angle[row, selected]
            selected = int(previous[row, selected])
    targets[~visible_colors] = colors[~visible_colors]
    output = source_native.copy()
    out_rgb = output[..., :3].copy().reshape(-1, 3)
    out_rgb[visible] = targets[inverse[visible]]
    output[..., :3] = out_rgb.reshape(output.shape[0], output.shape[1], 3)
    mappings = []
    for i, color in enumerate(colors):
        ramp = ramps[choice[i]]
        ramp_l = rgb_to_oklab(ramp.astype(np.float32) / 255)[:, 0]
        valid_ramp = ramp[ramp_l >= lab[i, 0] - .02]
        if retained[i]:
            valid_ramp = color[None, :]
        mappings.append({'source_rgb': color.tolist(), 'target_rgb': targets[i].tolist(),
                         'target_ramp': valid_ramp.tolist() if visible_colors[i] else [],
                         'reference_hue_distance_degrees': float(np.degrees(hue_error[i])) if visible_colors[i] else None,
                         'ambiguous_match': bool(ambiguous[i] and visible_colors[i]),
                         'retained_source_for_brightness_floor': bool(retained[i] and visible_colors[i])})
    palette = np.unique(np.concatenate(ramps), axis=0).tolist()
    group_counts = []
    for group in range(len(ramps)):
        members = (choice == group) & visible_colors & ~retained
        if not np.any(members):
            continue
        source_count = int(np.sum(members))
        target_count = int(len(np.unique(targets[members], axis=0)))
        group_counts.append({'reference_range': group,
                             'source_color_count': source_count,
                             'source_lightness_level_count': int(len(np.unique(lab[members, 0]))),
                             'target_color_count': target_count,
                             'collapsed_source_color_count': source_count - target_count})
    retained_count = int(np.sum(retained & visible_colors))
    metadata = {
        'method': 'bounded-reference-oklab-brightness-lookup/2',
        'mappings': mappings, 'reference_palette': palette,
        'reference_ramps': [ramp.tolist() for ramp in ramps],
        'tones_per_ramp': tones,
        'maximum_reference_palette_colors': (_HUE_BINS + 1) * tones,
        'maximum_palette_colors': (_HUE_BINS + 1) * tones + retained_count,
        'reference_dictionary_colors': int(len(dictionary)),
        'lightness_floor_tolerance': .02,
        'source_colors_retained_for_brightness_floor': retained_count,
        'range_tone_counts': group_counts,
        'collapsed_source_color_count': int(np.sum(visible_colors) - len(np.unique(targets[visible_colors], axis=0))),
        'ambiguous_source_color_count': int(np.sum(ambiguous & visible_colors)),
        'distant_hue_source_color_count': int(np.sum((hue_error > np.pi / 4) & ~neutral & visible_colors)),
        'geometry_unchanged': True, 'alpha_unchanged': True,
        'monotone_lightness_within_matched_reference_range': True,
        'target_rgb_provenance': 'actual nonzero-alpha reference pixels, or unchanged source RGB if no reference meets brightness floor; no averaged RGB',
        'notes': [
            '24 circular Oklab hue ranges plus near-channel-equal/near-black range; not semantic materials.',
            'RGB dictionary resolution is 8 channel levels; rare occupied cells are not population-pruned.',
            'Correspondence uses hue/chroma, absolute lightness and within-range frequency, without object names or coordinates.',
            'Exact-color frequency influences tones within each range, never deletes an independent occupied range.',
            'Absolute lightness matching with source L minus .02 floor; no rank expansion or midpoint assignment.',
            'Exact source colors already in the selected reference palette remain exact anchors.',
            'Within each matched reference range, a monotone RGB lookup preserves brightness order and exact anchors.',
            'Different source colors can share a target; range_tone_counts exposes collapsed tone steps.',
            'Zero-alpha RGB is preserved; mappings apply only to pixels with nonzero alpha.',
            'Absent reference hues, mixed edge colors and semantic correspondence cannot be guaranteed.',
        ],
    }
    return output, metadata
