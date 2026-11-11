"""Verify uploaded PIGMENT geometry and strict source rays, not material proxies."""
from pathlib import Path
import hashlib,io,itertools,json,struct,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2];G=H/'native-proof'
sys.path.insert(0,str(R/'resume-20261111'))
from replay_phase25 import FaceWithOneOriginalAlpha,NativeAlpha,geometry,read,buffer
sys.path.insert(0,str(R/'support-contract112'));from source112 import Source
from review_gate import columns

def bindings():
 f=io.BytesIO((R/'argon23-runtime113/PIGMENT113.bin').read_bytes())
 def string():
  n=shift=0
  while True:
   v=f.read(1)[0];n|=(v&127)<<shift
   if v<128:break
   shift+=7
  return f.read(n).decode()
 def integer():return struct.unpack('<i',f.read(4))[0]
 assert string()=='bounded-pigment113/v1';string();count=integer();segments=[]
 for _ in range(count):
  owner=integer();n=integer();points=[]
  for _ in range(n):points.append(struct.unpack('<iiifff',f.read(24)))
  segments.extend((owner,a,b)for a,b in zip(points,points[1:]))
 assert not f.read();return segments

def segment_buffer(path):
 data=path.read_bytes();count,stride=struct.unpack_from('<ii',data)
 assert 0<count<=2048 and stride in [16,32]and len(data)==8+count*stride
 return np.frombuffer(data,dtype='<f4',offset=8).reshape(-1,2,4)

def offset(src,c):
 _,_,mesh=src.binding();solutions=[]
 for permutation in itertools.permutations(range(3)):
  offsets=set()
  for sm,primitive in enumerate(mesh['primitives']):
   rows=np.where((c['sources'][:,0]==1)&(c['sources'][:,1]==sm))[0]
   original=src.accessor(primitive['indices']).reshape(-1,3)[:,permutation]
   assert np.array_equal(c['sources'][rows,2],np.arange(1,len(rows)+1))
   offsets.update(np.unique(c['triangles'][rows,:3].astype(np.int64)-original.astype(np.int64)))
  if len(offsets)==1:solutions.append((permutation,int(next(iter(offsets)))))
 assert len(solutions)==1;at=solutions[0][1]
 uv=src.accessor(mesh['primitives'][0]['attributes']['TEXCOORD_0']);actual=c['uv'][at:at+len(uv)]
 assert min(abs(actual-uv).max(),abs(actual-np.c_[uv[:,0],1-uv[:,1]]).max())<2e-7
 return at

