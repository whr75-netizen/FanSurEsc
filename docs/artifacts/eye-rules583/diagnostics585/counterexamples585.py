"""Analytic area/selection contract checks; not an implemented renderer fix."""
import numpy as np,json,math
from geometry_oracle585 import Frame,R
def fixture(area,shift=(0,0),hidden=False):
 f=object.__new__(Frame);xy=np.array([[[0,0],[2,0],[2,2]],[[0,0],[2,2],[0,2]]],float);f.xy=xy;f.B=np.linalg.inv(np.concatenate([xy.transpose(0,2,1),np.ones((2,1,3))],axis=1));f.depth=np.tile([0,0,10.],(2,1));f.s=np.zeros(2,int);f.prim=np.array([1,2]);f.rendered=np.ones(2,bool);f.front=np.ones(2,bool);f.owner=np.tile([0,0,2.],(2,1));f.uv=np.zeros((2,3,2));f.alpha=np.ones(2);f.mode=np.zeros(2,int);f.cut=np.full(2,.5);f.mi=np.zeros(2,int);f.box=np.stack([xy.min(axis=1),xy.max(axis=1)],axis=1)
 sx=.5;sy=area/(2.16*.58*sx);cx,cy=1+shift[0],1+shift[1];f.uc=np.tile([1/sx,0,-cx/sx],(2,1));f.vc=np.tile([0,1/sy,-cy/sy],(2,1));f.cfg={'ROI348':np.array([0,270,2,2]),'UpperLower348':np.array([0,.35,.72,-.26])};f.cells={(x,y,'HairMETA'):np.array([9,12,0,1.]if hidden else[0,0,0,0.])for x in range(2)for y in range(2)};return f
def N(a):return math.floor(a+.5)
invariance=[]
for dx in [0,.0625,.125,.1875]:
 for dy in [0,.0625,.125,.1875]:
  a4=fixture(.45,(dx,dy)).integrate_grid(4)['area'];invariance.append({'shift':[dx,dy],'analyticArea':.45,'area4':a4,'analyticN':0,'N4':N(a4)})
assert len({r['N4']for r in invariance})>1,'The fixed geometric counterexample must expose a sampled threshold flip'
shrink=[]
for area in [.65,.55,.45,.35]:
 q=fixture(area).integrate_grid(128);assert abs(q['area']-area)<.004;(shrink.append({'analyticArea':area,'integrated128':q['area'],'N':N(area)}))
assert [r['N']for r in shrink]==[1,1,0,0]
occluded=fixture(.65,hidden=True).integrate_grid(32)['area'];assert occluded==0
out={'scope':'Analytic fixtures only; no real animation validation or production change. Flat/parabolic upper-lash band is on two opaque plane triangles. Exact area=2.16*sx*.58*sy.','translationInvariance':invariance,'sampledAreaRange':[min(r['area4']for r in invariance),max(r['area4']for r in invariance)],'normalShrinking':shrink,'completeOcclusionArea':occluded,'passed':True};(R/'COUNTEREXAMPLES585.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':True,'translationArea4Range':out['sampledAreaRange'],'shrinkingN':[r['N']for r in shrink],'completeOcclusionArea':occluded}))
