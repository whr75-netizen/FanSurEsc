from pathlib import Path
import json,numpy as np
from projected_ribbon93 import raster,clip_triangle,witness
def main():
 checks=0;p=np.array([[-3.,0],[3.,0]]);edges=np.array([[0,1]]);zero,b=raster(p,p,edges);assert not zero;checks+=1
 previous=set()
 for width in [.025,.25,1.,2.,3.]:
  out,b=raster(p,p+[0,width],edges);assert previous<=set(out);previous=set(out);assert all(y>=0 for x,y in out);checks+=1
 # Transform the geometry and lattice together. Asymmetric source displacement
 # is retained; no symmetric-disc/one-cell widening is substituted.
 e=p+[0,.2];reference,_=raster(p,e,edges)
 for reflect in [False,True]:
  for k in range(4):
   m=np.linalg.matrix_power(np.array([[0.,-1],[1,0]]),k)@np.diag([-1 if reflect else 1,1]);out,_=raster(p@m.T,e@m.T,edges);expected={tuple(np.rint(m@q).astype(int))for q in reference};assert set(out)==expected;checks+=1
 anchor=np.array([.17,.23]);a,_=raster(p+anchor,e+anchor,edges,anchor);assert set(a)==set(reference);checks+=1
 a,c=clip_triangle(np.array([[-.5,-.5],[.5,-.5],[.5,.5]]),[0,0]);assert a==.5 and np.allclose(c,[1/6,-1/6]);checks+=1
 # Boundary contact without area must not make L-corner extra cells.
 a,c=clip_triangle(np.array([[.5,-.5],[1.5,-.5],[1.5,.5]]),[0,0]);assert a==0 and c is None;checks+=1
 try:raster(p,p+[0,100],edges,max_cells=10);raise AssertionError('budget accepted')
 except ValueError:checks+=1
 # In pre2021 HLSL, chained && calls with the same out variable all execute.
 # AB intersects this cell, CA does not, and(0,0) lies outside the triangle.
 # Preserve the first successful witness with explicit guarded assignments.
 t=np.array([[-2.,.7],[.2,.2],[2.,.7]]);r=witness(t,np.zeros(2));assert r is not None and np.linalg.norm(r['point'])>0 and(r['barycentric']>=0).all();assert t[:,1].min()>0;shader=(Path(__file__).resolve().parent/'ProjectedRibbon93.shader').read_text();assert '!ClipSegment93(a,b,p)&&'not in shader;checks+=1
 rng=np.random.default_rng(93)
 for case in range(1000):
  t=rng.uniform(-3,3,(3,2));area,_=clip_triangle(t,[0,0]);w=witness(t,np.zeros(2));assert(area>0)==(w is not None)
  if w is not None:assert(np.abs(w['point'])<=.5+1e-12).all()and(w['barycentric']>=-1e-12).all()and np.allclose(w['barycentric']@t,w['point'])
  checks+=1
 g=Path(__file__).resolve().parent/'face93';g.mkdir(exist_ok=True);d={'CPUChecks':checks,'D4CoverageInvariant':True,'translationLocalAnchorInvariant':True,'nativeOneSidedDisplacementPreserved':True,'zeroWidthNoInventedStroke':True,'positiveAreaNotClosedCornerContact':True,'constantSATWitnessMatchesPolygonClip1000Cases':True,'GPUExecuted':False};(g/'CPU_RIBBON93.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
