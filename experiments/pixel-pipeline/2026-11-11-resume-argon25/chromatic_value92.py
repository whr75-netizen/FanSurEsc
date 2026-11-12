"""Refine only an observed source-chroma contradiction inside value strata.

Each leaf retains actual native RGB candidates. Split along the offending
native RGB difference, between that source colour and its wrong representative.
This is source preprocessing, never a per-frame GPU search or semantic label.
No requested K, fitted/mean output RGB, RGB history or model/colour constants.
"""
import numpy as np

def medoid(colours,counts,ids):
 ids=np.sort(ids);c=colours[ids].astype(np.int64);w=counts[ids].astype(np.int64);s=(c*w[:,None]).sum(0);cost=w.sum()*(c*c).sum(1)-2*c@s
 return int(ids[int(np.argmin(cost))])

def build(colours,counts,initial,pairs,max_splits=512):
 rgb=np.asarray(colours,np.uint8);counts=np.asarray(counts,np.int64);initial=np.asarray(initial,int);n=len(rgb)
 if rgb.shape!=(n,3)or counts.shape!=(n,)or initial.shape!=(n,)or n>16384 or(counts<=0).any()or(initial<0).any():raise ValueError('bounded original-colour domain')
 code=rgb[:,0].astype(np.int64)*65536+rgb[:,1].astype(np.int64)*256+rgb[:,2]
 if np.any(code[1:]<=code[:-1]):raise ValueError('one canonical sorted original RGB key')
 p=np.asarray(sorted({tuple(sorted((int(a),int(b))))for a,b in pairs if a!=b}),int).reshape(-1,2)
 if len(p)>32768 or(len(p)and(p.min()<0 or p.max()>=n)):raise ValueError('bounded observed chromatic relations')
 delta=rgb[p[:,0]].astype(np.int64)-rgb[p[:,1]];magnitude=(delta*delta).sum(1);nodes={int(k):np.flatnonzero(initial==k)for k in np.unique(initial)};label=initial.copy();reference={k:medoid(rgb,counts,v)for k,v in nodes.items()};history=[];next_id=max(nodes)+1;complete=False
 for iteration in range(max_splits+1):
  current=np.array([reference[int(k)]for k in label]);difference=rgb[current[p[:,0]]].astype(np.int64)-rgb[current[p[:,1]]];dot=(difference*delta).sum(1);bad=np.flatnonzero(dot<=0)
  if not len(bad):complete=True;break
  if iteration==max_splits:break
  # Source RGB keys, not screen position or contour traversal, break equal
  # contradiction priorities. The ratio only orders failures, not output costs.
  ratio=dot[bad]/magnitude[bad];at=int(bad[np.lexsort((p[bad,1],p[bad,0],ratio))[0]]);direction=delta[at];options=[]
  for endpoint in p[at]:
   k=int(label[endpoint]);ids=nodes[k];rep=reference[k];value=rgb[ids].astype(np.int64)@direction;want=int(rgb[endpoint].astype(np.int64)@direction);wrong=int(rgb[rep].astype(np.int64)@direction)
   if want==wrong:continue
   order=np.lexsort((ids,value));v=value[order];native_ids=ids[order];w=counts[native_ids].astype(float);c=rgb[native_ids].astype(float);weight=np.cumsum(w);sums=np.cumsum(w[:,None]*c,axis=0);cuts=np.flatnonzero((v[:-1]<v[1:])&(v[:-1]>=min(want,wrong))&(v[:-1]<max(want,wrong)))
   if not len(cuts):continue
   total=weight[-1];s=sums[-1];left=sums[cuts];right=s-left;gain=(left*left).sum(1)/weight[cuts]+(right*right).sum(1)/(total-weight[cuts])-s@s/total;j=int(np.argmax(gain));cut=int(cuts[j]);a=np.sort(native_ids[:cut+1]);b=np.sort(native_ids[cut+1:]);score=(-float(gain[j]),int(code[rep]),int(v[cut]),int(code[endpoint]));options.append((score,k,a,b,int(v[cut])))
  if not options:raise AssertionError('nonpositive native contrast must separate at least one wrong representative')
  _,k,a,b,cut=min(options,key=lambda q:q[0]);nodes[k]=a;nodes[next_id]=b;label[a]=k;label[b]=next_id;reference[k]=medoid(rgb,counts,a);reference[next_id]=medoid(rgb,counts,b);history.append({'node':k,'newNode':next_id,'nativeDirection':direction.tolist(),'nativePair':p[at].tolist(),'projectionCut':cut,'leftColours':len(a),'rightColours':len(b)});next_id+=1
 keys=sorted(nodes,key=lambda k:int(code[reference[k]]));remap={k:i for i,k in enumerate(keys)};address=np.array([remap[int(k)]for k in label]);refs=np.array([reference[k]for k in keys]);mapped=rgb[refs[address]];dot=((mapped[p[:,0]].astype(np.int64)-mapped[p[:,1]])*delta).sum(1)
 return {'complete':complete,'colourAddress':address,'referenceIndices':refs,'history':history,'unresolvedPairs':p[dot<=0],'pairs':p,'initialStrata':len(np.unique(initial)),'addresses':len(refs),'singletonColourDomains':sum(len(nodes[k])==1 for k in nodes),'globalMinimumPaletteOrSSEClaimed':False,'sourceContrastDirectionsPreserved':bool((dot>0).all())}
