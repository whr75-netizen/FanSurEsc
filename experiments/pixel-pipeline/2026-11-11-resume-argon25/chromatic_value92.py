"""Refine only an observed source-chroma contradiction inside value strata.

Each leaf retains actual native RGB candidates. Split along the offending
native RGB difference, between that source colour and its wrong representative.
This is source preprocessing, never a per-frame GPU search or semantic label.
No requested K, fitted/mean output RGB, RGB history or model/colour constants.
"""
import numpy as np

def medoid(colours,counts,ids,allowed=None):
 ids=np.sort(ids);c=colours[ids].astype(np.int64);w=counts[ids].astype(np.int64);s=(c*w[:,None]).sum(0);candidates=ids if allowed is None else ids[allowed];q=colours[candidates].astype(np.int64);cost=w.sum()*(q*q).sum(1)-2*q@s
 return int(candidates[int(np.argmin(cost))])

def build(colours,counts,initial,pairs,max_splits=512,reference_bounds=None):
 rgb=np.asarray(colours,np.uint8);counts=np.asarray(counts,np.int64);initial=np.asarray(initial,int);n=len(rgb)
 if rgb.shape!=(n,3)or counts.shape!=(n,)or initial.shape!=(n,)or n>16384 or(counts<=0).any()or(initial<0).any():raise ValueError('bounded original-colour domain')
 code=rgb[:,0].astype(np.int64)*65536+rgb[:,1].astype(np.int64)*256+rgb[:,2]
 if np.any(code[1:]<=code[:-1]):raise ValueError('one canonical sorted original RGB key')
 bounds=None if reference_bounds is None else np.asarray(reference_bounds,int)
 if bounds is not None and(bounds.shape!=(n,2,3)or(bounds[:,0]>rgb).any()or(bounds[:,1]<rgb).any()or(bounds[:,0]<0).any()or(bounds[:,1]>255).any()):raise ValueError('observed ranges must contain their original RGB')
 def representative(ids):
  if bounds is None:return medoid(rgb,counts,ids)
  lo=bounds[ids,0].max(0);hi=bounds[ids,1].min(0);allowed=((rgb[ids]>=lo)&(rgb[ids]<=hi)).all(1)
  # If the intersection has no observed RGB, split a concrete contradiction.
  # Never manufacture an RGB at the intersection or silently drop the range.
  return medoid(rgb,counts,ids,allowed)if allowed.any()else medoid(rgb,counts,ids)
 p=np.asarray(sorted({tuple(sorted((int(a),int(b))))for a,b in pairs if a!=b}),int).reshape(-1,2)
 if len(p)>32768 or(len(p)and(p.min()<0 or p.max()>=n)):raise ValueError('bounded observed chromatic relations')
 delta=rgb[p[:,0]].astype(np.int64)-rgb[p[:,1]];magnitude=(delta*delta).sum(1);nodes={int(k):np.flatnonzero(initial==k)for k in np.unique(initial)};label=initial.copy();reference={k:representative(v)for k,v in nodes.items()};history=[];next_id=max(nodes)+1;complete=False
 for iteration in range(max_splits+1):
  current=np.array([reference[int(k)]for k in label]);difference=rgb[current[p[:,0]]].astype(np.int64)-rgb[current[p[:,1]]];dot=(difference*delta).sum(1);bad=np.flatnonzero(dot<=0)
  range_bad=np.empty(0,int)if bounds is None else np.flatnonzero(((rgb[current]<bounds[:,0])|(rgb[current]>bounds[:,1])).any(1))
  if not len(bad)and not len(range_bad):complete=True;break
  if iteration==max_splits:break
  # Source RGB keys, not screen position or contour traversal, break equal
  # contradiction priorities. The ratio only orders failures, not output costs.
  if len(range_bad):
   endpoint=int(range_bad[0]);pair=np.array([endpoint,current[endpoint]]);direction=rgb[endpoint].astype(np.int64)-rgb[current[endpoint]];reason='observed-support-range'
  else:
   ratio=dot[bad]/magnitude[bad];at=int(bad[np.lexsort((p[bad,1],p[bad,0],ratio))[0]]);pair=p[at];direction=delta[at];reason='native-contrast'
  options=[]
  for endpoint in pair:
   k=int(label[endpoint]);ids=nodes[k];rep=reference[k];value=rgb[ids].astype(np.int64)@direction;want=int(rgb[endpoint].astype(np.int64)@direction);wrong=int(rgb[rep].astype(np.int64)@direction)
   if want==wrong:continue
   order=np.lexsort((ids,value));v=value[order];native_ids=ids[order];w=counts[native_ids].astype(float);c=rgb[native_ids].astype(float);weight=np.cumsum(w);sums=np.cumsum(w[:,None]*c,axis=0);cuts=np.flatnonzero((v[:-1]<v[1:])&(v[:-1]>=min(want,wrong))&(v[:-1]<max(want,wrong)))
   if not len(cuts):continue
   total=weight[-1];s=sums[-1];left=sums[cuts];right=s-left;gain=(left*left).sum(1)/weight[cuts]+(right*right).sum(1)/(total-weight[cuts])-s@s/total;j=int(np.argmax(gain));cut=int(cuts[j]);a=np.sort(native_ids[:cut+1]);b=np.sort(native_ids[cut+1:]);score=(-float(gain[j]),int(code[rep]),int(v[cut]),int(code[endpoint]));options.append((score,k,a,b,int(v[cut])))
  if not options:raise AssertionError('nonpositive native contrast must separate at least one wrong representative')
  _,k,a,b,cut=min(options,key=lambda q:q[0]);nodes[k]=a;nodes[next_id]=b;label[a]=k;label[b]=next_id;reference[k]=representative(a);reference[next_id]=representative(b);event={'node':k,'newNode':next_id,'nativeDirection':direction.tolist(),'nativePair':pair.tolist(),'projectionCut':cut,'leftColours':len(a),'rightColours':len(b)}
  if bounds is not None:event['reason']=reason
  history.append(event);next_id+=1
 keys=sorted(nodes,key=lambda k:int(code[reference[k]]));remap={k:i for i,k in enumerate(keys)};address=np.array([remap[int(k)]for k in label]);refs=np.array([reference[k]for k in keys]);mapped=rgb[refs[address]];dot=((mapped[p[:,0]].astype(np.int64)-mapped[p[:,1]])*delta).sum(1)
 result={'complete':complete,'colourAddress':address,'referenceIndices':refs,'history':history,'unresolvedPairs':p[dot<=0],'pairs':p,'initialStrata':len(np.unique(initial)),'addresses':len(refs),'singletonColourDomains':sum(len(nodes[k])==1 for k in nodes),'globalMinimumPaletteOrSSEClaimed':False,'sourceContrastDirectionsPreserved':bool((dot>0).all())}
 if bounds is not None:result['unresolvedRangeColours']=np.flatnonzero(((mapped<bounds[:,0])|(mapped>bounds[:,1])).any(1))
 return result
