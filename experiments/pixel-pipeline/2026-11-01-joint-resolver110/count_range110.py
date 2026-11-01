"""Exact count feasibility at an already-proven geometric optimum.
These are diagnostic quotas, NOT a count target or a new appearance policy.
They test whether the 64-witness bound hid larger/smaller valid shapes.
"""
import json,time
import numpy as np
from stored110 import H
from resolver110 import constraints,feasible,metrics

def main():
    out=[];start=time.perf_counter()
    for frame,owner in [(99,1),(99,2),(103,1),(103,2),(107,1),(107,2),(207,1)]:
        base=H/'separated';stem=f'frame{frame}-eye{owner}';r=json.loads((base/(stem+'-result.json')).read_text());d=np.load(base/(stem+'.npz'));cells=[tuple(map(int,v))for v in d['cells']];refs={p:d['reference'+str(p)]for p in [1,2,3]};ds,clauses=constraints(cells,d['eligibility'],refs,r['errorPixels']);conn={int(k):v for k,v in r['connectivity'].items()};items={};witnesses=[]
        for p in [1,2,3]:
            counts=[]
            for k in range(sum(bool(v>>p&1)for v in ds)+1):
                q,info=feasible(ds,clauses,cells,conn,1,{p:(k,k)})
                if q:counts.append(k);witnesses.append({'part':p,'exactCount':k,'labels':list(q[0]),'metrics':metrics(cells,q[0],refs)})
            items[str(p)]=counts
        out.append({'frame':frame,'owner':owner,'errorPixels':r['errorPixels'],'feasibleCountsAtSameOptimum':items,'witnesses':witnesses,'notDefaultCountConstraints':True});print(json.dumps({k:v for k,v in out[-1].items()if k!='witnesses'}),flush=True)
    (H/'COUNT_RANGE110.json').write_text(json.dumps({'cases':out,'seconds':time.perf_counter()-start},indent=2)+'\n',encoding='utf8')
if __name__=='__main__':main()
