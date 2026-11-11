"""Same-frame geometry/effective normal ablation; never relax a threshold."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;G=H/'face34';C=G/'capture';O=G/'analysis'
def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];w,h=r['QROI'][2:];qx,qy=r['QROI'][:2]
 def field(n):
  p=[p for p in r['planes']if p['name']==n];assert len(p)==1 and p[0]['rows']==h and p[0]['bottomRow']==0
  return np.fromfile(C/p[0]['file'],dtype='<f4').reshape(h,w,4)
 eff,geom,meta,cls,mask=map(field,['q8','q10','q7','q5','q6']);old=mask[:,:,1];face=(np.rint(meta[:,:,1])==4)&(cls[:,:,3]>.5)
 def norm(a):
  a=a[:,:,:3].copy();return np.divide(a,np.linalg.norm(a,axis=2)[:,:,None],out=np.zeros_like(a),where=np.linalg.norm(a,axis=2)[:,:,None]>0)
 dirs=[(-1,0),(1,0),(0,-1),(0,1)];ring=[(-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)];nn=[norm(eff),norm(geom)];records=[]
 for y,x in np.argwhere(face):
  rows=[]
  for normals in nn:
   reasons=set();dots=[];depths=[]
   def neighbour(xx,yy):
    if not(0<=xx<w and 0<=yy<h):reasons.add('outside captured halo');return False
    m,n=meta[y,x],meta[yy,xx]
    if n[0]<=0 or abs(n[1]-m[1])>.1 or abs(n[2]-m[2])>.1 or cls[yy,xx,3]<.5:reasons.add('role/owner/alpha');return False
    dot=float(np.dot(normals[y,x],normals[yy,xx]));delta=float(abs(cls[yy,xx,2]-cls[y,x,2]));dots.append(dot);depths.append(delta)
    if dot<=.94:reasons.add('normal')
    if delta>=r['frameInfo']['worldPixel']*2:reasons.add('depth')
    return dot>.94 and delta<r['frameInfo']['worldPixel']*2
   safe=True
   for dx,dy in ring:safe=neighbour(x+dx,y+dy)and safe
   bits=[old[np.clip(y+dy,0,h-1),np.clip(x+dx,0,w-1)]for dx,dy in ring];q=old[y,x];card=[old[np.clip(y+dy,0,h-1),np.clip(x+dx,0,w-1)]for dx,dy in dirs];same=sum(abs(v-q)<.01 for v in card);opposite=next((v for v in card[::-1]if abs(v-q)>=.01),q);trans=sum(abs(bits[i]-bits[(i+1)%8])>.01 for i in range(8));step=1/(r['frameInfo']['faceSteps']-1)
   tip=same==1 and trans==2 and abs(max([q]+bits)-min([q]+bits)-step)<.01;uncertain=abs(cls[y,x,1]-(q+opposite)*.5)<=step*.1
   back=False
   if safe and tip and uncertain:back=any(neighbour(x+dx,y+dy)and neighbour(x+2*dx,y+2*dy)and abs(old[y+dy,x+dx]-q)<.01 and abs(old[y+2*dy,x+2*dx]-q)<.01 for dx,dy in dirs)
   rows.append({'safe':bool(safe),'tip':bool(tip),'uncertain':bool(uncertain),'eligible':bool(safe and tip and uncertain and back),'causes':sorted(reasons),'minSameSurfaceDot':min(dots)if dots else None,'maxSameSurfaceDepthDelta':max(depths)if depths else None})
  records.append({'xy':[int(qx+x),int(qy+h-1-y)],'Q0':float(q),'continuous':float(cls[y,x,1]),'effective':rows[0],'geometric':rows[1]})
 angle=np.degrees(np.arccos(np.clip(np.einsum('ijk,ijk->ij',*nn),-1,1)))[face]
 summary={'sourceId':r['frameKey'],'frame':r['capturedFrame'],'sameFrameSamples':int(face.sum()),'effectiveVsGeometricAngleDegrees':{'median':float(np.median(angle)),'mean':float(angle.mean()),'max':float(angle.max())},'guards':{k:{'safe':sum(p[k]['safe']for p in records),'eligible':sum(p[k]['eligible']for p in records),'tip':sum(p[k]['tip']for p in records),'normalRejected':sum('normal'in p[k]['causes']for p in records),'depthRejected':sum('depth'in p[k]['causes']for p in records),'roleOwnerAlphaRejected':sum('role/owner/alpha'in p[k]['causes']for p in records)}for k in ['effective','geometric']},'pivotalSafeCells':[p['xy']for p in records if p['effective']['safe']!=p['geometric']['safe']],'pivotalEligibleCells':[p['xy']for p in records if p['effective']['eligible']!=p['geometric']['eligible']],'records':records,'productModified':False,'claim':'Normal ablation only. Exact same original guard and measured Q/meta/depth. No normal-map removal or relaxed threshold.'}
 O.mkdir(exist_ok=True);(O/'NORMAL_COMPARISON34.json').write_text(json.dumps(summary,indent=2),encoding='utf-8',newline='\n')
 board=Image.new('RGB',(3*224,256),(35,37,43))
 for i,(label,a)in enumerate([('geometric',nn[1]*.5+.5),('effective',nn[0]*.5+.5),('absolute difference',np.abs(nn[0]-nn[1]))]):
  img=Image.fromarray(np.uint8(np.clip(a[::-1],0,1)*255));img=img.resize((224,232),Image.Resampling.NEAREST);board.paste(img,(224*i,24));ImageDraw.Draw(board).text((224*i+6,6),label,fill='white')
 board.save(O/'PAIRED_NORMALS34.png');print(json.dumps({k:v for k,v in summary.items()if k!='records'},indent=2))
if __name__=='__main__':main()
