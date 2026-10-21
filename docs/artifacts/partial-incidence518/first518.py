from pathlib import Path
import json,time,pickle,hashlib
import active516 as G,arc517 as A,arc518 as B,face518 as F
W=G.ROOT;D=W/'Region518';R=G.INPUT
minimum=json.loads((D/'MINIMUM518.json').read_text());assert minimum['minimumPassed']and all(t['passed']for t in minimum['fixtures'])
start=time.perf_counter();doc=json.loads((R/'000_curves.json').read_text());rings=[[(p['x'],p['y'])for p in r['points']]for r in doc['curves']];mask=G.read_mask(0);m=F.mask_from_array(mask)
o=F.Overlay(rings,m,F.auto_domain(rings,m),True);graphSeconds=time.perf_counter()-start
arcs,junctions=A.active_arcs(json.loads((W/'Temporal516/000_ACTIVE.json').read_text())['active']);bindings,unsupported=B.bind(mask,arcs,o)
edges=len(G.boundary(mask));bound=sum(len(v['samples'])for v in bindings.values());result={'minimumGatePassed':True,'target':0,'wholeGraphSeconds':graphSeconds,'totalSeconds':time.perf_counter()-start,'graph':o.summary(),'boundEdges':bound,'inputEdges':edges,'unsupported':unsupported,'fullFirstPosePassed':bound==edges and not unsupported,'maskSHA256':hashlib.sha256(mask.tobytes()).hexdigest(),'curveSHA256':hashlib.sha256((R/'000_curves.json').read_bytes()).hexdigest(),'newMaskChosen':False,'selectorRuns':0,'newUnityCalls':0}
(D/'FIRST_FULL518.json').write_text(json.dumps(result,indent=2,default=str)+'\n')
with(D/'FIRST_FULL518.pickle').open('wb')as f:pickle.dump({'graph':o,'arcs':arcs,'bindings':bindings,'unsupported':unsupported,'result':result},f)
print(json.dumps({k:v for k,v in result.items()if k!='graph'},ensure_ascii=False))
