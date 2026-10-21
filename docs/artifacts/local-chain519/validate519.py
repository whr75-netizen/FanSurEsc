from pathlib import Path
import json,hashlib,ast,zipfile
import active516 as G
W=G.ROOT;D=W/'Region519';FULL=D/'Stored81';P=Path('C:/Users/JG/Documents/work/Fantasy Survival Escape Game');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((FULL/'AUDIT519.json').read_text());p=json.loads((D/'BRANCH_EQUIVALENCE519.json').read_text());m=json.loads((D/'MINIMUM519.json').read_text());g=json.loads((D/'GENERALITY519.json').read_text());events=json.loads((D/'GEOMETRY_EVENT_INTERVALS519.json').read_text());assert a['poses']==81 and a['fullyBoundPoses']==81 and a['comparablePairs']==74 and p['passed']and m['minimumPassed']and g['passed'];assert a['allLoopAggregateTemporalCost']is None
for r in p['sources']:assert sha(W/r['name'])==r['sha256']
counts={};inputs=0
for i in range(81):
    row=json.loads((FULL/f'{i:03d}_AUDIT.json').read_text());assert row['target']==i and row['fullyBound']and row['boundUnitEdges']==row['inputUnitEdges'];assert row['selectorRuns']==row['newUnityCalls']==0
    for r in row['sourceInputs']:assert sha(Path(r['path']))==r['sha256'];inputs+=1
    assert hashlib.sha256(G.read_mask(i).tobytes()).hexdigest()==row['maskUnchangedSHA256'];assert sha(W/'Region518/PartialEdgeV2/Stored81'/f'{i:03d}_AUDIT.json')==row['source518RowSHA256']
    if i in a['geometryEventPairs']:assert row['comparablePairRaw']is None and row['geometryEventInterval']['currentPosePriorStatus']=='UNAVAILABLE_FOR_CHANGED_COMPONENTS'
    elif i:assert row['comparablePairRaw']is not None and row['costDetail']['valid']and not row['costDetail']['geometryEventResets']
    else:assert row['comparablePairRaw']is None
    counts[row['poseEvaluationMode']]=counts.get(row['poseEvaluationMode'],0)+1
assert counts==a['poseEvaluationModeCounts']and len(events['rows'])==6
baselineValidation=json.loads((W/'Region518/PartialEdgeV2/VALIDATION518.json').read_text());runtime=baselineValidation['runtimeUnchanged'];settings=baselineValidation['protectedSettings']
for r in runtime:assert sha(P/r['path'])==r['after']
for rel,h in settings.items():assert sha(P/rel)==h
for r in baselineValidation['frozen516517Sources']:assert sha(Path(r['path']))==r['sha256']
sources=[]
for name in['chain519.py','correspond519.py','arc519.py','inspect519.py','minimum519.py','events519.py','equivalence519.py','generic519.py','audit519.py','validate519.py']:
    src=W/name;ast.parse(src.read_text());sources.append({'name':name,'sha256':sha(src),'bytes':src.stat().st_size})
archives=[]
for name,files in[
    ('ALL81_DIFFERENTIAL_AUDITS519.zip',[(f,f.name)for f in sorted(FULL.glob('*_AUDIT.json'))]),
    ('REJECTED_ALL_PAIRED_V1_519.zip',[(f,f.name)for f in sorted((D/'AllPairedV1').iterdir())if f.is_file()]),
    ('EAGER_V2_CHECKPOINT519.zip',[(f,f.name)for f in sorted((D/'EagerV2').iterdir())if f.is_file()])]:
    dest=D/name
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
        for src,key in files:z.write(src,key)
    with zipfile.ZipFile(dest)as z:assert z.testzip()is None
    archives.append({'name':name,'bytes':dest.stat().st_size,'sha256':sha(dest),'entries':len(files)})
out={'artifactIntegrityPassed':True,'stored81CorrespondenceGatePassed':True,'fullyBoundPoses':81,'comparablePairs':74,'geometryEventPairs':a['geometryEventPairs'],'allLoopAggregateTemporalCost':None,'poseEvaluationModes':counts,'not81FreshOverlayComputations':True,'freshPairTargets':a['freshPairTargets'],'freshPairCosts':[{'target':i,'raw':json.loads((FULL/f'{i:03d}_AUDIT.json').read_text())['comparablePairRaw']}for i in a['freshPairTargets']],'inputsValidated':inputs,'sourceInputsAndMasksUnchanged':True,'generalConditionChecks':{'acceptedBranchASTEquality':p['passed'],'integerTranslation':g['fixtures'][0]['passed'],'rotation90':g['fixtures'][1]['passed'],'oppositeBoundaryRejected':m['oppositeBoundaryCounterexample']['passed'],'noEventCoordinateOrPhaseConstants':g['algorithmHasNoEventCoordinateOrPhaseConstants'],'lazyCorrespondenceNumericUnchanged':g['lazyConstructionPreservesTwoPoseNumericCorrespondence']},'sources':sources,'runtimeUnchanged':runtime,'protectedSettings':settings,'archives':archives,'selectorRuns':0,'newUnityCalls':0,'coefficientChanged':False,'timeStateCostChanged':False,'defaultOFF':True,'lastDirectUnityState':'RESTORED_LOOP514.json; no new live call in519','decision':'OFFLINE_CORRESPONDENCE_GATE_ONLY_PRODUCT_NOT_ADOPTED','checks':['All81 input poses accounted for with explicit evaluation mode and unchanged source hashes','79 accepted branches proven identical;2 directly cross-checked;2 changed poses current minimum','All74 comparable pairs retained separately;6 geometric interval boundaries and initial prior remain null','No global temporal cost fabricated across unavailable priors','Two source-chain recoveries separately inspected; no coordinate/phase rule in correspondence algorithm','Integer translation,90rotation and opposite-boundary counterexample distinguish general geometry from screen cases','No selector/state/weight or actual project runtime/settings changes','Ten new Python sources parse; three source/evidence archives passCRC'],'remaining':['Stationary shape locking/temporal state barrier remains unchanged and unvalidated by this correspondence gate','No new temporal-selected output or actual Unity animation capture; donor visibility/internal colour/native-world/packet cost unresolved','General multi-run and unanchored-ribbon correspondence has not been globally replaced; existing valid518 candidates are retained','All geometry and timings here are offline diagnostics, not realtime adoption']}
(D/'VALIDATION519.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k in['artifactIntegrityPassed','fullyBoundPoses','comparablePairs','geometryEventPairs','allLoopAggregateTemporalCost','poseEvaluationModes','freshPairCosts','inputsValidated','decision']},ensure_ascii=False),flush=True)
