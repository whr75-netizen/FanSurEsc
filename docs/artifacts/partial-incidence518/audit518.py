"""One stored81 expansion AFTER phase0 and counterexample gates passed.

Geometry/incidence/cost audit only. No new selection, state, Unity or capture.
Unbound/uncomparable totals are NULL, never accepted as zero.
"""
from pathlib import Path
import os,json,pickle,time,hashlib,collections,traceback
import numpy as np
import active516 as G,arc517 as A,arc518 as B,face518 as F,edge518 as E,span517 as N
W=G.ROOT;R=G.INPUT;D=W/'Region518/PartialEdgeV2';FULL=D/'Stored81';FULL.mkdir(exist_ok=True)
assert json.loads((D/'PHASE0.json').read_text())['fullFirstPosePassed']
assert json.loads((D/'FIXTURES518.json').read_text())['passed']
with(FULL/'STARTED.json').open('x')as f:json.dump({'pid':os.getpid(),'startedEpoch':time.time(),'gate':'phase0 plus19fixtures passed','exactlyOneExpansion':True},f)
sourceHashes=[{'path':str(W/name),'sha256':hashlib.sha256((W/name).read_bytes()).hexdigest()}for name in['face518.py','edge518.py','arc518.py','audit518.py','span517.py','span516.py']]
rows=[];previous=None;start=time.perf_counter();failureCacheSaved=False
for i in range(81):
    begin=time.perf_counter();stages={};inputs=[];mask=G.read_mask(i);doc=json.loads((R/f'{i:03d}_curves.json').read_text());rings=[[(p['x'],p['y'])for p in r['points']]for r in doc['curves']]
    for ending in['_curves.json','_MASK.bin.gz','_ALT_projection.json']:
        p=R/f'{i:03d}{ending}';inputs.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    arcs=[];bindings={};unsupported=[];junctions=[];incidence=None;overlay=None;annotation=[]
    try:
        if i==0:
            with(D/'PHASE0.pickle').open('rb')as f:cached=pickle.load(f)
            overlay,arcs,incidence,bindings=cached['graph'],cached['arcs'],cached['incidence'],cached['bindings']
            stages={'overlayCacheReused':True,'originalOverlaySeconds':cached['result']['exactOverlaySecondsFromOriginal'],'originalPartialSeconds':cached['result']['partialConstructionSeconds'],'originalBindingSeconds':cached['result']['bindingSeconds']}
            annotation=cached['result']['exactSourceAnnotation']
        else:
            at=time.perf_counter();m=F.mask_from_array(mask);overlay=F.Overlay(rings,m,F.auto_domain(rings,m),True);stages['exactOverlaySeconds']=time.perf_counter()-at
            at=time.perf_counter();active=json.loads((W/'Temporal516'/f'{i:03d}_ACTIVE.json').read_text());arcs,junctions=A.active_arcs(active['active']);annotation=E.attach_exact_sources(arcs,overlay);incidence=E.BoundaryIncidence(overlay);stages['partialIncidenceSeconds']=time.perf_counter()-at
            at=time.perf_counter();bindings,unsupported=B.bind(mask,arcs,incidence);stages['bindingSeconds']=time.perf_counter()-at
    except Exception as exc:
        unsupported.append({'reason':'REPRESENTATION_EXCEPTION','type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()})
    bound=sum(len(b['samples'])for b in bindings.values());edges=len(G.boundary(mask));fullyBound=bound==edges and not unsupported and not junctions
    anchorFailures=[]
    if incidence:
        for b in bindings.values():
            for s in b['samples']:
                support=incidence.candidate_support(s['edge'],E.source_segment(arcs[s['arc']],s['segment']))
                if not support['accepted']:anchorFailures.append({'edge':s['edge'],'arc':s['arc'],'segment':s['segment'],'support':support})
    fullyBound=fullyBound and not anchorFailures
    variantChecks=[]
    from fractions import Fraction as Q
    for t in[Q(1,4),Q(3,4)]:
        rr=[]
        for ring in rings:
            q=[tuple(Q(float(v))for v in p)for p in ring];p=[]
            for a,b in zip(q,q[1:]+q[:1]):p.extend([a,F.point(a,b,t)])
            rr.append(p[len(p)//2:]+p[:len(p)//2])
        variantChecks.append(F.canonical_rings(rr)==F.canonical_rings(rings))
    result=None;cost=None;status='INITIAL_POSE';old516=None
    at=time.perf_counter()
    if previous is not None:
        legacy=json.loads((W/'Temporal517/SpanArcV2'/f'{i:03d}_AUDIT.json').read_text());old516=legacy['old516RawCost']
        if not fullyBound or not previous['fullyBound']:status='UNBOUND_NULL_TOTAL'
        else:
            try:
                result=N.compare(previous['arcs'],previous['bindings'],arcs,bindings,True)
                if not result['valid']:status='TRANSPORT_FAILED_NULL_TOTAL'
                elif result['geometryEventResets']:status='GEOMETRY_EVENT_PARTIAL_NULL_TOTAL'
                else:status='FULL_GEOMETRIC_CORRESPONDENCE';cost=result['raw']
            except Exception as exc:status='COST_EXCEPTION_NULL_TOTAL';result={'error':str(exc),'traceback':traceback.format_exc()}
    stages['comparisonSeconds']=time.perf_counter()-at
    row={'target':i,'phase':i/80,'fullyBound':fullyBound,'inputUnitEdges':edges,'boundUnitEdges':bound,'unsupported':unsupported,'junctionEvents':junctions,'centreAnchorFailures':anchorFailures,'incidence':incidence.summary()if incidence else None,'exactSourceAnnotation':annotation,'reparameterizedCanonicalInputIdentical':all(variantChecks),'costStatus':status,'comparableTotalRaw':cost,'costDetail':result,'legacy516RawFromExisting517Audit':old516,'stageSeconds':stages,'seconds':time.perf_counter()-begin,'sourceInputs':inputs,'maskUnchangedSHA256':hashlib.sha256(mask.tobytes()).hexdigest(),'selectorRuns':0,'newUnityCalls':0}
    (FULL/f'{i:03d}_AUDIT.json').write_text(json.dumps(row,indent=2,default=str)+'\n')
    if not fullyBound and not failureCacheSaved:
        with(FULL/'FIRST_UNBOUND.pickle').open('wb')as f:pickle.dump({'target':i,'graph':overlay,'arcs':arcs,'incidence':incidence,'bindings':bindings,'row':row},f)
        failureCacheSaved=True
    rows.append({k:v for k,v in row.items()if k not in['costDetail','sourceInputs']})
    state={'pid':os.getpid(),'state':'RUNNING','completedPoses':i+1,'fullyBoundPoses':sum(r['fullyBound']for r in rows),'unboundTargets':[r['target']for r in rows if not r['fullyBound']],'costStatusCounts':dict(collections.Counter(r['costStatus']for r in rows)),'lastTarget':i,'elapsedSeconds':time.perf_counter()-start}
    (FULL/'STATE.json').write_text(json.dumps(state,indent=2)+'\n')
    print(json.dumps({**state,'thisPoseSeconds':row['seconds'],'edges':[bound,edges],'firstFailure':unsupported[:1]},default=str),flush=True)
    previous={'arcs':arcs,'bindings':bindings,'fullyBound':fullyBound}
valid=[r for r in rows if r['costStatus']=='FULL_GEOMETRIC_CORRESPONDENCE']
out={'mode':'ONE_STORED81_PARTIAL_INCIDENCE_EXPANSION_AFTER_PHASE0_GATE','poses':len(rows),'fullyBoundPoses':sum(r['fullyBound']for r in rows),'unboundTargets':[r['target']for r in rows if not r['fullyBound']],'fullComparablePairs':len(valid),'geometryEventPairs':[r['target']for r in rows if r['costStatus']=='GEOMETRY_EVENT_PARTIAL_NULL_TOTAL'],'costStatusCounts':dict(collections.Counter(r['costStatus']for r in rows)),'sumComparableRaw':sum(r['comparableTotalRaw']for r in valid),'all81ReparameterizedCanonicalInputIdentical':all(r['reparameterizedCanonicalInputIdentical']for r in rows),'rows':rows,'seconds':time.perf_counter()-start,'sourceScripts':sourceHashes,'coefficientChanged':False,'timeStateCostChanged':False,'selectorRuns':0,'newUnityCalls':0,'maskChanged':False,'scopeLimits':['Geometric correspondence only; numeric cost is not visual improvement.','Exact overlay and rational subdivisions are offline audit work, not runtime implementation/performance.','Physical visibility of new516 donors remains unverified; topology events are not assumed occlusions.','Unbound, failed transport and incomplete event comparisons retain null total, never zero.','Unresolved516 state barrier, internal colour and packet upload performance are unchanged.']}
(FULL/'AUDIT518.json').write_text(json.dumps(out,indent=2,default=str)+'\n')
(FULL/'STATE.json').write_text(json.dumps({'pid':os.getpid(),'state':'COMPLETED','poses':len(rows),'fullyBoundPoses':out['fullyBoundPoses'],'fullComparablePairs':len(valid),'unboundTargets':out['unboundTargets'],'seconds':out['seconds']},indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items()if k not in['rows','sourceScripts','scopeLimits']},default=str),flush=True)
