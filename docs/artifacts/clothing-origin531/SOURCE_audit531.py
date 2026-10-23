"""Narrow lineage audit. No selection rule, penalty, history or render output."""
from pathlib import Path
from collections import defaultdict,Counter
import struct,json,math,hashlib
import numpy as np
O=Path(__file__).resolve().parent;R=O/'Actual43_44_B';REF=O.parent/'Cloth527/FullLoopB'
class Reader:
    def __init__(self,b):self.b=b;self.at=0
    def integer(self):v=struct.unpack_from('<i',self.b,self.at)[0];self.at+=4;return v
    def array(self,dtype,n):v=np.frombuffer(self.b,np.dtype(dtype),n,self.at).copy();self.at+=v.nbytes;return v
def rings(path):
    r=Reader(path.read_bytes());groups=[]
    for _ in range(2):
        groups.append([r.array('<f4',r.integer()*2).reshape(-1,2)for _ in range(r.integer())])
    assert r.at==len(r.b);return groups
assert json.loads((R/'status.json').read_text())['status']=='EXTRACTED'
r=Reader((R/'MODEL531.bin').read_bytes());assert r.integer()==531
v=r.array([('p','<f4',(3,)),('uv','<f4',(2,)),('canonical','<i4')],r.integer());groups={};headers={};tags={}
for _ in range(r.integer()):
    sm=r.integer();headers[sm]=r.integer();groups[sm]=r.array('<i4',r.integer()).reshape(-1,3);tags[sm]=r.array('<i4',r.integer()).reshape(-1,3)
anchors=r.array([('ids','<i4',(3,)),('weights','<f4',(3,))],r.integer())
segments=r.array([('pr','<i4'),('a','<i4'),('b','<i4'),('opacity','u1')],r.integer());assert r.at==len(r.b)
incidence=defaultdict(list)
for sm,triangles in groups.items():
    for pr,tri in enumerate(triangles):
        ids=v['canonical'][tri]
        for a,b in zip(ids,np.roll(ids,-1)):incidence[tuple(sorted((int(a),int(b))))].append((sm,pr))
def anchor_support(i):
    a=anchors[i];return{int(v['canonical'][int(k)])for k,w in zip(a['ids'],a['weights'])if w!=0}
def origin(sid):
    s=segments[sid];pr=int(s['pr']);out={'sourceSegment':int(sid),'primitive':pr,'anchors':[int(s['a']),int(s['b'])],'opacity':bool(s['opacity']),'materialSlot':3,'declaredPartHeader':headers[3],'partTags':tags[3][pr].tolist()}
    if s['opacity']:out['kind']='ALPHA_CONTOUR';return out
    support=anchor_support(int(s['a']))|anchor_support(int(s['b']));tri=v['canonical'][groups[3][pr]]
    es=[tuple(sorted((int(a),int(b))))for a,b in zip(tri,np.roll(tri,-1))if support<={int(a),int(b)}]
    out['meshEdgeCandidates']=[]
    for e in es:
        owners=incidence[e];cloth=[p for sm,p in owners if sm==3]
        kind='OPEN_MESH_BOUNDARY'if len(cloth)==1 and len(owners)==1 else'MATERIAL_BOUNDARY'if len(cloth)==1 else'INTERIOR_PROJECTED_EDGE'if len(cloth)==2 else'NONMANIFOLD'
        out['meshEdgeCandidates'].append({'vertices':list(e),'clothIncidentTriangles':cloth,'allMaterialIncidence':[list(p)for p in owners],'kind':kind})
    out['kind']=out['meshEdgeCandidates'][0]['kind']if len(es)==1 else'UNRESOLVED_EDGE_SUPPORT'
    return out
def normalized(a,b):
    a=tuple(map(float,a));b=tuple(map(float,b));return(a,b)if a<=b else(b,a)
def distance(p,a,b):
    d=b-a;t=float(np.dot(p-a,d)/np.dot(d,d))if np.dot(d,d)>0 else 0.;return float(np.linalg.norm(p-(a+np.clip(t,0,1)*d))),t
def ulp_radius(p):
    # Only float32 storage rounding of the returned source-ring endpoint.
    return math.hypot(*(abs(float(np.spacing(np.float32(q))))*.5 for q in p))+1e-10
def shape_distance(a,b):
    def one(x,y):
        return max(min(distance(p,c,d)[0]for ring in y for c,d in zip(ring,np.roll(ring,-1,axis=0)))for ring in x for p in ring)
    return max(one(a,b),one(b,a))
