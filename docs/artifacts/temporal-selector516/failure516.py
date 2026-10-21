"""Stored-result attribution and counterexamples; no selector re-run."""
from pathlib import Path
import json,math,collections
import numpy as np
import active516 as G,span516 as S,select516 as C

D=G.OUTPUT;R=G.INPUT
def rect(x,y,xx,yy):return[(x,y),(xx,y),(xx,yy),(x,yy)]
def synthetic(rings,mask):
    active,stats=G.fragments(rings)
    packets={(int(x),int(y)):{'submesh':0,'primitive':0,'world':[0,0,0],'depth':1.,'bodyForeground':False}for y,x in zip(*np.where(mask))}
    ds=[G.descriptor(e,active,rings,packets)for e in G.boundary(mask)];ss,invalid=G.spans(ds);assert not invalid
    return active,ss
def temporal(old,new,prevActive,active,rings):
    groups=lambda ss:{k:[s for s in ss if(s['ring'],s['segment'])==k]for k in{(s['ring'],s['segment'])for s in ss}}
    a,b=groups(old),groups(new);values=[]
    for key in sorted(set(a)|set(b)):
        v=S.channel_cost(a.get(key,[]),b.get(key,[]),rings,prevActive,active,key,True);values.append({'key':key,**v})
    return sum(v['raw']for v in values),values

# Same closed region and pixel mask, same number/order of persistent controls.
# Only an intermediate control slides tangentially along a straight edge.
m=np.zeros((10,12),bool);m[2:6,2:8]=True
old=[[(2,2),(4,2),(8,2),(8,6),(2,6)]];new=[[(2,2),(6,2),(8,2),(8,6),(2,6)]]
aa,a=synthetic(old,m);bb,b=synthetic(new,m);reparam,trace=temporal(a,b,aa,bb,new)
assert reparam>0,'Counterexample changed; inspect rather than assume'

def samples_by_edge(doc):
    out={}
    for s in doc['spans']:
        dx,dy=s['direction']
        for p in s['samples']:
            x,y=p['q'];k=(round(x-dx*.5),round(y-dy*.5),round(x+dx*.5),round(y+dy*.5))
            out[k]={'channel':(s['ring'],s['segment']),'u':p['u'],'reference':p['reference'],'tangent':p['tangent']}
    return out
relabel=[];allUnchanged=0;geometricAbsent=[]
for i in range(1,81):
    prev=json.loads((D/f'{i-1:03d}_ACTIVE.json').read_text());cur=json.loads((D/f'{i:03d}_ACTIVE.json').read_text());p,q=samples_by_edge(prev),samples_by_edge(cur);lengths=cur['ringLengths'];activeKeys={(e['ring'],e['segment'])for e in cur['active']}
    for k in sorted(set(p)&set(q)):
        allUnchanged+=1;a,b=p[k],q[k]
        if a['channel']==b['channel']:continue
        ar,aseg=a['channel'];br,bseg=b['channel'];adjacent=ar==br and((aseg-bseg)%lengths[ar]in[1,lengths[ar]-1])
        angle=math.degrees(math.acos(float(np.clip(np.dot(a['tangent'],b['tangent']),-1,1))))
        relabel.append({'target':i,'edge':k,'previous':a,'current':b,'adjacentSourceSegments':adjacent,'bothCurrentSegmentsActive':a['channel']in activeKeys and b['channel']in activeKeys,'tangentAngleDegrees':angle})
    for v in cur['previousCorrespondence']:
        if not v['valid']:geometricAbsent.append({'target':i,**v,'interpretation':'NO_CURRENT_VISIBLE_SPAN means absent selected span in this channel, not a certified physical occlusion.'})

# Freeze the *existing* final result at its current geometry. Compare its shape
# with the static cut under the same span objective; do not solve or warm a loop.
root=D/'eta-1.0';i=80;sel=C.Selector(i,None,1.);baseline=sel.original.copy();chosen=np.load(root/f'{i:03d}.npy')
desc={}
for e in G.boundary(chosen):
    d=sel.describe(C.key(e));assert d is not None;desc[C.key(e)]=d
chosenGroups=C.groups(desc);chosenSpans=[s for ss in chosenGroups.values()for s in ss];baseSpans=[s for ss in sel.groupSpans.values()for s in ss]
stay,stayTrace=temporal(chosenSpans,chosenSpans,sel.active,sel.active,sel.rings)
recover,recoverTrace=temporal(chosenSpans,baseSpans,sel.active,sel.active,sel.rings)
baseE=C.spatial(baseline,sel.area,sel.bounds);chosenE=C.spatial(chosen,sel.area,sel.bounds);delta=baseE['total']-chosenE['total']+sel.beta*(recover-stay)

# Evaluate one-cell corrections toward the canonical static cut with fixed
# constant geometry/history. This is cost evaluation only, not another solve.
sel.mask=chosen.copy();sel.desc=desc;sel.groupEdges={}
for k,d in desc.items():sel.groupEdges.setdefault(C.channel(d),{})[k]=d
sel.groupSpans=chosenGroups;sel.previous={'spans':chosenGroups,'active':sel.active,'rings':sel.rings,'signature':sel.signature};sel.costs={ch:sel.cost(ch,ss)for ch,ss in chosenGroups.items()}
corrections=[]
for y,x in zip(*np.where(chosen!=baseline)):
    p=sel.proposal(int(x),int(y));corrections.append({'xy':[int(x),int(y)],'towardStatic':bool(baseline[y,x]),'admissible':p is not None,**({k:p[k]for k in ['deltaSpatial','deltaTemporal','deltaObjective']}if p else{})})

out={'mode':'ATTRIBUTION_AND_COUNTEREXAMPLE_ONLY_NO_NEW_SELECTION','unchangedRegionTangentialReparameterization':{'sameClosedRegion':True,'samePixelBoundary':True,'samePersistentControlCount':True,'oldControls':old,'newControls':new,'rawTemporalCost':reparam,'expectedGeometryOnlyTemporalCost':0.,'operatorTrace':trace,'verdict':'FAILED_GEOMETRIC_REPARAMETERIZATION_INVARIANT: per-segment channels and material-parameter advection are not sufficient geometric silhouette correspondence.'},'storedUnchangedGridEdgesExamined':allUnchanged,'storedUnchangedEdgeChannelRelabels':relabel,'storedSelectedSpanAbsence':geometricAbsent,'storedPhysicalOcclusionCertifiedByAbsence':False,'frozenEndpointCounterexample':{'target':80,'differentCells':int((chosen!=baseline).sum()),'stayTemporalCost':stay,'recoverStaticTemporalCost':recover,'staticSpatial':baseE,'chosenSpatial':chosenE,'recoverObjectiveMinusStay':delta,'individualCorrections':corrections,'operatorTraceRecover':recoverTrace,'verdict':'A positive recovery difference is evidence of a switching barrier at stationary geometry, not proof that the alternate pixel drawing is aesthetically wrong. No accumulated spatial regret exists in this greedy one-step objective.'},'noProductChanges':True,'noNewCaptures':True}
(D/'FAILURE516.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'tangentialReparameterizationCost':reparam,'unchangedEdgeRelabels':len(relabel),'adjacentActiveRelabels':sum(v['adjacentSourceSegments']and v['bothCurrentSegmentsActive']for v in relabel),'firstRelabels':relabel[:4],'selectedSpanAbsence':len(geometricAbsent),'frozenEndpoint':{k:v for k,v in out['frozenEndpointCounterexample'].items()if k not in ['operatorTraceRecover']}},ensure_ascii=False))
