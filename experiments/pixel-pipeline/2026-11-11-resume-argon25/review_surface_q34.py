"""Counterfactual Q guard from verified UV carrier continuity, not colour bins."""
from pathlib import Path
import json
import numpy as np
from surface_paths34 import native
H=Path(__file__).resolve().parent;G=H/'face34';C=G/'capture';O=G/'analysis'
def main():
 r=json.loads((C/'COMPLETE.json').read_text());w,h=r['QROI'][2:];field=lambda n:np.fromfile(C/(n+'-row0000.f32'),dtype='<f4').reshape(h,w,4)
 meta,uv,cls,mask=map(field,['q7','q9','q5','q6']);old=mask[:,:,1];face=(np.rint(meta[:,:,1])==4)&(cls[:,:,3]>.5);surface,binding=native();cache={};unknown=[]
 def neighbour(x,y,xx,yy):
  if not(0<=xx<w and 0<=yy<h):return False
  m,n=meta[y,x],meta[yy,xx]
  if n[0]<=0 or abs(n[1]-m[1])>.1 or abs(n[2]-m[2])>.1 or cls[yy,xx,3]<.5 or abs(cls[y,x,2]-cls[yy,xx,2])>=r['frameInfo']['worldPixel']*2:return False
  key=(x,y,xx,yy)
  if key not in cache:cache[key]=surface.path(uv[y,x,:2],uv[yy,xx,:2],int(round(m[3]))-1,int(round(n[3]))-1)
  return cache[key]['known']
 ring=[(-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)];dirs=[(-1,0),(1,0),(0,-1),(0,1)];candidate=old.copy();rows=[]
 for y,x in np.argwhere(face):
  q=old[y,x];safe=all(neighbour(x,y,x+dx,y+dy)for dx,dy in ring);bits=[old[np.clip(y+dy,0,h-1),np.clip(x+dx,0,w-1)]for dx,dy in ring];card=[old[np.clip(y+dy,0,h-1),np.clip(x+dx,0,w-1)]for dx,dy in dirs];same=sum(abs(v-q)<.01 for v in card);opposite=next((v for v in card[::-1]if abs(v-q)>=.01),q);trans=sum(abs(bits[i]-bits[(i+1)%8])>.01 for i in range(8));step=1/(r['frameInfo']['faceSteps']-1)
  tip=same==1 and trans==2 and abs(max([q]+bits)-min([q]+bits)-step)<.01;uncertain=abs(cls[y,x,1]-(q+opposite)*.5)<=step*.1
  back=any(neighbour(x,y,x+dx,y+dy)and neighbour(x,y,x+2*dx,y+2*dy)and abs(old[y+dy,x+dx]-q)<.01 and abs(old[y+2*dy,x+2*dx]-q)<.01 for dx,dy in dirs)if safe and tip and uncertain else False
  if safe and tip and uncertain and back:candidate[y,x]=opposite
  rows.append({'xy':[int(r['QROI'][0]+x),int(r['QROI'][1]+h-1-y)],'old':float(q),'proposed':float(candidate[y,x]),'continuous':float(cls[y,x,1]),'safe':safe,'tip':bool(tip),'uncertain':bool(uncertain),'back':back})
 changed=[p for p in rows if p['old']!=p['proposed']];report={'sourceId':r['frameKey'],'safeCarrierNeighborhoods':sum(p['safe']for p in rows),'changedQCells':changed,'queryCount':len(cache),'maxVisits':max(p.get('visits',0)for p in cache.values()),'proposalOnly':True,'notApplied':'Source UV connectivity is not a colour-region label, not midpath visibility. No finite RGB or final outline/quality improvement is asserted.','rows':rows};(O/'CARRIER_Q_COUNTERFACTUAL34.json').write_text(json.dumps(report,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items()if k!='rows'},indent=2))
if __name__=='__main__':main()