rows=[]
for frame,box in [(43,(198,95,204,103)),(44,(229,76,235,82))]:
    r=Reader((R/f'{frame:03d}_PROJECTION.bin').read_bytes());p=r.array('<f4',r.integer()*2).reshape(-1,2);xy=r.array('<f4',r.integer()*2).reshape(-1,2);emitted=r.array('<f4',r.integer()*4).reshape(-1,2,2);matrices=r.array('<f4',48);assert r.at==len(r.b)
    gs=rings(R/f'{frame:03d}_GEOMETRY.bin');reference=rings(REF/f'{frame:03d}_ALT_GEOMETRY.bin')
    raw=defaultdict(list)
    for sid,s in enumerate(segments):raw[normalized(xy[s['a']],xy[s['b']])].append(sid)
    endpointAnchors=defaultdict(list)
    for aid,q in enumerate(xy):endpointAnchors[tuple(map(float,q))].append(aid)
    alphaPr=defaultdict(set)
    for s in segments:
        if s['opacity']:alphaPr[int(s['a'])].add(int(s['pr']));alphaPr[int(s['b'])].add(int(s['pr']))
    def emitted_origin(eid):
        a,b=emitted[eid];ids=raw.get(normalized(a,b),[])
        if ids:return{'emittedSegment':eid,'resolution':'EXACT_RAW_ANCHOR_PAIR','origins':[origin(i)for i in ids]}
        aa=endpointAnchors.get(tuple(map(float,a)),[]);bb=endpointAnchors.get(tuple(map(float,b)),[])
        candidate=set().union(*(alphaPr[i]for i in aa))&set().union(*(alphaPr[i]for i in bb))
        return{'emittedSegment':eid,'resolution':'FITTED_ALPHA_PRIMITIVE_CANDIDATES'if candidate else'UNRESOLVED','aAnchors':aa,'bAnchors':bb,'primitiveCandidates':sorted(candidate),'exactSkippedSourceIntervalKnown':False}
    sourceRows=[]
    for ringId,ring in enumerate(gs[0]):
        for edge,(a,b)in enumerate(zip(ring,np.roll(ring,-1,axis=0))):
            if min(a[0],b[0])>box[2]or max(a[0],b[0])<box[0]or min(a[1],b[1])>box[3]or max(a[1],b[1])<box[1]:continue
            candidates=[]
            for eid,(c,d)in enumerate(emitted):
                if min(c[0],d[0])>max(a[0],b[0])+ulp_radius(a)or max(c[0],d[0])<min(a[0],b[0])-ulp_radius(a)or min(c[1],d[1])>max(a[1],b[1])+ulp_radius(a)or max(c[1],d[1])<min(a[1],b[1])-ulp_radius(a):continue
                da,ta=distance(a.astype(float),c.astype(float),d.astype(float));db,tb=distance(b.astype(float),c.astype(float),d.astype(float));length=float(np.linalg.norm(d-c))
                if da<=ulp_radius(a)and db<=ulp_radius(b)and min(ta,tb)>=-max(ulp_radius(a),ulp_radius(b))/max(length,1e-12)and max(ta,tb)<=1+max(ulp_radius(a),ulp_radius(b))/max(length,1e-12):
                    candidates.append({'endpointResiduals':[da,db],**emitted_origin(eid)})
            sourceRows.append({'ring':ringId,'edge':edge,'a':a.tolist(),'b':b.tolist(),'endpointStorageErrorBounds':[ulp_radius(a),ulp_radius(b)],'lineage':candidates})
    pose=json.loads((R/f'{frame:03d}_POSE.json').read_text());counts=Counter(o['kind']for e in sourceRows for l in e['lineage']for o in l.get('origins',[]))
    rows.append({'frame':frame,'pose':pose,'sourceHausdorffVs527':shape_distance(gs[0],reference[0]),'curveHausdorffVs527':shape_distance(gs[1],reference[1]),'roi':box,'sourceEdges':sourceRows,'originKindCounts':dict(counts),'unmappedSourceEdges':sum(not q['lineage']for q in sourceRows)})
out={'status':'LOCAL_LINEAGE_AUDIT_ONLY_NO_SELECTOR_CHANGE','model':{'vertices':len(v),'trianglesByMaterial':{str(k):len(a)for k,a in groups.items()},'declaredHeaders':headers,'anchors':len(anchors),'segments':len(segments),'partSideTagsClothHistogram':{','.join(map(str,k)):int(n)for k,n in Counter(map(tuple,tags[3][:,:2].astype(int))).items()},'tagThirdField':'global triangle identity, not a semantic feature tag'},'actualCases':rows,
 'limits':['IDs are provenance, not feature importance.','Union lineage is audited only in the two requested local ROIs.','Float endpoint matching uses half-ULP storage error, no free pixel radius.','Coincident source candidates are retained; no role-only same-surface assumption.']}
(O/'LINEAGE_AUDIT531.json').write_bytes(json.dumps(out,indent=2).encode())
print(json.dumps({'model':out['model'],'cases':[{'frame':q['frame'],'sourceHausdorffVs527':q['sourceHausdorffVs527'],'curveHausdorffVs527':q['curveHausdorffVs527'],'edges':len(q['sourceEdges']),'unmapped':q['unmappedSourceEdges'],'kinds':q['originKindCounts']}for q in rows]}))
