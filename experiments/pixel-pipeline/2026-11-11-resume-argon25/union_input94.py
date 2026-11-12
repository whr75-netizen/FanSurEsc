"""Bounded actual body1 source projection and directed opacity input."""
from pathlib import Path
import struct,json,hashlib,numpy as np
from native_width86 import text
def load(path):
 path=Path(path);assert path.stat().st_size<=4194304
 with path.open('rb')as f:
  version=text(f);assert version in ['union-input94/v1','union-input94/v2'];precise=version.endswith('/v2');sid=text(f);frame=struct.unpack('<i',f.read(4))[0]
  def array(dtype,cap):
   n=struct.unpack('<i',f.read(4))[0];assert 0<=n<=cap;size=np.dtype(dtype).itemsize;data=f.read(n*size);assert len(data)==n*size;return np.frombuffer(data,dtype).copy()
  points=array(np.dtype(('<f4',2)),32768);indices=array('<i4',196608);anchor_type=[('vertices','<i4',3),('weights','<f4',3)]+([('weights64','<f8',2)]if precise else[]);anchors=array(np.dtype(anchor_type),65536);boundaries=array(np.dtype([('primitive','<i4'),('a','<i4'),('b','<i4'),('opacity','?')]),65536);segments=array(np.dtype(('<f8'if precise else'<f4',(2,2))),65536);assert not f.read()
 assert np.isfinite(points).all()and np.isfinite(segments).all()and(len(indices)%3==0)and(indices>=0).all()and(indices<len(points)).all()and(anchors['vertices']>=0).all()and(anchors['vertices']<len(points)).all();assert(boundaries['a']>=0).all()and(boundaries['a']<len(anchors)).all()and(boundaries['b']>=0).all()and(boundaries['b']<len(anchors)).all()
 return {'version':version,'sourceId':sid,'frame':frame,'points':points,'indices':indices.reshape(-1,3),'anchors':anchors,'boundaries':boundaries,'segments':segments,'SHA256':hashlib.sha256(path.read_bytes()).hexdigest()}

def audit(d):
 from collections import Counter,defaultdict
 assert d['version']=='union-input94/v1','Use the high-precision receipt verifier for v2'
 points=d['points'];a=d['anchors'];p=points[a['vertices']];weights=a['weights'];position=(p[:,0]*weights[:,0,None]+p[:,1]*weights[:,1,None])+p[:,2]*weights[:,2,None];mapping=defaultdict(set)
 for i,v in enumerate(position):mapping[tuple(v)].add(i)
 primitive=defaultdict(set)
 for s in d['boundaries']:
  primitive[int(s['a'])].add(int(s['primitive']));primitive[int(s['b'])].add(int(s['primitive']))
 balance=Counter();missing=[];ambiguous=0;areas=Counter();group_edges=defaultdict(list)
 for i,(a,b)in enumerate(d['segments']):
  ka=tuple(np.rint(a.astype(float)*1e8).astype(np.int64));kb=tuple(np.rint(b.astype(float)*1e8).astype(np.int64));balance[ka]+=1;balance[kb]-=1
  sa=mapping.get(tuple(a),set());sb=mapping.get(tuple(b),set())
  if not sa or not sb:missing.append(i);continue
  pa=set().union(*(primitive[x]for x in sa));pb=set().union(*(primitive[x]for x in sb));both=pa&pb
  if len(both)!=1:ambiguous+=1;continue
  pr=next(iter(both));group_edges[pr].append((a.astype(float),b.astype(float)));areas[pr]+=(float(a[0])*float(b[1])-float(a[1])*float(b[0]))*.5
 neg=[]
 for pr,area in areas.items():
  if area>=0:continue
  ring_balance=Counter()
  for a,b in group_edges[pr]:ring_balance[tuple(a)]+=1;ring_balance[tuple(b)]-=1
  if not any(ring_balance.values()):neg.append({'primitive':pr,'area':area,'edges':len(group_edges[pr]),'closedAssignedComponent':True,'projectedSourceTriangle':points[d['indices'][pr]].tolist()})
 return {'sourceId':d['sourceId'],'frame':d['frame'],'segments':len(d['segments']),'unbalancedGridVertices':sum(v!=0 for v in balance.values()),'maximumGridDegreeImbalance':max(map(abs,balance.values()),default=0),'segmentsWithUnmatchedAnchor':missing,'segmentsWithAmbiguousPrimitive':ambiguous,'negativeAssignedTriangleSignedAreas':neg,'sumAnchorWeightErrorMaximum':float(abs(weights.sum(1)-1).max()),'partitionNotAssumedFromAmbiguousEdges':True}
if __name__=='__main__':
 import sys
 p=Path(sys.argv[1]);d=load(p);r=audit(d);p.with_suffix('.audit94.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
