"""Conditional connected-feature allocator, not a complete eye key-form solver.

Keep the actual legacy area budget and evidence score. A caller must supply an
explicit source/style connectivity contract. Never bridge disconnected visible
support, infer occlusion, add pixels, or alter colours. Enumeration is offline.
"""
import math,itertools
import numpy as np
def components(points,connectivity=4):
 left=set(map(tuple,points));groups=[];steps=[(-1,0),(1,0),(0,-1),(0,1)]
 if connectivity==8:steps += [(-1,-1),(-1,1),(1,-1),(1,1)]
 elif connectivity!=4:raise ValueError('Explicit4/8 connectivity required')
 while left:
  first=min(left);left.remove(first);g={first};todo=[first]
  while todo:
   x,y=todo.pop()
   for dx,dy in steps:
    q=(x+dx,y+dy)
    if q in left:left.remove(q);g.add(q);todo.append(q)
  groups.append(g)
 return groups
def legacy(packet):
 a=np.asarray(packet,np.float32)
 if a.ndim!=3 or a.shape[-1]!=12 or not np.isfinite(a).all():raise ValueError('Actual finite12-float packet grid required')
 I=np.float32(np.float32(a[...,2]+a[...,3])+a[...,4]);cost=np.float32(np.maximum(np.maximum(a[...,1],a[...,5]),a[...,6])-I)
 if np.any(I<0) or np.any(I>16+1e-4):raise ValueError('One family weight outside16 subsamples')
 area=np.float32(0)
 # Input row0 is top-left; original shader accumulates bottom-left first.
 for y in range(I.shape[0]-1,-1,-1):
  for x in range(I.shape[1]):area=np.float32(area+np.float32(I[y,x]/np.float32(16)))
 k=math.floor(float(np.float32(area+np.float32(.5))))
 ranked=[(int(x),int(y)) for y,x in np.argwhere(I>0)]
 ranked.sort(key=lambda p:(float(cost[p[1],p[0]]),float(a[p[1],p[0],8]),float(a[p[1],p[0],9]),-p[1],p[0]))
 return {'area':float(area),'budget':k,'ranked':ranked,'selected':ranked[:k],'iris':I,'cost':cost}
def connected(packet,contract=None,max_combinations=100000):
 old=legacy(packet);ranked=old['ranked'];k=old['budget'];result={key:old[key] for key in ['area','budget','ranked','selected']};result.update({'changed':False,'acceptedForProduct':False,'ambiguousOptimalSets':0})
 if not contract or contract.get('connectivity') not in [4,8] or not contract.get('provenance'):
  return dict(result,status='missing-source-style-connectivity-contract')
 c=contract['connectivity'];result['sourceComponents']=len(components(ranked,c));result['legacyComponents']=len(components(old['selected'],c))
 if k==0:return dict(result,status='zero-original-budget-no-minimum-added')
 if k>len(ranked):return dict(result,status='inconsistent-original-capacity')
 if result['sourceComponents']!=1:return dict(result,status='disconnected-visible-support-unresolved-no-bridge')
 if result['legacyComponents']==1:return dict(result,status='legacy-already-connected')
 count=math.comb(len(ranked),k);result['enumerationUpperBound']=count
 if count>max_combinations:return dict(result,status='offline-enumeration-budget-exceeded')
 choices=[]
 for indices in itertools.combinations(range(len(ranked)),k):
  pts=[ranked[n] for n in indices]
  if len(components(pts,c))!=1:continue
  score=sum(float(old['cost'][y,x]) for x,y in pts);choices.append((score,indices,pts))
 if not choices:return dict(result,status='no-connected-budget-preserving-solution')
 choices.sort();best=choices[0];ties=sum(v[0]==best[0] for v in choices)
 return dict(result,status='conditional-connectivity-candidate',selected=best[2],changed=set(best[2])!=set(old['selected']),legacyScore=sum(float(old['cost'][y,x]) for x,y in old['selected']),candidateScore=best[0],scoreIncrease=best[0]-sum(float(old['cost'][y,x]) for x,y in old['selected']),feasibleConnectedSets=len(choices),ambiguousOptimalSets=ties)
