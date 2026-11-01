"""Portable frozen-fixture checks. No raw paths, Unity, images or network needed."""
from pathlib import Path
import itertools,json,hashlib,time
import numpy as np
from joint108 import solve,tests,neighbours
H=Path(__file__).resolve().parent
POLICIES=[('noCurve',False,False,False),('arc4',True,False,False),('arc8',True,True,False),('relaxedCarrier4',True,False,True)]

def exact_model_oracle():
    rng=np.random.default_rng(8108);checks=0
    for case in range(12):
        # Small general eligibility graph; enumerate every full ROI assignment.
        fine=rng.integers(0,5,(4,2,3));fine[0]+=1;den=16
        source=np.zeros((7,2,3));source[:4]=fine/den;s=source>0;s[0]=True
        d={'lower':source,'upper':source.copy(),'support':s,'keys':np.array([(0,0),(1,1),(1,4),(1,6),(2,1),(2,4),(2,6)]),
           'sourceSegments':np.array([[[.5,.5,0,1],[2.5,1.5,0,1]]])}
        points=[tuple(map(int,q))for q in np.argwhere(s[1:4].any(0))]
        domains=[[p for p in range(4)if s[p,y,x]]for y,x in points];required=[p for p in range(1,4)if s[p].any()]
        for curve in [False,True]:
            for diag in [False,True]if curve else[False]:
                candidates=[];g=neighbours(points,diag)
                for labels in itertools.product(*domains):
                    if any(p not in labels for p in required):continue
                    if curve:
                        if(0,0)not in points or(1,2)not in points:continue
                        start=points.index((0,0));end=points.index((1,2))
                        if labels[start]!=3 or labels[end]!=3:continue
                        reached={start};todo=[start]
                        while todo:
                            for j in g[todo.pop()]:
                                if labels[j]==3 and j not in reached:reached.add(j);todo.append(j)
                        if end not in reached:continue
                    mass=sum(abs(labels.count(p)*den-int(fine[p].sum()))for p in range(1,4))
                    data=sum(den-int(fine[p,y,x])for(y,x),p in zip(points,labels));candidates.append((mass,data,labels))
                q=solve(d,1,curve,diag)
                if not candidates:assert q['status'].startswith('infeasible')
                else:
                    best=min((a,b)for a,b,c in candidates);dmin=min(b for a,b,c in candidates)
                    assert q['massFirst']['mass']==best[0]/den and q['massFirst']['data']==best[1]/den
                    assert q['dataFirst']['data']==dmin/den
                    assert q['massFirstIsUnique']==(sum((a,b)==best for a,b,c in candidates)==1)
                    assert q['dataFirstIsUnique']==(sum(b==dmin for a,b,c in candidates)==1)
                checks+=1
    return checks

def transformed(d,reflection=False):
    out={k:d[k].copy()for k in d.files};w=d['support'].shape[-1]
    for k in ['lower','upper','support','dominantSampleCounts']:
        out[k]=np.flip(d[k],axis=-1)if reflection else np.rot90(d[k],axes=(-2,-1))
    s=out['sourceSegments'];x=s[:,:,0].copy();y=s[:,:,1].copy()
    s[:,:,0]=w-x if reflection else y
    if not reflection:s[:,:,1]=w-x
    return out

def main():
    begin=time.perf_counter();base=tests();oracle=exact_model_oracle();rows=json.loads((H/'INPUT108.json').read_text());expected=json.loads((H/'RESULTS108.json').read_text());checks=0
    for row in rows:
        p=H/'fixtures'/(row['name']+'.npz');assert hashlib.sha256(p.read_bytes()).hexdigest()==row['fileSHA256'];d=np.load(p)
        assert not np.any(d['support'][1:4].any(0)&d['support'][4:7].any(0))
        for name,c,g,r in POLICIES:
            for owner in [1,2]:
                q=solve(d,owner,c,g,r);old=expected[row['name']][name][str(owner)];assert q['status']==old['status']
                if 'massFirst'in q:
                    for field in ['massFirst','dataFirst']:
                        for k in ['dataExactUnits','massExactUnits']:assert q[field][k]==old[field][k]
                    for k in ['exactCostUnitDenominator','massFirstIsUnique','dataFirstIsUnique']:assert q[k]==old[k]
                checks+=1
    metamorphic=0;d=np.load(H/'fixtures/actual107-frame103.npz')
    for reflection in [False,True]:
        rotated=transformed(d,reflection)
        for name,c,g,r in POLICIES:
            for owner in [1,2]:
                a=solve(d,owner,c,g,r);b=solve(rotated,owner,c,g,r);assert a['status']==b['status']
                if 'massFirst'in a:
                    assert a['exactCostUnitDenominator']==b['exactCostUnitDenominator']
                    for key in ['massFirst','dataFirst']:
                        assert a[key]['dataExactUnits']==b[key]['dataExactUnits']and a[key]['massExactUnits']==b[key]['massExactUnits']
                    assert a['massFirstIsUnique']==b['massFirstIsUnique']and a['dataFirstIsUnique']==b['dataFirstIsUnique']
                metamorphic+=1
    result=base|{'completeTinyROIAssignmentOracleCases':oracle,'frozenOwnerPolicySolves':checks,'fixturesSHA256':len(rows),'rotationReflectionObjectiveChecks':metamorphic,
      'seconds':time.perf_counter()-begin,'newPlay':0,'productApplied':False,'notAMotionStabilityTest':True}
    (H/'CHECK108.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