def main():
 global G
 surface='--surface'in sys.argv
 if surface:G=H/'surface27'
 pigment='--pigment'in sys.argv
 motion='--motion'in sys.argv;root=G/('pigment-motion'if motion and pigment else'motion-run'if motion else'pigment-run'if pigment else'phase-run'if surface else'typed-run')
 state=read(next(root.glob('STATE113-*-finished.json')));assert state['PlayExited']and not state.get('error')
 segments=bindings();src=Source();metadata=read(R/'aperture-runtime111/inputs/ALPHA111.json')
 alphaSrc=next(v for v in metadata['images']if v['renderer']==1 and v['submesh']==3)
 ip=R/'aperture-runtime111/inputs'/alphaSrc['file'];assert hashlib.sha256(ip.read_bytes()).hexdigest()==alphaSrc['sha256']
 im=Image.open(ip);image=np.array(im.convert('RGBA'))[:,:,3].astype(float)/255;im.close()
 rows=[];nativeMax=coordinateMax=0.;rayCount=0;pigmentAlphaChecks=0
 pigmentImage=np.load(R/'pigment-carrier109/NATIVE_DOMAIN109.npz')['rgba'][:,:,3]if pigment else None
 for pkt in state['sequencePackets']:
  p=Path(pkt['output']);m=read(p/'RAW_MANIFEST.json');c=geometry(p,m);base=offset(src,c)
  native=segment_buffer(p/'CURVE-native26.f32');display=segment_buffer(p/'curve-segments106.f32')
  bends=buffer(p/'CURVE-bend27.f32')if surface else None;surfaceData=read(G/'UV_SURFACE27.json')if surface else None
  assert len(native)==len(display)==len(segments)==846
  certain=np.array([set(a[:3])==set(b[:3])for _,a,b in segments]);assert certain.sum()==804
  if surface:
   assert int((bends[:,3]>0).sum())==42
   certain[:]=True
  expected=[]
  for owner,a,b in segments:
   expected.append([np.r_[np.array(q[3:],np.float32)@c['world4'][base+np.array(q[:3]),:3],0]for q in [a,b]])
  expected=np.array(expected);expected[:,:,3]=certain[:,None]
  # Captured world vertices were transformed before interpolation; the live
  # Point() interpolates local vertices before transforming. Record rounding
  # difference; verify its actual visibility effect below instead of silently
  # widening an endpoint tolerance.
  error=float(abs(expected-native).max());nativeMax=max(nativeMax,error);assert np.isfinite(error)
  cols=columns(p/'SOURCE-columns26.f32');nq=buffer(p/'COLUMN-native26.f32').reshape(-1,4)
  if pigment:
   tag=m['pigmentMaterialBinding27'];assert tag['actualGPUProofRecord']and[tag['part'],tag['submesh'],tag['renderer']]==[3,6,1]and tag['sourceId']==m['sourceId']and tag['frame']==m['frameIndex']
   for col in cols:
    if col[1,2]<=0:continue
    uu,vv=col[1,:2];xx,yy=np.floor([float(uu)*pigmentImage.shape[1]-.5,(1-float(vv))*pigmentImage.shape[0]-.5]).astype(int)
    assert 0<=xx<pigmentImage.shape[1]-1 and 0<=yy<pigmentImage.shape[0]-1
    patch=pigmentImage[yy:yy+2,xx:xx+2];lo=np.float32(patch.min())/np.float32(255);hi=np.float32(patch.max())/np.float32(255)
    assert round(float(col[1,3])*255)==int(patch.min())and round(float(col[2,3])*255)==int(patch.max())
    assert abs(float(lo)-float(col[1,3]))<=abs(float(np.spacing(lo)))and abs(float(hi)-float(col[2,3]))<=abs(float(np.spacing(hi)))
    pigmentAlphaChecks+=1
  valid=[];associations=[];originalQueries={}
  for ci,col in enumerate(cols):
   if col[0,3]<=0:continue
   point=col[0,:2].astype(float);a=display[:,0,:2].astype(float);d=display[:,1,:2].astype(float)-a;ds=(d*d).sum(1)
   u=((point-a)*d).sum(1)/np.maximum(ds,1e-30);dist=np.linalg.norm(a+u[:,None]*d-point,axis=1)
   validSegments=np.array([v[0]==int(col[0,3])for v in segments])&(u>=-1e-4)&(u<=1+1e-4)
   dist[~validSegments]=np.inf;si=int(dist.argmin());assert dist[si]<3e-5
   if not certain[si]:
    assert np.array_equal(nq[ci],np.zeros(4))and np.array_equal(col[2,:2],[0,1])
    associations.append({'column':ci,'segment':si,'state':'unknown cross-triangle source span'});continue
   def interpolate(endpoints,bend=None):
    if bend is not None and 0<bend[3]<1:
     t=u[si]/bend[3]if u[si]<bend[3]else(u[si]-bend[3])/(1-bend[3]);aa,bb=(endpoints[0,:3],bend[:3])if u[si]<bend[3]else(bend[:3],endpoints[1,:3]);return(1-t)*aa+t*bb
    return(1-u[si])*endpoints[0,:3]+u[si]*endpoints[1,:3]
   world=interpolate(native[si],bends[si]if surface else None);vv=c['view']@np.r_[world,1];clip=c['projection']@vv
   q=np.array([(clip[0]/clip[3]*.5+.5)*480,(.5-clip[1]/clip[3]*.5)*272,-vv[2],col[0,3]])
   err=float(abs(q-nq[ci]).max());coordinateMax=max(coordinateMax,err);assert err<1e-4
   originalBend=None
   if surface and surfaceData['bends'][si]['enabled']:
    bb=surfaceData['bends'][si];originalBend=np.r_[np.array(bb['barycentric'])@c['world4'][base+np.array(bb['vertices']),:3],bb['u']]
    assert abs(originalBend-bends[si]).max()<3e-6
   world2=interpolate(expected[si],originalBend);vv2=c['view']@np.r_[world2,1];clip2=c['projection']@vv2
   originalQueries[ci]=np.array([(clip2[0]/clip2[3]*.5+.5)*480,(.5-clip2[1]/clip2[3]*.5)*272,-vv2[2],col[0,3]])
   if col[1,3]>0:valid.append(ci)
   associations.append({'column':ci,'segment':si,'nativeQuery':nq[ci].tolist(),'state':'exact single-triangle source span','sourceFaceVisibility':col[2,:2].tolist()})
  mi=np.unique(c['triangles'][(c['sources'][:,0]==1)&(c['sources'][:,1]==3),3]);assert len(mi)==1
  alpha=NativeAlpha.__new__(NativeAlpha);alpha.ctx=c;alpha.images={int(mi[0]):image};alpha.sources={int(mi[0]):alphaSrc}
  face=FaceWithOneOriginalAlpha(c,np.zeros(4232,np.uint32),alpha)
  for ci in valid:
   q=nq[ci];cpu=face.query([q[:2]],[q[2]],int(q[3]),limit=m['runtime24']['socketDiameters'][int(q[3])-1])[0]
   assert np.array_equal(cpu['faceInterval'],cols[ci,2,:2]),(m['sourceId'],ci,cpu['faceInterval'],cols[ci,2,:2])
   qq=originalQueries[ci];original=face.query([qq[:2]],[qq[2]],int(qq[3]),limit=m['runtime24']['socketDiameters'][int(qq[3])-1])[0]
   assert np.array_equal(original['faceInterval'],cols[ci,2,:2]),('native interpolation rounding changes visibility',m['sourceId'],ci)
   rayCount+=1
  rows.append({'sourceId':m['sourceId'],'frame':m['frameIndex'],'nativeCurveEndpointMaxError':error,'validStrictRaysCPUExact':len(valid),'columns':associations})
 result={'frames':len(rows),'sourceCurveSegments':846,'exactSingleTriangleSegments':804,'crossTriangleUnknownSegments':0 if surface else 42,'piecewiseNativeSurfacePieces':888 if surface else None,'nativePigmentAlphaBoundsCPUChecks':pigmentAlphaChecks,'uploadedEndpointMaxErrorMetres':nativeMax,'nativeQueryMaxErrorPxOrMetres':coordinateMax,'strictSourceGPURaysCPUExact':rayCount,'worldInterpolationOrderVisibilityChanges':0,'rows':rows,
  'sourceMaterialProofIsNotGeometryProof':True,'strictSourceOwnAndSharedMasksExcluded':True,'earlierWrongPartAuditWithdrawn':True,'scope':'CPU checks of actual recorded GPU column queries and uploaded original PIGMENT geometry. No GPU call.'}
 (G/('NATIVE_MOTION26.json'if motion else'NATIVE_PROOF26.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
if __name__=='__main__':main()
