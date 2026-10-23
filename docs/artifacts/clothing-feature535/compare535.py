"""Bounded Eq3 applicability audit, not a selector or a paper reproduction.

Fixed pre-Fit closed contours and saved masks only. The existing region
Boundaries convention is ported for diagnostics. Region-edge polylines are
NOT the paper's authored pixel-line centre paths; this adaptation is explicit.
"""
from pathlib import Path
import hashlib, json, math, struct
import numpy as np

O = Path(__file__).resolve().parent
W = O.parent
S = W / 'Shape532'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

class Reader:
    def __init__(self, b): self.b, self.at = b, 0
    def i(self):
        q = struct.unpack_from('<i', self.b, self.at)[0]; self.at += 4; return q
    def a(self, dtype, n):
        q = np.frombuffer(self.b, dtype, n, self.at).copy(); self.at += q.nbytes; return q
    def rings(self):
        return [self.a('<f4', self.i() * 2).reshape(-1, 2).astype(float) for _ in range(self.i())]

def saved(p):
    r = Reader(p.read_bytes()); rings = r.rings(); box = tuple(r.i() for _ in range(4))
    _, _, w, h = box; a = r.a('<f4', w*h).reshape(h, w); mask = r.a('?', w*h).reshape(h, w)
    assert r.at == len(r.b)
    return rings, box, a, mask

def source(p): return Reader(p.read_bytes()).rings()

def signed_area(r): return float(sum(np.cross(a, b) for a, b in zip(r, np.roll(r, -1, axis=0)))) * .5

def boundaries(mask, box):
    # HeadRegion502.Boundaries scale=1 edge orientation and turn preference.
    x0, y0, w, h = box; edges = {}; ambiguous = 0
    def on(x, y): return 0 <= x < w and 0 <= y < h and bool(mask[y, x])
    def edge(a, b): edges.setdefault(a, []).append(b)
    for y, x in np.argwhere(mask):
        x, y = int(x), int(y)
        if not on(x, y-1): edge((x, y), (x+1, y))
        if not on(x+1, y): edge((x+1, y), (x+1, y+1))
        if not on(x, y+1): edge((x+1, y+1), (x, y+1))
        if not on(x-1, y): edge((x, y+1), (x, y))
    dirs = {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}
    direct = lambda a, b: dirs[(b[0]-a[0], b[1]-a[1])]
    loops = []
    while edges:
        start = min(edges, key=lambda p: (p[1], p[0])); at, prior = start, None
        loop = []; limit = sum(map(len, edges.values())) + 1
        while True:
            limit -= 1; assert limit >= 0 and at in edges
            loop.append((at[0]+x0, at[1]+y0)); nxt = edges[at]; to = nxt[0]
            if len(nxt) > 1:
                ambiguous += 1
                if prior is not None:
                    d = direct(prior, at)
                    to = max(nxt, key=lambda p: {1:4, 0:3, 3:2, 2:1}[(direct(at, p)-d) % 4])
            nxt.remove(to)
            if not nxt: del edges[at]
            prior, at = at, to
            if at == start: break
        if len(loop) >= 4: loops.append(np.array(loop, float))
    return loops, ambiguous

def extrema(r, axis):
    n = len(r); v = r[:, axis]
    cuts = [i for i in range(n) if v[i] != v[(i-1) % n]]
    if not cuts: return []
    groups = []
    for k, i in enumerate(cuts):
        end = cuts[(k+1) % len(cuts)]; end += n if end <= i else 0
        ids = [j % n for j in range(i, end)]
        groups.append((ids, float(v[i])))
    features = []
    for k, (ids, value) in enumerate(groups):
        prev, nxt = groups[k-1][1], groups[(k+1) % len(groups)][1]
        kind = 1 if value > prev and value > nxt else -1 if value < prev and value < nxt else 0
        if kind:
            features.append({'axis':axis, 'kind':kind, 'value':value, 'ids':ids,
                             'position':((r[ids[0]]+r[ids[-1]])*.5).tolist()})
    for k, e in enumerate(features):
        e['height'] = min(abs(e['value']-features[k-1]['value']), abs(e['value']-features[(k+1) % len(features)]['value']))
        # A .5-height width must not walk beyond a shallower neighbouring
        # extremum and silently include unrelated contour lobes. Paper-eligible
        # reference extrema (height>=1) are unaffected by this domain guard.
        if e['height'] < .5:
            e['widthCrossings'] = []; e['width'] = None
            e['referenceEligibleHeight1'] = False
            continue
        level = e['value'] - e['kind']*.5
        crossings = []
        for step, start in [(-1, e['ids'][0]), (1, e['ids'][-1])]:
            at = start
            for _ in range(n):
                to = (at+step) % n
                if (r[to,axis]-level)*e['kind'] <= 0:
                    den = r[to,axis]-r[at,axis]
                    t = (level-r[at,axis])/den if den else 0
                    crossings.append((r[at]+t*(r[to]-r[at])).tolist()); break
                at = to
        e['widthCrossings'] = crossings
        e['width'] = abs(crossings[0][1-axis]-crossings[1][1-axis]) if len(crossings)==2 else None
        e['referenceEligibleHeight1'] = e['height'] >= 1
    return features

