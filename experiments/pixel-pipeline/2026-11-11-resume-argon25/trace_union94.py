"""Exact integer-grid ray contributions at the observed failing fragment."""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
import json,numpy as np
from union_input94 import load
H=Path(__file__).resolve().parent;G=H/'face94'
def main():
 d=load(G/'capture/UNION94-failure-frame429.bin');e=np.rint(d['segments'].astype(float)*1e8).astype(np.int64);counts=Counter()
 for a,b in e:
  a,b=tuple(map(int,a)),tuple(map(int,b))
  if a==b:continue
  counts[tuple(sorted((a,b)))]+=1 if a<b else-1
 edges=[(a,b,n)if n>0 else(b,a,-n)for(a,b),n in counts.items()if n];a=(21034936523,10941592407);b=(21034767151,10942348480);q=(F(a[0]+b[0],2),F(a[1]+b[1],2));contrib=[]
 for c,z,n in edges:
  if not min(c[1],z[1])<=q[1]<max(c[1],z[1]):continue
  cross=(z[0]-c[0])*(q[1]-c[1])-(z[1]-c[1])*(q[0]-c[0]);sgn=1 if z[1]>c[1]else-1
  if cross*sgn<=0:continue
  x=F(c[0])+F(z[0]-c[0],z[1]-c[1])*(q[1]-c[1]);contrib.append({'a':list(c),'b':list(z),'weight':n,'windingContribution':sgn*n,'rayCrossingX':float(x/100000000)})
 out=defaultdict(list)
 for c,z,n in edges:out[c].append(z)
 loops=[];visited=0
 def walk(path):
  nonlocal visited
  visited+=1
  if visited>4096:return
  for p in out[path[-1]]:
   if p==a:
    ring=path+[a];area=sum(c[0]*z[1]-c[1]*z[0]for c,z in zip(ring,ring[1:]))/2e16;loops.append({'vertices':ring,'signedAreaCells':area});continue
   if p not in path and len(path)<512:walk(path+[p])
 if b in out[a]:walk([a,b])
 r={'sourceId':d['sourceId'],'frame':d['frame'],'integerGrid':100000000,'queryXYCells':[float(x/100000000)for x in q],'weightedEdges':len(edges),'summedExactWinding':sum(x['windingContribution']for x in contrib),'rayContributors':sorted(contrib,key=lambda x:x['rayCrossingX']),'inputCyclesThroughFailingDirectedEdge':loops,'cycleSearchVisits':visited,'cycleSearchBudget':4096,'cycleEnumerationComplete':visited<=4096};(G/'EXACT_FRAGMENT94.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
if __name__=='__main__':main()
