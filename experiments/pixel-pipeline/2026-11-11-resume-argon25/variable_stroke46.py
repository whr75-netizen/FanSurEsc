"""A geometric width operator, not a classifier or a native MToon equivalence.

The caller supplies endpoint radii in logical-grid units. The support is the
union of discs along a finite source segment with linearly varying radius.
This operator adds width; the executed44 thin-line minimum remains a separate
representation policy. No world->style radius policy is silently inferred.
"""
import numpy as np
def interval(a,b,c):
 if a==0:
  if b==0:return [(0.,1.)]if c<=0 else[]
  root=-c/b;return [(0.,min(1.,root))]if b>0 and root>=0 else [(max(0.,root),1.)]if b<0 and root<=1 else[]
 disc=b*b-4*a*c
 if disc<0:return [(0.,1.)]if a<0 else[]
 q=np.sqrt(disc);lo,hi=sorted([(-b-q)/(2*a),(-b+q)/(2*a)])
 spans=[(lo,hi)]if a>0 else[(-np.inf,lo),(hi,np.inf)]
 return[(max(0.,x),min(1.,y))for x,y in spans if max(0.,x)<=min(1.,y)]
def sample(point,start,end,radii,depths=(1.,1.)):
 p,a,b=np.asarray(point,float),np.asarray(start,float),np.asarray(end,float);r=np.asarray(radii,float);z=np.asarray(depths,float)
 if p.shape!=(2,)or a.shape!=(2,)or b.shape!=(2,)or r.shape!=(2,)or z.shape!=(2,)or not np.isfinite(np.r_[p,a,b,r,z]).all()or(r<0).any():raise ValueError('finite source segment, nonnegative logical radii, finite depths')
 if not(r>0).any():return {'covered':False}
 d=b-a;v=a-p;dr=r[1]-r[0];spans=interval(d@d-dr*dr,2*(v@d-r[0]*dr),v@v-r[0]*r[0])
 if not spans:return {'covered':False}
 t=spans[0][0]if z[1]>=z[0]else spans[-1][1];radius=r[0]+t*dr
 return {'covered':radius>0,'sourceT':t,'sourcePoint':(a+t*d).tolist(),'radius':radius,'depth':float(z[0]+t*(z[1]-z[0])),'feasibleIntervals':spans}
def test():
 a=np.array([3.2,4.6]);b=np.array([22.8,19.3]);tests=0
 for radius in [(0,0),(.2,.2),(.7,.7),(2.2,2.2),(.2,3.1),(3.1,.2)]:
  for y in range(32):
   for x in range(32):
    p=np.array([x+.5,y+.5]);s=sample(p,a,b,radius,(1.2,1.8));reverse=sample(p,b,a,radius[::-1],(1.8,1.2));assert s['covered']==reverse['covered'];tests+=1
    if s['covered']:assert abs(s['depth']-reverse['depth'])<1e-10 and 0<=s['sourceT']<=1
 for mirror in [False,True]:
  for angle in range(4):
   def transform(p):
    x,y=p;x=-x if mirror else x
    for _ in range(angle):x,y=-y,x
    return np.array([x,y])
   for p in [np.array([10.5,10.5]),np.array([12.5,8.5])]:
    left=sample(p,a,b,(.2,3.1));right=sample(transform(p),transform(a),transform(b),(.2,3.1));assert left['covered']==right['covered'];tests+=1
 # A short thin segment can miss every centre. Do not advertise this band as
 # the minimum-expression replacement for the original raster line.
 vanish=sum(sample((x+.5,y+.5),(1.,1.),(1.01,1.01),(.1,.1))['covered']for y in range(3)for x in range(3));assert vanish==0
 return {'CPUChecks':tests,'endpointReversalAndD4':True,'thinMinimumReplacementRejected':True,'nativeMToonWidthMappingSpecified':False,'fullFacePaletteSolved':False,'GPUOrUnityCalls':0}
if __name__=='__main__':
 import json
 from pathlib import Path
 p=Path(__file__).resolve().parent/'face46';p.mkdir(exist_ok=True);r=test();(p/'CPU_STROKE46.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
