"""Bounded provenance sufficiency counterexample. Never selects a new mask."""
from pathlib import Path
from collections import Counter,defaultdict
import struct,json,math
import numpy as np
O=Path(__file__).resolve().parent;R=O/'Actual43_44_B';REF=O.parent/'Cloth527/FullLoopB'
class Reader:
    def __init__(self,b):self.b=b;self.at=0
    def integer(self):v=struct.unpack_from('<i',self.b,self.at)[0];self.at+=4;return v
    def array(self,dtype,n):v=np.frombuffer(self.b,np.dtype(dtype),n,self.at).copy();self.at+=v.nbytes;return v
def rings(path):
    r=Reader(path.read_bytes());out=[]
    for _ in range(2):out.append([r.array('<f4',r.integer()*2).reshape(-1,2).astype(float)for _ in range(r.integer())])
    assert r.at==len(r.b);return out
def clip(a,b,box):
    lo,hi=0.,1.;d=b-a
    for axis in range(2):
        if d[axis]==0:
            if a[axis]<box[axis]or a[axis]>box[axis+2]:return None
        else:
            u,v=(box[axis]-a[axis])/d[axis],(box[axis+2]-a[axis])/d[axis]
            lo=max(lo,min(u,v));hi=min(hi,max(u,v))
    return (a+lo*d,a+hi*d)if hi>=lo else None
def distance(p,a,b):
    d=b-a;den=np.dot(d,d);t=np.clip(np.dot(p-a,d)/den,0,1)if den else 0
    return float(np.linalg.norm(p-a-t*d))
def local_shape(a,b,box):
    seg=lambda rs:[s for r in rs for x,y in zip(r,np.roll(r,-1,axis=0))if(s:=clip(x,y,box))is not None]
    x,y=seg(a),seg(b)
    def one(src,dst):return max(min(distance(p,c,d)for c,d in dst)for s in src for p in s)
    return {'maxEndpointToOtherSegments':max(one(x,y),one(y,x)),'newClippedEdges':len(x),'oldClippedEdges':len(y)}
def shape_distance(a,b):
    def one(x,y):return max(min(distance(p,c,d)for r in y for c,d in zip(r,np.roll(r,-1,axis=0)))for r in x for p in r)
    return max(one(a,b),one(b,a))
j=json.loads((O/'LINEAGE_AUDIT531.json').read_text());r=Reader((R/'MODEL531.bin').read_bytes());assert r.integer()==531
v=r.array([('p','<f4',(3,)),('uv','<f4',(2,)),('canonical','<i4')],r.integer());tags={}
for _ in range(r.integer()):
    sm=r.integer();header=r.integer();tri=r.array('<i4',r.integer());tags[sm]=r.array('<i4',r.integer()).reshape(-1,3)
j['model'].pop('partTagsClothHistogram',None)
j['model']['partSideTagsClothHistogram']={','.join(map(str,k)):int(n)for k,n in Counter(map(tuple,tags[3][:,:2].astype(int))).items()}
j['model']['tagThirdField']='global triangle identity, not a semantic feature tag'
for q in j['actualCases']:
    f=q['frame'];a=rings(R/f'{f:03d}_GEOMETRY.bin');b=rings(REF/f'{f:03d}_ALT_GEOMETRY.bin')
    q['ringPointCounts']={'newSource':[len(x)for x in a[0]],'oldSource':[len(x)for x in b[0]],'newCurve':[len(x)for x in a[1]],'oldCurve':[len(x)for x in b[1]]}
    q['localCurveComparison']=local_shape(a[1],b[1],q['roi'])
    q['localSourceComparison']=local_shape(a[0],b[0],q['roi'])
    q['unfilteredDiagnosticCurveDistance']=q['curveHausdorffVs527']
    q['curveHausdorffVs527']=shape_distance([r for r in a[1]if len(r)>=3],b[1])
    q['diagnosticCorrection']='ExtractOrigins531B wrote a 2-point degenerate fit. Production Prepare excludes fits with <3 points; compare valid closed regions only. Raw binary retained.'
j['limits']=[s for s in j['limits']if not s.startswith('Global newly fitted curves')]
j['limits'].append('Curve comparison applies the existing production fit.Length>=3 guard; unfiltered diagnostic binary and distances are preserved.')
(O/'LINEAGE_AUDIT531.json').write_bytes(json.dumps(j,indent=2).encode())
# A normal attached thin-end fixture already used in529, now with real closed
# topology. Front/back extrusion changes no orthographic boundary shape.
poly=np.array([[0,0],[4,0],[4,11],[0,11],[0,10],[-.75,10],[-.75,7],[0,7],[0,4],[-.75,4],[-.75,1],[0,1]],float)
def cross(a,b,c):
    u,v=b-a,c-a;return float(u[0]*v[1]-u[1]*v[0])
