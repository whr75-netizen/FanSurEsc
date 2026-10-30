"""Check saved layouts/PNG independently; no repeated phase generation."""
from pathlib import Path
import hashlib, json, re
import numpy as np
from PIL import Image
from joint43 import Cell, JointPlacement, JointPlacementCache, component_count

R = Path(__file__).resolve().parent
load = lambda p: json.loads(Path(p).read_text(encoding='utf8'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
provenance = load(R / 'CELL_AND_COLOUR_PROVENANCE.json')
cells = [Cell(q['cellId'], q['eye'], q['role'], tuple(q['referenceXY']), tuple(q['rgba8'])) for q in provenance['cells']]
registrations = load(R / 'REGISTRATIONS.json')
checks = []
def check(name, value):
    assert value, name
    checks.append({'name': name, 'pass': True})

cache = JointPlacementCache()
placements = {}
for entry in registrations:
    name = entry['pose']
    adapter = JointPlacement(entry['fingerprint'], entry['stateToken'], cells, entry['referenceAnchor'], entry['jointAnchor'])
    cache.register(adapter); placements[name] = adapter
    base = load(R / f'{name}-placed-cells.json')
    params = load(R.parents[3] / 'final-validation' / name / 'params.json')
    roi = params['roi']; bounds = (roi['x'] - 5, roi['y'] - 4, roi['width'] + 12, roi['height'] + 10)
    small = Image.open(R / f'{name}-template-colour-1x.png').convert('RGBA')
    expected = Image.new('RGBA', (bounds[2] * 2, bounds[3] * 2))
    for q in base:
        c = next(c for c in cells if c.id == q['cellId'])
        check_id = (q['eye'], q['role'], tuple(q['rgba8'])) == (c.eye, c.role, c.rgba)
        assert check_id
        x, y = (q['xy'][0] - bounds[0]) * 2, (q['xy'][1] - bounds[1]) * 2
        for dy in range(2):
            for dx in range(2): expected.putpixel((x + dx, y + dy), c.rgba)
    check(f'{name}: every saved RGBA pixel has exact reference-cell colour/family and outside-alpha0', expected.tobytes() == small.tobytes())
    large = Image.open(R / f'{name}-template-colour-12x.png').convert('RGBA')
    enlarged = small.resize((small.width * 12, small.height * 12), Image.Resampling.NEAREST)
    check(f'{name}: 12x RGBA nearest exact', enlarged.size == large.size and enlarged.tobytes() == large.tobytes())
    reordered = JointPlacement(entry['fingerprint'], entry['stateToken'], list(reversed(cells)), entry['referenceAnchor'], entry['jointAnchor'])
    reverse = reordered.place(entry['fingerprint'], entry['stateToken'], (.5625, .3125))[0]
    forward = adapter.place(entry['fingerprint'], entry['stateToken'], (.5625, .3125))[0]
    by_id = lambda rows: {q['cellId']: q for q in rows}
    check(f'{name}: reference iteration order cannot change placement', by_id(reverse) == by_id(forward))
    # Check serialized output independently of generator's online assertions.
    fixed = np.array([c.xy for c in cells])
    all_layouts = load(R / f'{name}-phase-layouts.json')
    check(f'{name}: all serialized layouts equal source cells plus one common integer translation',
          len(all_layouts) == 65 * 65 and all(np.array_equal(np.array(q['jointCells']) - q['translation'], fixed) for q in all_layouts))
    mask = {c.id: i % 3 != 0 for i, c in enumerate(cells)}
    hidden = adapter.place(entry['fingerprint'], entry['stateToken'], (0, 0), mask)[0]
    check(f'{name}: partial visibility does not generate replacement cells or change hidden intrinsic IDs',
          len(hidden) == len(cells) and all(q['visible'] == mask[q['cellId']] for q in hidden)
          and [q['xy'] for q in hidden] == [q['xy'] for q in base])

# Explicit pose round-trip in one cache, with no "last shape" state.
first, second = registrations[0], registrations[-1]
neutral = cache.place(first['fingerprint'], first['stateToken'])[0]
last = cache.place(second['fingerprint'], second['stateToken'])[0]
returned = cache.place(first['fingerprint'], first['stateToken'])[0]
check('registered pose round-trip chooses its own entry, not previous coordinates',
      neutral == returned and neutral == load(R / 'neutral-placed-cells.json') and last == load(R / 'walk-03-placed-cells.json'))
for state, fingerprint in [('blink50', first['fingerprint']), ('blink100', first['fingerprint']),
                           ('unseen-pose', first['fingerprint']), (first['stateToken'], 'changed-model'),
                           (first['stateToken'], 'changed-style'), (first['stateToken'], 'changed-role-or-colour')]:
    rejected = False
    try: cache.place(fingerprint, state)
    except ValueError: rejected = True
    check(f'unregistered input {state[:10]}/{fingerprint[:14]} rejects stale/open-eye substitution', rejected)

# Rounding convention includes negative ties and simultaneous axes, without per-cell rounding.
test = JointPlacement('test', 'test', cells, [0, 0], [0, 0])
for phase, expected in [((-.5, .5), [0, 1]), ((-.50001, .49999), [-1, 0]), ((1.5, -1.5), [2, -1])]:
    rows, shift, delta = test.place('test', 'test', phase)
    check(f'common snap tie/negative boundary {phase}', shift.tolist() == expected and np.max(np.abs(shift - delta)) <= .50000000001)

residuals = []
for q in registrations:
    values = {}
    for eye in [1, 2]:
        original = np.array(q['originalIrisCentres'][str(eye)])
        reference = np.mean([np.array(c.xy) + .5 for c in cells if c.eye == eye and c.role == 1], axis=0)
        predicted = reference + np.array(q['jointAnchor']) - np.array(q['referenceAnchor'])
        values[eye] = {'sourceCentre': original.tolist(), 'continuousReferenceCentre': predicted.tolist(),
                       'residualXY': (predicted - original).tolist(), 'distanceCells': float(np.linalg.norm(predicted - original))}
    residuals.append({'pose': q['pose'], 'perEyeRegistrationResidual': values,
                      'interpretation': 'Rigid-template mismatch to projected source; not corrected/hidden by independent eye offsets'})

check('all tracked product/template hashes still match initial audit', all(sha(p) == h for p, h in provenance['productSHA256'].items()))
result = {'passed': len(checks), 'checks': checks, 'layoutPlacementsRead': 5 * 65 * 65,
          'actualTemporalFrames': 0, 'UnityCalls': 0, 'productEdits': 0,
          'unsupportedBlinkStatesInvented': 0, 'registrationResiduals': residuals}
(R / 'OUTPUT_VERIFIED.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
page_path = R / 'INDEX.html'; page = page_path.read_text(encoding='utf8')
marker = '<!-- output-verified43 -->'
if marker not in page:
    note = marker + '<section><h2>출력·상태 전환 독립 검사</h2><p><a href="OUTPUT_VERIFIED.json">PNG RGBA·저장 배치·상태 round-trip·등록되지 않은 blink 거부·기준점 잔차</a> · <a href="VISUAL_REVIEW_KO.md">실제 PNG 검수</a></p><p>후보를 다른 pose에 정렬한 연속 기준점 잔차도 숨기지 않고 기록했습니다. 공동 이동만으로 투영 형태 차이를 해결하지는 않습니다.</p></section>'
    page = page.replace('</html>', note + '</html>'); page_path.write_text(page, encoding='utf8')
missing = [f for f in re.findall(r'(?:href|src)="([^"]+)"', page) if ':' not in f and not (R / f).exists()]
assert not missing, missing
manifest = load(R / 'MANIFEST.json')
manifest['missingLinks'] = missing
manifest['outputVerificationChecks'] = len(checks)
manifest['files'] = {p.name: sha(p) for p in R.iterdir() if p.is_file() and p.name != 'MANIFEST.json'}
(R / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
print(json.dumps({'passed': len(checks), 'outputRGBAExact': True, 'storedLayoutsChecked': 5 * 65 * 65,
                  'missingLinks': missing, 'maxRigidReferenceResidualCells': max(e['distanceCells'] for q in residuals for e in q['perEyeRegistrationResidual'].values())}))
