from pathlib import Path
import json, hashlib
import numpy as np

O = Path(__file__).resolve().parent
j = json.loads((O/'METRIC_AUDIT535.json').read_text())
g = json.loads((O/'GATE535.json').read_text())
old = json.loads((O/'METRIC_AUDIT535.before-width-domain.json').read_text())
assert g['allEightNormalOmissionsLowerScore'] and g['newUnityCalls']==0
same = all(a['alternatives'][v]['eq3HeightEligibility']['costBounds'] == b['alternatives'][v]['eq3HeightEligibility']['costBounds']
    for a,b in zip(j['rows'],old['rows']) for v in a['alternatives'])
assert same
correction = {'reason':'Width band .5 may not traverse beyond a neighbouring extremum shallower than .5; width undefined there.',
    'paperEligibleScoresUnchanged':same, 'oldFilesRetainedLocally':True,
    'unfilteredActualPoseScoresHaveUndefinedTerms':'Not ranked or treated as complete scores.',
    'thinControlUnfilteredScoresDefined':all(q['oldUnfilteredUndefined']==q['newUnfilteredUndefined']==0 for q in g['normalEndOmissionCounterexamples'])}
(O/'DIAGNOSTIC_CORRECTION535.json').write_text(json.dumps(correction,indent=2))
ns={'__file__':str(O/'compare535.py')}
exec((O/'compare535.py').read_text().split('\nrows = []')[0],ns)
source = np.array(j['rows'][3]['fixedReference'][0]); case = j['rows'][3]
variants={}
for v in ['baseline','halfcell']:
    _,box,_,mask=ns['saved'](Path(case['alternatives'][v]['path']))
    variants[v]=(box,mask)
box,m=variants['baseline'];drop=m.copy()
for yy,xx in np.argwhere(drop):
    if xx+box[0]+.5<0:drop[yy,xx]=False
variants['omitEnds']=(box,drop)
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="440" viewBox="0 0 1080 440"><rect width="1080" height="440" fill="white"/><g font-family="sans-serif" fill="#222"><text x="12" y="21">535 normal-end counterexample / stored geometry and masks / no Unity or new capture</text>']
for k,label in enumerate(['reference','baseline','halfcell','omitEnds']):
    ox=42+k*270;oy=67;sc=26
    xy=lambda p:(ox+(float(p[0])+1.5)*sc,oy+float(p[1])*sc)
    title={'reference':'Fixed reference H=.75, W=3','baseline':'Preserved ends: score 1.0000','halfcell':'Old damaged: score 1.0833','omitEnds':'Both ends lost: score .0909'}[label]
    svg.append(f'<text x="{k*270+10}" y="46" font-size="14">{title}</text>')
    for x in range(-1,6):
        px,py=xy((x,0));svg.append(f'<path d="M{px},{py}v{11*sc}" stroke="#ddd"/>')
    for y in range(12):
        px,py=xy((-1,y));svg.append(f'<path d="M{px},{py}h{6*sc}" stroke="#ddd"/>')
    if label!='reference':
        b,mm=variants[label]
        for yy,xx in np.argwhere(mm):
            px,py=xy((xx+b[0],yy+b[1]));svg.append(f'<rect x="{px}" y="{py}" width="{sc}" height="{sc}" fill="#c8daed" stroke="white" stroke-width=".4"/>')
    pts=' '.join(f'{xy(p)[0]},{xy(p)[1]}'for p in list(source)+[source[0]])
    svg.append(f'<polyline points="{pts}" fill="none" stroke="#23669c" stroke-width="2"/>')
svg.append('<text x="12" y="391" font-size="14">Blue=fixed pre-Fit reference. Light fill=saved candidate / omission counterfactual. Lower score is preferred.</text><text x="12" y="416" font-size="14">Eq3-like width term alone prefers losing intended ends. This is not a reproduction or failure verdict of the full paper.</text></g></svg>')
(O/'NORMAL_END_COUNTEREXAMPLE535.svg').write_text(''.join(svg),encoding='utf-8')
paths={Path(v['path'])for q in j['rows']for v in q['alternatives'].values()}
for f in [43,44]:paths.add(O.parent/'Cloth527/FullLoopB'/f'{f:03d}_ALT_GEOMETRY.bin')
paths.add(O.parent/'Outline533/FullLoop/050_ALT_GEOMETRY.bin')
paths.add(O.parent/'Shape532/Probe532.cs')
(O/'INPUT_MANIFEST535.json').write_text(json.dumps([
    {'path':str(p),'archiveName':str(p.relative_to(O.parent)).replace('\\','/'),
     'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    for p in sorted(paths)],indent=2))
summary={'status':g['status'],'newUnityCalls':0,'newCaptures':0,'newProductCode':False,
    'fixedReference':'saved pre-Fit Source per pose; no fitted candidate feedback; upstream opacity approximation/persistent cross-pose feature IDs not certified',
    'paperConstantsLogicalPixels':j['paperConstantsLogicalPixels'],
    'localRecordedEventComparisons':[{k:q[k]for k in ['case','oldScore','newScore','newUndefined','changedCells']}for q in g['localEventCounterfactuals']],
    'allEightNormalEndOmissionsPreferred':True,'normalPreservedScore':1,'normalBothEndsLostScore':1/11,
    'normalHeight':.75,'normalWidth':3,'noHeightFilterDiagnostic':{'preserve':0,'omit':1/11},
    'diagnosticCorrectionEligibleScoresUnchanged':True,
    'gatePassed':False,'paperFullMethodImplementedOrDisproved':False,
    'missingContract':['valid reference/output boundary feature-line pairing and line/band coordinate convention',
        'shape/location fidelity together with width; Eq3 alone is insufficient',
        'staircase span quality: recorded44 cell removal has unchanged Eq3',
        'candidate construction must preserve fixed reference information before final selected mask'],
    'replacementPoint':'SelectRegions boundary selection needs the fixed reference and boundary candidates; FitArea may not overwrite the reference. No replacement justified by this failed gate.',
    'defaultOFF':True,'runtimeValidation':'not executed; entry gate failed'}
(O/'SUMMARY535.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary))
