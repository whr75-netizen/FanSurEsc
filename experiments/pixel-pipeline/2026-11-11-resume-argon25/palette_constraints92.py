"""Bounded CPU feasibility of RGB8 rounding, not an RGB/style optimizer.

Reuse88's per-channel floor/ceil domains. Add only measured native RGB contrast
directions to existing strict Y orders. Arc consistency and bounded search are
CPU preprocessing; they never run in a shader or upload expected GPU output.
Infeasibility and search-budget exhaustion are distinct outcomes.
"""
from collections import deque
import itertools,numpy as np
from palette_round88 import solve
from audit_polarity76 import luminance

def constrained(targets,orders,vectors,node_budget=4096):
 t=np.asarray(targets,float);base=solve(t,orders)
 if not base['feasible']:return {'feasible':False,'reason':'Y-domain-infeasible','base':base}
 n=len(t);candidates=[np.asarray(list(itertools.product(*[sorted({int(np.floor(v)),int(np.ceil(v))})for v in row])),np.int64)for row in t];tables={};arcs=[[]for _ in range(n)];unique=np.unique(np.concatenate(candidates),axis=0);ys={tuple(c):float(y)for c,y in zip(unique,luminance(unique))}
 def relation(a,b,allowed):
  if not(0<=a<n and 0<=b<n)or a==b:raise ValueError('distinct bounded palette endpoints')
  if a>b:a,b=b,a;allowed=allowed.T
  key=(a,b);tables[key]=allowed if key not in tables else tables[key]&allowed
 for a,b in orders:
  va=np.asarray([ys[tuple(c)]for c in candidates[a]]);vb=np.asarray([ys[tuple(c)]for c in candidates[b]]);relation(int(a),int(b),va[:,None]<vb[None,:])
 for a,b,dr,dg,db in vectors:
  a,b=int(a),int(b);v=np.array([dr,dg,db],np.int64)
  if not(v!=0).any():raise ValueError('nonzero native colour contrast')
  relation(a,b,((candidates[a][:,None,:]-candidates[b][None,:,:])*v).sum(2)>0)
 for a,b in tables:arcs[a].append(b);arcs[b].append(a)
 def table(a,b):return tables[(a,b)]if a<b else tables[(b,a)].T
 revisions=0
 def propagate(domains,queue):
  nonlocal revisions
  queue=deque(queue)
  while queue:
   a,b=queue.popleft();revisions+=1
   if revisions>2000000:return 'budget'
   ids=np.flatnonzero(domains[a]);other=np.flatnonzero(domains[b]);valid=table(a,b)[np.ix_(ids,other)].any(1);remove=ids[~valid]
   if len(remove):
    domains[a][remove]=False
    if not domains[a].any():return 'infeasible'
    queue.extend((q,a)for q in arcs[a]if q!=b)
  return 'ok'
 domains=[np.ones(len(c),bool)for c in candidates];reason=propagate(domains,[(a,b)for a in range(n)for b in arcs[a]])
 if reason!='ok':return {'feasible':False,'reason':'arc-'+reason,'searchNodes':0,'arcRevisions':revisions}
 # Iterative, budgeted DFS; prefer the existing feasible-Y output. Otherwise
 # rank only original continuous-target rounding error then canonical RGB.
 # No claim of global minimum SSE or unique artistic solution.
 rank=[]
 for i,c in enumerate(candidates):
  cost=((c-t[i])**2).sum(1);rank.append(sorted(range(len(c)),key=lambda j:(not np.array_equal(c[j],base['rgb8'][i]),float(cost[j]),tuple(c[j]))))
 nodes=0;stack=[domains]
 while stack:
  if nodes>=node_budget:return {'feasible':False,'reason':'search-budget','searchNodes':nodes,'arcRevisions':revisions}
  domains=stack.pop();nodes+=1;undecided=[i for i,d in enumerate(domains)if np.count_nonzero(d)>1]
  if not undecided:
   selected=np.asarray([candidates[i][np.flatnonzero(domains[i])[0]]for i in range(n)],np.uint8);assert all(ys[tuple(selected[a])]<ys[tuple(selected[b])]for a,b in orders);assert all((selected[int(a)].astype(np.int64)-selected[int(b)])@np.array([dr,dg,db])>0 for a,b,dr,dg,db in vectors)
   return {'feasible':True,'rgb8':selected,'searchNodes':nodes,'arcRevisions':revisions,'maxTargetCodeError':float(np.max(abs(selected-t),initial=0)),'changedFromYOnlyEntries':int(np.count_nonzero((selected!=base['rgb8']).any(1))),'globalMinimumTotalSSEClaimed':False}
  i=min(undecided,key=lambda j:(int(domains[j].sum()),-len(arcs[j]),j));children=[]
  for at in rank[i]:
   if not domains[i][at]:continue
   child=[d.copy()for d in domains];child[i][:]=False;child[i][at]=True;status=propagate(child,[(q,i)for q in arcs[i]])
   if status=='budget':return {'feasible':False,'reason':'arc-budget','searchNodes':nodes,'arcRevisions':revisions}
   if status=='ok':children.append(child)
  stack.extend(reversed(children))
 return {'feasible':False,'reason':'complete-infeasible','searchNodes':nodes,'arcRevisions':revisions}
