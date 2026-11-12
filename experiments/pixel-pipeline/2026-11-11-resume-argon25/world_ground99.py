"""Bounded CPU audit of recorded world depth against the static ground plane.

The later Editor MeshData snapshot is not old-frame evaluated world geometry.
This checks the conditional static-ground model; grass/wind and unseen alpha
remain unknown. Matching a depth is consistency, not unique owner evidence.
"""
from pathlib import Path
import io,json,struct,hashlib,numpy as np
from actor_visibility96 import packet
H=Path(__file__).resolve().parent

def meshes99(path):
 raw=path.read_bytes();f=io.BytesIO(raw)
 def integer():return struct.unpack('<i',f.read(4))[0]
 def text():
  n=shift=0
  for _ in range(5):
   b=f.read(1);assert b;n|=(b[0]&127)<<shift
   if b[0]<128:break
   shift+=7
  else:raise ValueError('bounded BinaryWriter string')
  assert 0<=n<=8192;return f.read(n).decode('utf-8')
 assert text()=='world-assets99/v1';count=integer();assert 1<=count<=32;rows=[]
 for _ in range(count):
  path,name=text(),text();n,subs,attrs=integer(),integer(),integer();assert 1<=n<=65536 and 1<=subs<=32 and attrs&1
  stride=3+3*bool(attrs&2)+4*bool(attrs&4)+4*bool(attrs&8)+2*bool(attrs&16);v=np.frombuffer(f.read(4*n*stride),'<f4').reshape(n,stride).copy();assert np.isfinite(v).all();tri=[]
  for _ in range(subs):
   k=integer();assert 0<=k<=196608 and k%3==0;i=np.frombuffer(f.read(k*4),'<i4').reshape(-1,3).copy();assert(i>=0).all()and(i<n).all();tri.append(i)
  rows.append({'path':path,'name':name,'vertices':v,'triangles':tri})
 assert not f.read();return rows,hashlib.sha256(raw).hexdigest()

def ground_depth99(view,projection,pixels,y=0.):
 """Native raw texture pixel centres; +Y follows saved CPU projection.

 D3D RT GPU projection flips Y and viewport flips it back. CaptureWorld
 copies the texture without another resample/flip. No fitted UV offset.
 """
 pixels=np.asarray(pixels,dtype=float);inv=np.linalg.inv(projection@view);clip=np.c_[2*(pixels[:,0]+.5)/960-1,2*(pixels[:,1]+.5)/544-1,np.zeros(len(pixels)),np.ones(len(pixels))];a=clip@inv.T;a/=a[:,3:];clip[:,2]=1;b=clip@inv.T;b/=b[:,3:];direction=b-a
 t=(y-a[:,1])/direction[:,1];world=a+direction*t[:,None];depth=-(world@view.T)[:,2];return world[:,:3],depth

def main():
 root=H/'face99/long960';capture=json.loads((root/'capture/COMPLETE.json').read_text());inventory=json.loads((root/'capture/WORLD_INVENTORY99.json').read_text());frames=capture['stream77']['frames'];first=frames[0];assert inventory['sourceId']==first['sourceId']and inventory['frame']==first['frame'];ground,= [v for v in inventory['renderers']if v['name']=='Ground'];meshes,sha=meshes99(H/'face99/world-assets99/details/WORLD_ASSETS99.bin');mesh,=[v for v in meshes if v['name']=='Plane'];matrix=np.array(ground['matrix']).reshape(4,4,order='F');v=np.c_[mesh['vertices'][:,:3],np.ones(len(mesh['vertices']))]@matrix.T;assert np.ptp(v[:,1])<1e-12 and mesh['triangles'][0].shape==(200,3);groundY=float(np.median(v[:,1]));rows=[]
 # Only the inventory's exact frame is used. Applying its transforms to later
 # frames would silently assume static scene/material state not recorded there.
 a,world,depth=packet(root,first);pixels=depth[:,:,2:4].reshape(-1,2);view=np.array(first['sourceFootprint95']['worldView']).reshape(4,4,order='F');projection=np.array(first['sourceFootprint95']['worldProjection']).reshape(4,4,order='F');points,z=ground_depth99(view,projection,pixels,groundY);native=depth[:,:,0].ravel().astype(float);device=depth[:,:,1].ravel();far=first['sourceFootprint95']['far'];near=first['sourceFootprint95']['near'];ulp=np.abs(np.spacing(device))*(far-near);budget=ulp.astype(float)+32*np.finfo(np.float32).eps*(1+np.abs(z));inside=(points[:,0]>=v[:,0].min())&(points[:,0]<=v[:,0].max())&(points[:,2]>=v[:,2].min())&(points[:,2]<=v[:,2].max());match=inside&(np.abs(native-z)<=budget);front=inside&(native<z-budget);behind=inside&(native>z+budget)
 # Roundtrip of projected sample positions is independent of GPU depth.
 reprojection=np.c_[points,np.ones(len(points))]@(projection@view).T;xy=(reprojection[:,:2]/reprojection[:,3:]*.5+.5)*[960,544]-.5;assert np.max(np.abs(xy-pixels))<1e-8
 out={'CPUOnly':True,'frame':first['frame'],'sourceId':first['sourceId'],'worldSerial':first['worldSerial'],'worldInventorySameSourceFrame':True,'sourceAssetSHA256':sha,'assetSnapshotIsLaterNotSameFrameEvaluatedGeometry':True,'conditionalModel':'unchanged static Plane + recorded localToWorld + installed non-tessellated URP_ToonLit position-preserving vertex path','nativePixelCentresNoFittedOffset':True,'projectedRoundtripMaxPixelError':float(np.max(np.abs(xy-pixels))),'samples':len(pixels),'withinRecordedPlaneBounds':int(inside.sum()),'groundDepthConsistentSamples':int(match.sum()),'nearerThanConditionalGround':int(front.sum()),'fartherThanConditionalGround':int(behind.sum()),'minimumActualDepth':float(native.min()),'groundDepthRange':[float(z.min()),float(z.max())],'maximumGroundConsistentError':float(np.max(np.abs(native[match]-z[match])))if match.any()else None,'matchingDepthProvesUniqueOwner':False,'windAlphaAndRuntimeWorldPropertyBlocksCaptured':False,'continuousWorldVisibilitySolved':False,'newWorldPolicyApplied':False}
 (root/'WORLD_GROUND99.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
