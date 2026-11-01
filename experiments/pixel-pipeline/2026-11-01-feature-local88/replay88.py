"""Source-backed canonical feature88 on committed real87 open-state input."""
from pathlib import Path
import json,sys,struct,hashlib,math,numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'validated'
sys.path.insert(0,str(ROOT/'feature-audit86'));from analyse87 import load,texture
sys.path.insert(0,str(ROOT/'apply-capture66'));from analyse_capture68 import camera,rgb8
from feature_layer88 import *

def rays(cam):
 view=cam['view'];pv=cam['effective']@view;l=np.eye(4);l[0]=pv[0]*240;l[1]=pv[1]*-136;l[2]=-view[2];l[:3,3]=0;inv=np.linalg.inv(l);off=np.array([240+240*pv[0,3],136-136*pv[1,3],-view[2,3]]);basis=inv[:3,:3];return [-basis@off,basis[:,0],basis[:,1],basis[:,2]]

def depth_at(p,owner,ray,planes,owners):
 plane=np.array(planes[owners.index(owner)]);near=ray[0]+p[0]*ray[1]+p[1]*ray[2];return float(-(np.dot(plane[:3],near)+plane[3])/np.dot(plane[:3],ray[3]))

def canonical(d,source,cache):
 e=d['manifest']['eyeFeature'];owners=[int(v[3])for v in e['centres']];H={owner:np.linalg.inv(np.array(e['inverse'][i]).reshape(4,4,order='F')[:3,:3])for i,owner in enumerate(owners)}
 # Orthographic camera translation changes the anchor, not the feature pose.
 scope=(e['topologySHA256'],d['manifest']['sourceForm86']['sourceSHA'],'paired-eyes/head','registered-open')
 return cache.update(source,H,scope),H

def dotnet_string(f,s):
 b=s.encode();n=len(b)
 while n>127:f.write(bytes([(n&127)|128]));n>>=7
 f.write(bytes([n]));f.write(b)

def write_packet(path,d,state,palette,origin,size,ray):
 m=d['manifest'];e=m['eyeFeature'];owners=[int(v[3])for v in e['centres']]
 with path.open('xb')as f:
  dotnet_string(f,'feature-layer88/v1');dotnet_string(f,d['identity']['sourceId']);f.write(struct.pack('<4i',d['identity']['frameIndex'],d['identity']['renderSerial'],*size));f.write(struct.pack('<f4f',2,*origin,*state['anchor']));f.write(struct.pack('<i',len(state['rows'])))
  for row in state['rows']:f.write(struct.pack('<8f',*row['xy'],row['owner'],row['part'],row['palette'],row['sourceIndex'],row['foregroundArea'],row['partArea']))
  f.write(struct.pack('<i',len(palette)));f.write(np.c_[palette,np.ones(len(palette))].astype('<f4').tobytes());f.write(struct.pack('<4i',*d['eyeROI']))
  for ch in [0,3,4,5,6]:f.write(d['arrays'][f'S{ch}-meta'].astype('<f4').tobytes())
  f.write(np.array(ray,dtype='<f4').tobytes());f.write(np.array(e['planes'],dtype='<f4').tobytes());f.write(np.array(owners,dtype='<i4').tobytes())

