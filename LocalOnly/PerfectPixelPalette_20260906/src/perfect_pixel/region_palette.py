"""Experimental region-locked palette transfer, not a semantic style model.

Regions and pixel positions are immutable. A whole source region selects one
reference hue family; individual highlight pixels cannot choose another family.
All emitted RGB values are actual reference pixels or actual source pixels.
Feature averages are used for matching only, never as output colors.
"""
import numpy as np

from .palette import rgb_to_oklab


_MAX_PIXELS = 16_000_000
_MAX_REGIONS = 4096


def _validate(image, name):
    if (not isinstance(image, np.ndarray) or image.dtype != np.uint8 or
            image.ndim != 3 or image.shape[2] not in (3, 4) or
            min(image.shape[:2]) < 1):
        raise ValueError(name + ' must be nonempty uint8 RGB/RGBA')
    if image.shape[0] * image.shape[1] > _MAX_PIXELS:
        raise ValueError(name + ' exceeds 16 megapixels')


def _features(rgb):
    lab = rgb_to_oklab(rgb.astype(np.float32) / 255)
    chroma = np.linalg.norm(lab[..., 1:], axis=-1)
    hue = np.arctan2(lab[..., 2], lab[..., 1])
    return lab, chroma, hue


def _weighted_median(values, weights):
    order = np.argsort(values, kind='stable')
    index = np.searchsorted(np.cumsum(weights[order]), weights.sum() / 2)
    return float(values[order[min(index, len(order) - 1)]])


def _tone_ramp(colors, weights, tones, adaptive=False):
    """At most tones actual representatives; distinct seeds keep rare extrema."""
    lab, _, _ = _features(colors)
    values = lab[:, 0]
    distinct = np.unique(values)
    if adaptive:
        # SLIC regions are geometric pieces, not independent materials. Minor
        # within-piece noise must not expand to a full three-tone reference ramp.
        # True rare high-contrast extrema still count: use actual span, not a
        # population quantile which would delete a one-pixel bright highlight.
        span = float(values.max() - values.min())
        budget = 1 if span < .065 else (2 if span < .16 else 3)
        tones = min(tones, budget)
    centers = distinct[np.rint(np.linspace(0, len(distinct) - 1,
                                          min(tones, len(distinct)))).astype(int)]
    for _ in range(12):
        assigned = np.argmin(abs(values[:, None] - centers), axis=1)
        updated = np.array([_weighted_median(values[assigned == k], weights[assigned == k])
                            if np.any(assigned == k) else centers[k]
                            for k in range(len(centers))])
        updated = np.unique(updated)
        if len(updated) == len(centers) and np.max(abs(updated - centers)) < 1e-7:
            break
        centers = updated
    assigned = np.argmin(abs(values[:, None] - centers), axis=1)
    chosen = []
    for k in range(len(centers)):
        members = np.flatnonzero(assigned == k)
        if not len(members):
            continue
        # Actual medoid close to the tone's central Lab, frequency tie preference.
        center = np.array([_weighted_median(lab[members, j], weights[members]) for j in range(3)])
        score = np.sum((lab[members] - center) ** 2, axis=1)
        score -= 1e-5 * weights[members] / weights[members].max()
        chosen.append(int(members[np.argmin(score)]))
    chosen.sort(key=lambda i: float(values[i]))
    ramp = colors[chosen].copy()
    # L-only tone selection is confined to an already supplied spatial region.
    selected = np.argmin(abs(values[:, None] - values[chosen]), axis=1).astype(np.int32)
    return ramp, selected


def _reference_families(reference, tones):
    flat = reference.reshape(-1, reference.shape[2])
    visible = flat[:, :3] if flat.shape[1] == 3 else flat[flat[:, 3] > 0, :3]
    if not len(visible):
        raise ValueError('reference has no visible pixels')
    colors, weights = np.unique(visible, return_counts=True, axis=0)
    lab, chroma, hue = _features(colors)
    # Bounded 30-degree families, with chromatic pale colors kept distinct from
    # saturated colors and channel-equal colors. This is NOT material recognition.
    hue_id = np.floor((hue % (2 * np.pi)) / (np.pi / 6)).astype(int)
    neutral = (np.ptp(colors.astype(np.int16), axis=1) <= 6) | (lab[:, 0] < .20)
    pale = (lab[:, 0] >= .72) & (chroma <= .075) & ~neutral
    family_id = hue_id + 12 * pale.astype(int)
    family_id[neutral] = 24
    families = []
    for value in np.unique(family_id):
        members = family_id == value
        ramp, _ = _tone_ramp(colors[members], weights[members], tones)
        mean = np.average(lab[members], weights=weights[members], axis=0)
        families.append({'id': int(value), 'ramp': ramp, 'mean': mean,
                         'neutral': bool(value == 24), 'pale': bool(12 <= value < 24)})
    return families, set(map(tuple, colors))


