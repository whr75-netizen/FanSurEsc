import itertools,json,numpy as np
from pathlib import Path
from palette_constraints92 import constrained
from audit_polarity76 import luminance
def main():
 checks=0
 # Exhaustive two-address oracle, including exact-zero contrast and Y conflict.
 for seed in range(12):
  rng=np.random.default_rng(seed);t=rng.uniform(80,82,(2,3));v=rng.integers(-2,3,3)
  if not(v!=0).any():v[0]=1
  vec=[(0,1,*v)];domains=[list(itertools.product(*[(int(np.floor(x)),int(np.ceil(x)))for x in c]))for c in t];feasible=any(luminance(np.array(a))<luminance(np.array(b))and(np.array(a)-b)@v>0 for a in domains[0]for b in domains[1]);r=constrained(t,[(0,1)],vec);assert r['feasible']==feasible;checks+=1
  q=constrained(t,[(0,1)],[(1,0,*(-v))]);assert q['feasible']==r['feasible']
  if q['feasible']:assert np.array_equal(q['rgb8'],r['rgb8'])
  checks+=1
 t=np.array([[10.,10.,10.],[20.,20.,20.]]);assert not constrained(t,[(0,1)],[(0,1,1,1,1)])['feasible'];checks+=1
 assert constrained(np.array([[100.1,101.2,102.3]]),[],[],node_budget=0)['reason']=='search-budget';checks+=1
 g=Path(__file__).resolve().parent/'face92';d={'CPUChecks':checks,'exactTwoAddressEnumerationOracle':True,'pairEndpointSwapInvariant':True,'infeasibleAndSearchBudgetExplicit':True,'GPUUsed':False};(g/'CPU_PALETTE_CONSTRAINTS92.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
