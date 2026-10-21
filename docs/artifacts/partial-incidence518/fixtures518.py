"""Partial incidence: first cases plus prior structural/cost counterexamples."""
from pathlib import Path
from fractions import Fraction as Q
import json,pickle,copy,time,hashlib
import numpy as np
import active516 as G,arc517 as A,arc518 as B,face518 as F,edge518 as E,span517 as N,span516 as O
D=G.ROOT/'Region518/PartialEdgeV2';begin=time.perf_counter();rows=[]

def rect(a,b,c,d):return[(a,b),(c,b),(c,d),(a,d)]
def state(rings,mask):
    m=F.mask_from_array(mask);o=F.Overlay(rings,m,F.auto_domain(rings,m),True)
    fragments,_=G.fragments(rings);arcs,resets=A.active_arcs(fragments);assert not resets,resets
    exact=E.attach_exact_sources(arcs,o);incidence=E.BoundaryIncidence(o);bindings,unsupported=B.bind(mask,arcs,incidence)
    assert not unsupported,unsupported
    assert sum(len(b['samples'])for b in bindings.values())==len(G.boundary(mask))
    return arcs,bindings,incidence
def check(name,a,b,expected=None,positive=False):
    r=N.compare(a[0],a[1],b[0],b[1],True);assert r['valid'],r
    if expected is not None:assert abs(r['raw']-expected)<1e-7,(name,r)
    if positive:assert r['raw']>1e-7,(name,r)
    rows.append({'name':name,'passed':True,**r})
def structural(name,rings,m,verify):
    o=F.Overlay(rings,m,F.auto_domain(rings,m),True);e=E.BoundaryIncidence(o);evidence=verify(o,e)
    rows.append({'name':name,'passed':True,'evidence':evidence,'incidence':e.summary()});return o,e

with(D/'PHASE0.pickle').open('rb')as f:actual=pickle.load(f)
assert actual['result']['fullFirstPosePassed']
e=actual['incidence'];arcs=actual['arcs'];mask=G.read_mask(0)
for ea,eb in[((218,56,218,55),(218,55,217,55)),((209,53,209,52),(209,52,208,52))]:
    relation=e.relate(ea,eb,None);assert relation['boundaryPathJoin']and relation['visibleCorrespondenceAccepted']is None
    front=e.relate(ea,eb,False);assert not front['visibleCorrespondenceAccepted']
    rows.append({'name':f'actual-first-case-{ea[2:]}','passed':True,'relation':relation,'explicitFront':front})

def merge_verify(o,e):
    c=[c for c in o.summary()['components']if c['tag']=='A'and len(c['sourceRegions'])==2 and len(c['selectedRegions'])==1];assert c;return c
structural('prior-added-face-merge',[rect(.1,.1,.9,1.9),rect(2.1,.1,2.9,1.9)],{(x,y):True for x in range(3)for y in range(2)},merge_verify)
def split_verify(o,e):
    c=[c for c in o.summary()['components']if c['tag']=='D'and len(c['sourceRegions'])==1 and len(c['selectedRegions'])==2];assert c
    # The shared omitted face relates source geometry but does not join the
    # distinct selected regions on opposite sides of the omitted column.
    r=e.relate((1,0,1,1),(2,1,2,0),True);assert not r['boundaryPathJoin'];return{'components':c,'oppositeSides':r}
structural('prior-removed-face-split',[rect(.1,.1,2.9,1.9)],{(x,y):True for x in[0,2]for y in range(2)},split_verify)
def near_verify(o,e):
    r=e.relate((1,0,1,1),(1,1,2,1),True);assert not r['boundaryPathJoin'];return r
structural('prior-diagonal-point-contact-not-join',[rect(.1,.1,.9,.9),rect(1.1,1.1,1.9,1.9)],{(0,0):True,(1,1):True},near_verify)
def hole_verify(o,e):
    c=[c for c in o.summary()['components']if c['tag']=='A'and not c['analysisCutOpen']and c['pixelBoundaryCount']==0 and c['sourceBoundaryCount']>0];assert len(c)==1 and c[0]['areaExact']=='1';return c
structural('prior-hole-omission',[rect(0,0,3,3),list(reversed(rect(1,1,2,2)))],{(x,y):True for x in range(3)for y in range(3)},hole_verify)

