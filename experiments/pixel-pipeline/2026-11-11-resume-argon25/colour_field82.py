"""Constraint-directed native colour hierarchy, independent of UV owner IDs.

Same native RGB always has one colour address. UV geometry/feature components
remain separate metadata. Split only an unresolved measured contrast/range or
an infeasible source-order domain; choose the maximum native RGB variance
reduction, not a requested K or threshold sweep. Representatives are actual
observed RGB values. This is a stylization hypothesis, not authored semantics.
"""
import numpy as np
from audit_polarity76 import luminance
from region_order79 import feasible

def split(colours,counts,ids,pending,y_only=False):
 c=colours[ids].astype(float);w=counts[ids].astype(float);best=None;total=w.sum();s=(c*w[:,None]).sum(0);base=s@s/total
 for axis in([-1]if y_only else[0,1,2]):
  values=luminance(c)if axis<0 else c[:,axis];order=np.argsort(values,kind='stable');v=values[order];wc=w[order];cc=c[order];n=np.cumsum(wc);sc=np.cumsum(wc[:,None]*cc,axis=0);good=np.flatnonzero(v[:-1]<v[1:]);allowed=np.zeros(len(good),bool)
  if pending:
   coordinate=luminance(colours)if axis<0 else colours[:,axis]
   for a,b in pending:
    lo,hi=sorted([coordinate[a],coordinate[b]]);allowed|=(v[good]>=lo)&(v[good]<hi)
   good=good[allowed]
  if not len(good):continue
  left=sc[good];right=s-left;gain=(left*left).sum(1)/n[good]+(right*right).sum(1)/(total-n[good])-base;at=int(np.argmax(gain));i=int(good[at]);candidate=(float(gain[at]),-axis,-float(v[i]))
  if best is None or candidate>best[0]:best=(candidate,ids[order[:i+1]],ids[order[i+1:]],axis,float(v[i]))
 if best is None:raise ValueError('no actual native split separates required samples')
 return best[1:]

def build(colours,counts,strict_orders,range_pairs):
 rgb=np.asarray(colours,np.uint8);counts=np.asarray(counts,np.int64);n=len(rgb)
 if rgb.shape!=(n,3)or counts.shape!=(n,)or n>65536 or(counts<=0).any():raise ValueError('bounded unique native RGB histogram')
 if len(np.unique(rgb,axis=0))!=n:raise ValueError('one shared RGB node required')
 y=luminance(rgb);orders=sorted(set((int(a),int(b))for a,b in strict_orders));pairs=sorted(set(tuple(sorted((int(a),int(b))))for a,b in list(range_pairs)+orders if a!=b));nodes={0:np.arange(n)};leaf=np.zeros(n,int);history=[];next_id=1
 if any(y[a]>=y[b]for a,b in orders):raise ValueError('strict native luminance order required')
 for iteration in range(n):
  pending={}
  for a,b in pairs:
   if leaf[a]==leaf[b]:pending.setdefault(int(leaf[a]),[]).append((a,b))
  graph=None
  if pending:
   # All selected nodes contain an actual unresolved source pair.
   chosen=min(pending,key=lambda k:(-len(pending[k]),k));why='measured-pair';requirements=pending[chosen];y_only=False
  else:
   domains={k:np.unique(y[ids])for k,ids in nodes.items()};edges=[(int(leaf[a]),int(leaf[b]))for a,b in orders];graph=feasible(domains,edges)
   if graph['feasible']:break
   candidates=graph['cyclicOrDependentRegions'][:]
   for k in graph['exhaustedDomainRegions']:
    while k is not None and k not in candidates:candidates.append(k);k=graph['predecessor'].get(k)
   candidates=[k for k in candidates if np.ptp(y[nodes[k]])>0]
   if not candidates:raise AssertionError('strict native order has no refinable source domain')
   def variance(k):
    ids=nodes[k];c=rgb[ids].astype(float);w=counts[ids];s=(c*w[:,None]).sum(0);return float(((c*c).sum(1)*w).sum()-s@s/w.sum())
   chosen=min(candidates,key=lambda k:(-variance(k),k));why='source-order-domain';requirements=[];y_only=True
  ids=nodes.pop(chosen);a,b,axis,cut=split(rgb,counts,ids,requirements,y_only);nodes[chosen]=a;nodes[next_id]=b;leaf[a]=chosen;leaf[b]=next_id;history.append({'node':chosen,'newNode':next_id,'why':why,'axis':axis,'cut':cut,'leftNativeColours':len(a),'rightNativeColours':len(b)});next_id+=1
 else:raise AssertionError('native hierarchy termination bound exceeded')
 # Greatest feasible native luminance in reverse DAG order. A forward choice
 # within this bound always leaves a feasible successor domain. Choose the
 # actual native RGB of least regional RGB SSE, not an averaged output colour.
 edges=set((int(leaf[a]),int(leaf[b]))for a,b in orders);succ={k:set()for k in nodes};pred={k:set()for k in nodes}
 for a,b in edges:succ[a].add(b);pred[b].add(a)
 upper={}
 for k in reversed(graph['order']):
  bound=min((upper[q]for q in succ[k]),default=np.inf);valid=y[nodes[k]]<bound;assert valid.any();upper[k]=float(y[nodes[k]][valid].max())
 references={};chosen_y={}
 for k in graph['order']:
  ids=nodes[k];lo=max((chosen_y[p]for p in pred[k]),default=-np.inf);valid=ids[(y[ids]>lo)&(y[ids]<=upper[k])];assert len(valid);c=rgb[ids].astype(float);w=counts[ids];s=(c*w[:,None]).sum(0);candidate=rgb[valid].astype(float);cost=w.sum()*(candidate*candidate).sum(1)-2*candidate@s;ix=int(np.lexsort((candidate[:,2],candidate[:,1],candidate[:,0],cost))[0]);references[k]=int(valid[ix]);chosen_y[k]=float(y[valid[ix]])
 keys=sorted(nodes,key=lambda k:tuple(rgb[references[k]].tolist()));remap={k:i for i,k in enumerate(keys)};address=np.array([remap[int(k)]for k in leaf],np.int32);refs=np.array([references[k]for k in keys]);assert all(luminance(rgb[refs[address[a]]])<luminance(rgb[refs[address[b]]])for a,b in orders)
 return {'address':address,'referenceIndices':refs,'history':history,'strictOrders':len(orders),'rangePairs':len(pairs),'families':len(keys),'sameRGBInvariant':True,'sourceOrderSatisfied':True,'globalMinimumRGBSSEClaimed':False}
