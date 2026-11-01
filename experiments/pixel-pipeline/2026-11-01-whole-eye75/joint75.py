"""Joint ownership feasibility, no ranking/artist weights or renderer calls."""
from itertools import combinations
def hall(domains,demands):
 """Exact capacity check for identical per-family token domains.

 This is only a relaxation of shape-preserving joint placement. A failed Hall
 condition proves this declared restricted problem impossible; passing is not
 a complete pose/curve/colour solution.
 """
 families=sorted(demands)
 if any(demands[f]<0 or not isinstance(demands[f],int) for f in families):raise ValueError('Explicit nonnegative demands required')
 witnesses=[]
 for n in range(1,len(families)+1):
  for subset in combinations(families,n):
   slots=set().union(*(set(domains.get(f,()))for f in subset));need=sum(demands[f]for f in subset)
   if need>len(slots):witnesses.append({'families':list(subset),'need':need,'slots':len(slots),'deficit':need-len(slots),'cells':[list(p)for p in sorted(slots)]})
 witnesses.sort(key=lambda v:(len(v['families']),-v['deficit'],v['families']))
 return {'capacityFeasible':not witnesses,'witnesses':witnesses,'meaning':'declared domains/demands only; not actual physical visibility or full eye readability'}
def state_contract(state,parts):
 missing=[p for p in parts if not state.get(p,{}).get('intrinsicDefinition')]
 return {'complete':not missing,'missing':missing,'openFallbackAllowed':False}
def layered_identity(cells,visible_ids):
 ids=[c['cellId']for c in cells]
 if len(ids)!=len(set(ids))or not set(visible_ids)<=set(ids):raise ValueError('Source identity mismatch')
 return [{'cellId':c['cellId'],'eye':c['eye'],'role':c['role'],'rgba8':list(c['rgba8']),'visible':c['cellId']in visible_ids}for c in cells]
