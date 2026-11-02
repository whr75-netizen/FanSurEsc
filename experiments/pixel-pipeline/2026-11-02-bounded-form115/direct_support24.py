"""Argon2.4 direct-support tie-break on immutable113 inputs. CPU only.

Keep all four primary scores. Among their exact minimizers, maximize matching
part mass. This is an explicit fifth preference, not a proof the existing
canvas-relative Hamming reconstruction formula is arithmetically incorrect.
"""
from pathlib import Path
from fractions import Fraction
import hashlib, json, sys
import numpy as np

H = Path(__file__).resolve().parent
def sibling(name):
    for path in [H.parent / name, H.parent / ('2026-11-02-' + name)]:
        if path.exists(): return path
    raise FileNotFoundError(name)

P = sibling('argon23-runtime113'); F = sibling('gpu-form115')
sys.path.insert(0, str(P))
from inputs113 import load_packets, buffer

def direct_mass(masses, points, masks):
    assert len(masses.shape) == 2 and masses.shape[1] == 2
    assert masks[0] & masks[1] == 0
    assert (masks[0] | masks[1]) < (1 << len(points))
    return sum((Fraction(float(masses[cell, part]))
                for part in range(2) for point, cell in enumerate(points)
                if masks[part] & (1 << point)), Fraction(0))

def winners(values):
    assert values
    best = max(values)
    return [i for i, value in enumerate(values) if value == best]

def runtime_float_mass(masses, points, masks):
    partial = []
    for part in range(2):
        value = np.float32(0)
        for point, cell in enumerate(points):
            if masks[part] & (1 << point): value = np.float32(value + masses[cell, part])
        partial.append(value)
    return np.float32(partial[0] + partial[1])

