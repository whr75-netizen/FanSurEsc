"""One81-pose DIFFERENTIAL audit, with explicit proven-branch reuse.

This is not81 fresh exact-overlay computations.79 old fully-bound branches
are reused only after AST/input/evidence equality gates.Changed two poses and
three incident comparisons are current519; neighbours cross-check the replay.
No all-loop cost is fabricated across unavailable geometry-event priors.
"""
from pathlib import Path
import json,pickle,time,hashlib,zipfile,collections,os
import active516 as G,face518 as F,edge518 as E,arc517 as A,arc518 as OLD,arc519 as NEW,correspond519 as C,span517 as N
W=G.ROOT;D=W/'Region519';FULL=D/'Stored81';FULL.mkdir(exist_ok=True);BASE=W/'Region518/PartialEdgeV2/Stored81';P=Path('C:/Users/JG/Documents/work/Fantasy Survival Escape Game');ART=P/'docs/artifacts/partial-incidence518';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((D/'BRANCH_EQUIVALENCE519.json').read_text());minimum=json.loads((D/'MINIMUM519.json').read_text());generic=json.loads((D/'GENERALITY519.json').read_text());assert proof['passed']and minimum['minimumPassed']and generic['passed']
for r in proof['sources']:assert sha(W/r['name'])==r['sha256']
with(FULL/'STARTED.json').open('x')as f:json.dump({'pid':os.getpid(),'mode':'DIFFERENTIAL_PROVEN_BRANCH_REPLAY','startedEpoch':time.time()},f)
start=time.perf_counter();manifest=json.loads((ART/'manifest.json').read_text());fileManifest={r['name']:r for r in manifest}
for name in['AUDIT518.json','ALL81_AUDITS518.zip','VALIDATION518.json']:
    assert sha(ART/name)==fileManifest[name]['sha256'];assert sha((BASE/name)if name=='AUDIT518.json'else BASE.parent/name)==fileManifest[name]['sha256']
baseline=json.loads((BASE/'AUDIT518.json').read_text());assert baseline['poses']==81
for r in baseline['sourceScripts']:assert sha(Path(r['path']))==r['sha256']
oldRows=[];sourceInputs=[]
with zipfile.ZipFile(ART/'ALL81_AUDITS518.zip')as z:
    assert z.testzip()is None
    for i in range(81):
        data=z.read(f'{i:03d}_AUDIT.json');assert data==(BASE/f'{i:03d}_AUDIT.json').read_bytes();row=json.loads(data)
        for r in row['sourceInputs']:assert sha(Path(r['path']))==r['sha256'];sourceInputs.append(r)
        assert hashlib.sha256(G.read_mask(i).tobytes()).hexdigest()==row['maskUnchangedSHA256'];oldRows.append(row)
changed=baseline['unboundTargets'];assert changed==minimum['targets'];events=json.loads((D/'GEOMETRY_EVENT_INTERVALS519.json').read_text());eventByTarget={r['target']:r for r in events['rows']};assert sorted(eventByTarget)==baseline['geometryEventPairs']
states={};changedReceipts=[]
for i in changed:
    with(D/f'{i:03d}_BOUND.pickle').open('rb')as f:s=pickle.load(f)
    current=json.loads((G.INPUT/f'{i:03d}_curves.json').read_text());rings=[[(p['x'],p['y'])for p in r['points']]for r in current['curves']]
    assert s['row']['fullyBound']and s['correspondence'].incidence.overlay.rings==F.canonical_rings(rings);assert s['correspondence'].incidence.overlay.mask==F.mask_from_array(G.read_mask(i));states[i]=(s['arcs'],s['bindings']);changedReceipts.append({'target':i,'mode':'CURRENT519_CHANGED_POSE_MINIMUM_CACHE','sourceMinimumSHA256':sha(D/f'{i:03d}_MINIMUM.json'),'boundEdges':s['row']['boundEdges'],'candidateCounts':s['row']['complexity']['candidateCounts']})
neighbours=sorted({j for i in changed for j in[i-1,i+1]if 0<=j<81 and j not in changed});neighbourChecks=[]
def strip(value):
    if isinstance(value,dict):return{k:strip(v)for k,v in value.items()if k!='bindingRule'}
    if isinstance(value,list):return[strip(v)for v in value]
    if isinstance(value,tuple):return tuple(strip(v)for v in value)
    return value
for i in neighbours:
    begin=time.perf_counter();doc=json.loads((G.INPUT/f'{i:03d}_curves.json').read_text());rings=[[(p['x'],p['y'])for p in r['points']]for r in doc['curves']];mask=G.read_mask(i);m=F.mask_from_array(mask);o=F.Overlay(rings,m,F.auto_domain(rings,m),True);arcs,junctions=A.active_arcs(json.loads((W/'Temporal516'/f'{i:03d}_ACTIVE.json').read_text())['active']);assert not junctions;E.attach_exact_sources(arcs,o);incidence=E.BoundaryIncidence(o)
    old,oldFailures=OLD.bind(mask,arcs,incidence);corr=C.Correspondence(incidence,arcs);new,newFailures=NEW.bind(mask,arcs,corr);assert not oldFailures and not newFailures;assert strip(old)==strip(new);assert corr.chains is None
    states[i]=(arcs,new);record={'target':i,'mode':'DIRECT_OLD_NEW_BINDER_CROSS_CHECK','semanticBindingsIdentical':True,'newChainConstructed':False,'boundEdges':sum(len(b['samples'])for b in new.values()),'seconds':time.perf_counter()-begin};neighbourChecks.append(record);print(json.dumps(record),flush=True)