def features(rings):
    return [dict(e, ring=i) for i, r in enumerate(rings) for axis in [0,1] for e in extrema(r, axis)]

def eq3(output, reference, eligible=True):
    # Thresholds copied as paper design constants, no fitting/sweep.
    refs = [e for e in reference if not eligible or e['referenceEligibleHeight1']]
    rows = []; total_lo = total_hi = 0.; undefined = 0
    for e in output:
        w = e['width']
        near = [q for q in refs if q['axis']==e['axis'] and q['kind']==e['kind']
                and math.dist(q['position'], e['position']) <= 2]
        if w is None or w <= 0: costs = []
        elif near:
            costs = [abs(w-q['width'])/(w+q['width']) for q in near if q['width'] is not None and q['width'] > 0]
        else: costs = [1/w]
        if not costs: undefined += 1
        else: total_lo += min(costs); total_hi += max(costs)
        rows.append({'output':e, 'nearbyReference':near, 'costRange': [min(costs),max(costs)] if costs else None})
    return {'costBounds':[total_lo,total_hi], 'undefined':undefined,
            'boundsExcludeUndefinedTerms':True,
            'multipleNearbyReference':sum(len(e['nearbyReference'])>1 for e in rows), 'rows':rows}

def audit(name, refs, paths):
    # Stable reference reused for every alternative. No candidate drives refs.
    rf = features(refs); out = {'case':name,'fixedReference': [r.tolist() for r in refs],
                              'referenceFeatures':rf, 'alternatives':{}}
    for label, path in paths.items():
        _, box, _, mask = saved(path); rings, branches = boundaries(mask, box)
        # Compare full closed contour inventories, no ROI exceptions or optimizer.
        of = features(rings)
        out['alternatives'][label] = {'path':str(path), 'sha256':sha(path),
            'selectedCells':int(mask.sum()), 'regionLoops':len(rings), 'branchDecisions':branches,
            'eq3HeightEligibility':eq3(of,rf), 'unfilteredReferenceDiagnostic':eq3(of,rf,False)}
    return out

rows = []
for f in [43,44]:
    p = W/'Cloth527/FullLoopB'/f'{f:03d}_ALT_GEOMETRY.bin'
    rows.append(audit('actual'+str(f),source(p),{v:S/f'actual{f}_{v}.bin'for v in ['baseline','area','halfcell']}))
rows.append(audit('actual50',source(W/'Outline533/FullLoop/050_ALT_GEOMETRY.bin'),
    {v:W/'Contour534/Math'/f'50_{v}.bin'for v in ['source','distance','area']}))
base = np.array([[0,0],[4,0],[4,11],[0,11],[0,10],[-.75,10],[-.75,7],[0,7],[0,4],[-.75,4],[-.75,1],[0,1]],float)
for rot in range(4):
    r = base.copy()
    for _ in range(rot): r = np.c_[-r[:,1],r[:,0]]
    for sub in range(2):
        ref = r if not sub else np.array([p for a,b in zip(r,np.roll(r,-1,axis=0))for p in[a,(a+b)*.5]])
        rows.append(audit(f'thin{rot}_{sub}',[ref],{v:S/f'thin{rot}_{sub}_{v}.bin'for v in['baseline','area','halfcell']}))
result = {'status':'OFFLINE_METRIC_APPLICABILITY_ONLY_NO_SELECTOR',
    'paper':'https://yongliangyang.net/docs/pixelAnim_pg16.pdf', 'paperSections':'4.1 Fig7 Eq3; full method also has Eq1/Eq2 and Eq4',
    'adaptationsAndLimits':['Closed cell-edge contour is not the paper authored pixel-line centre path.',
        'Height<1 reference eligibility is recorded; iterative pixel perturbation of a continuous contour is not claimed implemented.',
        'Plateau representative is midpoint; paper does not fully specify plateau/tie policy.',
        'Same axis and polarity, Euclidean radius2; all ambiguous local matches produce cost bounds, never silent tie selection.',
        'Nearby candidates across different region rings are not certified same feature-line ownership.',
        'No mask optimization, similarity terms, temporal terms, product code, Unity execution or capture.'],
    'paperConstantsLogicalPixels':{'widthHeightBand':.5,'referenceHeightMinimum':1,'matchRadiusExperimental':2},
    'newUnityCalls':0,'newCaptures':0,'productChanged':False,'rows':rows}
(O/'METRIC_AUDIT535.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps([{'case':r['case'],'referenceExcluded':sum(not e['referenceEligibleHeight1']for e in r['referenceFeatures']),
    'alternatives':{k:{'score':v['eq3HeightEligibility']['costBounds'],'undefined':v['eq3HeightEligibility']['undefined'],
                       'multi':v['eq3HeightEligibility']['multipleNearbyReference'],'branches':v['branchDecisions']}
                    for k,v in r['alternatives'].items()}}for r in rows]))
