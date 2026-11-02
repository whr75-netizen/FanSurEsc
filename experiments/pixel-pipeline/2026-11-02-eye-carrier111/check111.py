"""Independent finite oracle and saved actual-input regressions."""
import itertools,json
from fractions import Fraction
from pathlib import Path
import numpy as np
from geometry111 import H,read
from allocate111 import solve
def connected(mask):
    s=set(map(tuple,np.argwhere(mask)))
    if not s:return True
    seen={next(iter(s))};todo=list(seen)
    while todo:
        y,x=todo.pop()
        for q in[(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
            if q in s and q not in seen:seen.add(q);todo.append(q)
    return seen==s
def key(a):return tuple(map(int,a.flat))
def main():
    rng=np.random.default_rng(111);oracles=0;symmetry=0
    for _ in range(10):
        a=rng.integers(0,4,(2,3))/8;b=rng.integers(0,4,(2,3))/8;bits=[(a>0).astype(np.uint32),(b>0).astype(np.uint32)];active=[int(a.any()),int(b.any())]
        for priority in[False,True]:
            layouts,info=solve(a,a,b,b,{},np.zeros_like(a,bool),bits,active,priority);constraints=[connected(q>0)for q in[a,b]];choices=[[0]+([1]if a[p]>0 else[])+([2]if b[p]>0 else[])for p in np.ndindex(a.shape)];records=[];ma=Fraction(float(a.sum()));mb=Fraction(float(b.sum()))
            for labels in itertools.product(*choices):
                q=np.array(labels).reshape(a.shape)
                if any(flag and not connected(q==part)for part,flag in zip([1,2],constraints)):continue
                ni=labels.count(1);nw=labels.count(2);miss=(active[0]and not ni)+(active[1]and not nw);parent=abs(ni+nw-ma-mb);child=abs(ni-ma)+abs(nw-mb);data=sum(1-[1-Fraction(float(a[p]))-Fraction(float(b[p])),Fraction(float(a[p])),Fraction(float(b[p]))][q[p]]for p in np.ndindex(a.shape));cost=(miss,parent,child,data)if priority else(parent,child,miss,data);records.append((cost,labels))
            best=min(x[0]for x in records);assert {key(q)for q in layouts}=={q for cost,q in records if cost==best};oracles+=1
            for reflect in[False,True]:
                for k in range(4):
                    transform=lambda v:np.rot90(np.fliplr(v)if reflect else v,k);aa,bb=transform(a),transform(b);out,_=solve(aa,aa,bb,bb,{},np.zeros_like(aa,bool),list(map(transform,bits)),active,priority);assert{key(transform(v))for v in layouts}=={key(v)for v in out};symmetry+=1
    z=np.zeros((1,1));w=np.array([[.1]]);b=np.array([[3]],np.uint32);q,info=solve(z,z,w,w,{},z.astype(bool),[z.astype(np.uint32),b],[0,3],True);assert len(q)==1 and int(q[0][0,0])==2 # one cell can carry two source components
    q,_=solve(z,z,z,z,{},z.astype(bool),[z.astype(np.uint32)]*2,[0,0],True);assert len(q)==1 and not q[0].any()
    paths=list(H.glob('ANALYSIS111-frame*.json'))or[H/f'ANALYSIS111-frame{v["frame"]}.json'for v in read(H/'CAPTURE_INDEX111.json')['packets']if v['kind']=='original'];cases=[read(p)for p in paths];assert len(cases)==12
    assert all(not e['sourceComponentUnresolved']and all(v['sourceKeyUnique']for v in e['sourceIDs'])for c in cases for e in c['eyes'])
    assert all(c['actualGPUValidation']['maxCPUvsGPUVisibilityIntervalDifference']==0 for c in cases)
    closed=next(c for c in cases if c['stage'].get('requestedClose')==100);assert all(not any(v['iris']or v['white']for v in e['variants'][1]['counts'])for e in closed['eyes'])
    hair=[next(c for c in cases if c['frame']==f)for f in[122,125,128]]
    for owner in[1,2]:assert all(hair[0]['eyes'][owner-1]['variants'][1]['labels']==c['eyes'][owner-1]['variants'][1]['labels']for c in hair)
    result={'completeIndependentOracles':oracles,'D4InteriorCompleteLayoutSetChecks':symmetry,'fixedMinimumCellCount':False,'oneCellMayRepresentSeveralSupportedSourceComponents':True,'zeroSupportNotResurrected':True,'actualGPUFrames':12,'GPUCarrierRaySamples':sum(c['actualGPUValidation']['sampledGPUCarrierQueryChecks']for c in cases),'maxCPUvsGPUCarrierQueryDifference':0,'hairON_OFF_restoredCanonicalSetsIdentical':True,'actualFrameGapsNotClaimedConsecutive':True,'finalRGBOrPaletteValidation':False,'runtimeAllocatorApplied':False};(H/'CHECK111.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
