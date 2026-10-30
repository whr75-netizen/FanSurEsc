"""One frozen-source shared-curve candidate; no RGB/g filtering or runtime calls."""
from pathlib import Path
import sys, json, math, collections, base64, hashlib
import numpy as np
from PIL import Image, ImageDraw

O = Path(__file__).resolve().parent; R = O.parent
sys.path.insert(0, str(R))
import candidate as c
from feature_curves import fit, sample_curves, winding
from geometry_edges import Geometry
from diagnose44 import INPUT, components, load, dump, sha

SPATIAL_BOUND = math.sqrt(.5)
# The guide is reconstructed from one-cell Q edges / selected coarse packets,
# not from a complete native960 isoline. Using the native half-pitch here would
# freeze the coarse staircase. Use this input lattice's half-diagonal bound.
FIT_BOUND = SPATIAL_BOUND


def edge_graph(q, mask, visibility):
    edge_map = {tuple(sorted(e['indices'])): e for e in visibility}
    edges = []; labels_at = collections.defaultdict(set)
    for e in visibility:
        (x, y), (xx, yy) = e['a'], e['b']; low, high = sorted(e['Q'])
        if xx != x:
            a, b = (x + 1, y), (x + 1, y + 1)
            if q[y, x] != low: a, b = b, a
        else:
            a, b = (x, y + 1), (x + 1, y + 1)
            if q[yy, xx] != low: a, b = b, a
        for p in [a, b]: labels_at[p].update([low, high])
        # Source interpolation is allowed only on a measured depth-continuous interval.
        # At an actual visibility jump we retain the coarse midpoint as an unknown
        # spatial reference, never interpolate light between front/back surfaces.
        guide = (np.array(a) + b) / 2
        used_source = False
        if not e['protectedActualVisibility'] and high - low == 1:
            threshold = DATA['thresholds'][high - 1]
            ga, gb = e['g']; t = (threshold - ga) / (gb - ga)
            guide = np.array(e['selectedPoints'][0]) * (1 - t) + np.array(e['selectedPoints'][1]) * t
            used_source = True
        edges.append({'a': a, 'b': b, 'pair': (low, high), 'guide': guide,
                      'sourceInterpolation': used_source, 'evidence': e})
    paths = []; used = set()
    for pair in sorted({e['pair'] for e in edges}):
        group = [i for i, e in enumerate(edges) if e['pair'] == pair]
        outgoing = collections.defaultdict(list); incoming = collections.defaultdict(list)
        for i in group:
            outgoing[edges[i]['a']].append(i); incoming[edges[i]['b']].append(i)
        junction = {p for p in set(outgoing) | set(incoming) if len(outgoing[p]) != 1 or len(incoming[p]) != 1 or len(labels_at[p]) >= 3}
        starts = sorted(group, key=lambda i: (edges[i]['a'] not in junction, edges[i]['a'], edges[i]['b']))
        for start in starts:
            if start in used: continue
            chain = []; i = start
            while i not in used:
                used.add(i); chain.append(i); p = edges[i]['b']
                if p == edges[start]['a'] or p in junction: break
                choices = [j for j in outgoing[p] if j not in used]
                if len(choices) != 1: break
                i = choices[0]
            raw = np.array([edges[chain[0]]['a']] + [edges[j]['b'] for j in chain], float)
            guide = np.vstack([raw[:1], [edges[j]['guide'] for j in chain], raw[-1:]])
            paths.append({'id': len(paths), 'pair': pair, 'raw': raw, 'guide': guide,
                          'edgeIndices': chain, 'closed': np.array_equal(raw[0], raw[-1]),
                          'sourceInterpolatedEdges': sum(edges[j]['sourceInterpolation'] for j in chain),
                          'actualVisibilityEdges': sum(edges[j]['evidence']['protectedActualVisibility'] for j in chain)})
    return paths


