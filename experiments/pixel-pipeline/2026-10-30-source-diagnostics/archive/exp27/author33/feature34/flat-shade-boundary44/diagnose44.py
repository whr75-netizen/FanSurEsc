"""Frozen flat-albedo Q diagnosis. CPU saved-geometry reads only."""
from pathlib import Path
import sys, json, hashlib, collections
import numpy as np

O = Path(__file__).resolve().parent
R = O.parent
sys.path.insert(0, str(R))
import candidate as c
from geometry_edges import Geometry

INPUT = Path('C:/Users/15352/Documents/Codex/2026-10-30/task/flat-albedo-control')
load = lambda p: json.loads(Path(p).read_text(encoding='utf8'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
dump = lambda name, obj: (O / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf8')


def components(labels, mask):
    rows = []
    for q in sorted(np.unique(labels[mask])):
        _, groups = c.binary_components(mask & (labels == q))
        for group in groups:
            rows.append({'Q': int(q), 'size': len(group), 'cells': [list(v) for v in group]})
    return rows


def main():
    data = load(INPUT / 'INPUT.json')
    packets_path = R / 'ribbon-path/GEOMETRY_PACKETS.json'
    assert sha(packets_path) == data['context']['packetSHA256']
    packets = load(packets_path)
    mask = np.array([q is not None for q in data['cells']]).reshape(40, 32)
    g = np.array([q['g'] if q else 0 for q in data['cells']]).reshape(40, 32)
    q = np.sum(g[..., None] >= data['thresholds'], -1); q[~mask] = -1
    assert all(p is None or (p['g'] == a['g'] and p['chart'] == a['chart'] and p['primitive'] == a['primitive']) for p, a in zip(packets, data['cells']))
    G = Geometry()
    edges = []; by_edge = {}
    for y, x in np.argwhere(mask):
        for dx, dy in [(1, 0), (0, 1)]:
            xx, yy = int(x + dx), int(y + dy)
            if xx >= 32 or yy >= 40 or not mask[yy, xx]: continue
            if q[y, x] == q[yy, xx]: continue
            i, j = int(y * 32 + x), yy * 32 + xx
            p, r = packets[i], packets[j]
            env = G.envelope(p['point'], r['point'])
            row = {'a': [int(x), int(y)], 'b': [xx, yy], 'indices': [i, j],
                   'Q': [int(q[y, x]), int(q[yy, xx])], 'g': [float(g[y, x]), float(g[yy, xx])],
                   'charts': [p['chart'], r['chart']], 'sampleKinds': [p['sampleKind'], r['sampleKind']],
                   'selectedPoints': [p['point'], r['point']], 'geometry': env,
                   'protectedActualVisibility': env['category'] in ['front/back occlusion', 'projected uncovered hair gap']}
            edges.append(row); by_edge[tuple(sorted((i, j)))] = row
    source_diag = load(INPUT / 'SHADE_FRAGMENTATION.json')
    singletons = []
    for s in source_diag['QSingletonEvidence']:
        i = s['index']; around = [e for key, e in by_edge.items() if i in key]
        prior = next(a for a in source_diag['priorCentreSamplingAudit']['singletonRows'] if a['index'] == i)
        singletons.append({**s, 'QArithmeticCorrect': int(sum(s['g'] >= t for t in data['thresholds'])) == s['Q'],
                           'selectedGeometryNeighbours': around, 'priorCentreSampling': prior,
                           'diagnosis': {'sourceAlbedoCause': False, 'paletteCause': False,
                                         'measuredGStraddlesThreshold': True,
                                         'actualVisibilityEdges': sum(e['protectedActualVisibility'] for e in around),
                                         'sameChartEdges': sum(e['charts'][0] == e['charts'][1] for e in around),
                                         'comment': 'Q is arithmetically correct. Visibility, continuous g and sample selection contributions remain separate; a singleton is not automatically noise.'}})
    np.savez_compressed(O / 'FROZEN_INPUT.npz', mask=mask, g=g, Q=q)
    dump('EDGE_VISIBILITY.json', edges)
    dump('SINGLETON_CAUSES.json', singletons)
    dump('SOURCE_BINDING.json', {'context': data['context'], 'inputSHA256': sha(INPUT / 'INPUT.json'),
                                'paletteSHA256': sha(INPUT / 'PALETTE_DISTINCT.json'),
                                'packetsSHA256': sha(packets_path), 'initialComponents': components(q, mask),
                                'initialQ': q.reshape(-1).tolist(), 'newUnityCalls': 0})
    print(json.dumps({'hair': int(mask.sum()), 'QRegions': len(components(q, mask)),
                      'QSingletons': sum(r['size'] == 1 for r in components(q, mask)),
                      'differentQEdges': len(edges), 'visibilityCategories': collections.Counter(e['geometry']['category'] for e in edges),
                      'sixSingletons': [{'xy': s['cell'], 'actualVisibilityEdges': s['diagnosis']['actualVisibilityEdges'],
                                         'sameChartEdges': s['diagnosis']['sameChartEdges']} for s in singletons]}))


if __name__ == '__main__': main()