def main():
 OUT.mkdir(exist_ok=False);bankpath,_,bank=texture('TemplateRole.asset','<f4');cp,_,colours=texture('TemplateRGBA.asset','u1');source=[];palette8=[]
 for y,x in np.argwhere(np.isin(bank[...,0],[1,4])&np.isin(bank[...,1],[1,2])):
  source.append(SourcePixel(int(x),int(y),int(bank[y,x,1]),int(bank[y,x,0]),len(palette8)));palette8.append(colours[y,x,:3])
 palette8=np.array(palette8);c=palette8.astype(np.float32)/255;palette=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4).astype(np.float32)
 st=json.loads(sorted((ROOT/'feature-audit86/run87').glob('STATE87*.json'))[-1].read_text());entries=[e for e in st['sequencePackets']if e['testStage82']!='blink'];assert len(entries)==24;cache=FeatureCache();data=[]
 for entry in entries:
  d=load(Path(entry['output']));state,H=canonical(d,source,cache);data.append((entry,d,{**state,'rows':[dict(r)for r in state['rows']]}))
 # Fixed display viewport across the sequence; not an output-following crop.
 points=np.concatenate([s['anchor']+np.array([r['xy']for r in s['rows']])for e,d,s in data]);origin=np.floor(points.min(0)-2);size=np.ceil((points.max(0)+2-origin)*2).astype(int)+1;size=tuple(map(int,size));rows=[];images=[];maxDepthError=0;nativePaletteBytes=[]
 for entry,d,state in data:
  m=d['manifest'];owners=[int(v[3])for v in m['eyeFeature']['centres']];ray=rays(camera(Path(entry['output'])/'source.camera'));planes=m['eyeFeature']['planes'];a=d['arrays'];rx,ry,rw,rh=d['eyeROI']
  # Verify reconstructed ray/depth convention against actual333 plane depth.
  x,y,w,h=d['roi'];intr=a['old-intrinsic'];err=[]
  for yy,xx in np.argwhere(intr[...,0]>0):
   z=depth_at([x+xx+.5,271-y-yy+.5],int(round(intr[yy,xx,1])),ray,planes,owners);err.append(abs(z-float(intr[yy,xx,2])))
  maxDepthError=max(maxDepthError,max(err,default=0));assert max(err,default=0)<2e-4
  def vis(p,row):
   sx=int(math.floor((p[0]-rx)*4));sy=int(math.floor((272-p[1]-ry)*4))
   if sx<0 or sy<0 or sx>=rw*4 or sy>=rh*4:return 0.,-1
   metas={s:a[f'S{s}-meta'][sy,sx]for s in [0,3,4,5,6]};return fragment_visibility(metas,depth_at(p,row['owner'],ray,planes,owners),row['owner'])
  intrinsic,identity,fullcov=raster(state['rows'],state['anchor'],palette,origin,size,2);visible,_,coverage=raster(state['rows'],state['anchor'],palette,origin,size,2,vis);assert all(tuple(v)in set(map(tuple,palette8.tolist()))for v in rgb8(intrinsic[intrinsic[...,3]>0,:3]).tolist())
  # Fixed relative shape signature covers owner/part/palette relations together.
  sig=sorted((tuple(r['xy']),r['owner'],r['part'],r['palette'])for r in state['rows']);r={'sourceId':d['identity']['sourceId'],'frame':entry['frame'],'stage':entry['testStage82'],'index':entry['stageIndex82'],'anchor':state['anchor'].tolist(),'rebuild':state['rebuild'],'builds':state['builds'],'deformationResidual':None if not math.isfinite(state['deformationResidual'])else state['deformationResidual'],'numericTolerance':state['numericTolerance'],'cells':state['rows'],'canonicalSignature':hashlib.sha256(repr(sig).encode()).hexdigest(),'intrinsicNativePixels':int((intrinsic[...,3]>0).sum()),'visibleNativePixels':int((visible[...,3]>0).sum()),'partialCoveragePixels':int(((coverage[...,0]>0)&(coverage[...,0]<1)).sum()),'depthMaxError':max(err,default=0)};rows.append(r)
  f=OUT/('frame'+str(entry['frame']));f.mkdir();write_packet(f/'INPUT88.bin',d,state,palette,origin,size,ray);np.savez_compressed(f/'EXPECTED88.npz',colour=visible,identity=identity,coverage=coverage,intrinsic=intrinsic)
  Image.fromarray(rgb8(intrinsic[...,:3])).save(f/'intrinsic-1x.png');Image.fromarray(rgb8(visible[...,:3])).save(f/'visible-1x.png');images.append((intrinsic,visible))
 sweep=[r for r in rows if r['stage']=='sweep'];assert len({r['canonicalSignature']for r in sweep})==1 and not any(r['rebuild']for r in sweep[1:]);assert len({r['intrinsicNativePixels']for r in sweep})==1
 for stage in ['phase','walk','sweep']:
  ids=[i for i,r in enumerate(rows)if r['stage']==stage];ww,hh=size;sheet=Image.new('RGB',(ww*8*len(ids),hh*8*2+50),'#171d24');draw=ImageDraw.Draw(sheet)
  for j,i in enumerate(ids):
   draw.text((j*ww*8+4,4),str(rows[i]['frame'])+' '+stage,fill='white')
   for k,title in enumerate(['intrinsic joint feature','source-fragment visibility']):
    sheet.paste(Image.fromarray(rgb8(images[i][k][...,:3])).resize((ww*8,hh*8),Image.Resampling.NEAREST),(j*ww*8,22+k*(hh*8+14)));draw.text((j*ww*8+3,22+k*(hh*8+14)),title,fill='#ff74c0')
  sheet.save(OUT/(stage+'-joint-vs-visible-nearest8.png'))
  ims=[Image.fromarray(rgb8(images[i][0][...,:3])).resize((ww*8,hh*8),Image.Resampling.NEAREST)for i in ids];ims[0].save(OUT/(stage+'-intrinsic-native2x.gif'),save_all=True,append_images=ims[1:],duration=160,loop=0,disposal=2)
 out={'status':'OFFLINE_CANDIDATE_NOT_PRODUCT','source87':st['sequenceId'],'sourceTemplateSHA':hashlib.sha256(bankpath.read_bytes()).hexdigest(),'sourceColourSHA':hashlib.sha256(cp.read_bytes()).hexdigest(),'originalPixels':len(source),'viewportOrigin':origin.tolist(),'viewportSizeNative':size,'maxReconstructedPlaneDepthError':maxDepthError,'frames':rows,'sweepCanonicalSignatures':len({r['canonicalSignature']for r in sweep}),'sweepIntrinsicNativePixelCounts':sorted({r['intrinsicNativePixels']for r in sweep}),'sweepVisibleNativePixelCounts':[r['visibleNativePixels']for r in sweep],'limits':['Parent/iris/sclera bank is jointly placed. Existing source-native lid is a separate observed occluding layer, not a newly authored canonical lid key-form.','Coverage/depth comes from actual saved4x source fragments; this is not exact analytic alpha-cutout geometry or new temporal observation.','Continuous anchor precedes final2x integer raster; native display still has finite resolution. No claim of sub-raster visible motion.','Only registered open forms used. Closed/reopening forms are explicitly unsupported, not filled with open art.','Final output here is an isolated feature layer. Old-eye removal/clean backing and product compositor are not implemented or validated by this test.']};(OUT/'RESULT88.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='frames'},indent=2))

if __name__=='__main__':main()
