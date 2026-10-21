"""Explain the first real-pose rejection without changing any correspondence."""
import json,pickle
import numpy as np
import active516 as G,edge518 as E,arc517 as A
D=G.ROOT/'Region518/PartialEdgeV2/Stored81'
with(D/'FIRST_UNBOUND.pickle').open('rb')as f:c=pickle.load(f)
r=c['incidence'];case=json.loads((D/'FIRST_REJECTION518.json').read_text())['missingCentreCandidateEdges'][0];edge=tuple(case['edge']);p=np.array([(edge[0]+edge[2])*.5,(edge[1]+edge[3])*.5]);direction=np.array([edge[2]-edge[0],edge[3]-edge[1]]);ends=np.array([p-direction*.5,p+direction*.5]);eligible=[]
for ai,arc in enumerate(c['arcs']):
    for si,(a,b)in enumerate(zip(arc['p'],arc['b'])):
        support=r.candidate_support(edge,E.source_segment(arc,si))
        if not support['accepted']:continue
        d=b-a;ll=d@d;t=np.clip(((ends-a)*d).sum(1)/ll,0,1);q=a+t[:,None]*d;dist=((ends-q)**2).sum(1);dot=float(direction@d);reason=[]
        if dist.max()>2+A.EPS:reason.append('EXISTING_UNIT_ENDPOINT_CORRIDOR')
        if dot<-A.EPS:reason.append('EXISTING_UNIT_TANGENT_DIRECTION')
        eligible.append({'arc':ai,'segment':si,'sourceExact':E.source_segment(arc,si),'sourceFloat':[a.tolist(),b.tolist()],'maxUnitEndpointDistance2':float(dist.max()),'unitDirectionDotSource':dot,'centreRegionEvidence':support,'rejectedBy':reason})
eligible.sort(key=lambda p:p['maxUnitEndpointDistance2']);assert eligible and all(p['rejectedBy']for p in eligible)
out={'target':c['target'],'phase':c['target']/80,'edge':edge,'partialIncidence':r.record(edge),'allSourceSegmentsOwningCentreRegion':eligible,'priorGeometryCandidateOwnsOnlyOtherPartialRegion':case['geometricCandidatesBeforeCentreOwnership'],'cause':'Partial P/M incidence is now represented, but the inherited whole-unit direction/corridor and one centre-anchor channel still exclude all exact source boundaries of the centre A region. This is not absent geometry, physical occlusion or a new area/mask decision.','nextDependency':'Define region-boundary-to-active-arc correspondence when the existing selector merges/omits concavity and a pixel unit has multiple oriented incidence portions. Reuse those exact portions instead of assigning its whole unit tangent to one source segment. No radius/coefficient/selector change was attempted.','newMask':False,'newUnityCalls':0,'newSelectorRuns':0,'notYetImplemented':True}
(D/'CENTRE_FILTER_DEPENDENCY518.json').write_text(json.dumps(out,indent=2,default=str)+'\n');print(json.dumps({**{k:v for k,v in out.items()if k not in['allSourceSegmentsOwningCentreRegion','priorGeometryCandidateOwnsOnlyOtherPartialRegion']},'nearestCentreOwnerCandidates':eligible[:3]},default=str),flush=True)
