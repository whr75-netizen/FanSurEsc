"""Clip the existing109 native UV polyline to actual source triangles.
No new eye shape, colour, snapping, Unity call or GPU device.
"""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
H=Path(__file__).resolve().parent;R=H.parents[2];G=H/'surface27'
sys.path.insert(0,str(R/'pigment-carrier109'));from native109 import uv_bary
sys.path.insert(0,str(H));from verify_native_proof import bindings

def clip(a,b,triangles,uv):
 intervals=[]
 for ti,ids in enumerate(triangles):
  ends=uv_bary(uv[ids],np.array([a,b]))
  if ends is None:continue
  lo,hi=0.,1.;origin=ends[0];delta=ends[1]-origin
  for c,d in zip(origin,delta):
   if abs(d)<1e-15:
    if c< -1e-12:lo,hi=1.,0.;break
   elif d>0:lo=max(lo,-c/d)
   else:hi=min(hi,-c/d)
  if hi-lo>1e-12:intervals.append((max(0.,lo),min(1.,hi),ti))
 cuts=sorted({0.,1.,*(v for q in intervals for v in q[:2])});merged=[]
 for x in cuts:
  if not merged or x-merged[-1]>1e-10:merged.append(x)
 return intervals,merged

def main():
 G.mkdir(exist_ok=True);cache= json.loads((R/'pigment-carrier109/NATIVE_CACHE109.json').read_text());data=np.load(R/'pigment-carrier109/NATIVE_DOMAIN109.npz')
 uv=data['uv'].astype(float);rest=data['rest'].astype(float);tri=data['triangles'];original=bindings();rows=[];pieces=[];ranges=[];unresolved=[];offset=0;maxGap=0.
 for curve in cache['curves']:
  for ai,(a,b)in enumerate(zip(curve['points'],curve['points'][1:])):
   index=offset+ai;owner,pa,pb=original[index];assert owner==curve['owner']and not a.get('unresolved')and not b.get('unresolved')
   for point,old in [(a,pa),(b,pb)]:
    assert list(old[:3])==point['vertices'];assert abs(np.array(old[3:])-point['barycentric']).max()<3e-8
   start=len(pieces);intervals,cuts=clip(a['sourceUV'],b['sourceUV'],tri,uv);previous=None;problems=[]
   for lo,hi in zip(cuts,cuts[1:]):
    mid=(lo+hi)*.5;candidates=[ti for l,r,ti in intervals if l-1e-10<=mid<=r+1e-10]
    if not candidates:problems.append({'interval':[lo,hi],'reason':'UV carrier gap'});continue
    endpoints=np.array([np.array(a['sourceUV'])*(1-u)+np.array(b['sourceUV'])*u for u in [lo,hi]])
    variants=[(ti,uv_bary(uv[tri[ti]],endpoints))for ti in candidates]
    world=np.array([weights@rest[tri[ti]]for ti,weights in variants])
    if len(world)>1 and np.linalg.norm(world-world[0],axis=2).max()>1e-7:problems.append({'interval':[lo,hi],'reason':'multiple physically distinct UV carriers','triangles':candidates});continue
    ti,weights=min(variants,key=lambda q:tuple(sorted(map(int,tri[q[0]]))))
    positions=weights@rest[tri[ti]]
    if previous is not None:
     gap=float(np.linalg.norm(positions[0]-previous));maxGap=max(maxGap,gap)
     if gap>1e-7:problems.append({'interval':[lo,hi],'reason':'surface discontinuity','gapMetres':gap})
    previous=positions[1]
    pieces.append({'segment':index,'owner':owner,'u':[lo,hi],'primitive':int(ti+1),'vertices':tri[ti].astype(int).tolist(),'barycentric':weights.tolist()})
   count=len(pieces)-start
   if problems:unresolved.append({'segment':index,'problems':problems});ranges.append([start,0])
   else:ranges.append([start,count])
   cross=set(pa[:3])!=set(pb[:3]);rows.append({'segment':index,'owner':owner,'originalCrossTriangle':cross,'pieceCount':count,'status':'unknown'if problems else'continuous native UV surface path'})
  offset+=len(curve['points'])-1
 assert offset==len(original)==846
 result={'reference':'Existing109 alpha-mass-centred UV polyline between consecutive native section centres; not recovered artist intent. Display shape/allocation and source colour unchanged.',
  'originalSegments':846,'originalCrossTriangle':sum(v['originalCrossTriangle']for v in rows),'pieces':pieces,'ranges':ranges,'segments':rows,'unresolved':unresolved,'pieceCount':len(pieces),'maxPiecesPerOriginalSegment':max(v['pieceCount']for v in rows),'maxRestSurfaceJoinGapMetres':maxGap,
  'cacheInputs':{p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in [R/'pigment-carrier109/NATIVE_CACHE109.json',R/'pigment-carrier109/NATIVE_DOMAIN109.npz',R/'argon23-runtime113/PIGMENT113.bin']},'GPUExecuted':False,'product77Changed':False}
 assert not unresolved and max(v['pieceCount']for v in rows)==2
 bends=[]
 for index,(start,count)in enumerate(ranges):
  if count==1:bends.append({'enabled':False,'vertices':[0,0,0],'barycentric':[1.,0.,0.],'u':-1.});continue
  a,b=pieces[start:start+2];assert set(a['vertices'])&set(b['vertices'])and abs(a['u'][1]-b['u'][0])<1e-10
  weights=np.array(a['barycentric'][1]);shared=set(a['vertices'])&set(b['vertices']);assert len(shared)==2
  assert all(abs(weights[j])<1e-9 for j,v in enumerate(a['vertices'])if v not in shared)
  bends.append({'enabled':True,'vertices':a['vertices'],'barycentric':weights.tolist(),'u':a['u'][1],'UV':(weights@uv[a['vertices']]).tolist()})
 result['bends']=bends
 def string(f,value):
  raw=value.encode();n=len(raw)
  while n>=128:f.write(bytes([(n&127)|128]));n>>=7
  f.write(bytes([n]));f.write(raw)
 with(G/'UV_BENDS27.bin').open('wb')as f:
  string(f,'native-uv-bends27/v1');string(f,json.loads((R/'argon23-runtime113/SOURCE113.json').read_text())['sourceTopology']);string(f,result['cacheInputs']['argon23-runtime113/PIGMENT113.bin']);f.write(struct.pack('<i',len(bends)))
  for b in bends:f.write(struct.pack('<iiii6f',int(b['enabled']),*b['vertices'],*b['barycentric'],b['u'],*b.get('UV',[0.,0.])))
 result['bendCacheSHA256']=hashlib.sha256((G/'UV_BENDS27.bin').read_bytes()).hexdigest()
 (G/'UV_SURFACE27.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:result[k]for k in ['originalSegments','originalCrossTriangle','pieceCount','maxPiecesPerOriginalSegment','maxRestSurfaceJoinGapMetres','unresolved','GPUExecuted']}))
if __name__=='__main__':main()
