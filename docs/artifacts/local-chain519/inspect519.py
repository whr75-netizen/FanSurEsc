"""Recover only the two requested poses; no stored81 expansion."""
from pathlib import Path
from fractions import Fraction as Q
import json,pickle,time,hashlib
import numpy as np
import active516 as G,face518 as F,edge518 as E,arc517 as A,chain519 as C
W=G.ROOT;D=W/'Region519';D.mkdir(exist_ok=True);rows=[]
for target in[4,5]:
    cache=D/f'{target:03d}_EXACT.pickle';begin=time.perf_counter()
    if cache.exists():
        with cache.open('rb')as f:s=pickle.load(f)
    elif target==4:
        with(W/'Region518/PartialEdgeV2/Stored81/FIRST_UNBOUND.pickle').open('rb')as f:s=pickle.load(f)
        with cache.open('wb')as f:pickle.dump(s,f)
    else:
        doc=json.loads((G.INPUT/f'{target:03d}_curves.json').read_text());rings=[[(p['x'],p['y'])for p in r['points']]for r in doc['curves']];mask=G.read_mask(target);m=F.mask_from_array(mask);o=F.Overlay(rings,m,F.auto_domain(rings,m),True);arcs,junctions=A.active_arcs(json.loads((W/'Temporal516'/f'{target:03d}_ACTIVE.json').read_text())['active']);E.attach_exact_sources(arcs,o);incidence=E.BoundaryIncidence(o);s={'target':target,'graph':o,'arcs':arcs,'incidence':incidence,'junctions':junctions}
        with cache.open('wb')as f:pickle.dump(s,f)
    loadSeconds=time.perf_counter()-begin;incidence,arcs=s['incidence'],s['arcs'];at=time.perf_counter();chains=C.LocalChains(incidence);chainSeconds=time.perf_counter()-at;missing=[]
    for li,loop in enumerate(A.pixel_loops(G.read_mask(target))):
        for edge in loop['edges']:
            p=np.array([(edge[0]+edge[2])*.5,(edge[1]+edge[3])*.5]);direction=np.array([edge[2]-edge[0],edge[3]-edge[1]]);ends=np.array([p-direction*.5,p+direction*.5]);eligible=[];legacy=[]
            for ai,arc in enumerate(arcs):
                a,d,ll=arc['p'],arc['d'],arc['length']**2;t=np.clip(((ends[:,None]-a)*d).sum(2)/ll,0,1);q=a+t[:,:,None]*d;dist=((ends[:,None]-q)**2).sum(2);dot=(direction*d).sum(1)
                for si in range(len(a)):
                    support=incidence.candidate_support(edge,E.source_segment(arc,si))
                    if support['accepted']:eligible.append({'arc':ai,'segment':si,'maxEndDistance2':float(dist[:,si].max()),'directionDot':float(dot[si]),'oldPass':bool(dist[:,si].max()<=2+A.EPS and dot[si]>=-A.EPS),'source':E.source_segment(arc,si)})
                    if support['accepted']and dist[:,si].max()<=2+A.EPS and dot[si]>=-A.EPS:legacy.append((ai,si))
            if not legacy:
                roots={r for p in incidence.at(edge,Q(1,2))for r in p['roots']};missing.append({'pixelLoop':li,'edge':edge,'parts':incidence.record(edge),'centreCandidates':sorted(eligible,key=lambda p:p['maxEndDistance2']),'changedBoundaryCycles':[chains.describe(root)for root in roots]})
    row={'target':target,'phase':target/80,'loadOrExactSeconds':loadSeconds,'chainConstructionSeconds':chainSeconds,'chains':chains.summary(),'missingCentreCandidateEdges':missing,'separatelyInspected':True,'newSelectorRuns':0,'newUnityCalls':0}
    (D/f'{target:03d}_INSPECT.json').write_text(json.dumps(row,indent=2,default=str)+'\n');rows.append(row)
    print(json.dumps({'target':target,'phase':target/80,'missing':[{'edge':p['edge'],'candidateSegments':[(q['segment'],q['maxEndDistance2'],q['directionDot'])for q in p['centreCandidates']],'cycles':[{'root':c['root'],'tag':c['tag'],'cycles':c['cycles']}for c in p['changedBoundaryCycles']]}for p in missing],'chains':chains.summary(),'chainSeconds':chainSeconds},default=str),flush=True)