def fit_path(path):
    guide = path['guide']; raw = path['raw']
    # Closed reference loops are split at extrema so the fitter's equal endpoints
    # are not passed to the open Schneider solver. No arbitrary corner template.
    if path['closed']:
        indices = sorted({0, len(guide) - 1, *[int(fn(guide[:-1, axis])) for axis in [0, 1] for fn in [np.argmin, np.argmax]]})
    else: indices = [0, len(guide) - 1]
    def certified(points):
        curves = fit(points, FIT_BOUND)
        fitted = sample_curves(curves, .025)
        error = max(float(c.nearest(points, fitted)[0].max()), float(c.nearest(fitted, points)[0].max()))
        if error <= FIT_BOUND + 1e-8 or len(points) <= 2: return curves
        # Schneider's knot-error acceptance does not certify the whole polyline.
        # Subdivide the input, rather than silently loosen the declared error.
        at = len(points) // 2
        return certified(points[:at + 1]) + certified(points[at:])
    curves = []
    for a, b in zip(indices, indices[1:]):
        points = guide[a:b + 1]
        points = points[np.r_[True, np.linalg.norm(np.diff(points, axis=0), axis=1) > 1e-12]]
        if len(points) > 1: curves.extend(certified(points))
    if not curves: return None, [], {'reason': 'degenerate reference'}
    fitted = sample_curves(curves, .025)
    error = max(float(c.nearest(guide, fitted)[0].max()), float(c.nearest(fitted, guide)[0].max()))
    coarse = max(float(c.nearest(raw, fitted)[0].max()), float(c.nearest(fitted, raw)[0].max()))
    # Coarse staircase corners are observations, not source-feature landmarks.
    # Their distance is reported, but not used to freeze every old jagged corner.
    # The source guide fit and the new raster still have explicit spatial bounds.
    if error > FIT_BOUND + 1e-8:
        return None, curves, {'reason': 'fitted source guide exceeds declared bound', 'fitError': error, 'rawError': coarse}
    return fitted, curves, {'fitError': error, 'rawError': coarse}


def grid_path(curve):
    """Regular cell-edge chain from a curve, distinct from fitting/colour mapping."""
    knots = np.floor(curve + .5).astype(int)
    out = [knots[0].copy()]
    for target in knots[1:]:
        while np.any(out[-1] != target):
            current = out[-1]; step = np.sign(target - current)
            options = [current + [int(step[0]), 0]] if step[1] == 0 else [current + [0, int(step[1])]] if step[0] == 0 else [current + [int(step[0]), 0], current + [0, int(step[1])]]
            mid = np.array([(current + p) / 2 for p in options])
            distance = c.nearest(curve, mid)[0]
            chosen = min(range(len(options)), key=lambda i: (round(float(distance[i]), 12), tuple(options[i])))
            nxt = np.asarray(options[chosen])
            if len(out) > 1 and np.array_equal(nxt, out[-2]): out.pop()
            else: out.append(nxt)
    return np.array(out, float)


def span_tangent_error(path, reference):
    """Compare on fixed reference arclength, not an output-edge denominator."""
    runs = []
    for a, b in zip(path[:-1], path[1:]):
        d = b - a
        if np.linalg.norm(d) == 0: continue
        direction = tuple(np.sign(d).astype(int))
        if runs and runs[-1][0] == direction: runs[-1][2] = b
        else: runs.append([direction, a.copy(), b.copy()])
    spans = [(a[1], b[2]) for a, b in zip(runs[:-1], runs[1:])]
    if not spans: spans = [(a[1], a[2]) for a in runs]
    if not spans: return float('inf')
    poly = np.concatenate([np.vstack([a, b, [np.nan, np.nan]]) for a, b in spans])
    delta = np.diff(reference, axis=0); length = np.linalg.norm(delta, axis=1); good = length > 1e-12
    mid = (reference[:-1] + reference[1:])[good] / 2
    tangent = delta[good] / length[good, None]
    _, raster_tangent = c.nearest(poly, mid)
    return float(np.sum(length[good] * (1 - np.sum(tangent * raster_tangent, axis=1) ** 2)) / length[good].sum())


def trace_shared_trial(q, mask, pair, start, end):
    """A constrained fill must still be one shared path, not disconnected edits."""
    low, high = pair; outgoing = collections.defaultdict(list)
    for y, x in np.argwhere(mask):
        for dx, dy in [(1, 0), (0, 1)]:
            xx, yy = x + dx, y + dy
            if xx >= 32 or yy >= 40 or not mask[yy, xx] or sorted([q[y, x], q[yy, xx]]) != [low, high]: continue
            if dx:
                a, b = (int(x + 1), int(y)), (int(x + 1), int(y + 1))
                if q[y, x] != low: a, b = b, a
            else:
                a, b = (int(x), int(y + 1)), (int(x + 1), int(y + 1))
                if q[yy, xx] != low: a, b = b, a
            outgoing[a].append(b)
    start, end = tuple(map(int, start)), tuple(map(int, end)); result = [start]; used = set()
    while True:
        at = result[-1]; options = outgoing[at]
        if len(options) != 1: return None
        nxt = options[0]
        if (at, nxt) in used: return None
        used.add((at, nxt)); result.append(nxt)
        if nxt == end: return np.array(result, float)
        if len(result) > 2000: raise AssertionError('invalid boundary cycle')


