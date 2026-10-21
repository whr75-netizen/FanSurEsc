"""Rebind the existing stationary516 counterexample with frozen519 rules.

No state-cost change is accepted before the real two-drawing precondition is
known. Geometry support here does not certify novel-pixel physical visibility.
"""
from pathlib import Path
import json,pickle,time,hashlib
import numpy as np
import active516 as G,select516 as S,face518 as F,edge518 as E,arc517 as A,arc519 as B,correspond519 as C,span517 as N
W=G.ROOT;D=W/'State520';D.mkdir(exist_ok=True);i=80;start=time.perf_counter();doc=json.loads((G.INPUT/f'{i:03d}_curves.json').read_text());rings=[[(p['x'],p['y'])for p in r['points']]for r in doc['curves']];arcs,junctions=A.active_arcs(json.loads((W/'Temporal516'/f'{i:03d}_ACTIVE.json').read_text())['active']);assert not junctions;bounds,area=S.areas(i);rows=[];states={}
for name,path in[('current-static',None),('past-held516',W/'Temporal516/eta-1.0/080.npy')]:
    begin=time.perf_counter();mask=G.read_mask(i)if path is None else np.load(path);m=F.mask_from_array(mask);o=F.Overlay(rings,m,F.auto_domain(rings,m),True);E.attach_exact_sources(arcs,o);incidence=E.BoundaryIncidence(o);corr=C.Correspondence(incidence,arcs);bindings,unsupported=B.bind(mask,arcs,corr);bound=sum(len(v['samples'])for v in bindings.values());edges=len(G.boundary(mask));fullyBound=bound==edges and not unsupported;row={'drawing':name,'boundEdges':bound,'inputEdges':edges,'fullyBound':fullyBound,'unsupported':unsupported,'spatial':S.spatial(mask,area,bounds),'stairRhythm':S.loop_quality(mask),'chainSummary':corr.summary(),'maskSHA256':hashlib.sha256(mask.tobytes()).hexdigest(),'seconds':time.perf_counter()-begin,'physicalNovelFillVisibility':'UNVERIFIED'}
    rows.append(row);states[name]={'arcs':arcs,'bindings':bindings,'mask':mask,'row':row,'corr':corr}
    with(D/(name+'.pickle')).open('wb')as f:pickle.dump(states[name],f)
    print(json.dumps(row,default=str),flush=True)
good,bad=states['current-static'],states['past-held516'];forward=N.compare(bad['arcs'],bad['bindings'],good['arcs'],good['bindings'],True)if all(r['fullyBound']for r in rows)else None;backward=N.compare(good['arcs'],good['bindings'],bad['arcs'],bad['bindings'],True)if forward is not None else None;passed=forward is not None and forward['valid']and not forward['geometryEventResets']and backward['valid']and not backward['geometryEventResets']
out={'stationaryCurrentGeometryTarget':i,'preconditionPassed':passed,'rows':rows,'differentCells':int((good['mask']!=bad['mask']).sum()),'recoverRaw519':forward['raw']if passed else None,'reverseRaw519':backward['raw']if passed else None,'recoverDetail':forward,'reverseDetail':backward,'old516Cost42IsNotAssumed519Cost':True,'newStateCostImplemented':False,'coefficientChanged':False,'newUnityCalls':0,'selectorRuns':0,'seconds':time.perf_counter()-start}
(D/'PREFLIGHT520.json').write_text(json.dumps(out,indent=2,default=str)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in['rows','recoverDetail','reverseDetail']},default=str),flush=True)
