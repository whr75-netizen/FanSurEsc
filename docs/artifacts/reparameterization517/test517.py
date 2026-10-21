from pathlib import Path
import json,copy,math
import numpy as np
import active516 as G,arc517 as A,span517 as N,span516 as O
D=G.ROOT/'Temporal517'/'SpanArcV2';D.mkdir(parents=True,exist_ok=True)
def state(rings,mask):
    fragments,_=G.fragments(rings);arcs,resets=A.active_arcs(fragments);assert not resets,resets;bindings,unsupported=A.bind(mask,arcs);assert not unsupported,unsupported;return arcs,bindings
def check(name,a,b,expected=None,positive=False):
    result=N.compare(a[0],a[1],b[0],b[1],True)
    assert result['valid'],result
    if expected is not None:assert abs(result['raw']-expected)<1e-7,(name,result)
    if positive:assert result['raw']>1e-7,(name,result)
    return {'name':name,'expected':expected,'expectedPositive':positive,**result}
m=np.zeros((12,14),bool);m[2:6,2:8]=True
old=[[(2,2),(4,2),(8,2),(8,6),(2,6)]];slide=[[(2,2),(6,2),(8,2),(8,6),(2,6)]]
split=[[(2,2),(3,2),(5,2),(8,2),(8,3),(8,6),(5,6),(2,6),(2,4)]]
start=[split[0][4:]+split[0][:4]]
a=state(old,m);results=[check('identity',a,a,0),check('unchanged-region-control-slide',a,state(slide,m),0),check('unchanged-region-control-split',a,state(split,m),0),check('unchanged-region-cyclic-parameter-start',a,state(start,m),0)]
mt=np.zeros_like(m);mt[2:6,3:9]=True;rt=[[(x+1,y)for x,y in old[0]]]
results.append(check('integer-translation',a,state(rt,mt),0))
mr=np.zeros_like(m)
for y,x in zip(*np.where(m)):mr[x,9-y]=True
rr=[[(10-y,x)for x,y in old[0]]]
results.append(check('rigid-rotation90',a,state(rr,mr),0))
# Actual geometry moved but the pixel mask did not: do not erase its residual
# merely because the same fixed mask is being compared.
quarter=[[(x+.25,y)for x,y in old[0]]]
results.append(check('geometry-moved-quarter-cell-pixels-still',a,state(quarter,m),positive=True))
# A changed drawing in the exact same region must retain a real edit cost.
changed=m.copy();changed[:,7]=False
results.append(check('same-geometry-pixel-edit',a,state(old,changed),positive=True))
grown=np.zeros_like(m);grown[2:6,2:9]=True;growth=[[(2,2),(4,2),(9,2),(9,6),(2,6)]]
results.append(check('actual-growth-adds-boundary-pixels',a,state(growth,grown),positive=True))
# Explicit physical visibility owns reset; absent selected spans do not.
hidden=copy.deepcopy(a[0]);hidden[0]['visible']=False
r=N.compare(a[0],a[1],hidden,{},True);assert r['raw']==0 and any(v['reason']=='EXPLICIT_VISIBILITY_EVENT'for v in r['geometryEventResets']);results.append({'name':'explicit-occlusion-reset',**r})
r=N.compare(a[0],a[1],a[0],{},True);assert r['raw']>0 and not r['geometryEventResets'];results.append({'name':'selected-span-absence-is-delete-not-occlusion',**r})
# Geometry separates into two components; do not force old single-arc identity.
two=[[(2,2),(4,2),(4,6),(2,6)],[(6,2),(8,2),(8,6),(6,6)]];mm=m.copy();mm[:,4:6]=False;b=state(two,mm)
r=N.compare(a[0],a[1],b[0],b[1],True);assert any(v['reason']=='GEOMETRIC_COMPONENT_SPLIT_MERGE_OR_BIRTH_DEATH'for v in r['geometryEventResets']);results.append({'name':'geometric-split-reset',**r})
r=N.compare(b[0],b[1],a[0],a[1],True);assert r['geometryEventResets'];results.append({'name':'geometric-merge-reset',**r})

# Freeze the 516 edit arithmetic independently of the new correspondence.
# With identical pretransported sample positions and connection order, the
# unrotated DP and all atomic operations must produce the same numeric costs.
arithmetic=[]
for dx in [0.,.2,1.]:
    def oldspan(points):return {'length':len(points),'ring':0,'segment':0,'samples':[{'q':p,'u':(k+.5)/len(points),'reference':[(k+.5)/len(points),0.],'tangent':[1.,0.]}for k,p in enumerate(points)]}
    oldpoints=[[.25,0.],[.75,0.]];newpoints=[[.25+dx,0.],[.75+dx,0.]];x=[oldspan(oldpoints)];y=[oldspan(newpoints)];spec=[[(0.,0.),(1.,0.),(1.,1.)]]
    before=O.edit(x,y,spec,True);after=N.linear_edit([{'length':2,'points':oldpoints}],[{'length':2,'points':newpoints}],trace=True)
    assert abs(before['raw']-after['raw'])<1e-12 and before['operations']==after['operations'];arithmetic.append({'displacement':dx,'raw516':before['raw'],'raw517':after['raw']})
out={'passed':True,'tests':results,'atomicCostAndLinearDPUnchanged':arithmetic,'betaUnchanged':.14,'temporalStateCostChanged':False,'selectorRun':False,'unityCalls':0,'scope':'Synthetic geometry/correspondence tests, not actual new-model/occlusion Unity validation.'}
(D/'FIXTURES517.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':True,'tests':[{'name':r['name'],'raw':r['raw'],'resets':r['geometryEventResets']}for r in results],'arithmetic':arithmetic}))