m=np.zeros((12,14),bool);m[2:6,2:8]=True
old=[[(2,2),(4,2),(8,2),(8,6),(2,6)]];slide=[[(2,2),(6,2),(8,2),(8,6),(2,6)]]
split=[[(2,2),(3,2),(5,2),(8,2),(8,3),(8,6),(5,6),(2,6),(2,4)]];start=[split[0][4:]+split[0][:4]]
a=state(old,m)
for name,rings in [('identity',old),('control-slide',slide),('control-split',split),('cyclic-start',start)]:check(name,a,state(rings,m),0)
mt=np.zeros_like(m);mt[2:6,3:9]=True;check('integer-translation',a,state([[(x+1,y)for x,y in old[0]]],mt),0)
mr=np.zeros_like(m)
for y,x in zip(*np.where(m)):mr[x,9-y]=True
check('rotation90',a,state([[(10-y,x)for x,y in old[0]]],mr),0)
check('geometry-quarter-cell-move-mask-still',a,state([[(x+.25,y)for x,y in old[0]]],m),positive=True)
changed=m.copy();changed[:,7]=False;check('same-geometry-pixel-edit',a,state(old,changed),positive=True)
grown=np.zeros_like(m);grown[2:6,2:9]=True;check('actual-growth',a,state([[(2,2),(4,2),(9,2),(9,6),(2,6)]],grown),positive=True)
hidden=copy.deepcopy(a[0]);hidden[0]['visible']=False
r=N.compare(a[0],a[1],hidden,{},True);assert r['raw']==0 and r['geometryEventResets'];rows.append({'name':'explicit-physical-occlusion-reset','passed':True,**r})
r=N.compare(a[0],a[1],a[0],{},True);assert r['raw']>0 and not r['geometryEventResets'];rows.append({'name':'selected-span-absence-is-delete','passed':True,**r})
two=[rect(2,2,4,6),rect(6,2,8,6)];mm=m.copy();mm[:,4:6]=False;b=state(two,mm)
for name,x,y in [('actual-geometric-split',a,b),('actual-geometric-merge',b,a)]:
    r=N.compare(x[0],x[1],y[0],y[1],True);assert r['geometryEventResets'];rows.append({'name':name,'passed':True,**r})

arithmetic=[]
for dx in[0.,.2,1.]:
    def oldspan(points):return{'length':len(points),'ring':0,'segment':0,'samples':[{'q':p,'u':(k+.5)/len(points),'reference':[(k+.5)/len(points),0.],'tangent':[1.,0.]}for k,p in enumerate(points)]}
    p=[[.25,0.],[.75,0.]];q=[[.25+dx,0.],[.75+dx,0.]]
    before=O.edit([oldspan(p)],[oldspan(q)],[[[0.,0.],[1.,0.],[1.,1.]]],True)
    after=N.linear_edit([{'length':2,'points':p}],[{'length':2,'points':q}],trace=True)
    assert before['raw']==after['raw']and before['operations']==after['operations'];arithmetic.append({'dx':dx,'raw':after['raw']})

# No new geometry calculation is needed for exact collinear split/slide/start:
# canonical rational input is identical, therefore the existing overlay and
# per-edge incidence are literally the same input to the correspondence.
doc=json.loads((G.INPUT/'000_curves.json').read_text());rings=[[(Q(float(p['x'])),Q(float(p['y'])))for p in r['points']]for r in doc['curves']];variants=[]
for t in[Q(1,4),Q(3,4)]:
    rr=[]
    for ring in rings:
        p=[]
        for u,v in zip(ring,ring[1:]+ring[:1]):p.extend([u,F.point(u,v,t)])
        rr.append(p[len(p)//2:]+p[:len(p)//2])
    same=F.canonical_rings(rr)==e.overlay.rings;assert same;variants.append({'splitAt':str(t),'exactCanonicalInputIdentical':same})
out={'passed':True,'tests':rows,'testCount':len(rows),'actualPhase0Reparameterization':variants,'atomicArithmeticUnchanged':arithmetic,'betaUnchanged':.14,'temporalStateCostChanged':False,'selectorRuns':0,'newUnityCalls':0,'seconds':time.perf_counter()-begin,'newDonorVisibility':'unverified; correspondence fixtures do not certify physical occlusion','phase0Gate':actual['result']['fullFirstPosePassed']}
(D/'FIXTURES518.json').write_text(json.dumps(out,indent=2,default=str)+'\n')
print(json.dumps({'passed':True,'testCount':len(rows),'costs':[{'name':r['name'],'raw':r.get('raw')}for r in rows],'seconds':out['seconds']},default=str),flush=True)
