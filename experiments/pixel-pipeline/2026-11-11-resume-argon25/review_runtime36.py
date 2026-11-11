"""Compare actual runtime source-area output against independent source samples."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from test_source_area36 import resolve
H=Path(__file__).resolve().parent;G=H/'face36';C=G/'fix1/capture';O=G/'analysis'
def load(r,frame,name):
 rows=sorted([p for p in r['planes']if p['frame']==frame and p['name']==name],key=lambda p:p['bottomRow']);assert rows,name
 w,h=rows[0]['width'],rows[0]['height'];a=np.empty((h,w,4),np.float32);at=0
 for p in rows:
  assert p['bottomRow']==at and p['sourceId']==next(f['sourceId']for f in r['frames']if f['frame']==frame);raw=(C/p['file']).read_bytes();assert len(raw)==p['rows']*w*16;a[at:at+p['rows']]=np.frombuffer(raw,'<f4').reshape(p['rows'],w,4);at+=p['rows']
 assert at==h and np.isfinite(a).all();return a
def components(q,face):
 h,w=face.shape;result={}
 for v in np.unique(q[face]):
  m=face&(q==v);seen=np.zeros_like(m);sizes=[]
  for y,x in np.argwhere(m):
   if seen[y,x]:continue
   todo=[(y,x)];seen[y,x]=True
   for yy,xx in todo:
    for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]:
     b,a=yy+dy,xx+dx
     if 0<=b<h and 0<=a<w and m[b,a]and not seen[b,a]:seen[b,a]=True;todo.append((b,a))
   sizes.append(len(todo))
  result[str(float(v))]=sorted(sizes,reverse=True)
 return result
def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['actualConsecutive']and r['ownedResourcesReleased']and r['restorationChecksPass']and not r['errors'];frames=r['frames'];assert len(frames)==6 and [f['frame']for f in frames]==list(range(frames[0]['frame'],frames[0]['frame']+6));O.mkdir(exist_ok=True)
 source=json.loads((G/'WATCH36.json').read_text());watch=[];states=[];imgs=[];firstMismatch=0;fineError=None;firstCells=None
 for i,fr in enumerate(frames):
  frame=fr['frame'];q0=load(r,frame,'q6')[:,:,1];meta=load(r,frame,'q7');uv=load(r,frame,'q9');gpu=load(r,frame,'q18');rgb=load(r,frame,'q12');face=(meta[:,:,0]>0)&(np.rint(meta[:,:,1])==4);coords=fr['QROI'];qx,qy,w,h=coords
  if i==0:
   fq,fm=load(r,frame,'q16'),load(r,frame,'q17');expected=np.zeros_like(gpu);expected[:,:,0]=q0;errorOld=errorNew=0
   for y in range(h):
    for x in range(w):
     if not(face[y,x]and meta[y,x,2]==0):continue
     q=fq[8*y:8*y+8,8*x:8*x+8];m=fm[8*y:8*y+8,8*x:8*x+8];own=(m[:,:,0]>0)&(np.rint(m[:,:,1])==4)&(m[:,:,2]==0)&(q[:,:,3]>.5)&(m[:,:,3]>.5);expected[y,x]=resolve(q0[y,x],q[:,:,0],own,fr['frameInfo']['faceSteps'])
     if own.all():errorOld+=int((q[:,:,0]!=q0[y,x]).sum());errorNew+=int((q[:,:,0]!=gpu[y,x,0]).sum())
   firstCells=w*h;firstMismatch=int(np.any(expected!=gpu,axis=2).sum());fineError={'originalMismatchSubsamples':errorOld,'candidateMismatchSubsamples':errorNew,'differenceInCellArea':(errorNew-errorOld)/64};assert expected.tobytes()==gpu.tobytes(),'Actual GPU source-area differs from CPU source oracle'
  changed=np.argwhere(face&(gpu[:,:,0]!=q0));xy=[[int(qx+x),int(qy+h-1-y)]for y,x in changed];assert not np.any((~face)&(gpu[:,:,0]!=q0))
  before,after=components(q0,face),components(gpu[:,:,0],face)
  states.append({'frame':frame,'sourceId':fr['sourceId'],'cameraInstance':fr['frameInfo']['view'].split('/')[0],'model':fr['frameInfo']['model'],'deltaTime':fr['frameInfo'].get('deltaTime'),'evaluatedFrame':fr['frameInfo'].get('evaluatedFrame'),'renderedSource':fr['frameInfo'].get('renderedSource'),'changed':xy,'componentsBefore':before,'componentsAfter':after,'GPUStatusCounts':{str(int(v)):int(n)for v,n in zip(*np.unique(gpu[:,:,3],return_counts=True))}})
  for wi,(gx,gy)in enumerate(source['points']):
   x,y=gx-qx,qy+h-1-gy
   if i==0:q=fq[y*8:y*8+8,x*8:x*8+8];m=fm[y*8:y*8+8,x*8:x*8+8]
   else:q=load(r,frame,'q16-watch'+str(wi));m=load(r,frame,'q17-watch'+str(wi))
   own=(m[:,:,0]>0)&(np.rint(m[:,:,1])==4)&(m[:,:,2]==0)&(q[:,:,3]>.5)&(m[:,:,3]>.5);cpu=np.asarray(resolve(q0[y,x],q[:,:,0],own,fr['frameInfo']['faceSteps']),np.float32);assert np.array_equal(cpu,gpu[y,x])
   vals,cnt=np.unique(q[:,:,0][own],return_counts=True);watch.append({'frame':frame,'xy':[gx,gy],'initial':float(q0[y,x]),'GPU':gpu[y,x].tolist(),'CPU':cpu.tolist(),'sourceQCounts':{str(float(v)):int(n)for v,n in zip(vals,cnt)},'UV':uv[y,x,:2].tolist(),'continuousRange':[float(q[:,:,1].min()),float(q[:,:,1].max())]})
  # Actual colour remains the existing renderer. Q panels are metadata previews,
  # never advertised as a completed colour/outline rendering.
  panel=Image.new('RGB',(3*224,270),(35,37,43));draw=ImageDraw.Draw(panel)
  colour=np.clip(rgb[::-1,:,:3],0,1);colour=np.where(colour<=.0031308,12.92*colour,1.055*np.power(colour,1/2.4)-.055)
  for k,(title,a)in enumerate([('actual existing RGB',colour),('initial Q',np.repeat(q0[::-1,:,None],3,2)),('runtime area Qprime',np.repeat(gpu[::-1,:,0:1],3,2))]):
   im=Image.fromarray(np.uint8(np.rint(np.clip(a,0,1)*255)));im.resize((224,232),Image.Resampling.NEAREST).save(O/('frame'+str(frame)+'-'+str(k)+'-nearest.png'));panel.paste(im.resize((224,232),Image.Resampling.NEAREST),(224*k,30));draw.text((224*k+5,6),title+' F'+str(frame),fill='white')
  panel.save(O/('frame'+str(frame)+'-comparison.png'));imgs.append(panel)
 strip=Image.new('RGB',(imgs[0].width,imgs[0].height*len(imgs)),(35,37,43))
 for i,p in enumerate(imgs):strip.paste(p,(0,i*p.height))
 strip.save(O/'SIX_ACTUAL_FRAMES36.png');imgs[0].save(O/'Q_AREA_SEQUENCE36.webp',save_all=True,append_images=imgs[1:],duration=200,loop=0,lossless=True)
 uvWatch=np.array([p['UV']for p in watch]);summary={'actualConsecutiveFrames':[f['frame']for f in frames],'firstWholeROICPUComparisonCells':int(firstCells),'firstWholeROIByteMismatch':firstMismatch,'watchCPUComparisons':len(watch),'watchGPUQValues':sorted(set(p['GPU'][0]for p in watch)),'watchInitialQValues':sorted(set(p['initial']for p in watch)),'watchUVRange':(uvWatch.max(0)-uvWatch.min(0)).tolist(),'sameSourcePointTemporalStabilityValidated':False,'sourceAreaError':fineError,'actualFinalRGBModified':False,'product77DefaultChanged':False,'states':states,'watch':watch,'limits':['Six consecutive normal Animator-driven renders; deltaTime=.3333s and source pose changes. Not a locked-pose or rotation/walk/subpixel suite.','The same screen coordinate samples different source UV. Its constant Q is not a source-feature history/stability proof.','No source colour-region/LUT or final outline activation.','Area reference is directly observed source lighting, not an authored art ground truth.','Diagnostic view handle GUID varies per owner; cameraInstance/model prove common physical view, no temporal cache was claimed.']};(O/'GPU_AREA36.json').write_text(json.dumps(summary,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in summary.items()if k not in ['states','watch']},indent=2))
if __name__=='__main__':main()