changedPairs=sorted({j for i in changed for j in[i,i+1]if 0<j<81});fresh={}
for i in changedPairs:
    value=N.compare(states[i-1][0],states[i-1][1],states[i][0],states[i][1],True);assert value['valid']and not value['geometryEventResets'];fresh[i]=value
    print(json.dumps({'currentPair':[i-1,i],'rawComparableDiagnostic':value['raw'],'fullyComparable':True}),flush=True)
rows=[];interval=0
for i,old in enumerate(oldRows):
    if i in eventByTarget:interval+=1
    mode='CURRENT519_CHANGED_POSE_MINIMUM_CACHE'if i in changed else'DIRECT_OLD_NEW_BINDER_CROSS_CHECK'if i in neighbours else'PROVEN_UNCHANGED_ACCEPTED_BRANCH_REPLAY'
    bound=old['fullyBound']or i in changed;assert bound
    cost=None;detail=None;event=None
    if i==0:status='INITIAL_NO_PRIOR'
    elif i in eventByTarget:status='GEOMETRY_INTERVAL_END_RESTART';event=eventByTarget[i];assert event['fullTransitionCost']is None
    elif i in fresh:status='CURRENT519_COMPARABLE_PAIR';detail=fresh[i];cost=detail['raw']
    else:
        assert old['costStatus']=='FULL_GEOMETRIC_CORRESPONDENCE';status='PROVEN_UNCHANGED_COMPARABLE_PAIR_REPLAY';cost=old['comparableTotalRaw'];detail=old['costDetail']
    row={'target':i,'phase':i/80,'poseEvaluationMode':mode,'fullyBound':True,'boundUnitEdges':old['inputUnitEdges'],'inputUnitEdges':old['inputUnitEdges'],'newChainEvaluated':i in changed,'bindingNumericEqualityBasis':'current519 minimum'if i in changed else'AST-equivalent accepted candidate/link/DP and verified unchanged inputs','costStatus':status,'comparablePairRaw':cost,'costDetail':detail,'geometryEventInterval':event,'reportingInterval':interval,'source518RowSHA256':sha(BASE/f'{i:03d}_AUDIT.json'),'sourceInputs':old['sourceInputs'],'maskUnchangedSHA256':old['maskUnchangedSHA256'],'newUnityCalls':0,'selectorRuns':0}
    if status in['INITIAL_NO_PRIOR','GEOMETRY_INTERVAL_END_RESTART']:assert cost is None
    (FULL/f'{i:03d}_AUDIT.json').write_text(json.dumps(row,indent=2,default=str)+'\n');rows.append({k:v for k,v in row.items()if k not in['costDetail','sourceInputs']})
intervals=[]
for k in range(interval+1):
    rr=[r for r in rows if r['reportingInterval']==k];intervals.append({'id':k,'firstTarget':rr[0]['target'],'lastTarget':rr[-1]['target'],'availablePairTargets':[r['target']for r in rr if r['comparablePairRaw']is not None],'perPairCosts':[{'target':r['target'],'raw':r['comparablePairRaw']}for r in rr if r['comparablePairRaw']is not None],'intervalAggregateCost':None,'startPrior':'INITIAL_UNAVAILABLE'if k==0 else'CHANGED_GEOMETRY_COMPONENT_PRIOR_UNAVAILABLE'})
out={'mode':'ONE_STORED81_DIFFERENTIAL_CORRESPONDENCE_AUDIT_WITH_PROVEN_REPLAY','poses':81,'fullyBoundPoses':81,'comparablePairs':sum(r['comparablePairRaw']is not None for r in rows),'geometryEventPairs':sorted(eventByTarget),'changedPoseTargets':changed,'directNeighbourCrossChecks':neighbourChecks,'changedPoseReceipts':changedReceipts,'freshPairTargets':changedPairs,'unchangedPoseBranchProof':'BRANCH_EQUIVALENCE519.json','poseEvaluationModeCounts':dict(collections.Counter(r['poseEvaluationMode']for r in rows)),'costStatusCounts':dict(collections.Counter(r['costStatus']for r in rows)),'rows':rows,'reportingIntervals':intervals,'allLoopAggregateTemporalCost':None,'aggregateReason':'Six geometric interval boundaries have no full prior. No all-loop cost, improvement score or zero event cost is fabricated.','sourceInputsValidated':len(sourceInputs),'all81MasksUnchanged':True,'canonicalReparameterizationReceipt':'All81 exact canonical inputs unchanged in518; geometry/selection not changed by519.','newUnityCalls':0,'selectorRuns':0,'coefficientChanged':False,'temporalStateCostChanged':False,'defaultOFF':True,'seconds':time.perf_counter()-start,'not81FreshOverlayComputations':True,'sources':proof['sources'],'decision':'STORED_CORRESPONDENCE_GATE_PASSED_WITH_EXPLICIT_GEOMETRY_EVENTS_ONLY','limits':['77 poses are proven-branch replay,2 neighbours directly cross-checked,2 changed poses reused from the current519 minimum run.','No new temporal selector, state-barrier repair, physical donor visibility or animation quality pass.','Exact geometry and local-chain work is offline diagnosis, not realtime implementation.']}
(FULL/'AUDIT519.json').write_text(json.dumps(out,indent=2,default=str)+'\n');(FULL/'STATE.json').write_text(json.dumps({'state':'COMPLETED','poses':81,'fullyBoundPoses':81,'comparablePairs':out['comparablePairs'],'geometryEventPairs':sorted(eventByTarget),'allLoopAggregateTemporalCost':None,'seconds':out['seconds']},indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in['rows','reportingIntervals','sources','limits','changedPoseReceipts','directNeighbourCrossChecks']},default=str),flush=True)