def triangulate(p):
    live=list(range(len(p)));out=[]
    while len(live)>3:
        found=False
        for k,b in enumerate(live):
            a,c=live[k-1],live[(k+1)%len(live)]
            if cross(p[a],p[b],p[c])<=1e-12:continue
            if any(all(cross(p[u],p[w],p[z])>=-1e-12 for u,w in [(a,b),(b,c),(c,a)])for z in live if z not in(a,b,c)):continue
            out.append((a,b,c));live.pop(k);found=True;break
        assert found,'invalid fixture triangulation'
    out.append(tuple(live));return out
def mesh_test(p,closed):
    ts=triangulate(p);n=len(p)
    if closed:ts=ts+[tuple(x+n for x in t[::-1])for t in ts]+[t for i in range(n)for t in [(i,(i+1)%n,(i+1)%n+n),(i,(i+1)%n+n,i+n)]]
    inc=defaultdict(list)
    for pr,t in enumerate(ts):
        for a,b in zip(t,t[1:]+t[:1]):inc[tuple(sorted((a,b)))].append(pr)
    counts=[len(inc[tuple(sorted((i,(i+1)%n)))])for i in range(n)]
    assert set(counts)==({2}if closed else{1})
    if closed:assert all(len(x)==2 for x in inc.values())
    return {'closedMesh':closed,'triangles':len(ts),'projectedBoundaryVertices':n,'boundaryEdgeTriangleIncidences':counts,'topologyClass':'INTERIOR_PROJECTED_EDGE'if closed else'OPEN_MESH_BOUNDARY','materialSlot':3,'partSideTags':[3,0],'alphaCut':False,'selectedMaskComputed':False}
tests=[]
for turn in range(4):
    c,s=math.cos(turn*math.pi/2),math.sin(turn*math.pi/2);p=poly@np.array([[c,-s],[s,c]]).T
    for subdivide in [False,True]:
        q=np.array([x for a,b in zip(p,np.roll(p,-1,axis=0))for x in[a,(a+b)*.5]])if subdivide else p
        tests.append({'quarterTurns':turn,'collinearSubdivision':subdivide,'open':mesh_test(q,False),'closed':mesh_test(q,True)})
result={'status':'PROVENANCE_RECOVERED_CATEGORY_ALONE_INSUFFICIENT_NO_SELECTOR_CHANGE',
 'actual43':'7 local source edges, interior cloth edges, right lower-arm weights; no opacity cut or open hem',
 'actual44':'6 local source edges, interior cloth edges, left lower-arm weights; no opacity cut or open hem',
 'fixture':{'source':'529 normal paired0.75x3 thin ends','polygon':poly.tolist(),'perEndArea':2.25,'sameProjectionUnderClosedExtrusion':True,'tests':tests},
 'conclusion':'An intentional closed thin end can have the same origin category/material/part as43. Category and primitive IDs alone cannot supply keep/omit significance.',
 'notProved':'Full continuous shape/rest geometry cannot distinguish the cases. Their geometric shapes differ; this test rejects origin-category-only decisions, not all geometry-based design.',
 'exactRemainingDependency':'A model-independent shape-design decision using ordered continuous feature geometry must define which quantized extent is retained or merged. Mere ID propagation supplies correspondence, not that decision;529 already fails if its return rule is reused.',
 'forbiddenShortcutNotApplied':['interior edge=>omit','all thin ends=>omit','part2=>keep/part3=>omit','coordinate/phase exceptions','new penalties or time history'],
 'productCodeChanged':False,'newFullWalkCapture':False,'actualGeometryPosesExtracted':2,'newRGBFrames':0}
(O/'PROVENANCE_GATE531.json').write_bytes(json.dumps(result,indent=2).encode())
print(json.dumps({'status':result['status'],'normalClosedThinTests':len(tests),'actual':[{'frame':q['frame'],'edges':len(q['sourceEdges']),'unmapped':q['unmappedSourceEdges'],'localSource':q['localSourceComparison'],'localCurve':q['localCurveComparison'],'counts':q['ringPointCounts']}for q in j['actualCases']]}))
