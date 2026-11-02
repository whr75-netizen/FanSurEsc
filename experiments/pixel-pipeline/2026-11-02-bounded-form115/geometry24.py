"""Argon2.4 geometry proposals against saved113 sources. CPU counterfactual only."""
from pathlib import Path
import json, sys, struct, numpy as np
from direct_support24 import H, P, F, sibling
T = sibling('eye-failures114'); sys.path.insert(0, str(T))
from inputs113 import load_packets, buffer, plane
from trace114 import geometry, read
from geometry114 import mapped, Face114, carriers
from pairing114 import compose
from pigment114 import clip_column

def affiliation():
    for name in ['support-contract112', '2026-11-01-support-contract112', '2026-11-02-eye-support112']:
        path = H.parent / name / 'AFFILIATION_CACHE112.json'
        if path.exists(): return json.loads(path.read_text())
    raise FileNotFoundError('Saved registered ring cache112 required; do not infer a ring from nearest eye')

def ring_limits(ctx, cache):
    offset = cache['captureFaceVertexOffset']; out = {}
    for key, record in cache['rings'].items():
        indices = np.asarray(record['sourceVertices'], int) + offset
        points = ctx['world4'][indices, :3].astype(float)
        diameter = float(np.linalg.norm(points[:, None] - points[None, :], axis=2).max())
        depth = ctx['depth'][indices]
        assert 0 < diameter < 1 and np.isfinite(points).all()
        out[int(key)] = {'diameterWorld': diameter, 'depthRange': [float(depth.min()), float(depth.max())], 'vertices': len(indices)}
    return out

def column_curve(segs, owner, x):
    pieces = []
    for index, (a, b) in enumerate(segs):
        if round(float(a[3])) != owner: continue
        clipped = clip_column(a[:3].astype(float), b[:3].astype(float), x)
        if clipped is None: continue
        aa, bb = clipped; length = float(np.linalg.norm(bb[:2] - aa[:2]))
        if length > 0: pieces.append((index, (aa + bb) * .5, length))
    if not pieces: return None
    length = sum(item[2] for item in pieces)
    mid = sum(item[1] * item[2] for item in pieces) / length
    return {'midXYZ': mid.tolist(), 'arcLength': length, 'segments': [v[0] for v in pieces]}

def transport_assigned_depth(known_depth, selected_source_depth, policy='mean'):
    """Keep measured samples; extend only an already assigned opaque cell.

    Missing source and missing destination geometry stay unknown. Extension is
    explicit stylized-cell transport, not a newly measured native surface.
    """
    z = np.asarray(known_depth, dtype=float).copy(); known = np.isfinite(z)
    assert z.shape == (16,) and np.all(z[known] > 0)
    if known.any(): fill = float(np.mean(z[known]) if policy == 'mean' else np.min(z[known]))
    elif np.isfinite(selected_source_depth) and selected_source_depth > 0: fill = float(selected_source_depth)
    else: return z
    z[~known] = fill
    return z

