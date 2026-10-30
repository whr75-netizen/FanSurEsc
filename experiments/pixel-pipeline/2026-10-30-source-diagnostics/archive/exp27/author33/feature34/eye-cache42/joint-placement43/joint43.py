"""Offline joint-template cell placement. No Unity/product/desktop writes."""
from pathlib import Path
from dataclasses import dataclass
import hashlib, json, math, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FEATURE = HERE.parents[1]
sys.path.insert(0, str(FEATURE))
from eye_cache42 import buffers, classify, PROJECT, ROOT

load = lambda p: json.loads(Path(p).read_text(encoding='utf8'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
dump = lambda name, data: (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf8')


@dataclass(frozen=True)
class Cell:
    id: str
    eye: int
    role: int
    xy: tuple
    rgba: tuple


class JointPlacement:
    """Explicit state entry + one integer translation for all reference cells."""
    def __init__(self, fingerprint, state_token, cells, reference_anchor, projected_anchor):
        self.fingerprint = fingerprint
        self.state_token = state_token
        self.cells = tuple(cells)
        self.reference_anchor = np.asarray(reference_anchor, float)
        self.projected_anchor = np.asarray(projected_anchor, float)

    def place(self, fingerprint, state_token, phase=(0., 0.), visibility=None):
        if fingerprint != self.fingerprint:
            raise ValueError('Source/style fingerprint changed; explicit rebind required')
        if state_token != self.state_token:
            raise ValueError('Unregistered pose/lid state; no open-eye fallback')
        delta = self.projected_anchor - self.reference_anchor + np.asarray(phase)
        translation = np.floor(delta + .5).astype(int)
        rows = []
        for c in self.cells:
            visible = visibility is None or visibility.get(c.id, True)
            rows.append({'cellId': c.id, 'eye': c.eye, 'role': c.role,
                         'referenceXY': list(c.xy), 'xy': (np.asarray(c.xy) + translation).tolist(),
                         'rgba8': list(c.rgba), 'visible': bool(visible)})
        return rows, translation, delta


class JointPlacementCache:
    """States enter explicitly; there is no previous/open state substitution."""
    def __init__(self):
        self.entries = {}

    def register(self, placement):
        self.entries[(placement.fingerprint, placement.state_token)] = placement

    def place(self, fingerprint, state_token, phase=(0., 0.), visibility=None):
        key = (fingerprint, state_token)
        if key not in self.entries:
            raise ValueError('No bound source/state entry; no implicit shape fallback')
        return self.entries[key].place(fingerprint, state_token, phase, visibility)


def asset_cells():
    base = PROJECT / 'SocketTemplate216/Inputs'
    def raw(file, dtype):
        s = (base / file).read_text(encoding='utf8')
        return np.frombuffer(bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)', s).group(1)), dtype).reshape(272, 480, 4)[::-1]
    role, rgba = raw('TemplateRole.asset', '<f4'), raw('TemplateRGBA.asset', np.uint8)
    cells = []
    for y, x in np.argwhere(np.isin(np.rint(role[..., 0]), [1, 4]) & np.isin(np.rint(role[..., 1]), [1, 2])):
        r, e = int(round(float(role[y, x, 0]))), int(round(float(role[y, x, 1])))
        cells.append(Cell(f'eye{e}:role{r}:template:{x},{y}', e, r, (int(x), int(y)), tuple(map(int, rgba[y, x]))))
    centres = [np.mean([np.array(c.xy) + .5 for c in cells if c.eye == eye and c.role == 1], axis=0) for eye in [1, 2]]
    return cells, np.mean(centres, axis=0)


def valid(meta, point, eye):
    return (meta[..., 0] > 0) & (meta[..., 1] > .5) & (meta[..., 3] > 1e-6) & (np.rint(meta[..., 2]) == eye) & (point[..., 3] > .5)


def source_packets(b, params):
    """Known intrinsic S1/S2/S3 only; absent S0/S4/S5/S6 never fabricated."""
    packets, projected = {}, {}
    h, w = b['S2META'].shape[:2]
    yy, xx = np.indices((h, w))
    centres = np.stack([params['roi']['x'] + (xx + .5) / 4,
                        params['roi']['y'] + (yy + .5) / 4], axis=-1)
    for idx in range(2):
        eye = int(round(params['centres'][idx]['w']))
        m1, m2, m3 = (b[f'S{q}META'] for q in [1, 2, 3])
        p1, p2, p3 = (b[f'S{q}POINT'] for q in [1, 2, 3])
        v1, v2, v3 = valid(m1, p1, eye), valid(m2, p2, eye), valid(m3, p3, eye)
        f1, _, _ = classify(p1[..., :3], params, idx)
        f2, u, v = classify(p2[..., :3], params, idx)
        a1, a2, a3 = (np.clip(q[..., 3], 0, 1) for q in [m1, m2, m3])
        iris_valid = v2 & np.isin(f2, [2, 3, 4])
        iw = np.where(iris_valid, a2, 0)
        iw *= np.where(v3 & (m3[..., 0] < m2[..., 0]), 1 - a3, 1)
        ww = np.where(v1 & np.isin(f1, [1, 2, 3, 4]), a1, 0)
        ww *= np.where(iris_valid & (m2[..., 0] < m1[..., 0]), 1 - a2, 1)
        ww *= np.where(v3 & (m3[..., 0] < m1[..., 0]), 1 - a3, 1)
        lw = np.where(v3, a3, 0)
        # Registration uses original iris source membership, not distorted final raster.
        projected[eye] = np.average(centres[v2], axis=0, weights=a2[v2]).tolist()
        rows = []
        for weights, family in [(iw, 1), (ww, 4), (lw, 6)]:
            keep = weights > 0
            rows.append({'xy': centres[keep], 'weight': weights[keep].astype(float),
                         'uv': np.stack([u, v], axis=-1)[keep].astype(float) if family == 1 else np.zeros((int(keep.sum()), 2)),
                         'family': family})
        packets[eye] = rows
    return packets, projected


def splat(rows, phase, bounds):
    """Translate 1/4-square footprints; exact area overlap, not colour filtering."""
    x0, y0, width, height = bounds
    count = np.zeros((3, width * height), float)
    uv_sum = np.zeros((2, width * height), float)
    for family, row in enumerate(rows):
        left = row['xy'] + phase - .125
        base = np.floor(left).astype(int)
        first = np.clip((base + 1 - left) * 4, 0, 1)
        for oy in [0, 1]:
            for ox in [0, 1]:
                weights = row['weight'] * (first[:, 0] if ox == 0 else 1 - first[:, 0]) * (first[:, 1] if oy == 0 else 1 - first[:, 1])
                x, y = base[:, 0] + ox - x0, base[:, 1] + oy - y0
                assert np.all((x >= 0) & (x < width) & (y >= 0) & (y < height))
                at = y * width + x
                count[family] += np.bincount(at, weights=weights, minlength=width * height)
                if family == 0:
                    for axis in range(2):
                        uv_sum[axis] += np.bincount(at, weights=weights * row['uv'][:, axis], minlength=width * height)
    means = np.divide(uv_sum, count[0], out=np.zeros_like(uv_sum), where=count[0] > 0).T
    return count, means


def allocator(rows, phase, bounds):
    count, uv = splat(rows, phase, bounds)
    x0, y0, width, height = bounds
    eligible = np.flatnonzero(count[0] > 0)
    cost = np.maximum(count[1], count[2]) - count[0]
    # Last tie coordinate follows GPU bottom-up y (all serialized samples here are top-down).
    order = sorted(eligible, key=lambda i: (cost[i], uv[i, 0], uv[i, 1], -(i // width + y0), i % width + x0))
    budget = math.floor(float(count[0].sum() / 16) + .5)
    selected = [(int(i % width + x0), int(i // width + y0)) for i in order[:budget]]
    return selected, {'areaCells': float(count[0].sum() / 16), 'budget': budget,
                       'cellWeights': [{'xy': [int(i % width + x0), int(i // width + y0)],
                                        'iris': float(count[0, i]), 'white': float(count[1, i]),
                                        'line': float(count[2, i]), 'uv': uv[i].tolist(),
                                        'selected': i in order[:budget]} for i in eligible]}


def component_count(points):
    todo = set(map(tuple, points)); result = 0
    while todo:
        result += 1; stack = [todo.pop()]
        while stack:
            x, y = stack.pop()
            for q in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
                if q in todo:
                    todo.remove(q); stack.append(q)
    return result


def shape_key(points):
    if not points:
        return ()
    p = np.asarray(points, int)
    return tuple(sorted(map(tuple, p - p.min(axis=0))))


def pair_key(by_eye):
    pts = [(e, x, y) for e in [1, 2] for x, y in by_eye[e]]
    if not pts:
        return ()
    xmin, ymin = min(p[1] for p in pts), min(p[2] for p in pts)
    return tuple(sorted((e, x - xmin, y - ymin) for e, x, y in pts))


def layer(rows, bounds, actual_colour=False):
    x0, y0, width, height = bounds
    im = Image.new('RGBA', (width, height))
    for r in rows:
        if not r.get('visible', True):
            continue
        x, y = r['xy'][0] - x0, r['xy'][1] - y0
        if not (0 <= x < width and 0 <= y < height):
            raise AssertionError('Preview bounds would crop a candidate cell')
        color = r['rgba8'] if actual_colour else ((220, 84, 115, 255) if r['eye'] == 1 else (72, 190, 149, 255)) if r['role'] == 1 else (221, 226, 233, 255)
        im.putpixel((x, y), tuple(color))
    return im


def show(im, scale=10):
    bg = Image.new('RGBA', im.size)
    for y in range(im.height):
        for x in range(im.width):
            bg.putpixel((x, y), (37, 40, 47, 255) if (x + y) % 2 else (29, 32, 38, 255))
    return Image.alpha_composite(bg, im).convert('RGB').resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)


def row_old(by_eye):
    return [{'eye': e, 'role': 1, 'xy': list(q), 'rgba8': [0, 0, 0, 255]} for e in [1, 2] for q in by_eye[e]]


def write_page(results, checks):
    table = ''.join(f'<tr><td>{r["pose"]}</td><td>{r["samples"]}</td><td>{r["oldPairShapes"]}</td><td>{r["oldPerEyeShapes"]}</td><td>{r["oldDisconnectedStates"]}</td><td>{r["jointPairShapes"]}</td></tr>' for r in results)
    figures = ''.join(f'<section><h2>{r["pose"]}</h2><p>원본 source 중심으로 공통 이동만 등록. 이 pose에 맞는 디자인·가림은 미검증.</p><img src="{r["pose"]}-phase-contact.png"><p>위: 기존 allocator 코어의 intrinsic 홍채 / 아래: 실제 Template216의 공동 셀 배치(흰자 포함). 역할색은 진단용입니다.</p><div class="flex"><figure><img src="{r["pose"]}-template-colour-1x.png"><figcaption>template RGBA8 직접 배치, 원래 2× 표시 크기</figcaption></figure><figure><img src="{r["pose"]}-template-colour-12x.png"><figcaption>최근접 확대, 실제 최종 얼굴 합성 아님</figcaption></figure><figure><img src="../{r["pose"]}-saved-final-12x.png"><figcaption>과거 저장 얼굴: 후보 합성 아님</figcaption></figure></div></section>' for r in results)
    page = f'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>눈 특징 공동 배치 43 — 위상 진단</title><style>body{{background:#161a21;color:#e5e8ef;font:16px/1.65 system-ui;max-width:1400px;margin:auto;padding:28px}}a{{color:#9ccaff}}img{{image-rendering:pixelated;max-width:100%}}table{{border-collapse:collapse}}td,th{{border:1px solid #556;padding:8px}}section{{margin:35px 0}}.flex{{display:flex;gap:20px;align-items:start;flex-wrap:wrap}}figure{{margin:0}}.notice{{background:#493d27;padding:16px}}</style><h1>눈 특징 공동 배치 — 제품 미적용</h1><p class="notice">기존 템플릿 전체를 한 공통 기준점으로 배치하는 독립 adapter입니다. source ID 자료구조만이 아니라 RGBA 셀 배치를 출력했습니다. <strong>실제 GPU 재렌더·최종 가림·연속 움직임·blink 디자인 검증은 아닙니다.</strong> 다른 포즈에 같은 템플릿을 둔 것은 이동 진단이며 모든 pose에 이 눈 모양을 승인한 것이 아닙니다.</p><p><a href="CONTRACT_KO.md">좌표·수식·합격 계약</a> · <a href="REPORT_KO.md">결과와 남은 한계</a> · <a href="RESULTS.json">위상별 집계</a> · <a href="TESTS.json">검사</a> · <a href="CELL_AND_COLOUR_PROVENANCE.json">원본 셀·색 출처</a> · <a href="STATE_TESTS.json">상태 전환·무효화</a> · <a href="PHASE_FAILURES.json">기존 allocator의 첫 형태 변화</a> · <a href="joint43.py">구현</a></p><table><tr><th>저장 pose</th><th>x/y 시험</th><th>기존 좌우 배치 종류</th><th>기존 각 눈 형태 종류</th><th>분리된 홍채 발생 상태</th><th>공동 배치 종류</th></tr>{table}</table><p>기존 비교군은 저장 표본을 보존적으로 이동시킨 intrinsic 재구성입니다. 누락된 skin/hair/body 가림을 추정해 넣지 않았습니다. 면적 반올림 budget은 이 보존적 이동에서는 일정하며, 이번 결과의 차이는 셀 순위·배치 변화입니다.</p>{figures}<p>통과한 계약 검사 {len(checks)}개. 검사 수를 미감 성공 근거로 삼지 않습니다. 제품·Unity·31·34·Desktop 변경 없음.</p></html>'''
    (HERE / 'INDEX.html').write_text(page, encoding='utf8')


def main():
    cells, ref_anchor = asset_cells()
    baseline = load(HERE.parent / 'VERIFIED.json')['productInputSHA256']
    provenance = {'reference': 'Existing Template216 asset; not the current distorted raster; no new all-pose art approval asserted',
                  'referenceAnchorCellCentre': ref_anchor.tolist(), 'axes': 'x-right/y-down', 'units': 'logical cells',
                  'colourEncoding': 'literal stored TemplateRGBA RGBA8, directly exported to PNG; no S2 replacement or new colour correction',
                  'cells': [dict(cellId=c.id, eye=c.eye, role=c.role, referenceXY=list(c.xy), rgba8=list(c.rgba)) for c in cells],
                  'role6Absent': True, 'productSHA256': baseline}
    dump('CELL_AND_COLOUR_PROVENANCE.json', provenance)
    phases = [(x / 64, y / 64) for y in range(65) for x in range(65)]
    report, failures, registrations, all_outputs = [], [], [], []
    check_list = []
    def check(name, condition):
        assert condition, name
        check_list.append({'name': name, 'pass': True})
    fixed = np.array([c.xy for c in cells], int)
    canonical = pair_key({e: [c.xy for c in cells if c.eye == e and c.role == 1] for e in [1, 2]})
    state_tests = []
    for name in ['neutral', 'walk-00', 'walk-01', 'walk-02', 'walk-03']:
        folder = ROOT / 'final-validation' / name
        params = load(folder / 'params.json'); b = buffers(folder / 'buffers.gz')
        packets, projected = source_packets(b, params)
        anchor = np.mean(list(projected.values()), axis=0)
        declared_model = load(HERE.parent / 'CACHE_BINDING.json')['declaredPrefabTopologySHA256']
        fingerprint = hashlib.sha256(json.dumps([declared_model, baseline, params['style']], sort_keys=True).encode()).hexdigest()
        token = hashlib.sha256((sha(folder / 'params.json') + ':lid-state-not-separately-measured').encode()).hexdigest()
        adapter = JointPlacement(fingerprint, token, cells, ref_anchor, anchor)
        registration = {'pose': name, 'sourceBuffersSHA256': sha(folder / 'buffers.gz'), 'sourceParamsSHA256': sha(folder / 'params.json'),
                        'sourcePhase': params['source'], 'angle': params['angle'], 'boneLocalSHA256': params['boneLocalSHA256'],
                        'originalIrisCentres': projected, 'jointAnchor': anchor.tolist(), 'referenceAnchor': ref_anchor.tolist(),
                        'stateToken': token, 'fingerprint': fingerprint, 'lidStateMeasured': False,
                        'referenceUsage': 'borrowed Template216 for translation-only probe; pose-specific form not approved'}
        registrations.append(registration)
        # Generous bounds independent of source ROI clipping.
        roi = params['roi']; bounds = (roi['x'] - 5, roi['y'] - 4, roi['width'] + 12, roi['height'] + 10)
        base_old = {}; old_shapes = {1: set(), 2: set()}; pair_shapes = set(); joint_shapes = set()
        disconnected = 0; budgets = {1: set(), 2: set()}; area_error = 0.; max_pos_error = 0.
        first_failure = None; frame_rows = []
        base_areas = {e: sum(r['weight'].sum() for r in packets[e] if r['family'] == 1) / 16 for e in [1, 2]}
        selected_phases = [(0., 0.), (.25, 0.), (.5, 0.), (.75, 0.), (0., .5), (.5, .5), (.75, .75)]
        illustrated = {}
        for index, phase in enumerate(phases):
            current, info = {}, {}
            for e in [1, 2]:
                current[e], info[e] = allocator(packets[e], np.array(phase), bounds)
                old_shapes[e].add(shape_key(current[e])); budgets[e].add(info[e]['budget'])
                area_error = max(area_error, abs(info[e]['areaCells'] - base_areas[e]))
            key = pair_key(current); pair_shapes.add(key)
            if index == 0: base_old = current; base_pair = key
            if any(component_count(current[e]) > 1 for e in [1, 2]): disconnected += 1
            if key != base_pair and first_failure is None:
                first_failure = {'pose': name, 'phase': list(phase), 'baselinePhase': [0, 0],
                                 'baselineCells': base_old, 'selectedCells': current, 'intrinsicPackets': info,
                                 'reason': 'relative cell arrangement changed after quotienting a common integer translation; not a full GPU or temporal reproduction'}
            out, translation, delta = adapter.place(fingerprint, token, phase)
            actual = np.array([q['xy'] for q in out])
            assert np.array_equal(actual - translation, fixed)
            assert [q['rgba8'] for q in out] == [list(c.rgba) for c in cells]
            assert [(q['cellId'], q['eye'], q['role']) for q in out] == [(c.id, c.eye, c.role) for c in cells]
            jk = pair_key({e: [tuple(q['xy']) for q in out if q['eye'] == e and q['role'] == 1] for e in [1, 2]})
            assert jk == canonical; joint_shapes.add(jk)
            max_pos_error = max(max_pos_error, float(np.max(abs(translation - delta))))
            if phase in selected_phases: illustrated[phase] = (current, out)
            frame_rows.append({'phase': list(phase), 'translation': translation.tolist(),
                               'oldIrisCells': current, 'jointCells': [q['xy'] for q in out]})
        if first_failure:
            failures.append(first_failure)
            p = tuple(first_failure['phase'])
            if p not in illustrated:
                current = {e: allocator(packets[e], np.array(p), bounds)[0] for e in [1, 2]}
                illustrated[p] = (current, adapter.place(fingerprint, token, p)[0])
        dump(f'{name}-phase-layouts.json', frame_rows)
        base_out = adapter.place(fingerprint, token, (0, 0))[0]
        dump(f'{name}-placed-cells.json', base_out)
        rgba = layer(base_out, bounds, actual_colour=True)
        # Each logical cell is 2x2 display pixels in the stored project; retain that scale explicitly.
        rgba.resize((rgba.width * 2, rgba.height * 2), Image.Resampling.NEAREST).save(HERE / f'{name}-template-colour-1x.png')
        rgba.resize((rgba.width * 24, rgba.height * 24), Image.Resampling.NEAREST).save(HERE / f'{name}-template-colour-12x.png')
        width, height = bounds[2] * 10, bounds[3] * 10
        board = Image.new('RGB', ((width + 12) * len(illustrated), height * 2 + 65), (21, 25, 32)); draw = ImageDraw.Draw(board)
        for column, (phase, (old, out)) in enumerate(illustrated.items()):
            x = column * (width + 12)
            draw.text((x + 4, 5), f'phase {phase[0]:.4f}, {phase[1]:.4f}', fill='white')
            board.paste(show(layer(row_old(old), bounds)), (x, 25))
            board.paste(show(layer(out, bounds)), (x, height + 50))
        board.save(HERE / f'{name}-phase-contact.png')
        for requested, supplied_key in [('blink-50', fingerprint), ('blink-100', fingerprint), ('other-pose', fingerprint), (token, 'different-source'), (token, 'different-style')]:
            rejected = False
            try: adapter.place(supplied_key, requested)
            except ValueError: rejected = True
            state_tests.append({'registeredPose': name, 'requestedState': requested, 'sourceKey': supplied_key,
                                'rejectedWithoutStaleFallback': rejected})
            assert rejected
        hidden = {c.id: False for c in cells}
        hidden_out = adapter.place(fingerprint, token, (0, 0), hidden)[0]
        assert not any(q['visible'] for q in hidden_out)
        assert [q['xy'] for q in hidden_out] == [q['xy'] for q in base_out]
        check(f'{name}: all {len(phases)} joint placements preserve every cell ID/relative position/role/RGBA', len(joint_shapes) == 1)
        check(f'{name}: conservative source area unchanged; existing budget not artificially changed', area_error < 1e-10 and all(len(budgets[e]) == 1 for e in [1, 2]))
        check(f'{name}: common snap position error <=0.5 logical cell on each axis', max_pos_error <= .50000000001)
        check(f'{name}: hidden feature is not force drawn and keeps intrinsic shape', True)
        item = {'pose': name, 'samples': len(phases), 'phaseStepLogicalCells': 1 / 64,
                'oldPairShapes': len(pair_shapes), 'oldPerEyeShapes': {e: len(old_shapes[e]) for e in [1, 2]},
                'oldDisconnectedStates': disconnected, 'oldBudgets': {e: sorted(budgets[e]) for e in [1, 2]},
                'oldIntrinsicSourceAreaCells': base_areas, 'conservativeAreaMaximumError': area_error,
                'jointPairShapes': len(joint_shapes), 'jointCellCount': len(cells), 'jointIrisCellsPerReferenceEye': {e: sum(c.eye == e and c.role == 1 for c in cells) for e in [1, 2]},
                'maxSnapErrorPerAxis': max_pos_error, 'finalOcclusionReplayed': False, 'actualTemporalSequence': False}
        report.append(item)
        print(json.dumps({'completedPose': name, 'oldPairShapes': len(pair_shapes), 'jointPairShapes': len(joint_shapes), 'disconnectedStates': disconnected}), flush=True)
    check('all source/model/style/lid-state changes reject stale shape reuse', all(q['rejectedWithoutStaleFallback'] for q in state_tests))
    check('tracked product/template inputs unchanged', all(sha(p) == h for p, h in baseline.items()))
    dump('RESULTS.json', report); dump('PHASE_FAILURES.json', failures); dump('REGISTRATIONS.json', registrations)
    dump('STATE_TESTS.json', state_tests); dump('TESTS.json', {'passed': len(check_list), 'checks': check_list})
    write_page(report, check_list)
    report_text = '# 눈 특징 공동 배치 검사 결과\n\n' + '\n'.join(f'- {r["pose"]}: 65×65 위상에서 기존 좌우 배치 {r["oldPairShapes"]}종 → 공동 배치 {r["jointPairShapes"]}종. 기존 각 눈 형태 {r["oldPerEyeShapes"]}, 분리된 홍채 발생 {r["oldDisconnectedStates"]}상태.' for r in report)
    report_text += '\n\n고정 source footprint를 보존적으로 평행이동했으므로 기존 면적 budget은 이 시험에서 고정이다. 선택 셀의 상대 배치 변화와 개수 변화를 혼동하지 않는다. 현재 실제 GPU의 모든 selector·가림을 재현하지 않았다.\n\n후보는 실제 Template216의 셀별 RGBA와 역할을 보존하고 공통 이동만 snap한다. 이 제한 조건에서는 구조상 형상이 유지되어야 하며, 출력된 전 셀과 RGBA를 검사했다. 실제 pose/blink에서 형태를 어떻게 바꿀지 해결한 결과는 아니다. 5pose의 각 등록에서 동일 템플릿을 차용한 것은 위상 진단용이다. blink50/100 및 미등록 pose를 요청하면 열린 눈으로 대체하지 않고 거부한다.\n\nTemplateRole에 upperLine role6이 없어 상안검 디자인 완성 검증은 할 수 없다. 눈꺼풀·머리 가림 자료가 빠져 후보는 투명한 분리 레이어만 출력했다. 과거 최종 얼굴 사진 위에 덧칠하거나 실제 가림을 무시한 합성은 하지 않았다. 실제 연속 프레임·포즈 적합성·미감 통과 주장은 하지 않는다.\n\n색은 원래 TemplateRGBA의 정확한 셀 색을 직접 사용했다. 이전 S2와의 차이만으로 색을 고치지 않았다. source-role1/4와 동일 eyeID만 대응시키고 다른 palette family를 넣지 않았다. 원본 상안검/홍채의 디자인 provenance가 적합한지는 별도 문제다.\n\n제품/Unity/31/34/Desktop 변경 0.\n'
    (HERE / 'REPORT_KO.md').write_text(report_text, encoding='utf8')
    missing = []
    html = (HERE / 'INDEX.html').read_text(encoding='utf8')
    for href in re.findall(r'(?:href|src)="([^"]+)"', html):
        if ':' not in href and not (HERE / href).exists(): missing.append(href)
    assert not missing, missing
    dump('MANIFEST.json', {'newUnityCalls': 0, 'productChanges': 0, 'DesktopWrites': 0, 'phasePlacements': len(phases) * len(report),
                           'missingLinks': missing, 'files': {p.name: sha(p) for p in HERE.iterdir() if p.is_file() and p.name != 'MANIFEST.json'}})
    print(json.dumps({'output': str(HERE / 'INDEX.html'), 'passed': len(check_list), 'placements': len(phases) * len(report)}))


if __name__ == '__main__':
    main()
