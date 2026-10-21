"""One rejected vertex witness from the completed517V2 audit; no rerun."""
import json,math
import numpy as np
import active516 as G,arc517 as A
D=G.ROOT/'Temporal517'/'SpanArcV2'
old=json.loads((G.ROOT/'Temporal516/000_ACTIVE.json').read_text());arcs,_=A.active_arcs(old['active']);loop=A.pixel_loops(G.read_mask(0))[0];edges=loop['edges'];EPS=A.EPS
def candidates(edge):
    p=np.array([(edge[0]+edge[2])*.5,(edge[1]+edge[3])*.5]);direction=np.array([edge[2]-edge[0],edge[3]-edge[1]]);out=[]
    for ai,arc in enumerate(arcs):
        a,d,ll=arc['p'],arc['d'],arc['length']**2;ends=np.array([p-direction*.5,p+direction*.5]);t=np.clip(((ends[:,None]-a)*d).sum(2)/ll,0,1);q=a+t[:,:,None]*d;dist=(ends[:,None]-q)**2
        dist=dist.sum(2);ok=(dist.max(0)<=2+EPS)&((direction*d).sum(1)>=-EPS);tm=np.clip(((p-a)*d).sum(1)/ll,0,1)
        for si in np.where(ok)[0]:out.append({'arc':ai,'segment':int(si),'t':float(tm[si]),'fit':float(dist[:,si].mean()),'reference':(a[si]+tm[si]*d[si]).tolist(),'sourceA':a[si].tolist(),'sourceB':arc['b'][si].tolist()})
    return out
cache={}
def cells(s,vertex):
    key=(s['arc'],s['segment'],vertex)
    if key not in cache:
        x,y=vertex;arc=arcs[s['arc']];i=s['segment'];cache[key]={c for c in[(x-1,y-1),(x,y-1),(x-1,y),(x,y)]if A.segment_cell(arc['p'][i],arc['b'][i],c)}
    return cache[key]
def link(a,b,vertex):
    if a['arc']==b['arc']:
        arc=arcs[a['arc']];sa,sb=a['segment'],b['segment']
        if sa==sb and b['t']>=a['t']-1e-10:return 'CONTINUOUS_ARC'
        if sb==(sa+1)%len(arc['p']):
            node=arc['b'][sa]
            if abs(node[0]-vertex[0])<=1+EPS and abs(node[1]-vertex[1])<=1+EPS:return 'CONTINUOUS_ARC_CORNER'
    if cells(a,vertex)&cells(b,vertex):return 'QUANTIZED_REGION_JOIN'
    return None
states=[candidates(e)for e in edges];assert all(states)
barriers=[]
for i in range(len(edges)):
    vertex=tuple(edges[i][:2]);possible=[link(a,b,vertex)for a in states[i-1]for b in states[i]]
    if not any(possible):
        barriers.append({'edgeIndex':i,'pixelVertex':vertex,'previousPixelEdge':edges[i-1],'currentPixelEdge':edges[i],'previousCandidates':[dict(s,intersectedIncidentCells=sorted(cells(s,vertex)))for s in states[i-1]],'currentCandidates':[dict(s,intersectedIncidentCells=sorted(cells(s,vertex)))for s in states[i]],'allPairTransitionsRejected':True})
out={'target':0,'phase':0.,'pixelLoopArea':loop['area'],'pixelLoopUnitEdges':len(edges),'allIndividualUnitEdgesHaveGeometricCandidates':True,'forcedLocalBarriers':barriers,'barrierCount':len(barriers),'physicalOcclusionQueried':False,'reason':'The recorded rejection is a geometry-correspondence connection rule, not depth/alpha/owner occlusion. A source path outside the four incident cells can be omitted/merged by the existing region selector, but517V2 requires direct continuation or same-cell intersection.','completedAuditRoot':str(D/'AUDIT517.json'),'selectorRuns':0,'newUnityCalls':0,'noCoefficientOrTemporalStateChanges':True}
(D/'FIRST_REJECTION517.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'barrierCount':len(barriers),'firstBarrier':barriers[0]if barriers else None,'allIndividualUnitEdgesSupported':True},ensure_ascii=False))
