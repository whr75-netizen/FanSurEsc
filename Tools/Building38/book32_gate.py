"""N32 actual receiver-cell gate. Fixed thresholds are not fitted after failure."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
LUMA = np.array([.2126729, .7151522, .0721750])
MIN_CELLS = 8
MIN_DELTA_Y_BYTE = 8.0


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'),
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def xyz(v):
    return np.array([v[k] for k in ('x', 'y', 'z')], dtype=float)


def world(points, geometry):
    m = np.array(geometry['localToWorld'], float).reshape(4, 4)
    return points @ m[:3, :3].T + m[:3, 3] + xyz(geometry['offset'])


def maps(folder, geometry):
    shape = (geometry['height'], geometry['width'], 4)
    return tuple(np.fromfile(folder / geometry[k], dtype='<f4').reshape(shape)
        for k in ('positionsFile', 'normalsFile'))


def ray_hits(origins, directions, triangles, segment):
    """Two-sided Moller-Trumbore, world metres; segments use t in (0,1)."""
    lo = triangles.reshape(-1, 3).min(0)
    hi = triangles.reshape(-1, 3).max(0)
    near = np.full(len(origins), -np.inf)
    far = np.full(len(origins), np.inf)
    possible = np.ones(len(origins), bool)
    for axis in range(3):
        nonzero = np.abs(directions[:, axis]) > 1e-12
        possible &= nonzero | ((origins[:, axis] >= lo[axis]) & (origins[:, axis] <= hi[axis]))
        aa = np.full(len(origins), -np.inf)
        bb = np.full(len(origins), np.inf)
        aa[nonzero] = (lo[axis] - origins[nonzero, axis]) / directions[nonzero, axis]
        bb[nonzero] = (hi[axis] - origins[nonzero, axis]) / directions[nonzero, axis]
        near = np.maximum(near, np.minimum(aa, bb))
        far = np.minimum(far, np.maximum(aa, bb))
    upper = 1.0 - 1e-6 if segment else 1000.0
    possible &= (far > 1e-6) & (near < upper) & (near <= far)
    indexes = np.nonzero(possible)[0]
    out = np.zeros(len(origins), bool)
    o, d = origins[indexes], directions[indexes]
    hit = np.zeros(len(indexes), bool)
    for a, b, c in triangles:
        e1, e2 = b-a, c-a
        h = np.cross(d, e2)
        det = h @ e1
        inv = np.divide(1.0, det, out=np.zeros_like(det), where=np.abs(det) > 1e-10)
        s = o-a
        u = np.einsum('ij,ij->i', s, h) * inv
        q = np.cross(s, e1)
        v = np.einsum('ij,ij->i', d, q) * inv
        t = (q @ e2) * inv
        hit |= (np.abs(det) > 1e-10) & (u >= 0) & (v >= 0) & (u+v <= 1) & (t > 1e-6) & (t < upper)
    out[indexes] = hit
    return out


def projected(context, points):
    vp = np.array(context['projection']).reshape(4, 4) @ np.array(context['view']).reshape(4, 4)
    clip = np.c_[points, np.ones(len(points))] @ vp.T
    return np.c_[(clip[:, 0]/clip[:, 3]+1)*context['width']/2,
        (1-clip[:, 1]/clip[:, 3])*context['height']/2]


def receiver(folder):
    context = read(folder/'context.json')
    if context['orthographic'] is not True:
        raise ValueError('N32 fixed orthographic contract required')
    geometry = context['counter']
    p, n = maps(folder, geometry)
    valid = (p[:, :, 3] > .5) & (n[:, :, 1] > .999)
    top = float(p[:, :, 1][valid].max())
    valid &= np.abs(p[:, :, 1]-top) <= 1e-5
    rows, cols = np.nonzero(valid)
    points = world(p[rows, cols, :3], geometry)
    caster = context['caster']
    vertices = world(np.array([xyz(v) for v in caster['vertices']]), caster)
    triangles = vertices[np.array(caster['triangles']).reshape(-1, 3)]
    hidden = ray_hits(points, np.broadcast_to(-xyz(context['cameraForward']), points.shape), triangles, False)
    # Also exclude the actual displayed target cache, not merely its tessellated proxy.
    target_p, _ = maps(folder, context['target'])
    target_valid = target_p[:, :, 3] > .5
    target_world = world(target_p[target_valid, :3], context['target'])
    target_xy = np.rint(projected(context, target_world)).astype(int)
    view = np.array(context['view']).reshape(4, 4)
    target_depth = (np.c_[target_world, np.ones(len(target_world))] @ view.T)[:, 2]
    actual_target = {}
    for key, depth in zip(map(tuple, target_xy), target_depth):
        actual_target[key] = max(depth, actual_target.get(key, -np.inf))
    counter_xy = np.rint(projected(context, points)).astype(int)
    counter_depth = (np.c_[points, np.ones(len(points))] @ view.T)[:, 2]
    hidden |= np.array([actual_target.get(tuple(key), -np.inf) > depth+1e-6
        for key, depth in zip(counter_xy, counter_depth)])
    shadow = np.zeros(len(points), bool)
    by_light = {}
    for lamp in context['lamps']:
        part = ray_hits(points, xyz(lamp['position'])-points, triangles, True)
        by_light[lamp['name']] = int(np.sum(part & ~hidden))
        shadow |= part
    roi = shadow & ~hidden
    xy = projected(context, points)
    # Native centres are on integer screen coordinates. A 2px cell has 2x2 samples.
    if np.max(np.abs(xy-np.rint(xy))) > .001:
        raise ValueError('Native projected centres are not on the preserved screen grid')
    starts = np.rint(xy-1).astype(int)
    roi &= (starts[:, 0] >= 0) & (starts[:, 1] >= 0) & (starts[:, 0]+1 < context['width']) & (starts[:, 1]+1 < context['height'])
    return context, valid.shape, rows, cols, starts, roi, by_light


def components(mask):
    unseen = set(zip(*np.nonzero(mask)))
    largest = []
    while unseen:
        start = unseen.pop()
        points, stack = [start], [start]
        while stack:
            y, x = stack.pop()
            for other in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
                if other in unseen:
                    unseen.remove(other); stack.append(other); points.append(other)
        if len(points) > len(largest):
            largest = points
    return largest


def analyze(folder, on_name, off_name):
    context, shape, rows, cols, starts, roi, lights = receiver(folder)
    on = np.array(Image.open(folder/on_name).convert('RGB'), dtype=float)
    off = np.array(Image.open(folder/off_name).convert('RGB'), dtype=float)
    if on.shape != off.shape or on.shape != (context['height'], context['width'], 3):
        raise ValueError('Actual capture dimensions differ from context')
    selected = np.nonzero(roi)[0]
    if not len(selected):
        raise ValueError('No visible receiving cells in actual ray-shadow footprint')
    delta = np.zeros(len(rows))
    uniform = True
    for i in selected:
        x, y = starts[i]
        a, b = on[y:y+2, x:x+2], off[y:y+2, x:x+2]
        uniform &= bool(np.all(a == a[0, 0]) and np.all(b == b[0, 0]))
        # All four samples must meet brightness loss; no RGB-peak or averaging loophole.
        delta[i] = float(np.min((b-a) @ LUMA))
    qualified = np.zeros(shape, bool)
    qualified[rows[roi & (delta >= MIN_DELTA_Y_BYTE)], cols[roi & (delta >= MIN_DELTA_Y_BYTE)]] = True
    largest = components(qualified)
    xy = starts[selected]
    result = {'visibleReceiverCells': int(roi.sum()), 'rayReceiverCellsByLight': lights,
        'qualifiedCells': int(qualified.sum()), 'largestConnectedCells': len(largest),
        'receiverScreenRect': [int(xy[:, 0].min()), int(xy[:, 1].min()), int(xy[:, 0].max()+2), int(xy[:, 1].max()+2)],
        'deltaYByteMedian': float(np.median(delta[roi])), 'deltaYByteMaximum': float(delta[roi].max()),
        'native2x2Uniform': uniform, 'minimumCells': MIN_CELLS, 'minimumDeltaYByte': MIN_DELTA_Y_BYTE}
    return result


def preserved(output):
    hashes = read(output/'baseline-hashes.json')
    return bool(hashes) and all((ROOT/name).is_file() and
        hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == value for name, value in hashes.items())


def receipt_checks(receipt):
    return {'actualPlay': receipt.get('playMode') is True,
        'geometryWithinPhase': receipt.get('sameGeometry') is True,
        'lightingWithinPhase': receipt.get('sameLighting') is True,
        'sameActualEntities': receipt.get('samePlayer') is True and receipt.get('sameCamera') is True,
        'controlsRestored': receipt.get('controlsRestored') is True,
        'shaderError0': receipt.get('shaderErrors') == 0,
        'integer2px': abs(receipt.get('screenPixelsPerCell', 0)-2) <= 1e-5}


def policy_ranges(context, receipt):
    wanted = []
    for lamp in context['lamps']:
        corners = np.array([xyz(v) for v in lamp['roomCorners']])
        if not len(corners):
            return False
        distance = np.linalg.norm(corners-xyz(lamp['position']), axis=1).max()
        wanted.append(max(3.2, 2*distance))
        if abs(wanted[-1]-lamp['policyRange']) > 1e-4:
            return False
    return bool(wanted) and np.allclose(receipt['directRanges'], wanted, rtol=0, atol=1e-4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--experiment-only', action='store_true')
    args = parser.parse_args()
    output = Path(args.output).resolve()
    experiment = output/'experiment01'
    before = read(experiment/'observation.json')
    ctx = read(experiment/'context.json')
    baseline = analyze(experiment, 'baseline-on.png', 'baseline-off.png')
    policy = analyze(experiment, 'policy-on.png', 'policy-off.png')
    checks = receipt_checks(before)
    checks.update({'sourceHashes': preserved(output),
        'actualBrownTarget': ctx['target']['name'] == 'checkout_produce/Native surface',
        'policyRangeMatchesRoomGeometry': policy_ranges(ctx, before),
        'experimentConnectedReadableShadow': policy['largestConnectedCells'] >= MIN_CELLS,
        'experimentNativeUniform': policy['native2x2Uniform']})
    metrics = {'baseline': baseline, 'policy': policy}
    if not args.experiment_only:
        final = output/'final01'
        after = read(final/'observation.json'); end_ctx = read(final/'context.json')
        actual = analyze(final, 'shadow-on.png', 'shadow-off.png')
        checks.update({'final_'+k: v for k, v in receipt_checks(after).items()})
        checks.update({'sameGeometryAcross': before['geometry'] == after['geometry'],
            'sameLightingOwnerSettings': before['lighting'] == after['lighting'],
            'sameCameraAcross': np.allclose(ctx['view'], end_ctx['view'], rtol=0, atol=1e-5) and
                np.allclose(ctx['projection'], end_ctx['projection'], rtol=0, atol=1e-6) and
                all(abs(before[k]-after[k]) <= 1e-5 for k in ('cameraPitch', 'cameraYaw')),
            'sameCachedPixels': all((experiment/ctx[g][f]).read_bytes() == (final/end_ctx[g][f]).read_bytes()
                for g in ('counter', 'target') for f in ('positionsFile', 'normalsFile')),
            'finalActualBrownTarget': end_ctx['target']['name'] == 'checkout_produce/Native surface',
            'finalRangeMatchesRoomGeometry': policy_ranges(end_ctx, after),
            'finalConnectedReadableShadow': actual['largestConnectedCells'] >= MIN_CELLS,
            'finalNativeUniform': actual['native2x2Uniform'],
            'lampControl': after.get('lampsControlPixels', 0) > 0,
            'movingControl': after.get('movingControlPixels', 0) > 0})
        metrics['final'] = actual
    result = {'passed': all(checks.values()), 'checks': checks, 'metrics': metrics,
        'artApprovalClaimed': False, 'criterion': 'visible counter-top ray-shadow: 4-neighbor native cells >=8, every sample deltaY >=8 byte'}
    path = output/('experiment-validation.json' if args.experiment_only else 'validation32.json')
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
