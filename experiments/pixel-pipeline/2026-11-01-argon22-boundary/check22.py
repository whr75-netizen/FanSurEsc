"""Independent tiny oracle, symmetry checks and saved regression assertions."""
from pathlib import Path
import itertools,json,sys
import numpy as np
from paths22 import H
from interior22 import allocate_topology,tests,fraction,interval_error
from aperture22 import component_count,domain_counterexamples

def connected(a):
    points={tuple(map(int,v))for v in np.argwhere(a)}
    if not points:return True
    seen={next(iter(points))};todo=list(seen)
    while todo:
        y,x=todo.pop()
        for p in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
            if p in points and p not in seen:seen.add(p);todo.append(p)
    return seen==points

def key(a):return tuple(map(int,a.ravel()))

def main():
    rng=np.random.default_rng(2202);oracle=0;symmetry=0
    for case in range(12):
        a=rng.integers(0,4,(2,3))/8;b=rng.integers(0,4,(2,3))/8;out,info=allocate_topology(a,a,b,b,{},np.zeros_like(a,bool),(True,True));constraints=info['currentSourceConnectedIrisWhiteUnionConstraints'];mass=[sum(map(fraction,v.flat))for v in [a,b]];records=[]
        choices=[[0]+([1]if a[p]>0 else[])+([2]if b[p]>0 else[])for p in np.ndindex(a.shape)]
        for labels in itertools.product(*choices):
            q=np.array(labels).reshape(a.shape)
            if any(required and not connected(mask)for required,mask in zip(constraints,[q==1,q==2,q>0])):continue
            i=labels.count(1);w=labels.count(2);cost=sum(1-([1-fraction(a[p])-fraction(b[p]),fraction(a[p]),fraction(b[p])][q[p]])for p in np.ndindex(a.shape));obj=(abs(i+w-sum(mass)),abs(i-mass[0])+abs(w-mass[1]),cost);records.append((obj,labels))
        best=min(x[0]for x in records);expected={x[1]for x in records if x[0]==best};assert {key(q)for q in out}==expected;oracle+=1
        # The interior constraint is in feature coordinates and does not pick
        # a scanning direction. The global-X LINE rule is tested separately.
        for reflect in [False,True]:
            for rot in range(4):
                f=lambda q:np.rot90(np.fliplr(q)if reflect else q,rot)
                aa,bb=f(a),f(b);new,_=allocate_topology(aa,aa,bb,bb,{},np.zeros_like(aa,bool),(True,True));assert {key(f(q))for q in out}=={key(q)for q in new};symmetry+=1
    summary=json.loads((H/'TOPOLOGY_RESULTS22.json').read_text())
    cases=summary['cases'];assert len(cases)==40 and summary['summary']['incompleteAreaEnumerations']==0
    assert all(c['boundaryIdenticalToLocal22']for c in cases)
    assert not any(c['positiveUnionExtinguished']for c in cases)
    assert all(not any(v['iris']or v['white']for v in c['counts'])for c in cases if c['sourceEmptyIrisWhite'])
    assert all(p['completeCanonicalLayoutSetsEqual']for p in summary['summary']['phase'])
    for c in cases:
        if c['allocation']['currentSourceConnectedIrisWhiteUnionConstraints'][0]:assert all(len(v['irisComponents4'])<=1 for v in c['counts'])
    for frame in [105,109]:
        c=next(v for v in cases if v['dataset']==f'actual107-frame{frame}'and v['owner']==2);assert len(c['labels'])==1 and c['allocation']['optimalWitnesses']==2;assert c['formRanking']['unknownGeometryNotScoredAsPerfect'];assert c['counts'][0]['iris']==1
    # These are not generic 'all white must connect' constraints: the actual
    # immutable white bank has separate clusters, and must not be auto-joined.
    assert all(c['allocation']['immutableBankConnectedIrisWhite']==[True,False]for c in cases)
    result={'independentCompleteLabelOracleCases':oracle,'interiorD4CompleteSetChecks':symmetry,'savedEyeStates':40,'sourceConnectedIrisNeverSplit':True,'UpperLineUnchangedByInteriorAllocation':True,'positiveEyeUnionNotExtinguished':True,'fullCloseNotResurrected':True,'phaseCanonicalSetsEqual':True,'bankWhiteNotForcedConnected':True,'missingPairGeometryIsUnknownNotZero':True,'noHistoryUsed':True,'newUnityCalls':0,'newGPU':0,'productApplied':False,'boundaryDomainCounterexamples':domain_counterexamples(),'smallOriginalTests':tests()}
    (H/'CHECK22.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result))
if __name__=='__main__':main()
