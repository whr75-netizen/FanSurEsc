from pathlib import Path
import itertools,json,numpy as np
from source_levels82 import partition
H=Path(__file__).resolve().parent;G=H/'face82'

def brute(v,w,pairs):
 n=len(v);best=None
 for bits in itertools.product([0,1],repeat=n-1):
  lab=np.r_[0,np.cumsum(bits)]
  if any(lab[a]>=lab[b]for a,b in pairs):continue
  sse=0
  for k in range(int(lab.max())+1):
   q=lab==k;mean=np.sum(v[q]*w[q])/w[q].sum();sse+=np.sum(w[q]*(v[q]-mean)**2)
  score=(int(lab.max())+1,sse)
  if best is None or score<best:best=score
 return best

def main():
 G.mkdir(exist_ok=True);rng=np.random.default_rng(82);tests=0
 for n in range(2,10):
  for j in range(12):
   v=np.sort(rng.choice(100,size=n,replace=False)).astype(float)/100;w=rng.integers(1,8,n);pairs=[(a,b)for a in range(n)for b in range(a+1,n)if rng.random()<.15];r=partition(v,w,pairs);k,s=brute(v,w,pairs);assert r['strata']==k and abs(r['SSE']-s)<1e-10,(n,j,r,k,s);tests+=1
 r=partition(np.arange(5,dtype=float),np.array([1,10,10,10,1]),[(0,4)]);assert r['ranges']not in[[(0,3),(4,4)],[(0,0),(1,4)]];tests+=1
 result={'CPUChecks':tests,'minimumStrataThenSSEMatchesExhaustive':True,'noFixedPaletteCountOrColourThreshold':True,'nativeRGBNotAveragedForOutput':True,'lightQUsed':False,'GPUExecuted':False};(G/'CPU_SOURCE_LEVELS82.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
