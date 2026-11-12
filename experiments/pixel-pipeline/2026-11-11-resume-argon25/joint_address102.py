"""Joint finite addresses over adjacent native8-bit RGB uncertainty cells.

Range witnesses are fidelity bounds, not automatically paint-contrast labels.
The caller supplies hard observed feature relations separately. Reuse existing
original-RGB representatives and LUT colours; never change source support/RGB.
"""
import numpy as np

def uncertainty_edges(rgb):
 c=np.asarray(rgb,np.int64);code=c@np.array([65536,256,1]);lookup={int(k):i for i,k in enumerate(code)};edges=[];distance=[]
 for i,v in enumerate(c):
  for dr in [-1,0,1]:
   for dg in [-1,0,1]:
    for db in [-1,0,1]:
     d=np.array([dr,dg,db]);q=v+d
     if not d.any()or(q<0).any()or(q>255).any():continue
     j=lookup.get(int(q@np.array([65536,256,1])))
     if j is not None and j>i:edges.append((i,j));distance.append(int(d@d))
 return np.asarray(edges,int).reshape(-1,2),np.asarray(distance,np.int64)

def optimize(colours,counts,initial,reference_indices,palette,hard_pairs,orders,max_passes=8):
 rgb=np.asarray(colours,np.int64);weight=np.asarray(counts,np.int64);labels=np.asarray(initial,int).copy();refs=rgb[np.asarray(reference_indices,int)];lut=np.asarray(palette,np.int64);pairs=np.asarray(hard_pairs,int).reshape(-1,2);order=np.asarray(orders,int).reshape(-1,2);n=len(rgb);m=len(refs)
 if rgb.shape!=(n,3)or n<1 or n>16384 or weight.shape!=(n,)or(weight<1).any()or labels.shape!=(n,)or m<1 or m>1024 or lut.shape!=(m,3,3)or len(pairs)>32768 or len(order)>32768 or max_passes<1:raise ValueError('bounded source/LUT contract')
 codes=rgb@np.array([65536,256,1]);refcodes=refs@np.array([65536,256,1]);assert(codes[1:]>codes[:-1]).all()and(labels>=0).all()and(labels<m).all()and(rgb>=0).all()and(rgb<=255).all()
 if len(pairs):assert pairs.min()>=0 and pairs.max()<n
 if len(order):assert order.min()>=0 and order.max()<n
 edges,denom=uncertainty_edges(rgb);assert len(edges)<=400000;neighbours=[[]for _ in range(n)];relations=[[]for _ in range(n)];rank=[[]for _ in range(n)]
 for (a,b),d in zip(edges,denom):neighbours[a].append((b,int(d)));neighbours[b].append((a,int(d)))
 for k,(a,b)in enumerate(pairs):relations[a].append((k,True));relations[b].append((k,False))
 for k,(a,b)in enumerate(order):rank[a].append((k,True));rank[b].append((k,False))
 direction=rgb[pairs[:,0]]-rgb[pairs[:,1]];lower=((lut[labels[pairs[:,0]]]-lut[labels[pairs[:,1]]])*direction[:,None,:]).sum(2);native_lower=((refs[labels[pairs[:,0]]]-refs[labels[pairs[:,1]]])*direction).sum(1);assert(lower>0).all()and(native_lower>0).all()
 value=lut/255.;linear=np.where(value<=.04045,value/12.92,((value+.055)/1.055)**2.4);Y=linear@np.array([.2126,.7152,.0722]);gap=Y[labels[order[:,1]]]-Y[labels[order[:,0]]];assert(gap>0).all()
 error=np.abs(refs[labels]-rgb);domains=[np.flatnonzero((np.abs(refs-rgb[i])<=error[i]).all(1))for i in range(n)];distance=((lut[:,None]-lut[None,:])**2).sum(3).max(2);history=[];complete=False
 def verify():
  assert(np.abs(refs[labels]-rgb)<=error).all();assert(((lut[labels[pairs[:,0]]]-lut[labels[pairs[:,1]]])*direction[:,None,:]).sum(2)>=lower).all();assert(((refs[labels[pairs[:,0]]]-refs[labels[pairs[:,1]]])*direction).sum(1)>=native_lower).all();assert(Y[labels[order[:,1]]]-Y[labels[order[:,0]]]>=gap).all()
 def objective():
  q=distance[labels[edges[:,0]],labels[edges[:,1]]]*6//denom;return q,int((q>0).sum()),int((((refs[labels]-rgb)**2).sum(1)*weight).sum())
 verify();initial_cost,initial_nonzero,initial_sse=objective()
 for pass_index in range(max_passes):
  moves=0;before,nonzero,sse=objective()
  for i in range(n):
   if len(domains[i])<2 or not neighbours[i]:continue
   adjacent=np.asarray([j for j,d in neighbours[i]],int);den=np.asarray([d for j,d in neighbours[i]],np.int64);old=int(labels[i]);oldcost=distance[old,labels[adjacent]]*6//den;before_key=tuple(sorted(oldcost.tolist(),reverse=True));old_nonzero=int((oldcost>0).sum());old_error=int(((refs[old]-rgb[i])**2).sum());best=(before_key,old_error,int(refcodes[old]));chosen=old
   for candidate in domains[i]:
    candidate=int(candidate)
    if candidate==old or(np.abs(refs[candidate]-rgb[i])>np.abs(refs[old]-rgb[i])).any():continue
    cost=distance[candidate,labels[adjacent]]*6//den
    if int((cost>0).sum())>old_nonzero:continue
    key=(tuple(sorted(cost.tolist(),reverse=True)),int(((refs[candidate]-rgb[i])**2).sum()),int(refcodes[candidate]))
    if key>=best:continue
    valid=True
    for k,first in relations[i]:
     a=candidate if first else labels[pairs[k,0]];b=labels[pairs[k,1]]if first else candidate
     if np.any(((lut[a]-lut[b])*direction[k]).sum(1)<lower[k])or((refs[a]-refs[b])*direction[k]).sum()<native_lower[k]:valid=False;break
    if not valid:continue
    for k,first in rank[i]:
     a=candidate if first else labels[order[k,0]];b=labels[order[k,1]]if first else candidate
     if np.any(Y[b]-Y[a]<gap[k]):valid=False;break
    if valid:best=key;chosen=candidate
   if chosen!=old:labels[i]=chosen;moves+=1
  verify();after,new_nonzero,new_sse=objective();assert tuple(sorted(after,reverse=True))<=tuple(sorted(before,reverse=True))and new_nonzero<=nonzero and new_sse<=sse;history.append({'pass':pass_index,'moves':moves,'uncertaintyRGBEdges':len(edges),'nonzeroEdgesBefore':nonzero,'nonzeroEdgesAfter':new_nonzero,'maximumGainSquaredBefore':float(before.max()/6)if len(before)else 0.,'maximumGainSquaredAfter':float(after.max()/6)if len(after)else 0.,'weightedSourceSSEBefore':sse,'weightedSourceSSEAfter':new_sse})
  if moves==0:complete=True;break
 final_cost,nonzero,sse=objective();return {'labels':labels,'history':history,'converged':complete,'edges':edges,'edgeDenominator':denom,'initialEdgeCosts':initial_cost,'finalEdgeCosts':final_cost,'hardPairCount':len(pairs),'orderCount':len(order),'sameRGBSameAddress':True,'newPaletteColours':0,'sourceChannelErrorNeverWorse':True,'hardProfileProjectionAndLuminanceNeverWeaker':True,'globalOptimumClaimed':False,'semanticPigmentGradientAAInferred':False}
