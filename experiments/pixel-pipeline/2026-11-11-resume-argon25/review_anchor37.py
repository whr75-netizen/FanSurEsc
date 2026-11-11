from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
import review_runtime36 as common
from test_source_area36 import resolve
from surface_paths34 import native
H=Path(__file__).resolve().parent;G=H/'face37';C=G/'capture';O=G/'analysis';common.C=C
def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and r['actualConsecutive']and not r['errors'];frames=r['frames'];anchor=json.loads((G/'ANCHOR37.json').read_text());surface,binding=native();O.mkdir(exist_ok=True);records=[];inputs=[];outputs=[];colours=[];imgs=[];firstMismatch=None
 for i,f in enumerate(frames):
  frame=f['frame'];a=f['frameInfo']['sourceAnchor'];assert a['indicesUVVerified']and a['sourceKey']==anchor['sourceKey']and f['frameInfo']['timeScale']==0
  qx,qy,w,h=f['QROI'];gx,gy=a['headPixel'];x,y=gx-qx,qy+h-1-gy;initial=common.load(r,frame,'q6');meta=common.load(r,frame,'q7');uv=common.load(r,frame,'q9');gpu=common.load(r,frame,'q18');rgb=common.load(r,frame,'q12')
  if i==0:
   fullQ,fullMeta=common.load(r,frame,'q16'),common.load(r,frame,'q17');q=fullQ[8*y:8*y+8,8*x:8*x+8];m=fullMeta[8*y:8*y+8,8*x:8*x+8];expected=np.zeros_like(gpu);expected[:,:,0]=initial[:,:,1]
   for yy in range(h):
    for xx in range(w):
     mm=meta[yy,xx]
     if mm[0]<=0 or round(mm[1])!=4 or mm[2]!=0:continue
     fq=fullQ[yy*8:yy*8+8,xx*8:xx*8+8];fm=fullMeta[yy*8:yy*8+8,xx*8:xx*8+8];own=(fm[:,:,0]>0)&(np.rint(fm[:,:,1])==4)&(fm[:,:,2]==0)&(fq[:,:,3]>.5)&(fm[:,:,3]>.5);expected[yy,xx]=resolve(initial[yy,xx,1],fq[:,:,0],own,f['frameInfo']['faceSteps'])
   firstMismatch=int(np.any(expected!=gpu,axis=2).sum());assert expected.tobytes()==gpu.tobytes()
  else:q=common.load(r,frame,'q16-watch0');m=common.load(r,frame,'q17-watch0')
  own=(m[:,:,0]>0)&(np.rint(m[:,:,1])==4)&(m[:,:,2]==0)&(q[:,:,3]>.5)&(m[:,:,3]>.5);cpu=np.asarray(resolve(initial[y,x,1],q[:,:,0],own,f['frameInfo']['faceSteps']),np.float32);assert np.array_equal(cpu,gpu[y,x])
  fx=int(np.floor((a['head'][0]-gx)*8));fy=7-int(np.floor((a['head'][1]-gy)*8));assert 0<=fx<8 and 0<=fy<8
  sourcePath=surface.path(np.array(anchor['UV']),uv[y,x,:2],anchor['triangleZeroBased'],int(round(uv[y,x,2]))-1)
  record={'frame':frame,'sourceId':f['sourceId'],'anchor':a,'deltaTime':f['frameInfo']['deltaTime'],'evaluatedFrame':f['frameInfo']['evaluatedFrame'],'Q0':float(initial[y,x,1]),'Qprime':gpu[y,x].tolist(),'CPU':cpu.tolist(),'sampledUV':uv[y,x,:2].tolist(),'sampledPrimitive':int(round(uv[y,x,2]))-1,'nativeSurfacePathKnown':sourcePath['known'],'nearestFineSample':{'pixel':[fx,fy],'role':int(round(m[fy,fx,1]))-1,'depth':float(m[fy,fx,0]),'alpha':float(m[fy,fx,3]),'continuous':float(q[fy,fx,1]),'Q':float(q[fy,fx,0])}}
  records.append(record);inputs.append(hashlib.sha256(initial.tobytes()+meta.tobytes()+uv.tobytes()).hexdigest());outputs.append(hashlib.sha256(gpu.tobytes()).hexdigest());colours.append(hashlib.sha256(rgb.tobytes()).hexdigest())
  panel=Image.new('RGB',(672,270),(35,37,43));d=ImageDraw.Draw(panel);colour=np.clip(rgb[::-1,:,:3],0,1);colour=np.where(colour<=.0031308,12.92*colour,1.055*np.power(colour,1/2.4)-.055)
  for k,(title,p)in enumerate([('actual existing RGB',colour),('source Q0',np.repeat(initial[::-1,:,1:2],3,2)),('runtime Qprime',np.repeat(gpu[::-1,:,0:1],3,2))]):
   im=Image.fromarray(np.uint8(np.rint(np.clip(p,0,1)*255)));panel.paste(im.resize((224,232),Image.Resampling.NEAREST),(224*k,30));d.text((224*k+4,6),title+' F'+str(frame),fill='white')
  panel.save(O/('frame'+str(frame)+'.png'));imgs.append(panel)
 world=np.array([p['anchor']['world']for p in records]);head=np.array([p['anchor']['head']for p in records]);uv=np.array([p['sampledUV']for p in records]);report={'actualFrames':[p['frame']for p in records],'sameCanonicalSourceKey':len(set(p['anchor']['sourceKey']for p in records))==1,'sameActorAndCamera':len(set((p['anchor']['actorInstance'],p['anchor']['camera'])for p in records))==1,'modelUVIndicesVerifiedPerFrame':True,'worldAnchorRange':np.ptp(world,axis=0).tolist(),'projectedAnchorRange':np.ptp(head,axis=0).tolist(),'observedUVFootprintRange':np.ptp(uv,axis=0).tolist(),'nativeSurfacePathsKnown':sum(p['nativeSurfacePathKnown']for p in records),'wholeInputUniqueHashes':len(set(inputs)),'wholeQOutputUniqueHashes':len(set(outputs)),'wholeRGBUniqueHashes':len(set(colours)),'firstROICPUByteMismatch':firstMismatch,'watchCPUMatches':len(records),'actualFinalRGBModified':False,'samePoseFixedPoint':len(set(inputs))==len(set(outputs))==len(set(colours))==1,'records':records,'limits':['Controlled same-pose native-face footprint; no actual translation/rotation/blink suite.','Nearest fine sample is a footprint sample, not an exact mathematical-point shading query or complete world-occlusion proof.','Existing RGB is still original pipeline; no final face colour-region/LUT/outline completion.','No RGB history/averaging or arbitrary geometry fill.']};(O/'SOURCE_ANCHOR37.json').write_text(json.dumps(report,indent=2),encoding='utf-8',newline='\n');imgs[0].save(O/'ANCHORED_SEQUENCE37.webp',save_all=True,append_images=imgs[1:],duration=200,loop=0,lossless=True);print(json.dumps({k:v for k,v in report.items()if k!='records'},indent=2))
if __name__=='__main__':main()
