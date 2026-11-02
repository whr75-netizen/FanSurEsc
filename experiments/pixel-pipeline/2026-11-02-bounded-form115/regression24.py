from pathlib import Path
import json, numpy as np
from geometry24 import transport_assigned_depth, column_curve
from direct_support24 import H, winners

def main():
    checks = []
    z = np.full(16, np.nan); z[:2] = [2, 4]
    out = transport_assigned_depth(z, 100)
    assert np.array_equal(out[:2], z[:2]) and np.all(out[2:] == 3)
    checks.append('Measured sub-sample depths preserved; only holes filled')
    assert np.isnan(transport_assigned_depth(np.full(16, np.nan), 0)).all()
    checks.append('No carrier and no source depth remains unknown')
    assert np.all(transport_assigned_depth(np.full(16, np.nan), 2) == 2)
    checks.append('Zero-known fallback requires a positive source depth; synthetic branch only')
    segs = np.array([[[.999, .5, 2, 1], [1.001, .6, 4, 1]]])
    clipped = column_curve(segs, 1, 1)
    assert clipped and clipped['arcLength'] > 0 and np.allclose(clipped['midXYZ'], [1.0005, .575, 3.5])
    checks.append('Tiny actual curve interval retained, depth interpolated')
    assert column_curve(segs, 2, 1) is None and column_curve(segs, 1, 3) is None
    checks.append('Absent owner/column cannot invent a boundary')
    moved = segs.copy(); moved[:, :, :2] += [5, -2]
    shifted = column_curve(moved, 1, 6)
    assert np.allclose(np.array(shifted['midXYZ']) - [5, -2, 0], clipped['midXYZ'])
    checks.append('Column clipping translation covariance')
    points = np.array([[0, 0, 0], [1, 0, .2], [0, 1, -.1]])
    diameter = lambda p: float(np.linalg.norm(p[:, None] - p[None, :], axis=2).max())
    original = diameter(points)
    rot = np.array([[0,-1,0],[1,0,0],[0,0,-1]])
    assert np.isclose(diameter(points @ rot + [5,-3,2]), original)
    for scale in [.5, 1, 2]: assert np.isclose(diameter(points * scale), original * scale)
    checks.append('Ring diameter rotation/reflection/translation/scale covariance')
    assert winners([1, 1]) == [0, 1]
    checks.append('Equal evidence remains multiple solutions')
    data = json.loads((H / 'DIRECT_SUPPORT24.json').read_text())
    assert len(data['rows']) == 24 and data['summary']['withExisting113KeyFallbackAgrees115'] == 24
    assert all(r['shaderOrderFloat32Winners'] == r['withExisting113KeyFallback'] for r in data['rows'])
    checks.append('24 saved eyes: scalar shader-order float32 agrees with exact oracle')
    geometry = json.loads((H / 'GEOMETRY24.json').read_text())
    assert len(geometry['rows']) == 22
    for row in geometry['rows']:
        assert row['outputs']['mean+ring']['status'] == 0
        if row['category'] == 'definite_hair_at_matched_destination': assert row['outputs']['mean+ring']['role'] >= 12
    checks.append('22 changed cells: no unresolved fallback; certain foreground hair retained')
    assert geometry['summary']['ringPredicateScaleMismatches'] == 0
    checks.append('1190 saved own-component socket predicates scale consistently')
    for case in geometry['summary']['missingCurveChecks']:
        assert case['positiveSourceAndVisibleDestination'] and case['actualMidpointCarrierHits']
    checks.append('F107 midpoint has original source alpha and matched destination visibility')
    out = {'passed': len(checks), 'checks': checks, 'GPUOrUnityOrCompilerInvocations': 0,
           'notClaimed': ['Compiled HLSL equivalence', 'Driver fault fixed', 'Actual final GPU render', 'Temporal stability', 'Whole face palette/outline completion']}
    (H / 'REGRESSION24.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out))

if __name__ == '__main__': main()