def candidate(q, mask, visibility, packets, pool, reverse=False):
    paths = edge_graph(q, mask, visibility)
    if reverse: paths = paths[::-1]
    points = np.c_[np.indices(q.shape)[1].ravel() + .5, np.indices(q.shape)[0].ravel() + .5]
    native = collections.defaultdict(list)
    for p in pool:
        if p['sampleKind'] != 'native960': continue
        native[p['chart']].append(p)
    geometry = Geometry(); witness_cache = {}; rows = []; proposals = []
    def witness(i, new):
        key = (i, new)
        if key in witness_cache: return witness_cache[key]
        source = packets[i]; found = []; x, y = i % 32, i // 32
        for p in native[source['chart']]:
            xy = np.array(p['point'])
            distance_outside = float(np.linalg.norm(np.maximum(np.maximum([x, y] - xy, xy - [x + 1, y + 1]), 0)))
            # A post-quantization boundary can move within its declared spatial
            # corridor. Restricting witnesses to the old cell interior would
            # freeze a boundary merely because a sparse native sample is 0.5px
            # across that cell's edge. Require actual visible same-chart support
            # within the same geometric bound instead of a hard cell bucket.
            if distance_outside > SPATIAL_BOUND: continue
            stage = sum(p['g'] >= t for t in DATA['thresholds'])
            if stage != new: continue
            relation = geometry.envelope(source['point'], p['point'])
            if relation['category'] in ['front/back occlusion', 'projected uncovered hair gap']: continue
            found.append({'point': p['point'], 'g': p['g'], 'Q': stage, 'chart': p['chart'],
                          'primitive': p['primitive'], 'visibility': relation['category'],
                          'distanceOutsideCell': distance_outside})
        witness_cache[key] = found
        return found
    for path in paths:
        fitted, cubics, error = fit_path(path)
        record = {k: v for k, v in path.items() if k not in ['raw', 'guide']}
        record.update({'raw': path['raw'].tolist(), 'guide': path['guide'].tolist(),
                       'fitted': fitted.tolist() if fitted is not None else None,
                       'cubics': [a.tolist() for a in cubics], 'fitMetric': error,
                       'accepted': False})
        if fitted is None: record['reason'] = error['reason']; rows.append(record); continue
        raster = grid_path(fitted)
        record['raster'] = raster.tolist()
        # Existing tiny islands have actual measured g support. This diagnostic
        # does not remove them merely because rounded corners shrink their loop.
        if path['closed'] and len(raster) < 4:
            record['reason'] = 'curve raster cannot represent the measured closed feature'; rows.append(record); continue
        before_tangent = span_tangent_error(path['raw'], fitted)
        after_tangent = span_tangent_error(raster, fitted)
        record['fixedArclengthTangent'] = {'before': before_tangent, 'after': after_tangent}
        distance = max(float(c.nearest(raster, fitted)[0].max()), float(c.nearest(fitted, raster)[0].max()))
        record['rasterCurveHausdorff'] = distance
        if distance > SPATIAL_BOUND + 1e-8:
            record['reason'] = 'raster exceeds spatial bound'; rows.append(record); continue
        if after_tangent > before_tangent + 1e-10:
            record['reason'] = 'raster tangent progression regresses on fixed source arclength'; rows.append(record); continue
        # Each shared path updates the two faces with opposite winding changes.
        change = winding(raster, points) - winding(path['raw'], points)
        changed = np.flatnonzero(change)
        low, high = path['pair']; proposed = []; pins = []; invalid = False
        for i in changed:
            if not mask.flat[i]:
                proposed = []; invalid = True; record['reason'] = 'would alter external domain or silhouette'; break
            a = int(q.flat[i] == low) + int(change[i]); b = int(q.flat[i] == high) - int(change[i])
            if (a, b) not in [(1, 0), (0, 1)] or q.flat[i] not in path['pair']:
                proposed = []; invalid = True; record['reason'] = 'shared-face winding would create gap/overlap or third-label overwrite'; break
            new = low if a else high
            evidence = witness(int(i), new)
            if not evidence:
                pins.append({'index': int(i), 'xy': [int(i % 32), int(i // 32)], 'proposedQ': new,
                             'keptQ': int(q.flat[i]), 'reason': 'no measured visible native stage witness on selected source chart in declared curve corridor'})
                continue
            proposed.append({'index': int(i), 'xy': [int(i % 32), int(i // 32)], 'beforeQ': int(q.flat[i]), 'afterQ': new,
                             'g': float(G.flat[i]), 'sourceChart': packets[i]['chart'], 'sourceWitnesses': evidence})
        record['sourcePins'] = pins
        if proposed and not invalid:
            trial = q.copy()
            for entry in proposed: trial.flat[entry['index']] = entry['afterQ']
            # Do not turn an unchanged, measured shade feature into a new lonely
            # cell by cutting its thin connection. This does not freeze every old
            # component, forbid merging, or impose a minimum area on old islands.
            old_singletons = {tuple(v['cells'][0]) for v in components(q, mask) if v['size'] == 1}
            new_fragments = []
            for group in components(trial, mask):
                if group['size'] != 1: continue
                x, y = group['cells'][0]; i = y * 32 + x
                if (x, y) in old_singletons or trial.flat[i] != q.flat[i]: continue
                evidence = witness(i, int(q.flat[i]))
                if evidence:
                    new_fragments.append({'xy': [x, y], 'Q': int(q.flat[i]), 'sourceG': float(G.flat[i]),
                                          'sourceChart': packets[i]['chart'], 'sourceWitnesses': evidence})
            if new_fragments:
                record['newSourceBackedFragments'] = new_fragments
                proposed = []; record['reason'] = 'cuts a thin connection and creates a new source-supported isolated cell'
                record['proposed'] = proposed; rows.append(record); continue
            constrained = trace_shared_trial(trial, mask, path['pair'], path['raw'][0], path['raw'][-1])
            if constrained is None:
                proposed = []; record['reason'] = 'source-constrained raster creates ambiguous junction or loses the shared path'
            else:
                actual_change = winding(constrained, points) - winding(path['raw'], points)
                expected_change = np.zeros(q.size, int)
                for entry in proposed: expected_change[entry['index']] = 1 if entry['afterQ'] == low else -1
                if not np.array_equal(actual_change, expected_change):
                    proposed = []; record['reason'] = 'raster would split a thin connection or create an extra closed island'
                else:
                    tangent = span_tangent_error(constrained, fitted)
                    distance = max(float(c.nearest(constrained, fitted)[0].max()), float(c.nearest(fitted, constrained)[0].max()))
                    old_distance = max(float(c.nearest(path['raw'], fitted)[0].max()), float(c.nearest(fitted, path['raw'])[0].max()))
                    record['constrainedRaster'] = constrained.tolist()
                    record['constrainedMetrics'] = {'tangent': tangent, 'maxDistance': distance, 'baselineMaxDistance': old_distance}
                    if tangent > before_tangent + 1e-10 or distance > max(SPATIAL_BOUND, old_distance) + 1e-8:
                        proposed = []; record['reason'] = 'source-constrained shared path regresses tangent/spatial fidelity'
        record['proposed'] = proposed
        if not changed.size: record['reason'] = 'curve reconstructed; no output cell crosses this curve'
        elif proposed and not invalid:
            record['accepted'] = True; record['reason'] = 'shared curve and measured same-owner source stage support'; proposals.append(record)
        rows.append(record)
    # Simultaneous commit; reject interacting changes rather than apply in-place.
    touching = collections.defaultdict(list)
    for row in proposals:
        for p in row['proposed']: touching[p['index']].append(row['id'])
    conflict = {i for ids in touching.values() if len(ids) > 1 for i in ids}
    after = q.copy(); changes = []
    for row in rows:
        if row['id'] in conflict:
            row['accepted'] = False; row['reason'] = 'overlapping curve strips need a joint subdivision; not scan-order resolution'
        if row['accepted']:
            for p in row['proposed']:
                after.flat[p['index']] = p['afterQ']; changes.append({**p, 'pathId': row['id']})
    assert np.array_equal(after[~mask], q[~mask])
    return after, sorted(rows, key=lambda p: p['id']), sorted(changes, key=lambda p: p['index'])


def boundary_image(q, mask, paths=None):
    palette = np.array([[52, 57, 67, 255], [86, 112, 150, 255], [194, 157, 93, 255], [231, 229, 216, 255]], np.uint8)
    rgba = np.zeros((40, 32, 4), np.uint8); rgba[mask] = palette[q[mask]]
    im = Image.fromarray(rgba).resize((512, 640), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(im)
    for y, x in np.argwhere(mask):
        for dx, dy in [(1, 0), (0, 1)]:
            xx, yy = x + dx, y + dy
            if xx >= 32 or yy >= 40 or not mask[yy, xx] or q[y, x] == q[yy, xx]: continue
            a, b = ([(x + 1) * 16, y * 16], [(x + 1) * 16, (y + 1) * 16]) if dx else ([x * 16, (y + 1) * 16], [(x + 1) * 16, (y + 1) * 16])
            draw.line([tuple(a), tuple(b)], fill=(12, 15, 22, 255), width=2)
    if paths:
        for row in paths:
            if row['fitted'] is not None:
                draw.line([tuple(np.array(p) * 16) for p in row['fitted']], fill=(70, 250, 180, 255) if row['accepted'] else (130, 160, 190, 180), width=2)
    return im


def main():
    visibility = load(O / 'EDGE_VISIBILITY.json')
    packets = load(R / 'ribbon-path/GEOMETRY_PACKETS.json'); pool = load(R / 'coverage-v3/PACKET_POOL.json')
    after, paths, changes = candidate(Q, MASK, visibility, packets, pool)
    reverse, _, reverse_changes = candidate(Q, MASK, visibility, packets, pool, reverse=True)
    assert np.array_equal(after, reverse) and changes == reverse_changes
    palette = load(INPUT / 'PALETTE_DISTINCT.json'); refs = palette['perReferenceShadePaletteIndices'][23]
    P = np.array([palette['compactPaletteRGB8'][v] for v in refs], np.uint8)
    original = np.frombuffer(base64.b64decode(DATA['originalRGBA']), np.uint8).reshape(80, 64, 4)
    for name, q in [('before', Q), ('corrected', after)]:
        rgba = original.copy()
        labels = np.zeros((40, 32, 4), np.uint8)
        for y, x in np.argwhere(MASK):
            rgba[y * 2:y * 2 + 2, x * 2:x * 2 + 2, :3] = P[q[y, x]]
            labels[y, x] = [*[int(q[y, x]) * 80] * 3, 255]
        Image.fromarray(rgba).save(O / f'{name}-RGB-1x.png')
        Image.fromarray(rgba).resize((512, 640), Image.Resampling.NEAREST).save(O / f'{name}-RGB-8x.png')
        Image.fromarray(labels).save(O / f'{name}-labels-logical.png')
        Image.fromarray(labels).resize((512, 640), Image.Resampling.NEAREST).save(O / f'{name}-labels-8x.png')
        boundary_image(q, MASK).save(O / f'{name}-boundary.png')
        if name == 'corrected': boundary_image(q, MASK, paths).save(O / 'curve-reference-overlay.png')
    for p in changes:
        lo = 0 if p['afterQ'] == 0 else DATA['thresholds'][p['afterQ'] - 1]
        hi = float('inf') if p['afterQ'] == 3 else DATA['thresholds'][p['afterQ']]
        p['addedGIntervalDistance'] = max(lo - p['g'], p['g'] - hi, 0)
        p['beforeRGB8'] = P[p['beforeQ']].tolist(); p['afterRGB8'] = P[p['afterQ']].tolist()
    before_cc, after_cc = components(Q, MASK), components(after, MASK)
    result = {'sourceId': DATA['context']['primarySourceId'], 'frame': DATA['context']['frame'],
              'pathCount': len(paths), 'acceptedPaths': sum(p['accepted'] for p in paths),
              'correctedCells': len(changes), 'beforeQRegions': len(before_cc), 'afterQRegions': len(after_cc),
              'beforeSingletons': sum(p['size'] == 1 for p in before_cc), 'afterSingletons': sum(p['size'] == 1 for p in after_cc),
              'paletteRGB8': P.tolist(), 'changes': changes, 'pathDecisions': collections.Counter(p['reason'] for p in paths),
              'reverseScanExact': True, 'QAndGFrozen': True, 'nativeWitnessRequired': True,
              'scope': 'single frozen flat-albedo frame; joint label-face correction, no product/runtime/temporal claim'}
    np.savez_compressed(O / 'LAYERS.npz', mask=MASK, g=G, Q=Q, correctedQ=after)
    dump('CURVES.json', paths); dump('RESULTS.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'changes'}))


DATA = load(INPUT / 'INPUT.json')
FROZEN = np.load(O / 'FROZEN_INPUT.npz')
MASK, G, Q = FROZEN['mask'], FROZEN['g'], FROZEN['Q']
if __name__ == '__main__': main()
