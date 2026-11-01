"""Actual89 GPU packets. Source-visible warp and raw retarget are separate.

No RGB averaging, inferred backing, runtime calls or artist intent claims.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'apply-capture66'));from analyse_capture68 import plane,Reader,camera,rgb8
sys.path.insert(0,str(ROOT/'eye-observer73'));from analyse73 import read
sys.path.insert(0,str(HERE));from native_raster89 import mesh
PARTS=[3,1,4,6]
REST=np.load(ROOT/'whole-eye52/SOURCE_SURFACES52.npz')['native_xyz_head']
REG=json.loads((HERE/'REGISTRATION89.json').read_text())
PROJ={e['eye']:np.asarray(e['nativeToAuthoredProjection'])for e in REG['eyes']}

def packet(path):
 m=json.loads((path/'RAW_MANIFEST.json').read_text());assert(path/'RAW_COMPLETE76.marker').read_text()==hashlib.sha256((path/'RAW_MANIFEST.json').read_bytes()).hexdigest()
 a={};heads={}
 for p in path.glob('*.plane'):
  h,v=plane(p);assert all(h[k]==m[k]for k in ['sourceId','frameIndex']);assert h['renderSerial']==m['mainSerial'];assert np.isfinite(v).all();a[p.stem]=v;heads[p.stem]=h
 r=Reader(path/'baseline76.buffer');assert r.s()=='baseline76/v1';ident=[r.s(),r.s(),r.i(),r.i()];roi=[r.i()for _ in range(4)];assert r.i()==96
 baseline=r.a(roi[2]*roi[3]*24).reshape(roi[3],roi[2],6,4);r.end()
 h,c=read(path/'eye-counts76.bin.partial',True);h,z=read(path/'eye-records76.bin.partial',False)
 return {'path':path,'m':m,'a':a,'heads':heads,'baseline':baseline,'roi':roi,'records':z.reshape(z.shape[0],z.shape[1],16,4),'eyeROI':h['roi']}

def barycentric(points,tri):
 v0=tri[:,1]-tri[:,0];v1=tri[:,2]-tri[:,0];v2=points-tri[:,0]
 a=(v0*v0).sum(1);b=(v0*v1).sum(1);c=(v1*v1).sum(1);d=(v2*v0).sum(1);e=(v2*v1).sum(1);den=a*c-b*b
 assert (abs(den)>1e-20).all()
 u=(d*c-e*b)/den;v=(e*a-d*b)/den;return np.c_[1-u-v,u,v]

def geometry(d):
 m=d['m'];a=d['a'];v,n,uv,tris,world=mesh(d['path']/'eye-evaluated.mesh');head=np.asarray(m['eyeFeature']['headMatrix']).reshape(4,4,order='F');wh=np.linalg.inv(head);cam=camera(d['path']/'source.camera');worldv=np.c_[v,np.ones(len(v))]@world.T
 H={int(c[3]):np.linalg.inv(np.asarray(m['eyeFeature']['inverse'][i]).reshape(4,4,order='F')[:3,:3])for i,c in enumerate(m['eyeFeature']['centres'])};anchor=np.asarray(m['retarget89']['anchor']);bounds=np.asarray(m['retarget89']['bounds']);layers=[];worlds=[];physical=[];local=[];orientation=[];depthErrors=[]
 for part,sm in enumerate(PARTS):
  layer=[a[f'retarget-part{part}-{ch}']for ch in range(5)];h,w=layer[0].shape[:2];valid=layer[1][...,0]>0;yy,xx=np.where(valid);ix=tris[sm][np.rint(layer[3][valid,2]).astype(int)-1];b=barycentric(layer[2][valid,:3].astype(float),REST[ix]);wp=np.einsum('ni,nij->nj',b,worldv[ix]);restCurrent=wp@wh.T;q=np.empty((len(wp),2));owner=np.rint(layer[1][valid,2]).astype(int)
  for sid in PROJ:
   take=owner==sid;source=restCurrent[take]@PROJ[sid];p=np.c_[source,np.ones(take.sum())]@H[sid].T;q[take]=p[:,:2]/p[:,2,None]-anchor
  expectedX=bounds[0]+(xx+.5)/4;ys=[bounds[1]+(yy+.5)/4,bounds[3]-(yy+.5)/4];errors=[float(np.max(np.linalg.norm(q-np.c_[expectedX,y],axis=1),initial=0))for y in ys];flip=int(np.argmin(errors));orientation.append(errors);depthErrors.append(float(np.max(abs(-(wp@cam['view'].T)[:,2]-layer[1][valid,0]),initial=0)))
  g=np.zeros((h,w,4));g[valid]=wp;xy=np.zeros((h,w,2));clip=wp@(cam['projection']@cam['view']).T;xy[valid]=np.c_[(clip[:,0]/clip[:,3]*.5+.5)*480,(.5-clip[:,1]/clip[:,3]*.5)*272];loc=np.zeros((h,w,2));loc[valid]=q
  if flip:layer=[x[::-1].copy()for x in layer];g=g[::-1].copy();xy=xy[::-1].copy();loc=loc[::-1].copy()
  layers.append(layer);worlds.append(g);physical.append(xy);local.append(loc)
 assert max(min(e)for e in orientation)<.005,orientation
 # Same source camera physical sample projection is checked against actual S3.
 sourceErrors=[];ph=a['S3-meta'];yy,xx=np.where(ph[...,0]>0)
 if len(xx):
  ix=tris[6][np.rint(a['S3-uv'][yy,xx,2]).astype(int)-1];b=barycentric(a['S3-point'][yy,xx,:3],REST[ix]);wp=np.einsum('ni,nij->nj',b,worldv[ix]);clip=wp@(cam['projection']@cam['view']).T;xy=np.c_[(clip[:,0]/clip[:,3]*.5+.5)*480,(.5-clip[:,1]/clip[:,3]*.5)*272];rx,top,rw,rh=m['eyeFeature']['roiTopLeft'];actual=np.c_[rx+(xx+.5)/4,top+rh-(yy+.5)/4];sourceErrors=np.linalg.norm(xy-actual,axis=1).tolist()
 return layers,np.asarray(physical),{'canonicalProjectionErrors':orientation,'depthMaxErrors':depthErrors,'sourcePhysicalProjectionMax':max(sourceErrors,default=0)}

def visibility(d,layers,physical):
 a=d['a'];m=d['m'];rx,top,rw,rh=m['eyeFeature']['roiTopLeft'];out=np.ones((4,)+layers[0][0].shape[:2]);unknown=np.zeros_like(out,dtype=bool)
 v,n,uv,tris,world=mesh(d['path']/'eye-evaluated.mesh');cam=camera(d['path']/'source.camera');wp=np.c_[v,np.ones(len(v))]@world.T;clip=wp@(cam['projection']@cam['view']).T;vertices=np.c_[(clip[:,0]/clip[:,3]*.5+.5)*480,(.5-clip[:,1]/clip[:,3]*.5)*272,-(wp@cam['view'].T)[:,2]]
 for part in range(4):
  xy=physical[part];xx=np.floor((xy[...,0]-rx)*4).astype(int);yy=rh*4-1-np.floor((xy[...,1]-top)*4).astype(int);valid=layers[part][1][...,0]>0;inside=(xx>=0)&(xx<rw*4)&(yy>=0)&(yy<rh*4);unknown[part]=valid&~inside;out[part,~inside]=0;px=np.clip(xx,0,rw*4-1);py=np.clip(yy,0,rh*4-1);depth=layers[part][1][...,0]
  # Every actual physical source layer may occlude, including real skin/lid.
  # A single foreground sample does not discard an entire logical cell.
  for src in range(7):
   sample=a[f'S{src}-meta'][py,px];sampleDepth=sample[...,0].copy();exists=sampleDepth>0
   if src<4:
    # Re-evaluate the selected actual triangle at the QUERY ray. Comparing
    # its neighbouring sample depth directly can occlude a surface by itself.
    ids=np.maximum(0,np.rint(a[f'S{src}-uv'][py,px,2]).astype(int)-1);t=vertices[tris[[3,4,1,6][src]][ids]];p0=t[...,0,:2];u=t[...,1,:2]-p0;v2=t[...,2,:2]-p0;q=xy-p0;den=u[...,0]*v2[...,1]-u[...,1]*v2[...,0];safe=np.where(abs(den)>1e-12,den,1);bu=(q[...,0]*v2[...,1]-q[...,1]*v2[...,0])/safe;bv=(u[...,0]*q[...,1]-u[...,1]*q[...,0])/safe;inside=(abs(den)>1e-12)&(bu>=-1e-4)&(bv>=-1e-4)&(bu+bv<=1.0001);unknown[part]|=valid&exists&~inside;exists&=inside;sampleDepth=t[...,0,2]*(1-bu-bv)+t[...,1,2]*bu+t[...,2,2]*bv
   front=exists&(sampleDepth<depth-3e-5);alpha=np.where(front,np.clip(sample[...,3],0,1),0);out[part]*=1-alpha
 return out,unknown

def joint(layers,visible,raw):
 rgba=np.stack([s[0]for s in layers]);meta=np.stack([s[1]for s in layers]);h,w=rgba.shape[1:3];depth=np.where(meta[...,0]>0,meta[...,0],np.inf);alpha=np.clip(rgba[...,3],0,1);weight=np.zeros_like(alpha)
 if raw:
  order=np.argsort(depth,axis=0,kind='stable');T=np.ones((h,w))
  for rank in range(4):
   k=order[rank];v=T*np.take_along_axis(alpha,k[None],axis=0)[0];np.put_along_axis(weight,k[None],v[None],axis=0);T*=1-np.take_along_axis(alpha,k[None],axis=0)[0]
 else:
  # Skin is an actual physical visibility test at the source eye point,
  # not a face point from elsewhere that happens to alias after warping.
  weight=alpha*visible;weight[0]=0
  # Eye parts still share a single colour/owner decision and depth ordering.
  order=np.argsort(depth[1:],axis=0,kind='stable')+1;T=np.ones((h,w));weight[:]=0
  for rank in range(3):
   k=order[rank];aa=np.take_along_axis(alpha*visible,k[None],axis=0)[0];v=T*aa;np.put_along_axis(weight,k[None],v[None],axis=0);T*=1-aa
 ch,cw=h//4,w//4;mass=weight.reshape(4,ch,4,cw,4).sum((2,4));winner=np.argmax(mass,axis=0);valid=mass.max(0)>0
 if not raw:
  backing=(1-weight.sum(0)).reshape(ch,4,cw,4).sum((1,3));valid&=mass.max(0)>backing
 colour=np.zeros((ch,cw,4));identity=np.zeros_like(colour);details=[]
 for y,x in np.argwhere(valid):
  p=winner[y,x];patch=weight[p,y*4:y*4+4,x*4:x*4+4];sy,sx=np.unravel_index(np.argmax(patch),patch.shape);sy+=y*4;sx+=x*4;colour[y,x]=rgba[p,sy,sx];colour[y,x,3]=1;identity[y,x]=[PARTS[p],meta[p,sy,sx,2],mass[p,y,x]/16,meta[p,sy,sx,0]];details.append({'cell':[int(x),int(y)],'part':PARTS[p],'owner':int(round(float(meta[p,sy,sx,2]))),'sample':[int(sx),int(sy)],'primitive':int(round(float(layers[p][3][sy,sx,2]))),'UV':layers[p][3][sy,sx,:2].tolist(),'RGB8':rgb8(rgba[p,sy,sx,:3]).tolist(),'coverageMass':float(mass[p,y,x]/16)})
 return colour,identity,details,weight

def main():
 run=HERE/'capture89f';state=json.loads(sorted(run.glob('STATE89-*.json'))[-1].read_text());assert state['PlayExited']and not state.get('error')and not state.get('restorationError');assert len(state['sequencePackets'])==32
 out=HERE/'result89-ray';out.mkdir(exist_ok=False);rows=[];boards={};allDetails=[]
 for entry in state['sequencePackets']:
  d=packet(Path(entry['output']));layers,physical,geom=geometry(d);assert geom['sourcePhysicalProjectionMax']<.005,geom
  vis,unknown=visibility(d,layers,physical);c0,id0,det0,w0=joint(layers,vis,True);c1,id1,det1,w1=joint(layers,vis,False);m=d['m'];frame=m['frameIndex'];stage=entry['testStage82'];idx=entry['stageIndex82'];bounds=m['retarget89']['bounds'];np.savez_compressed(out/f'frame{frame}.npz',rawColour=c0,rawIdentity=id0,visibleColour=c1,visibleIdentity=id1,visibleSamples=vis,physical=physical,**{f'rgba{p}':v[0]for p,v in enumerate(layers)},**{f'meta{p}':v[1]for p,v in enumerate(layers)})
  for name,c in [('raw',c0),('source-visible',c1)]:Image.fromarray(rgb8(c[...,:3])).save(out/f'{stage}{idx}-{name}-1x.png')
  original=np.flipud(rgb8(d['a']['head-final'][...,:3]));Image.fromarray(original).save(out/f'{stage}{idx}-product77-1x.png');local=rgb8(c1[...,:3]);panel=Image.new('RGB',(max(original.shape[1],local.shape[1])*12*3,max(original.shape[0],local.shape[0])*12+30),'#141922');dr=ImageDraw.Draw(panel)
  for i,(title,pic)in enumerate([('Product77 same frame',original),('Raw coupled native depth',rgb8(c0[...,:3])),('Physical source visible - candidate',local)]):panel.paste(Image.fromarray(pic).resize((pic.shape[1]*12,pic.shape[0]*12),Image.Resampling.NEAREST),(i*(panel.width//3),30));dr.text((i*(panel.width//3)+3,8),title,fill='white')
  panel.save(out/f'{stage}{idx}-comparison12.png');boards.setdefault(stage,[]).append(panel)
  def counts(identity):return{str(p):int((identity[...,0]==p).sum())for p in PARTS}
  row={'frame':frame,'sourceId':m['sourceId'],'stage':stage,'index':idx,'CloseGetter':m['eyeFeature']['closeMorphs']['Fcl_EYE_Close'],'evaluatedMeshSHA256':hashlib.sha256((d['path']/'eye-evaluated.mesh').read_bytes()).hexdigest(),'anchor':m['retarget89']['anchor'],'bounds':bounds,'rawCounts':counts(id0),'sourceVisibleCounts':counts(id1),'geometry':geom,'unknownVisibilitySamples':int(unknown.sum()),'nativeAlphaOrLightingPolicy':'literal observed RGBA; no RGB mix; original producer continuous shade mismatch blocks adoption','visibleSignature':hashlib.sha256(id1[...,:2].astype('<i4').tobytes()).hexdigest()};rows.append(row);allDetails.append({'frame':frame,'raw':det0,'sourceVisible':det1})
 for stage,pics in boards.items():
  # A bounded readable strip; animated GIF retains original individual panels.
  pics[0].save(out/(stage+'.gif'),save_all=True,append_images=pics[1:],duration=350,loop=0)
  selected=range(len(pics))if len(pics)<=8 else[0,1,3,5,7,9];canvas=Image.new('RGB',(pics[0].width,pics[0].height*len(selected)),'#141922')
  for y,i in enumerate(selected):canvas.paste(pics[i],(0,y*pics[i].height))
  canvas.save(out/(stage+'-strip.png'))
 (out/'CELL_PROVENANCE89.json').write_text(json.dumps(allDetails,indent=2)+'\n');(out/'RESULT89.json').write_text(json.dumps({'status':'REAL_GPU_SOURCE_WITH_OFFLINE_JOINT_CANDIDATES_NOT_ADOPTED','rows':rows,'limitations':['Continuous illumination control differs; source-visible candidate uses physical source4x visibility with finite sampling, not exact analytic alpha visibility.','Source-visible joint assignment and whole-character composition not GPU integrated yet.','Raw native joint depth can introduce occlusion between points that were separate in physical source projection.','Reference palette is literal observed source; not artist approval.']},indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items()if k in ['frame','stage','index','CloseGetter','rawCounts','sourceVisibleCounts','unknownVisibilitySamples']}for r in rows],indent=2))

if __name__=='__main__':main()
