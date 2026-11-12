"""Audit necessary conditions of the active335 rule without relaxing it.

Depth is deliberately omitted only for an upper bound. If a pixel already fails
the upper bound, no unknown world-pixel depth constant can make it pass.
"""
from pathlib import Path
import json,numpy as np
from frame_bytes77 import decode
H=Path(__file__).resolve().parent;G=H/'face84';C=G/'capture'
def main():
 report=json.loads((C/'COMPLETE.json').read_text());rows=[]
 for f in report['stream77']['frames']:
  w,h=f['QROI'][2:];a=np.frombuffer(decode((C/f['compressedFile']).read_bytes(),f['bytes']),'<f4').reshape(h,16,w,4).transpose(1,0,2,3);cls,meta,normal,uv,addr,hu,hm,mask=a[8:];valid=(meta[:,:,1]==4)&(cls[:,:,3]>.5)&(meta==hm).all(2)&(uv[:,:,:2]==hu[:,:,:2]).all(2)&(hu[:,:,2]==cls[:,:,0]);visible=addr[:,:,3]==1;safe=[];conditions={'allSourceNeighbours':0,'normalSafeUpperBound':0,'oneSameCardinal':0,'oneConnectedArc':0,'withinLightBudget':0,'allNecessaryConditions':0};rowpoints=[]
  for y,x in np.argwhere(valid):
   if x<1 or y<1 or x+1>=w or y+1>=h:continue
   neighbours=[(y+dy,x+dx)for dy in [-1,0,1]for dx in [-1,0,1]if dx or dy];membership=all(valid[t]for t in neighbours);conditions['allSourceNeighbours']+=int(membership)
   n=normal[y,x,:3].astype(float);n/=np.linalg.norm(n);dots=[float(n@(normal[t][:3]/np.linalg.norm(normal[t][:3])))if np.linalg.norm(normal[t][:3])>0 else -1. for t in neighbours];ns=membership and min(dots)>.94;conditions['normalSafeUpperBound']+=int(ns)
   q=cls[y,x,0];four=[cls[y+dy,x+dx,0]for dy,dx in[(0,-1),(0,1),(-1,0),(1,0)]];same=sum(abs(t-q)<.01 for t in four);one=same==1;conditions['oneSameCardinal']+=int(one)
   ring=[cls[y+dy,x+dx,0]for dy,dx in[(-1,-1),(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1)]];arcs=sum(abs(ring[i]-ring[(i+1)%8])>.01 for i in range(8))==2;step=1/(f['light84']['faceSteps']-1);adjacent=abs(max(ring+[q])-min(ring+[q])-step)<.01;conditions['oneConnectedArc']+=int(arcs and adjacent)
   targets=[t for t in four if abs(t-q)>.01];target=targets[-1]if targets else q;uncertain=abs(float(cls[y,x,1])-(q+target)*.5)<=step*.1;conditions['withinLightBudget']+=int(uncertain)
   necessary=ns and one and arcs and adjacent and uncertain;conditions['allNecessaryConditions']+=int(necessary)
   rowpoints.append({'localXY':[int(x),int(y)],'visibleOrdinary':bool(visible[y,x]),'Q':float(q),'g':float(cls[y,x,1]),'allSourceNeighbours':membership,'minimumEffectiveNormalDot':min(dots),'sameCardinal':int(same),'ringTransitions':int(sum(abs(ring[i]-ring[(i+1)%8])>.01 for i in range(8))),'uncertain':bool(uncertain),'allNecessary':bool(necessary)})
  rows.append({'frame':f['frame'],'sourceKnown':int(valid.sum()),'visibleKnown':int(visible.sum()),'sourceInitialVsAppliedQDifferences':int((valid&(mask[:,:,0]!=mask[:,:,1])).sum()),'conditions':conditions,'points':rowpoints})
 result={'CPUReadsActualGPUOnly':True,'depthGateNotRelaxedForRendering':True,'normalSafeCountIsUpperBoundWithoutDepth':True,'rows':rows};(G/'SHADE_GATE85.json').write_text(json.dumps(result,indent=2));print(json.dumps({'rows':[{k:v for k,v in r.items()if k!='points'}for r in rows]}))
if __name__=='__main__':main()
