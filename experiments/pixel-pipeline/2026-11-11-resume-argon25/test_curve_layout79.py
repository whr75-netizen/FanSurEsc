from pathlib import Path
import json,numpy as np
from curve_layout79 import localize,anchor_candidates,raster,intersects
H=Path(__file__).resolve().parent;G=H/'face79'

def main():
 G.mkdir(exist_ok=True);tests=0;p=np.array([[.125,.25],[3.25,.5],[4.125,2.75],[2.25,4.125],[-.25,2.5]]);edges=np.array([[0,1],[1,2],[2,3],[3,4],[4,0]]);r=np.full(len(p),.07);a,local=localize(p);reference=set(raster(local,edges,r))
 for x in np.arange(17)/16:
  for y in np.arange(17)/16:
   an,q=localize(p+[x,y]);assert np.array_equal(q,local)and set(raster(q,edges,r))==reference;tests+=1
 for mirror in[False,True]:
  for k in range(4):
   t=k*np.pi/2;m=np.rint([[np.cos(t),-np.sin(t)],[np.sin(t),np.cos(t)]]);m[:,0]*=-1 if mirror else 1;_,q=localize(p@m.T);observed=set(raster(q,edges,r));expected={tuple((np.array(c)@m.T).astype(int))for c in reference};assert observed==expected;tests+=1
 assert len(anchor_candidates([.5,.5]))==4 and len(anchor_candidates([.25,.5]))==2 and len(anchor_candidates([.25,.75]))==1;tests+=1
 assert intersects([-2,0],[2,0],0,0,[0,0])and not intersects([-2,.6],[2,.6],0,0,[0,0])and intersects([-2,.6],[2,.6],.2,.2,[0,0]);tests+=1
 # Continuous radius, including a zero endpoint, not one radius per segment.
 assert intersects([-2,.7],[2,.7],0,.5,[0,0]);tests+=1
 result={'CPUChecks':tests,'pureSubpixelTranslationLocalShapeInvariant':True,'D4Exact':True,'halfAnchorTiesExplicit':True,'boundedAnalyticCellFootprint':True,'occlusionOrGPUValidated':False,'fullArtAdopted':False};(G/'CPU_CURVE_LAYOUT79.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
