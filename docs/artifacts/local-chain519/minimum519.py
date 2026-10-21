"""Two real poses and the opposite-branch gate BEFORE any full81 audit."""
from pathlib import Path
import pickle,json,time,hashlib
import numpy as np
import active516 as G,arc517 as A,face518 as F,edge518 as E,correspond519 as C,arc519 as B,span517 as N
W=G.ROOT;D=W/'Region519';rows=[];states=[];start=time.perf_counter()
for target in[4,5]:
    with(D/f'{target:03d}_EXACT.pickle').open('rb')as f:cached=pickle.load(f)
    mask=G.read_mask(target);arcs=cached['arcs'];begin=time.perf_counter();correspondence=C.Correspondence(cached['incidence'],arcs);construction=time.perf_counter()-begin
    begin=time.perf_counter();bindings,unsupported=B.bind(mask,arcs,correspondence);bindingSeconds=time.perf_counter()-begin;bound=sum(len(b['samples'])for b in bindings.values());edges=len(G.boundary(mask));eventEdge=(209,53,208,53);eventSamples=[s for b in bindings.values()for s in b['samples']if s['edge']==eventEdge]
    passed=bound==edges and not unsupported and len(eventSamples)==1 and eventSamples[0]['bindingRule']=='EXACT_ENDPOINT_PAIRED_LOCAL_CHAIN'
    row={'target':target,'phase':target/80,'fullyBound':passed,'inputEdges':edges,'boundEdges':bound,'unsupported':unsupported,'eventSamples':eventSamples,'complexity':correspondence.summary(),'constructionSeconds':construction,'bindingSeconds':bindingSeconds,'maskSHA256':hashlib.sha256(mask.tobytes()).hexdigest(),'newSelectorRuns':0,'newUnityCalls':0}
    (D/f'{target:03d}_MINIMUM.json').write_text(json.dumps(row,indent=2,default=str)+'\n')
    with(D/f'{target:03d}_BOUND.pickle').open('wb')as f:pickle.dump({'arcs':arcs,'bindings':bindings,'correspondence':correspondence,'row':row},f)
    rows.append(row);states.append((arcs,bindings))
    print(json.dumps({'target':target,'fullyBound':passed,'edges':[bound,edges],'unsupported':unsupported,'eventSamples':eventSamples,'complexity':correspondence.summary(),'constructionSeconds':construction,'bindingSeconds':bindingSeconds},default=str),flush=True)

def rect(a,b,c,d):return[(a,b),(c,b),(c,d),(a,d)]
def synthetic(rings,mask):
    m=F.mask_from_array(mask);o=F.Overlay(rings,m,F.auto_domain(rings,m),True);arcs,junction=A.active_arcs(G.fragments(rings)[0]);assert not junction;E.attach_exact_sources(arcs,o);return C.Correspondence(E.BoundaryIncidence(o),arcs),arcs
ring=rect(2.25,2.25,7.75,5.75);m=np.zeros((10,12),bool);m[2:6,2:8]=True;c,arcs=synthetic([ring],m);edge=(3,2,4,2);local=c.local(edge);candidates=c.candidates(edge);opposite=[]
for s in candidates:
    a,b=E.source_segment(arcs[s['arc']],s['segment'])
    if float(a[1])==float(b[1])==5.75:opposite.append(s)
assert not local and candidates and not opposite
far={'name':'same-added-ribbon-opposite-boundary-not-admitted','passed':True,'localChainStatus':'UNANCHORED_CLOSED_RIBBON_NO_CROSSING_PAIR','localCandidates':local,'existingGeometryCandidates':candidates,'oppositeCandidates':opposite,'scope':'This keeps the518 rule on unanchored boundaries; it does not claim a new pure-closed-ribbon map.'}

# The actual two runs have identical exact crossing endpoints.  The mapping
# stays on their one source chain, whose order is defined independently of
# whole-unit tangent or a nearest-branch search.
pairChecks=[]
for target in[4,5]:
    with(D/f'{target:03d}_BOUND.pickle').open('rb')as f:s=pickle.load(f)
    corr=s['correspondence'];sample=s['row']['eventSamples'][0]if s['row']['eventSamples']else None
    if sample:
        pair=corr.pairs[sample['chain']['pair']];p=pair['pixel'];q=pair['source'];assert p[0]['a']==q[0]['a']and p[-1]['b']==q[-1]['b'];pairChecks.append({'target':target,'endpointsExactEqual':True,'uniquePixelRun':True,'uniqueSourceRun':True,'sourceSegmentsInOrder':[corr.source_owner(e)for e in q]})

comparison=N.compare(states[0][0],states[0][1],states[1][0],states[1][1],True)if all(r['fullyBound']for r in rows)else None
comparisonPassed=comparison is not None and comparison['valid']and not comparison['geometryEventResets'];passed=all(r['fullyBound']for r in rows)and far['passed']and comparisonPassed
out={'minimumPassed':passed,'targets':[4,5],'rows':rows,'oppositeBoundaryCounterexample':far,'exactPairedRunChecks':pairChecks,'twoPoseCostCorrespondence':comparison,'twoPoseCostComparable':comparisonPassed,'all81AuditStarted':False,'coefficientOrStateCostChanged':False,'maskChanged':False,'newUnityCalls':0,'seconds':time.perf_counter()-start,'scope':'Offline correspondence gate, not temporal selection, animation quality or realtime pass.'}
(D/'MINIMUM519.json').write_text(json.dumps(out,indent=2,default=str)+'\n');print(json.dumps({'minimumPassed':passed,'oppositeBoundaryCounterexamplePassed':far['passed'],'twoPoseCostComparable':comparisonPassed,'rawComparableDiagnostic':comparison['raw']if comparisonPassed else None,'seconds':out['seconds']},default=str),flush=True)
