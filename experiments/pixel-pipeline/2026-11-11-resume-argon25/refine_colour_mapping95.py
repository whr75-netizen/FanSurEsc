"""Remove a value-stratum membership restriction, keeping measured constraints.

Reassign an original RGB key only to an existing observed representative that
strictly reduces its RGB squared error, stays in every observed support range,
and preserves all incident source-profile contrast and brightness relations.
No new colours/families, RGB average, semantic region claim or frame state.
"""
import numpy as np
from audit_polarity76 import luminance

def refine(colours,initial,reference_indices,bounds,pairs,orders,max_passes=8):
 rgb=np.asarray(colours,np.int64);mapping=np.asarray(initial,int).copy();refs=rgb[np.asarray(reference_indices,int)];bounds=np.asarray(bounds,int);pairs=np.asarray(pairs,int).reshape(-1,2);orders=np.asarray(orders,int).reshape(-1,2);n=len(rgb);m=len(refs)
 if rgb.shape!=(n,3)or n>16384 or not 0<m<=1024 or bounds.shape!=(n,2,3)or mapping.shape!=(n,)or(mapping<0).any()or(mapping>=m).any()or len(pairs)>32768 or len(orders)>32768:raise ValueError('bounded original source domain')
 codes=rgb@np.array([65536,256,1]);refcodes=refs@np.array([65536,256,1]);
 if(codes[1:]<=codes[:-1]).any()or len(set(refcodes))!=m:raise ValueError('canonical original RGB keys/unique observed references')
 if bounds.min()<0 or bounds.max()>255 or(bounds[:,0]>rgb).any()or(bounds[:,1]<rgb).any():raise ValueError('source support interval')
 adjacent=[set()for _ in range(n)];lower=[set()for _ in range(n)];upper=[set()for _ in range(n)]
 for a,b in pairs:
  if not(0<=a<n and 0<=b<n)or a==b:raise ValueError('contrast endpoints')
  adjacent[a].add(int(b));adjacent[b].add(int(a))
 for a,b in orders:
  if not(0<=a<n and 0<=b<n)or a==b:raise ValueError('brightness endpoints')
  upper[a].add(int(b));lower[b].add(int(a))
 ys=luminance(refs);history=[]
 def verify():
  out=refs[mapping]
  assert((out>=bounds[:,0])&(out<=bounds[:,1])).all()
  assert(((out[pairs[:,0]]-out[pairs[:,1]])*(rgb[pairs[:,0]]-rgb[pairs[:,1]])).sum(1)>0).all()
  assert(ys[mapping[orders[:,0]]]<ys[mapping[orders[:,1]]]).all()
 verify();complete=False
 for pass_index in range(max_passes):
  moves=0;before=int(((refs[mapping]-rgb)**2).sum())
  for i in range(n):
   cost=((refs-rgb[i])**2).sum(1);valid=(cost<cost[mapping[i]])&((refs>=bounds[i,0])&(refs<=bounds[i,1])).all(1)
   ids=np.flatnonzero(valid)
   if not len(ids):continue
   for j in sorted(adjacent[i]):
    delta=rgb[i]-rgb[j];ids=ids[((refs[ids]-refs[mapping[j]])*delta).sum(1)>0]
    if not len(ids):break
   for j in sorted(lower[i]):ids=ids[ys[ids]>ys[mapping[j]]]
   for j in sorted(upper[i]):ids=ids[ys[ids]<ys[mapping[j]]]
   if not len(ids):continue
   chosen=int(ids[np.lexsort((refcodes[ids],cost[ids]))[0]]);mapping[i]=chosen;moves+=1
  after=int(((refs[mapping]-rgb)**2).sum());assert after<=before;verify();history.append({'pass':pass_index,'moves':moves,'unweightedRGBSquaredErrorBefore':before,'after':after})
  if not moves:complete=True;break
 used=np.unique(mapping);remap=np.full(m,-1,int);remap[used]=np.arange(len(used));return {'colourAddress':remap[mapping],'referenceIndices':np.asarray(reference_indices)[used],'history':history,'converged':complete,'newRepresentatives':0,'activeReferences':len(used),'globalOptimumClaimed':False}
