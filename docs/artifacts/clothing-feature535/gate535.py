"""Recorded-event counterfactuals and normal-end omission counterexample.

Coordinates label existing evidence, never production selection conditions.
No weights, thresholds, selector, fitting, mask postprocess or Unity calls.
"""
from pathlib import Path
import json
import numpy as np

O = Path(__file__).resolve().parent
ns = {'__file__':str(O/'compare535.py')}
exec((O/'compare535.py').read_text().split('\nrows = []')[0], ns)
j = json.loads((O/'METRIC_AUDIT535.json').read_text())
saved, boundaries, features, eq3 = [ns[k] for k in ['saved','boundaries','features','eq3']]
byname = {q['case']:q for q in j['rows']}

def evaluate(name, label, transform):
    case = byname[name]; base = case['alternatives'][label]
    _, box, _, mask = saved(Path(base['path'])); other = mask.copy(); transform(other, box)
    rings, branches = boundaries(other, box); fs = features(rings)
    rf = case['referenceFeatures']
    filtered, raw = eq3(fs,rf), eq3(fs,rf,False)
    return {'case':name, 'from':label, 'changedCells':int(np.count_nonzero(mask != other)),
        'selectedCells':int(other.sum()), 'branchDecisions':branches,
        'oldScore':base['eq3HeightEligibility']['costBounds'],
        'newScore':filtered['costBounds'], 'newUndefined':filtered['undefined'],
        'oldUnfilteredReferenceScore':base['unfilteredReferenceDiagnostic']['costBounds'],
        'newUnfilteredReferenceScore':raw['costBounds'],
        'oldUnfilteredUndefined':base['unfilteredReferenceDiagnostic']['undefined'],
        'newUnfilteredUndefined':raw['undefined'],
        'newFeatures':fs}

local = []
for name, label, cells, value in [
    ('actual43','baseline',[(200,98),(200,99)],False),
    ('actual50','area',[(201,97)],True),
    ('actual44','area',[(231,78)],False)
]:
    def change(m,b):
        for x,y in cells: m[y-b[1],x-b[0]] = value
    q = evaluate(name,label,change); q['recordedEventCells']=cells; q['setTo']=value; local.append(q)

normal = []
for rot in range(4):
    for sub in range(2):
        # Competing output is the fixture main rectangle with its appendages
        # omitted. It is a counterexample, not an algorithm proposed for use.
        def omit(m,b):
            for yy,xx in np.argwhere(m):
                p = np.array([xx+b[0]+.5,yy+b[1]+.5])
                for _ in range(rot): p = np.array([p[1],-p[0]])
                if p[0] < 0: m[yy,xx] = False
        q=evaluate(f'thin{rot}_{sub}','baseline',omit)
        q['normalEndsOmitted']=2
        q['referenceShallowFeatures']=[e for e in byname[q['case']]['referenceFeatures']if not e['referenceEligibleHeight1']]
        normal.append(q)

# Invariance of this diagnostic under exact collinear subdivision and quarter
# rotation is checked from the existing eight inputs; no new input generation.
summaries = {q['case']:{'old':q['oldScore'],'omitEnds':q['newScore'],
    'oldUnfiltered':q['oldUnfilteredReferenceScore'],'omitEndsUnfiltered':q['newUnfilteredReferenceScore']}
    for q in normal}
failed = all(q['newScore'][1] < q['oldScore'][0] for q in normal)
result = {'status':'EQ3_ONLY_GATE_FAILED_NORMAL_END_OMISSION' if failed else 'UNRESOLVED',
    'newUnityCalls':0,'newCaptures':0,'productChange':False,
    'localEventCounterfactuals':local,'normalEndOmissionCounterexamples':normal,
    'scope':'one Eq3-like closed-region-edge diagnostic, not full paper optimizer or authored centreline reproduction',
    'paperConstantsUnchanged':True,'coefficientSearch':False,
    'allEightNormalOmissionsLowerScore':failed,
    'inputReferenceFixedBeforeFit':True,
    'selectorProduced':False,
    'conclusion':'Existing desired alternatives rank better, but Eq3 alone also prefers deleting both intended .75x3 ends. Full paper shape/location terms and valid reference/output feature-line correspondence are missing; no product patch follows.'}
(O/'GATE535.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],
    'local':[{k:v for k,v in q.items()if k not in ['newFeatures']}for q in local],
    'normal':summaries,'newUnityCalls':0,'newCaptures':0}))