def main():
    cache = affiliation(); source = read(P / 'SOURCE113.json'); reg = read(T / 'REGISTRATION_CURRENT102.json')
    paired = read(T / 'PAIRING_ALL114.json'); traces = read(T / 'TRACE_ALL114.json')
    changes = json.loads((F / 'DELTA_CLASSIFICATION115.json').read_text())
    wanted = {(r['frame'], tuple(r['mainXYBottomLeft'])): r for r in changes['rows']}
    _, packets = load_packets(P); rows = []; rings = []; curves = []
    for entry, packet in packets:
        frame = entry['frame']; manifest = read(packet / 'RAW_MANIFEST.json'); raw = geometry(packet, manifest)
        trace = next(r for r in traces['frames'] if r['frame'] == frame)
        paired_frame = next(r for r in paired['rows'] if r['frame'] == frame)
        ctx = mapped(raw, reg, np.asarray(trace['carrierOrigin'])); face = Face114(ctx, source['ownSkinMask'])
        limits = ring_limits(ctx, cache); rings.append({'frame': frame, 'sourceId': entry['sourceId'], 'eyes': limits})
        canvas = plane(packet / 'L0-RGBA.plane')[1]; canvasmeta = plane(packet / 'L0-META.plane')[1]
        hairmeta = plane(packet / 'S4-meta.plane')[1]; hairrgba = plane(packet / 'S4-rgba.plane')[1]
        selected = buffer(packet / 'curve-colour.f32').reshape(-1, 4); identities = buffer(packet / 'curve-identity.f32').reshape(-1, 4)
        width = manifest['forward102']['canonicalSize'][0] // 4
        for case in trace['issues']:
            key = (frame, tuple(case['mainXYBottomLeft']))
            if key not in wanted: continue
            row = next(r for r in paired_frame['issues'] if r['mainXY'] == case['mainXYBottomLeft'])
            assert entry['sourceId'] == paired_frame['sourceId'] == wanted[key]['sourceId']
            owner = case['owner']; known_depth = np.array([hs[0]['depth'] if hs else np.nan for hs in row['CPUActualCarriersAt4x']])
            known = np.isfinite(known_depth); points = np.array([v['desiredPhysicalXY'] for v in case['fine']])
            cx, cy = case['canonicalXY']; at = cy * width + cx; zcell = float(identities[at, 2]); assert zcell > 0
            px, py = case['tileXYBottomLeft']; c = canvas[py * 4 + 1, px * 4 + 1]; cm = canvasmeta[py * 4 + 1, px * 4 + 1]
            outputs = {}; details = {}
            for policy in ['mean', 'minimum']:
                z = transport_assigned_depth(known_depth, zcell, policy)
                for depth_policy, limit in [('12mm', .012), ('ring', limits[owner]['diameterWorld'])]:
                    q = face.query(points, z, owner, limit=limit)
                    vis = np.array([r['faceInterval'] for r in q])
                    result = compose(case, vis, z, c, cm, selected[at], case['part'], owner, hairmeta[py*4:py*4+4,px*4:px*4+4], hairrgba[py*4:py*4+4,px*4:px*4+4])
                    name = policy + '+' + depth_policy; outputs[name] = result
                    details[name] = {'faceInterval16': vis.sum(0).tolist(), 'externalOpaqueHits': sum(any(not h['exempt113'] and h['alphaBounds'][0] > 0 for h in r['hits']) for r in q)}
            lo, hi = limits[owner]['depthRange']
            rows.append({'frame': frame, 'sourceId': entry['sourceId'], 'mainXY': case['mainXYBottomLeft'], 'category': wanted[key]['category'],
                         'owner': owner, 'part': case['part'], 'known16': int(known.sum()), 'zCell': zcell, 'ringDepthRange': [lo, hi],
                         'zeroKnownFallbackWithinRingDepthRange': lo <= zcell <= hi if not known.any() else None,
                         'baselinePaired': row['correctPointFinal'], 'outputs': outputs, 'visibility': details,
                         'meanVsMinimumFinalRGBDiffers': outputs['mean+ring']['linearRGBA'] != outputs['minimum+ring']['linearRGBA'],
                         'existingKnownDepthsRetained': True, 'missingDepthIsPolicyTransportNotMeasuredSurface': True})
        # Exact same recorded current curve, not an invented eye size. Test only
        # the known missing F107 cell; a column mean may be off the source path.
        if frame == 107:
            raw_segments = (packet / 'curve-segments106.f32').read_bytes()
            count, stride = struct.unpack_from('<ii', raw_segments)
            assert stride == 32 and len(raw_segments) == 8 + count * stride
            segs = np.frombuffer(raw_segments, offset=8, dtype='<f4').reshape(count, 2, 4)
            for missing in trace['unsupportedSourceLid']:
                cx, cy = missing['canonicalXY']; owner = missing['owner']; curve = column_curve(segs, owner, cx)
                assert curve is not None
                curve_ctx = mapped(raw, reg, np.asarray(trace['sourceOrigin']))
                hitlist = carriers(curve_ctx, owner, 3, np.array([curve['midXYZ'][:2]]))[0]
                hits = []
                for hit in hitlist:
                    world = np.r_[hit['world'], 1]; view = ctx['view'] @ world; clip = ctx['projection'] @ view
                    xy = [(clip[0]/clip[3]*.5+.5)*480, (.5-clip[1]/clip[3]*.5)*272]
                    q = face.query([xy], [hit['depth']], owner, limit=limits[owner]['diameterWorld'])[0]
                    destination_xy = np.asarray(trace['sourceOrigin']) + np.asarray(curve['midXYZ'][:2])
                    destination_query = face.query([destination_xy], [curve['midXYZ'][2]], owner, limit=limits[owner]['diameterWorld'])[0]
                    alpha = face.alpha.bounds(hit['material'], [hit['UV']])[0]
                    hits.append({'primitive': hit['primitive'], 'UV': hit['UV'], 'depth': hit['depth'], 'depthMinusCurveMean': hit['depth']-curve['midXYZ'][2], 'alphaBounds': alpha.tolist(),
                                 'sourcePhysicalXY': xy, 'sourceVisibility': q['faceInterval'], 'destinationPhysicalXY': destination_xy.tolist(),
                                 'sourceDestinationDistancePixels': float(np.linalg.norm(destination_xy-xy)), 'destinationVisibilityAtCurveDepth': destination_query['faceInterval']})
                curves.append({'frame': frame, 'canonicalXY': [cx, cy], 'owner': owner, 'column': curve, 'actualMidpointCarrierHits': hits,
                               'positiveSourceAndVisibleDestination': any(h['alphaBounds'][0] > 0 and h['destinationVisibilityAtCurveDepth'][0] > 0 for h in hits),
                               'linearMeanDepthIsNotAutomaticallyMeasuredCarrier': True})
    lookup = {r['frame']: r['eyes'] for r in rings}; scale_checks = []
    for q in paired['scaleHitRecords']:
        if not q['unilateralRingComponent']: continue
        # Analytic unit/geometry scaling of the explicit socket predicate.
        d = lookup[q['frame']][q['eye']]['diameterWorld']; gap = q['depthGapMetres']
        results = [gap * s <= d * s for s in [.5, 1, 2]]
        assert results[0] == results[1] == results[2]
        scale_checks.append(results)
    assert len(rows) == 22
    summary = {'changedCoordinateCases': len(rows), 'meanVsMinimumRGBDisagreements': sum(r['meanVsMinimumFinalRGBDiffers'] for r in rows),
               'afterTransportRingStatusCounts': {str(k): sum(r['outputs']['mean+ring']['status']==k for r in rows) for k in sorted({r['outputs']['mean+ring']['status'] for r in rows})},
               'zeroKnownCases': sum(r['known16']==0 for r in rows),
               'zeroKnownOutsideRingDepthRange': sum(r['zeroKnownFallbackWithinRingDepthRange'] is False for r in rows),
               'ringPredicateScaleChecks': len(scale_checks), 'ringPredicateScaleMismatches': 0,
               'missingCurveChecks': curves, 'GPUOrUnityOrCompilerInvocations': 0, 'runtimeApplied': False,
               'scope': '22 saved changed-coordinate CPU counterfactuals, not a full render or driver safety validation; depth extension is an explicit style policy, not extra measured geometry.'}
    (H / 'GEOMETRY24.json').write_text(json.dumps({'summary': summary, 'ringMeasurements': rings, 'rows': rows}, indent=2) + '\n')
    print(json.dumps(summary))

if __name__ == '__main__': main()
