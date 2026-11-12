"""Ordered source-field strata, distinct from semantic features and light Q.

Minimize the number of strata that separate measured native contrast pairs;
among solutions of that size minimize native weighted luminance SSE. No K,
colour-distance threshold or fitted RGB. This is a proposed source-field model,
not an author-semantic classifier. RGB representatives must remain observed.
"""
import numpy as np

def partition(values,weights,strict_pairs):
 v=np.asarray(values,float);w=np.asarray(weights,float);n=len(v)
 if n<1 or w.shape!=v.shape or not np.isfinite(v).all()or not np.isfinite(w).all()or(w<=0).any()or(v[1:]<=v[:-1]).any():raise ValueError('sorted unique finite native values and positive counts')
 pairs=sorted(set((int(a),int(b))for a,b in strict_pairs))
 if any(not(0<=a<b<n)for a,b in pairs):raise ValueError('strict native low/high order')
 # Interval stabbing gives the exact minimum number of cuts. SSE then chooses
 # their positions; it does not leave a giant flat interval plus max singleton.
 cuts=[]
 for lo,hi in sorted(pairs,key=lambda p:(p[1],p[0])):
  if not cuts or not(lo<cuts[-1]<=hi):cuts.append(hi)
 kmax=len(cuts)+1;start=np.zeros(n,int)
 for lo,hi in pairs:start[hi]=max(start[hi],lo+1)
 start=np.maximum.accumulate(start);s0=np.r_[0,np.cumsum(w)];s1=np.r_[0,np.cumsum(w*v)];s2=np.r_[0,np.cumsum(w*v*v)]
 def cost(i,j):
  a=s0[j+1]-s0[i];b=s1[j+1]-s1[i];c=s2[j+1]-s2[i];return np.maximum(0,c-b*b/a)
 previous=np.full(n,np.inf);back=[];previous[:]=cost(np.zeros(n,int),np.arange(n));previous[start>0]=np.inf;back.append(np.zeros(n,int))
 for k in range(2,kmax+1):
  current=np.full(n,np.inf);at=np.full(n,-1,int)
  # Scalar interval SSE is Monge; monotone hard start bounds preserve the
  # staircase domain. D&C avoids quadratic whole-texture palette searches.
  def solve(left,right,optlo,opthi):
   if left>right:return
   mid=(left+right)//2;lo=max(k-1,int(start[mid]),optlo);hi=min(mid,opthi)
   if lo<=hi:
    ix=np.arange(lo,hi+1);c=previous[ix-1]+cost(ix,mid);best=int(np.argmin(c));current[mid]=c[best];at[mid]=int(ix[best]);pivot=at[mid]
   else:pivot=lo
   solve(left,mid-1,optlo,min(opthi,pivot));solve(mid+1,right,max(optlo,pivot),opthi)
  solve(k-1,n-1,k-1,n-1);back.append(at);previous=current
 if not np.isfinite(previous[-1]):raise AssertionError('minimum ordered partition not found')
 ranges=[];end=n-1
 for k in range(kmax,0,-1):
  begin=int(back[k-1][end]);assert begin>=0;ranges.append((begin,end));end=begin-1
 ranges.reverse();label=np.zeros(n,int)
 for i,(lo,hi)in enumerate(ranges):label[lo:hi+1]=i
 assert all(label[a]<label[b]for a,b in pairs)
 return {'ranges':ranges,'labels':label,'strata':kmax,'SSE':float(previous[-1]),'strictPairCount':len(pairs)}
