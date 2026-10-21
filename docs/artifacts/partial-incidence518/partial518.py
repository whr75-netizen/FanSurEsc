"""Phase0 gate only. Reuse cached exact overlay; no 81-pose audit here."""
from pathlib import Path
import json,pickle,time,hashlib
import active516 as G,arc518 as B,edge518 as E

W=G.ROOT;D=W/'Region518/PartialEdgeV2';D.mkdir(exist_ok=True)
start=time.perf_counter()
with(W/'Region518/FIRST_FULL518.pickle').open('rb')as f:old=pickle.load(f)
mask=G.read_mask(0);assert hashlib.sha256(mask.tobytes()).hexdigest()==old['result']['maskSHA256']
assert hashlib.sha256((G.INPUT/'000_curves.json').read_bytes()).hexdigest()==old['result']['curveSHA256']
overlay,arcs=old['graph'],old['arcs'];begin=time.perf_counter();exactSources=E.attach_exact_sources(arcs,overlay);incidence=E.BoundaryIncidence(overlay);splitSeconds=time.perf_counter()-begin
cases=[]
for ea,eb in[((218,56,218,55),(218,55,217,55)),((209,53,209,52),(209,52,208,52))]:
    relation=incidence.relate(ea,eb,None)
    assert relation['boundaryPathJoin'],relation
    cases.append({'edges':[ea,eb],'pieces':[incidence.record(ea),incidence.record(eb)],'relation':relation})
begin=time.perf_counter();bindings,unsupported=B.bind(mask,arcs,incidence);bindSeconds=time.perf_counter()-begin
bound=sum(len(v['samples'])for v in bindings.values());edges=old['result']['inputEdges'];samples=[s for b in bindings.values()for s in b['samples']]
anchorFailures=[]
for s in samples:
    arc=arcs[s['arc']];i=s['segment'];support=incidence.candidate_support(s['edge'],E.source_segment(arc,i))
    if not support['accepted']:anchorFailures.append({'edge':s['edge'],'arc':s['arc'],'segment':i,'support':support})
out={'phase':0,'unitEdges':edges,'boundEdges':bound,'unsupported':unsupported,'centreAnchorFailures':anchorFailures,'fullFirstPosePassed':bound==edges and not unsupported and not anchorFailures,'exactSourceAnnotation':exactSources,'incidence':incidence.summary(),'partialConstructionSeconds':splitSeconds,'bindingSeconds':bindSeconds,'seconds':time.perf_counter()-start,'exactOverlaySecondsFromOriginal':old['result']['wholeGraphSeconds'],'cases':cases,'selectorRuns':0,'newUnityCalls':0,'editCostPerUnitUnchanged':True,'maskSHA256':old['result']['maskSHA256'],'curveSHA256':old['result']['curveSHA256']}
(D/'PHASE0.json').write_text(json.dumps(out,indent=2,default=str)+'\n')
with(D/'PHASE0.pickle').open('wb')as f:pickle.dump({'graph':overlay,'arcs':arcs,'incidence':incidence,'bindings':bindings,'unsupported':unsupported,'result':out},f)
print(json.dumps({k:v for k,v in out.items()if k not in['cases','centreAnchorFailures']},default=str),flush=True)
print(json.dumps({'centreAnchorFailureCount':len(anchorFailures),'firstAnchorFailure':anchorFailures[:1]},default=str),flush=True)
