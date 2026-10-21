"""Rigid-transform fixtures test geometric dispatch, not screen exceptions."""
from pathlib import Path
import json,time,pickle,hashlib
import numpy as np
import active516 as G,face518 as F,edge518 as E,arc517 as A,arc519 as B,correspond519 as C
W=G.ROOT;D=W/'Region519';doc=json.loads((G.INPUT/'004_curves.json').read_text());rings=[[(p['x'],p['y'])for p in r['points']]for r in doc['curves']];mask=G.read_mask(4);original=json.loads((D/'004_MINIMUM.json').read_text());source=original['eventSamples'][0];edge=tuple(source['edge']);rows=[]
transforms=[('integer-translation',lambda x,y:(x+13,y+7),lambda x,y:(x+13,y+7)),('rotation90',lambda x,y:(272-y,x),lambda x,y:(271-y,x))]
for name,point,cell in transforms:
    begin=time.perf_counter();rr=[[point(x,y)for x,y in r]for r in rings];mm=np.zeros_like(mask)
    for y,x in zip(*mask.nonzero()):xx,yy=cell(int(x),int(y));assert 0<=xx<480 and 0<=yy<272;mm[yy,xx]=True
    m=F.mask_from_array(mm);o=F.Overlay(rr,m,F.auto_domain(rr,m),True);arcs,junctions=A.active_arcs(G.fragments(rr)[0]);assert not junctions;E.attach_exact_sources(arcs,o);corr=C.Correspondence(E.BoundaryIncidence(o),arcs);mappedEdge=tuple(point(*edge[:2]))+tuple(point(*edge[2:]));assert not corr.existing_candidates(mappedEdge),'The transformed test must still exercise the recovered branch'
    bindings,unsupported=B.bind(mm,arcs,corr);samples=[s for b in bindings.values()for s in b['samples']if s['edge']==mappedEdge];bound=sum(len(b['samples'])for b in bindings.values());count=len(G.boundary(mm));expected=np.array(point(*source['reference']));error=float(np.max(abs(np.array(samples[0]['reference'])-expected)))if len(samples)==1 else None
    passed=not unsupported and bound==count and len(samples)==1 and samples[0]['bindingRule']=='EXACT_ENDPOINT_PAIRED_LOCAL_CHAIN'and error<=A.EPS
    row={'fixture':name,'passed':passed,'boundEdges':bound,'inputEdges':count,'transformedEdge':mappedEdge,'originalAcceptedCandidateCount':0,'eventSample':samples,'expectedTransformedReference':expected.tolist(),'maximumReferenceError':error,'tolerance':'existing517 EPS1e-9, numeric geometry equality only','candidateCounts':corr.summary()['candidateCounts'],'seconds':time.perf_counter()-begin,'kind':'Synthetic rigid transform of stored geometry/mask, no new Unity pose/capture.'};rows.append(row);print(json.dumps(row,default=str),flush=True)
astSource='\n'.join((W/n).read_text()for n in['chain519.py','correspond519.py','arc519.py']);import ast;nodes=ast.parse(astSource);hardcoded=[n.value for n in ast.walk(nodes)if isinstance(n,ast.Constant)and isinstance(n.value,(int,float))and n.value in[208,209,52,53,.05,.0625]];assert not hardcoded
old=json.loads((D/'EagerV2/MINIMUM519.json').read_text());new=json.loads((D/'MINIMUM519.json').read_text());assert old['twoPoseCostCorrespondence']==new['twoPoseCostCorrespondence'];assert all(a['eventSamples']==b['eventSamples']for a,b in zip(old['rows'],new['rows']))
out={'passed':all(r['passed']for r in rows),'fixtures':rows,'algorithmHasNoEventCoordinateOrPhaseConstants':True,'lazyConstructionPreservesTwoPoseNumericCorrespondence':True,'newUnityCalls':0,'newMaskSelection':False,'scope':'Geometric condition generality on these fixtures, not all models/cameras or visual/runtime adoption.'}
(D/'GENERALITY519.json').write_text(json.dumps(out,indent=2,default=str)+'\n');print(json.dumps({'passed':out['passed'],'fixtures':[r['fixture']for r in rows],'coordinateOrPhaseExceptions':False,'lazyNumericEquality':True}))
