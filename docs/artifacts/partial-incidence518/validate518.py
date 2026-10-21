from pathlib import Path
import json,hashlib,ast,zipfile,statistics,subprocess
import active516 as G
W=G.ROOT;D=W/'Region518/PartialEdgeV2';FULL=D/'Stored81';P=Path('C:/Users/JG/Documents/work/Fantasy Survival Escape Game');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
state=json.loads((FULL/'STATE.json').read_text());assert state['state']=='COMPLETED'and state['poses']==81
audit=json.loads((FULL/'AUDIT518.json').read_text());assert audit['poses']==81 and len(audit['rows'])==81
phase0=json.loads((D/'PHASE0.json').read_text());fixtures=json.loads((D/'FIXTURES518.json').read_text());filters=json.loads((D/'FILTER_COUNTEREXAMPLES518.json').read_text());assert phase0['fullFirstPosePassed']and fixtures['passed']and filters['passed']
inputCount=0
for i in range(81):
    row=json.loads((FULL/f'{i:03d}_AUDIT.json').read_text());assert row['target']==i
    assert sha(G.INPUT/f'{i:03d}_curves.json')==next(v['sha256']for v in row['sourceInputs']if v['path'].endswith('_curves.json'))
    for r in row['sourceInputs']:assert sha(Path(r['path']))==r['sha256'];inputCount+=1
    mask=G.read_mask(i);assert hashlib.sha256(mask.tobytes()).hexdigest()==row['maskUnchangedSHA256']
    assert row['selectorRuns']==row['newUnityCalls']==0
    assert row['reparameterizedCanonicalInputIdentical']
    if row['costStatus']!='FULL_GEOMETRIC_CORRESPONDENCE':assert row['comparableTotalRaw']is None
    else:assert row['fullyBound']and not row['costDetail']['geometryEventResets']and row['costDetail']['valid']
for r in audit['sourceScripts']:assert sha(Path(r['path']))==r['sha256']
frozen=[]
for previous in[W/'Temporal516/VALIDATION516.json',W/'Temporal517/SpanArcV2/VALIDATION517.json']:
    for r in json.loads(previous.read_text())['sources']:
        path=W/r['name'];assert sha(path)==r['sha256'];frozen.append({'path':str(path),'sha256':r['sha256']})
runtime=json.loads((W/'APPLIED_SOURCE512.json').read_text())['files']
for r in runtime:assert sha(P/r['path'])==r['after']
ray=json.loads((W/'APPLIED_RAY512.json').read_text());assert sha(Path(ray['path']))==ray['sha256']
settings={'ProjectSettings/QualitySettings.asset':'819a7e0414a299c9a208fe6958a929df8c23c83bda91d9fb57b90ba7776d9ba6','ProjectSettings/TimeManager.asset':'3396f52fdc16d445024e01d7a2d99db6f0a37569d1d73c0302e9ffb857d90287'}
for rel,h in settings.items():assert sha(P/rel)==h
sources=[]
for name in['face518.py','edge518.py','arc518.py','minimum518.py','first518.py','probe_full518.py','partial518.py','fixtures518.py','audit518.py','probe_audit518.py','dependency518.py','filter_evidence518.py','validate518.py']:
    p=W/name;ast.parse(p.read_text(encoding='utf-8'));sources.append({'name':name,'sha256':sha(p),'bytes':p.stat().st_size})
archives=[]
for name,items in[
    ('ALL81_AUDITS518.zip',[(p,p.name)for p in sorted(FULL.glob('*_AUDIT.json'))]),
    ('PRIOR_FAILURE_CHECKPOINTS518.zip',[(p,p.relative_to(W/'Region518').as_posix())for p in sorted((W/'Region518/WholeEdgeV1').iterdir())if p.is_file()]+[(p,p.relative_to(D).as_posix())for p in sorted((D/'UnfilteredAnchor').iterdir())if p.is_file()]+[(D/name,name)for name in['FLOAT_EXACT_COLLINEAR_REJECTION.json','MISSING_CENTRE_CANDIDATES.json']])]:
    p=D/name
    with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
        for src,key in items:z.write(src,key)
    with zipfile.ZipFile(p)as z:assert z.testzip()is None
    archives.append({'name':name,'bytes':p.stat().st_size,'sha256':sha(p),'entries':len(items)})
stats={}
for key in['unitEdges','rawSweepFragments','normalizedPartialPieces','splitUnitEdges','maxPiecesPerUnit','sourceBoundaryCrossings']:
    values=[r['incidence'][key]for r in audit['rows']if r['incidence']];stats[key]={'sum':sum(values),'min':min(values),'max':max(values),'mean':statistics.mean(values)}
times={}
for key in['exactOverlaySeconds','partialIncidenceSeconds','bindingSeconds','comparisonSeconds']:
    values=[r['stageSeconds'][key]for r in audit['rows']if key in r['stageSeconds']];times[key]={'poses':len(values),'sum':sum(values),'min':min(values),'max':max(values),'mean':statistics.mean(values)}
passed=audit['fullyBoundPoses']==81 and audit['fullComparablePairs']==80
out={'artifactIntegrityPassed':True,'phase0FullCorrespondencePassed':True,'fixtureCount':fixtures['testCount'],'all81CorrespondencePassed':passed,'fullyBoundPoses':audit['fullyBoundPoses'],'fullComparablePairs':audit['fullComparablePairs'],'unboundTargets':audit['unboundTargets'],'geometryEventPairs':audit['geometryEventPairs'],'costStatusCounts':audit['costStatusCounts'],'sourceInputsValidated':inputCount,'all81MaskHashesUnchanged':True,'all81ReparameterizedCanonicalInputIdentical':True,'partialRepresentationStats':stats,'offlineTimingSeconds':times,'phase0Costs':{k:phase0[k]for k in['partialConstructionSeconds','bindingSeconds','exactOverlaySecondsFromOriginal']},'timingScope':'Python exact-geometry offline diagnostic only. No real-time implementation or adoption claim.','runtimeUnchanged':runtime,'rayDiagnosticUnchanged':ray,'protectedSettings':settings,'frozen516517Sources':frozen,'sources':sources,'archives':archives,'newUnityCalls':0,'selectorRuns':0,'timeStateCostChanged':False,'coefficientChanged':False,'defaultOFF':True,'decision':'INCOMPLETE_OFFLINE_CORRESPONDENCE_NOT_ADOPTED','lastDirectUnityState':'RESTORED_LOOP514.json; no fresh live query in518','checks':['Phase0 both first cases and120/120 edges bound with centre incidence support','19 prior correspondence/structural fixtures preserved; exact canonical split/slide/start invariant','Whole unit lengths/cost arithmetic unchanged; added partial counts do not become new cost samples','243 stored input hashes and81 selected masks unchanged','All rejected/incomplete/event totals remain null rather than0/pass','First real rejection retains exact portion, candidate, direction and corridor evidence','Filter deletion counterexamples are diagnostic predicates only, no selector or production patch','516517 cost/state sources and actual project runtime/settings hashes unchanged','13 prototype/diagnostic sources parse; two evidence archives passCRC']}
(D/'VALIDATION518.json').write_text(json.dumps(out,indent=2,default=str)+'\n')
print(json.dumps({k:v for k,v in out.items()if k in['artifactIntegrityPassed','fullyBoundPoses','fullComparablePairs','unboundTargets','costStatusCounts','sourceInputsValidated','partialRepresentationStats','offlineTimingSeconds','decision']},default=str),flush=True)
