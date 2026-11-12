"""Exact feasibility of native contrast orders on proposed closed regions.

One RGB per region is only a proposal. Directed u->v means output luminance(u)
must be strictly below(v). Same-label edges, cycles and exhausted observed RGB
domains are explicit witnesses that representative selection cannot repair the
partition. Native colour domains and no fitted/averaged output RGB are required.
"""
import heapq,numpy as np

def feasible(domains,orders):
 nodes=set(domains);succ={n:set()for n in nodes};pred={n:set()for n in nodes};same=[]
 for u,v in orders:
  if u not in nodes or v not in nodes:raise ValueError('registered native region required')
  if u==v:same.append((u,v));continue
  succ[u].add(v);pred[v].add(u)
 degree={n:len(pred[n])for n in nodes};ready=[n for n in nodes if degree[n]==0];heapq.heapify(ready);order=[]
 while ready:
  n=heapq.heappop(ready);order.append(n)
  for q in sorted(succ[n]):
   degree[q]-=1
   if degree[q]==0:heapq.heappush(ready,q)
 cyclic=sorted(nodes-set(order));least={};parents={};exhausted=[]
 if not cyclic:
  for n in order:
   values=np.asarray(domains[n],float)
   if values.ndim!=1 or not len(values)or not np.isfinite(values).all():raise ValueError('finite nonempty observed luminance domain')
   bound=max((least[p]for p in pred[n]),default=-np.inf);possible=values[values>bound]
   if not len(possible):exhausted.append(n);break
   least[n]=float(possible.min());parents[n]=min((p for p in pred[n]if least[p]==bound),default=None)
 return {'feasible':not same and not cyclic and not exhausted,'sameLabelOrders':same,'cyclicOrDependentRegions':cyclic,'exhaustedDomainRegions':exhausted,'leastNativeLuminance':least,'order':order,'predecessor':parents}
