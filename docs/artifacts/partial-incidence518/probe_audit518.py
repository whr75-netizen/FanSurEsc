"""Inspect the first stored81 rejection. Does not modify the running audit."""
from fractions import Fraction as Q
import json,pickle
import numpy as np
import active516 as G,arc517 as A,edge518 as E
D=G.ROOT/'Region518/PartialEdgeV2/Stored81'
with(D/'FIRST_UNBOUND.pickle').open('rb')as f:c=pickle.load(f)
r,arcs=c['incidence'],c['arcs'];o=r.overlay;rows=[]
for li,loop in enumerate(A.pixel_loops(G.read_mask(c['target']))):
    for e in loop['edges']:
        p=np.array([(e[0]+e[2])*.5,(e[1]+e[3])*.5]);direction=np.array([e[2]-e[0],e[3]-e[1]]);candidates=[]
        for ai,arc in enumerate(arcs):
            a,d,ll=arc['p'],arc['d'],arc['length']**2;ends=np.array([p-direction*.5,p+direction*.5]);t=np.clip(((ends[:,None]-a)*d).sum(2)/ll,0,1);q=a+t[:,:,None]*d;dist=((ends[:,None]-q)**2).sum(2);ok=(dist.max(0)<=2+A.EPS)&((direction*d).sum(1)>=-A.EPS)
            for si in np.where(ok)[0]:
                segment=E.source_segment(arc,int(si));support=r.candidate_support(e,segment)
                candidates.append({'arc':ai,'segment':int(si),'sourceExact':segment,'sourceFloat':[a[si].tolist(),arc['b'][si].tolist()],'fit':float(dist[:,si].mean()),'wholeEdgeOwners':sorted(o.candidate_components(e,segment)),'support':support})
        if not any(s['support']['accepted']for s in candidates):
            roots={root for p in r.at(e,Q(1,2))for root in p['roots']};ownerSources=[]
            for root in roots:
                comp=o.components[root];records=[]
                for s in comp['sourceBoundary']:
                    av,bv=np.array(s['a'],float),np.array(s['b'],float);dv=bv-av;length2=float(dv@dv)
                    tt=np.clip(((ends-av)*dv).sum(1)/length2,0,1);dd=((ends-(av+tt[:,None]*dv))**2).sum(1)
                    records.append({'a':s['a'],'b':s['b'],'sourceIds':s['sourceIds'],'directionDot':float(direction@dv),'maxEndDistance2':float(dd.max())})
                ownerSources.append({'component':root,'tag':comp['tag'],'cells':sorted(comp['cells']),'sourceRegions':sorted(comp['sourceRegions']),'selectedRegions':sorted(comp['selectedRegions']),'sourceBoundary':records})
            rows.append({'pixelLoop':li,'edge':e,'pieces':r.record(e),'geometricCandidatesBeforeCentreOwnership':candidates,'centreOwnerSources':ownerSources})
out={'target':c['target'],'phase':c['target']/80,'missingCentreCandidateEdges':rows,'count':len(rows),'maskUnchanged':True,'newSelectorRuns':0,'newUnityCalls':0}
(D/'FIRST_REJECTION518.json').write_text(json.dumps(out,indent=2,default=str)+'\n')
print(json.dumps({'target':c['target'],'phase':c['target']/80,'count':len(rows),'first':rows[:1]},default=str),flush=True)