def main():
    reference = json.loads((F / 'REFERENCE115.json').read_text())
    by_frame = {row['frame']: row for row in reference['rows']}
    _, packets = load_packets(P); rows = []; all_integer = True; fractional_examples = []
    for entry, packet in packets:
        meta = json.loads((packet / 'RAW_MANIFEST.json').read_text())
        width = meta['forward102']['canonicalSize'][0] // 4
        height = meta['forward102']['canonicalSize'][1] // 4
        cells = buffer(packet / 'REGION113-cells.f32').reshape(512, 7, 4)
        mass = cells[:, 0, [0, 2]]
        assert np.isfinite(mass).all() and np.all(mass >= 0)
        all_integer = all_integer and bool(np.all(mass == np.rint(mass)))
        if len(fractional_examples) < 4:
            for cell, part in np.argwhere(mass[:width * height] != np.rint(mass[:width * height])):
                fractional_examples.append({'frame': entry['frame'], 'cellYX': list(map(int, divmod(int(cell), width))), 'partIndex': int(part),
                                            'massUnits': float(mass[cell, part]), 'sourceOwner': float(cells[cell, 3, 0]), 'regionPolicy': float(cells[cell, 5, 0])})
                if len(fractional_examples) == 4: break
        raw_best = buffer(packet / 'REGION113-best.f32').reshape(2, 12)
        tags = buffer(packet / 'REGION113-tags.f32').view(np.uint32).reshape(512, 4)
        frame_data = buffer(packet / 'REGION113-frame.f32').view(np.uint32).reshape(2, 32, 4)
        for eye in by_frame[entry['frame']]['eyes']:
            points = [y * width + x for y, x in eye['pointsYX']]
            assert all(0 <= p < width * height for p in points)
            values = [direct_mass(mass, points, pair) for pair in eye['masks']]
            chosen = winners(values)
            active = int(frame_data[eye['owner'] - 1, 2, 2])
            missing = []
            for pair in eye['masks']:
                selected = 0
                for part in range(2):
                    for point, cell in enumerate(points):
                        if pair[part] & (1 << point): selected |= int(tags[cell, part + 2])
                missing.append((active & ~selected).bit_count())
            # This fallback already exists in113 Less113. Keep it explicit:
            # it is a source-key preservation heuristic, not relative geometry.
            compatible = [index for index in chosen if missing[index] == min(missing[i] for i in chosen)]
            float_values = [float(runtime_float_mass(mass, points, pair)) for pair in eye['masks']]
            float_chosen = winners(float_values)
            float_compatible = [index for index in float_chosen if missing[index] == min(missing[i] for i in float_chosen)]
            assert float_compatible == compatible
            # Coordinates do not enter the fifth objective: reflect/rotate the
            # cell plane without changing source identity or masses.
            rotated_mass = np.zeros((width * height, 2), dtype=np.float32)
            rotated_points = []
            for point in points:
                y, x = divmod(point, width); rotated = x * height + (height - 1 - y)
                rotated_mass[rotated] = mass[point]; rotated_points.append(rotated)
            assert [direct_mass(rotated_mass, rotated_points, pair) for pair in eye['masks']] == values
            order = list(reversed(range(len(points))))
            permuted_points = [points[i] for i in order]
            remapped_masks = [[sum(1 << new for new, old in enumerate(order) if mask & (1 << old)) for mask in pair] for pair in eye['masks']]
            assert [direct_mass(mass, permuted_points, pair) for pair in remapped_masks] == values
            gpu = raw_best[eye['owner'] - 1].view(np.uint32)
            rows.append({'frame': entry['frame'], 'sourceId': entry['sourceId'], 'owner': eye['owner'],
                         'primaryPool': len(values), 'masks': eye['masks'], 'directMassExact': [str(x) for x in values],
                         'selectedIndices': chosen, 'sourceForm115Selected': eye['selectedIndices'],
                         'missingObservedSourceKeys': missing, 'withExisting113KeyFallback': compatible,
                         'shaderOrderFloat32DirectMass': float_values, 'shaderOrderFloat32Winners': float_compatible,
                         'agreesWithSourceForm115': chosen == eye['selectedIndices'],
                         'stored113BestMasks': [int(x) for x in gpu[4:8]],
                         'selectedCellsYX': [[{'part': part, 'YX': eye['pointsYX'][point],
                                               'matchingMassUnits': float(mass[cell, part]),
                                               'otherPartMassUnits': float(mass[cell, 1 - part])}
                                              for part in range(2) for point, cell in enumerate(points)
                                              if eye['masks'][index][part] & (1 << point)] for index in chosen]})
    # A minimal analytical check: the old formula is the difference from
    # canvas error, not an isolated cost. Test all small categorical masses.
    for k in [1, 4, 64]:
        for mi in range(k + 1):
            for mw in range(k - mi + 1):
                for selected in [mi, mw]:
                    assert mi + mw + (k - mi - mw - selected) == k - selected
    assert winners([Fraction(1), Fraction(1)]) == [0, 1], 'Do not force arbitrary equal support into a unique answer'
    zero = np.zeros((2, 2), dtype=np.float32)
    assert direct_mass(zero, [0, 1], [1, 2]) == 0
    summary = {'eyes': len(rows), 'oldFourMetricTies': sum(r['primaryPool'] > 1 for r in rows),
               'newTies': sum(len(r['selectedIndices']) > 1 for r in rows),
               'agreesWithSourceForm115': sum(r['agreesWithSourceForm115'] for r in rows),
               'withExisting113KeyFallbackTies': sum(len(r['withExisting113KeyFallback']) > 1 for r in rows),
               'withExisting113KeyFallbackAgrees115': sum(r['withExisting113KeyFallback'] == r['sourceForm115Selected'] for r in rows),
               'serializedMassesIntegralInThisDataset': all_integer,
               'fractionalMassExamples': fractional_examples,
               'GPUOrUnityOrCompilerInvocations': 0, 'productionApplied': False,
               'limitations': ['Only saved113 primary pools tested, no new live visibility or temporal input.',
                               'Direct support is not equivalent to the full six-dimensional relative-geometry objective in general.',
                               'Old reconstruction is a canvas-relative categorical error; cross term alone is not an arithmetic bug.',
                               'No GPU safety or final visual validation is established.']}
    (H / 'DIRECT_SUPPORT24.json').write_text(json.dumps({'summary': summary, 'rows': rows}, indent=2) + '\n')
    print(json.dumps(summary))
    print(json.dumps([{'frame': r['frame'], 'owner': r['owner'], 'mass': r['directMassExact'], 'selected': r['selectedIndices'], 'missingKeys': r['missingObservedSourceKeys'], 'compatible': r['withExisting113KeyFallback']} for r in rows if r['primaryPool'] > 1]))

if __name__ == '__main__': main()
