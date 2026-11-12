"""Constrained RGB8 rounding of existing58 continuous palette targets.

Only floor/ceil of each target channel is allowed. Source-feature contrast
orders are explicit inputs, not inferred from material IDs or fitted colours.
No new light/colour artistic parameter is introduced. If these finite domains
cannot satisfy the orders, fail rather than changing target colours or bounds.
"""
import itertools,numpy as np
from audit_polarity76 import luminance
from region_order79 import feasible

def solve(targets,orders):
 t=np.asarray(targets,float)
 if t.ndim!=2 or t.shape[1]!=3 or len(t)>16384 or not np.isfinite(t).all()or(t<0).any()or(t>255).any():raise ValueError('bounded encoded-RGB palette targets')
 edges=sorted(set((int(a),int(b))for a,b in orders));candidates={i:np.array(list(itertools.product(*[sorted({int(np.floor(v)),int(np.ceil(v))})for v in row])),np.uint8)for i,row in enumerate(t)}
 # One shared value per actual RGB tuple. Recomputing a scalar dot product
 # after a batch BLAS dot can differ by one floating ULP and falsely treat
 # identical RGB as a strict contrast. Never create order from that artifact.
 unique=np.unique(np.concatenate(list(candidates.values())),axis=0);shared={tuple(c):float(y)for c,y in zip(unique,luminance(unique))};ys={i:np.array([shared[tuple(v)]for v in c])for i,c in candidates.items()};graph=feasible(ys,edges)
 if not graph['feasible']:return {'feasible':False,'witness':graph}
 succ={i:set()for i in candidates};pred={i:set()for i in candidates}
 for a,b in edges:succ[a].add(b);pred[b].add(a)
 upper={}
 for i in reversed(graph['order']):
  bound=min((upper[j]for j in succ[i]),default=np.inf);v=ys[i][ys[i]<bound];assert len(v);upper[i]=float(v.max())
 out=np.empty((len(t),3),np.uint8);chosen_y={}
 for i in graph['order']:
  bound=max((chosen_y[j]for j in pred[i]),default=-np.inf);ok=(ys[i]>bound)&(ys[i]<=upper[i]);c=candidates[i][ok];cost=((c.astype(float)-t[i])**2).sum(1);at=int(np.lexsort((c[:,2],c[:,1],c[:,0],cost))[0]);out[i]=c[at];chosen_y[i]=shared[tuple(c[at])]
 assert all(chosen_y[a]<chosen_y[b]for a,b in edges);assert np.max(abs(out-t),initial=0)<1+1e-12
 return {'feasible':True,'rgb8':out,'maxTargetCodeError':float(np.max(abs(out-t),initial=0)),'globalMinimumTotalSSEClaimed':False}