def _family_score(mean, family):
    c = float(np.linalg.norm(mean[1:]))
    target = family['mean']
    tc = float(np.linalg.norm(target[1:]))
    h = float(np.arctan2(mean[2], mean[1]))
    th = float(np.arctan2(target[2], target[1]))
    angle = abs((h - th + np.pi) % (2 * np.pi) - np.pi)
    neutral = c < .018 or mean[0] < .20
    pale = mean[0] >= .72 and c <= .075 and not neutral
    cost = 5 * (angle / (np.pi / 3)) ** 2 * min(c, tc, .04) / .04
    cost += 2 * np.log((c + .02) / (tc + .02)) ** 2
    cost += float((mean[0] - target[0]) ** 2)
    cost += 20 * (neutral != family['neutral'])
    cost += 8 * (pale != family['pale']) if not neutral else 0
    return float(cost)


def color_regions(image, labels, reference, tones=3, *, min_retained_tone_delta_l=.025):
    """Color immutable region/tone nodes using a palette fixed BEFORE ICM.

    The candidate bank is reference representatives plus at most ``tones`` actual
    source representatives per GLOBAL source family. It never grows to restore
    an individual region. Infeasible protected edges are reported, not concealed
    with thousands of photograph colors. Labels -1/alpha-zero remain unchanged.
    """
    _validate(image, 'image')
    _validate(reference, 'reference')
    if (not isinstance(labels, np.ndarray) or labels.shape != image.shape[:2] or
            labels.dtype.kind not in 'iu' or np.any(labels < -1)):
        raise ValueError('labels must be an integer HxW array with values >= -1')
    if isinstance(tones, (bool, np.bool_)) or not isinstance(tones, (int, np.integer)) or not 1 <= tones <= 3:
        raise ValueError('tones must be an integer in [1,3]')
    tones = int(tones)
    if (isinstance(min_retained_tone_delta_l, (bool, str)) or
            not np.isscalar(min_retained_tone_delta_l) or
            not np.isfinite(min_retained_tone_delta_l) or
            not 0 <= min_retained_tone_delta_l <= 1):
        raise ValueError('min_retained_tone_delta_l must be a finite number in [0,1]')
    min_retained_tone_delta_l = float(min_retained_tone_delta_l)
    valid = labels >= 0
    if image.shape[2] == 4:
        valid = valid & (image[..., 3] > 0)
    ids = np.unique(labels[valid])
    if len(ids) > _MAX_REGIONS:
        raise ValueError('more than 4096 regions exceeds the processing bound')
    families, _ = _reference_families(reference, tones)
    output = image.copy()
    source_rgb = image[..., :3]
    source_lab = rgb_to_oklab(source_rgb.astype(np.float32) / 255)
    valid_indices = np.flatnonzero(valid)
    source_families = (_reference_families(source_rgb[valid].reshape(1, -1, 3), tones)[0]
                       if len(valid_indices) else [])
    reference_bank = np.unique(np.concatenate([f['ramp'] for f in families]), axis=0)
    source_bank = (np.concatenate([f['ramp'] for f in source_families])
                   if source_families else np.empty((0, 3), np.uint8))
    bank = np.unique(np.concatenate([reference_bank, source_bank]), axis=0)
    reference_set = set(map(tuple, reference_bank))
    is_reference = np.array([tuple(rgb) in reference_set for rgb in bank])
    blab, bc, bh = _features(bank)
    bank_neutral = (np.ptp(bank.astype(np.int16), axis=1) <= 6) | (blab[:, 0] < .20)
    # One global palette per source family, not one palette per SLIC fragment.
    # Hue and chroma matching remains continuous; hard bins only bound the bank.
    shifts = {}
    for family in source_families:
        mean = family['mean']
        c = np.linalg.norm(mean[1:])
        h = np.arctan2(mean[2], mean[1])
        angle = abs((bh - h + np.pi) % (2 * np.pi) - np.pi)
        eligible = is_reference & ~bank_neutral & (angle <= np.pi / 6) & (bc <= max(.075, c * 1.3))
        if family['pale'] and np.any(eligible):
            source_high = float(_features(family['ramp'])[0][-1, 0])
            shift = float(np.clip(blab[eligible, 0].max() - source_high, 0, .15))
        else:
            shift = 0.0
        shifts[family['id']] = shift
    regions, prepared, node_rgb, node_costs = {}, {}, [], []
    node_regions = []
    node_map = np.full(labels.shape, -1, np.int32)
    order = np.argsort(labels.ravel()[valid_indices], kind='stable')
    sorted_indices = valid_indices[order]
    _, region_counts = np.unique(labels.ravel()[sorted_indices], return_counts=True)
    begin = 0
    for identifier, pixel_count in zip(ids, region_counts):
        indices = sorted_indices[begin:begin + pixel_count]
        begin += pixel_count
        rgb, inverse, counts = np.unique(source_rgb.reshape(-1, 3)[indices], axis=0, return_inverse=True, return_counts=True)
        lab, _, _ = _features(rgb)
        mean = np.average(lab, weights=counts, axis=0)
        ramp, color_tones = _tone_ramp(rgb, counts, tones, adaptive=True)
        local_tones = color_tones[inverse]
        ranked = sorted(source_families, key=lambda f: (_family_score(mean, f), f['id']))
        family = ranked[0]
        offset = len(node_rgb)
        node_map.ravel()[indices] = local_tones + offset
        rc = float(np.linalg.norm(mean[1:]))
        rh = float(np.arctan2(mean[2], mean[1]))
        region_angle = abs((bh - rh + np.pi) % (2 * np.pi) - np.pi)
        source_is_neutral = rc < .018 or mean[0] < .20
        pale = mean[0] >= .72 and rc <= .075 and not source_is_neutral
        source_global_allowed = np.array([tuple(color) in set(map(tuple, family['ramp'])) for color in bank])
        allowed = (bank_neutral == source_is_neutral)
        if not source_is_neutral:
            allowed &= region_angle <= np.pi / 6
        if pale:
            allowed &= bc <= max(.075, rc * 1.3)
        # Source-bank alternatives are confined to this global family. If no
        # reference family exists, this still cannot enlarge the fixed bank.
        allowed &= is_reference | source_global_allowed
        if not np.any(allowed):
            allowed = source_global_allowed
        for color in ramp:
            nl, nc, _ = _features(color[None])
            desired_l = float(nl[0, 0] + shifts[family['id']])
            cost = ((blab[:, 0] - desired_l) / .075) ** 2
            cost += .8 * ((bc - float(nc[0])) / .04) ** 2
            cost += 2 * (region_angle / (np.pi / 6)) ** 2 * min(rc / .04, 1)
            cost += .65 * ~is_reference
            cost[~allowed] = np.inf
            if nl[0, 0] <= .23 and nc[0] <= .075:
                dark = allowed & (blab[:, 0] <= .27) & (bc <= .075)
                if np.any(dark):
                    cost[~dark] = np.inf
            # Only a flat region matching an actual selected reference
            # representative is an anchor; incidental screenshot RGBs are not.
            if len(rgb) == 1 and tuple(color) in reference_set:
                cost[:] = np.inf
                cost[np.all(bank == color, axis=1)] = 0
            node_rgb.append(color)
            node_costs.append(cost)
            node_regions.append(int(identifier))
        prepared[int(identifier)] = (indices, local_tones, offset)
        regions[int(identifier)] = {'region_id': int(identifier), 'pixel_count': int(len(indices)),
            'reference_family': family['id'], 'source_ramp': ramp.tolist(),
            'shared_family_lightness_shift': shifts[family['id']],
            'source_tone_count': len(ramp), 'exact_flat_anchor': len(rgb) == 1 and tuple(ramp[0]) in reference_set}

    # Strong source edges connect immutable tone nodes. Aggregate source
    # lightness with a consistent node-ID orientation to retain brightness order.
    edge_values = {}
    for first, second in ((np.s_[:, :-1], np.s_[:, 1:]), (np.s_[:-1, :], np.s_[1:, :])):
        a, b = node_map[first], node_map[second]
        mask = (a >= 0) & (b >= 0) & (a != b)
        if not np.any(mask):
            continue
        pairs = np.sort(np.stack((a[mask], b[mask]), axis=1), axis=1)
        delta = source_lab[second][mask] - source_lab[first][mask]
        signed_l = delta[:, 0] * np.where(a[mask] < b[mask], 1, -1)
        distance = np.linalg.norm(delta, axis=1)
        unique, inverse, counts = np.unique(pairs, axis=0, return_inverse=True, return_counts=True)
        sorted_edges = np.argsort(inverse, kind='stable')
        begin = 0
        for pair, count in zip(unique, counts):
            subset = sorted_edges[begin:begin + count]
            begin += count
            data = edge_values.setdefault(tuple(map(int, pair)), ([], []))
            data[0].extend(distance[subset].tolist())
            data[1].extend(signed_l[subset].tolist())
    edges = []
    for (a, b), (distances, lightness) in edge_values.items():
        distance, signed_l = float(np.median(distances)), float(np.median(lightness))
        if distance >= .05:
            edges.append((a, b, min(.025, distance * .45),
                          float(np.sign(signed_l)) if abs(signed_l) >= .025 else 0.0,
                          min(.015, abs(signed_l) * .25)))
    # A gradual original gradient can have tiny per-pixel changes while its
    # selected dark/light roles differ strongly. Preserve those roles as an
    # explicit within-region graph relation, not just observed boundary edges.
    edge_indices = {(edge[0], edge[1]): i for i, edge in enumerate(edges)}
    within_region_constraints = 0
    mergeable_weak_tone_pairs = 0
    node_lab = (_features(np.asarray(node_rgb, dtype=np.uint8))[0]
                if node_rgb else np.empty((0, 3)))
    for identifier, (_, _, offset) in prepared.items():
        count = regions[identifier]['source_tone_count']
        for a in range(offset, offset + count - 1):
            b = a + 1
            delta_l = float(node_lab[b, 0] - node_lab[a, 0])
            # A design setting, not a universal image-independent threshold.
            # Weak shading may share one color; real observed strong boundaries
            # remain in the preceding graph, independent of this setting.
            if delta_l < min_retained_tone_delta_l:
                mergeable_weak_tone_pairs += 1
                continue
            minimum = min(.025, delta_l * .45)
            relation = (a, b, minimum, 1.0, min(.015, delta_l * .25))
            if (a, b) in edge_indices:
                existing = edge_indices[(a, b)]
                previous = edges[existing]
                edges[existing] = (a, b, max(previous[2], minimum), 1.0,
                                   max(previous[4], relation[4]))
            else:
                edge_indices[(a, b)] = len(edges)
                edges.append(relation)
            within_region_constraints += 1
    costs = np.array(node_costs, dtype=float).reshape(len(node_rgb), len(bank))
    choice = np.argmin(costs, axis=1) if len(node_rgb) else np.empty(0, np.int32)
    initial_choice = choice.copy()
    neighbours = [[] for _ in node_rgb]
    for edge in edges:
        a, b = edge[:2]
        neighbours[a].append((b, edge[2], edge[3], edge[4]))
        neighbours[b].append((a, edge[2], -edge[3], edge[4]))

    def penalties(node, candidate_ids):
        penalties = np.zeros(len(candidate_ids))
        for other, gap, sign, lgap in neighbours[node]:
            distance = np.linalg.norm(blab[candidate_ids] - blab[choice[other]], axis=1)
            penalties += 30 * np.maximum(0, (gap - distance) / gap)
            if sign:
                directed = (blab[choice[other], 0] - blab[candidate_ids, 0]) * sign
                penalties += 45 * np.maximum(0, (lgap - directed) / max(lgap, .005))
        return penalties

    # Bounded coordinate descent: one node changes at a time, and only when its
    # local (therefore global) energy decreases. Neither graph nor bank expands.
    updates = 0
    passes = 0
    for _ in range(5):
        changed = False
        passes += 1
        for node in range(len(node_rgb)):
            if not neighbours[node]:
                continue
            candidates = np.flatnonzero(np.isfinite(costs[node]))
            energy = costs[node, candidates] + penalties(node, candidates)
            best = int(candidates[np.argmin(energy)])
            current_energy = float(costs[node, choice[node]] + penalties(node, np.array([choice[node]]))[0])
            if float(energy.min()) < current_energy - 1e-9:
                choice[node] = best
                updates += 1
                changed = True
        if not changed:
            break
    unresolved = []
    for a, b, gap, sign, lgap in edges:
        distance = float(np.linalg.norm(blab[choice[a]] - blab[choice[b]]))
        directed = float((blab[choice[b], 0] - blab[choice[a], 0]) * sign)
        if distance < gap - 1e-6 or (sign and directed < lgap - 1e-6):
            unresolved.append({'nodes': [a, b], 'regions': [node_regions[a], node_regions[b]],
                               'contrast': distance, 'minimum_contrast': gap,
                               'lightness_order_preserved': not sign or directed >= lgap - 1e-6})
    for identifier, (indices, local_tones, offset) in prepared.items():
        count = regions[identifier]['source_tone_count']
        selected = choice[offset:offset + count]
        target = bank[selected]
        output.reshape(-1, output.shape[2])[indices, :3] = target[local_tones]
        uses_source = bool(np.any(~is_reference[selected]))
        regions[identifier].update({'target_ramp': target.tolist(),
            'target_tone_count': len(np.unique(target, axis=0)),
            'fallback_reason': 'fixed_global_source_family' if uses_source else None,
            'uses_global_source_fallback': uses_source})
    tone_labels = np.full(labels.shape, -1, np.int32)
    if np.any(valid):
        palette, indices = np.unique(output[..., :3][valid], axis=0, return_inverse=True)
        tone_labels[valid] = indices.astype(np.int32)
    else:
        palette = np.empty((0, 3), np.uint8)
    changed_regions = sorted({node_regions[n] for n in range(len(choice)) if choice[n] != initial_choice[n]})
    metadata = {'method': 'custom-fixed-palette-region-icm-heuristic/3',
        'semantic_matching': False, 'region_labels_changed': False,
        'pixel_positions_changed': False, 'alpha_unchanged': True,
        'global_same_rgb_lookup': False, 'tones_per_region': tones,
        'reference_family_tone_limit': tones, 'region_count': len(regions),
        'tone_budget_lightness_spans': {'one_tone_below': .065, 'two_tones_below': .16},
        'absolute_family_lightness_shifts': {str(k): v for k, v in shifts.items()},
        'protected_boundary_minimum_oklab_distance': .05,
        'regions': list(regions.values()), 'protected_boundary_count': len(edges),
        'boundary_fallback_regions': [], 'boundary_reassigned_regions': changed_regions,
        'unresolved_quantized_boundary_pairs': [u['regions'] for u in unresolved],
        'unresolved_protected_edges': unresolved,
        'icm_passes': passes, 'icm_node_updates': updates,
        'within_region_tone_order_constraints': within_region_constraints,
        'min_retained_tone_delta_l': min_retained_tone_delta_l,
        'mergeable_weak_tone_pairs': mergeable_weak_tone_pairs,
        'candidate_palette_fixed_before_optimization': True,
        'candidate_palette': bank.tolist(), 'candidate_palette_count': len(bank),
        'reference_palette': reference_bank.tolist(),
        'source_families': [{'id': f['id'], 'ramp': f['ramp'].tolist()} for f in source_families],
        'source_palette_limit': 25 * tones, 'total_palette_limit': 50 * tones,
        'region_original_color_restoration': False,
        'reference_families': [{'id': f['id'], 'ramp': f['ramp'].tolist()} for f in families],
        'rgb_provenance': 'fixed actual reference representatives or global source-family representatives',
        'limitations': ['Color families are not semantic material IDs.',
                       'Input segmentation errors cannot be repaired by recoloring.',
                       'A fixed limited palette can leave protected edges infeasible; no local original-color restoration is allowed.',
                       'ICM is bounded local optimization, not a guarantee of a global optimum.']}
    return output, tone_labels, palette, metadata
