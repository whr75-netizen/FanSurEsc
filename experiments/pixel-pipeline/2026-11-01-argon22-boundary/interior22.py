"""Whole-feature area allocation INSIDE a fixed source-derived upper boundary.

UpperLine has no area quota. Parent EyeUnion count error is minimized first,
then iris/white area error, then source evidence. This is the102 parent/child
hierarchy at REGION scope instead of applying a half-coverage veto per cell.
Area counts are discovered from current intrinsic support, never from a fixed
glyph size or immutable-bank texel count. Complete optimal labelings are
backtracked; if a resource bound is reached the result is explicitly incomplete
and must not be ranked as a unique final selection.
"""
from fractions import Fraction
import numpy as np

def fraction(v):return Fraction(float(v))
def interval_error(v,lo,hi):return max(Fraction(0),lo-v,v-hi)

def allocate(lowI,highI,lowW,highW,rows,lineCarrier,max_witnesses=65536):
    h,w=lowI.shape;fixed=np.zeros((h,w),np.int8);points=[];domains=[];costs=[]
    for y in range(h):
        for x in range(w):
            boundary=rows.get(x)
            if boundary is not None and y<boundary:continue
            if boundary is not None and y==boundary:fixed[y,x]=3 if lineCarrier[y,x]else-1;continue
            choices=[0]
            if lowI[y,x]>0:choices.append(1)
            if lowW[y,x]>0:choices.append(2)
            if len(choices)==1:continue
            points.append((y,x));domains.append(choices);values=[max(0,1-float(lowI[y,x])-float(lowW[y,x])),float(lowI[y,x]),float(lowW[y,x])];costs.append([1-fraction(v)for v in values])
    lo=[sum(map(fraction,a.flat))for a in [lowI,lowW]];hi=[sum(map(fraction,a.flat))for a in [highI,highW]]
    # Each state stores only its exact minimum source-reconstruction cost.
    # Earlier states are retained for COMPLETE optimal backtracking.
    dp=[{(0,0):Fraction(0)}]
    for choices,values in zip(domains,costs):
        new={}
        for (i,j),value in dp[-1].items():
            for p in choices:
                key=(i+(p==1),j+(p==2));cost=value+values[p]
                if key not in new or cost<new[key]:new[key]=cost
        dp.append(new)
    objective={}
    for key,value in dp[-1].items():
        i,j=key;parent=interval_error(Fraction(i+j),sum(lo),sum(hi));child=interval_error(Fraction(i),lo[0],hi[0])+interval_error(Fraction(j),lo[1],hi[1]);objective[key]=(parent,child,value)
    best=min(objective.values());counts=[k for k,v in objective.items()if v==best];solutions=[];truncated=False
    def back(n,key,path):
        nonlocal truncated
        if n==0:
            a=fixed.copy()
            for point,p in zip(points,path[::-1]):a[point]=p
            solutions.append(a)
            if max_witnesses and len(solutions)>=max_witnesses:truncated=True
            return
        for p in domains[n-1]:
            old=(key[0]-(p==1),key[1]-(p==2))
            if old in dp[n-1]and dp[n-1][old]+costs[n-1][p]==dp[n][key]:
                back(n-1,old,path+[p])
                if truncated:return
    for key in counts:
        back(len(points),key,[])
        if truncated:break
    return solutions,{'sourceMassBounds':[[str(a),str(b)]for a,b in zip(lo,hi)],'sourceMassBoundsFloat':[[float(a),float(b)]for a,b in zip(lo,hi)],'objective':['parent EyeUnion area error','child iris/white area error','source reconstruction error'],
      'exactObjective':[str(v)for v in best],'optimalChildCounts':[list(k)for k in counts],'completeOptimalEnumeration':not truncated,'optimalWitnesses':len(solutions),'DPStates':sum(map(len,dp)),
      'fixedTargetCount':False,'UpperLineIncludedInAreaQuota':False,'usesRGBOrLightQ':False,'unknownSourceSupportNotMadeVisible':True}

def connected_mask(mask,neighbours):
    if not mask:return True
    reached=mask&-mask;front=reached
    while front:
        nxt=0
        while front:
            bit=front&-front;front-=bit;nxt|=neighbours[bit.bit_length()-1]
        front=nxt&mask&~reached;reached|=front
    return reached==mask

def allocate_topology(lowI,highI,lowW,highW,rows,lineCarrier,bank_connected=(False,False)):
    """Exact small-ROI allocator, with source-justified component constraints.

    This is not a GPU algorithm: it enumerates source-supported subsets only,
    with a checked input bound (12 candidates/part on the saved40 inputs).
    A connected immutable source bank AND a connected certain-support graph
    justify the raster constraint. Already-split current support is NOT joined.
    This is a conservative SOURCE-GRID hypothesis, not a proof of the topology
    of unsampled continuous surfaces. Unknown-only support is not invented.
    Empty output remains feasible: there is no minimum size/part count.
    """
    from aperture22 import component_count
    h,w=lowI.shape;fixed=np.zeros((h,w),np.int8);points=[]
    for y in range(h):
        for x in range(w):
            b=rows.get(x)
            if b is not None and y==b:fixed[y,x]=3 if lineCarrier[y,x]else-1
            if (b is None or y>b)and(lowI[y,x]>0 or lowW[y,x]>0):points.append((y,x))
    ids={p:k for k,p in enumerate(points)};neighbours=[]
    for y,x in points:neighbours.append(sum(1<<ids[p]for p in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]if p in ids))
    inputs=[lowI,lowW];uppers=[highI,highW];masses=[sum(map(fraction,a.flat))for a in inputs];highMasses=[sum(map(fraction,a.flat))for a in uppers]
    conditions=[bool(bank_connected[k])and len(component_count(a>0,False))==1 for k,a in enumerate(inputs)];unionCondition=all(bank_connected)and len(component_count((lowI+lowW)>0,False))==1
    base=sum(fraction(lowI[p])+fraction(lowW[p])for p in points)
    # Source reconstruction increments from the all-canvas solution.
    increments=[[Fraction(1)-fraction(lowI[p])-fraction(lowW[p])-fraction(a[p])for p in points]for a in inputs]
    subsets=[];checked=[]
    for part,a in enumerate(inputs):
        candidates=[k for k,p in enumerate(points)if a[p]>0]
        if len(candidates)>20:raise ValueError('ROI exceeds exact offline subset budget; no truncated selection is accepted')
        table={};seen=0
        for bits in range(1<<len(candidates)):
            mask=sum(1<<k for j,k in enumerate(candidates)if bits>>j&1);seen+=1
            if conditions[part]and not connected_mask(mask,neighbours):continue
            table.setdefault(bits.bit_count(),[]).append((mask,sum(increments[part][k]for k in candidates if mask>>k&1)))
        subsets.append(table);checked.append(seen)
    countGroups={}
    for ni in subsets[0]:
        for nw in subsets[1]:
            parent=interval_error(Fraction(ni+nw),sum(masses),sum(highMasses));child=sum(interval_error(Fraction(n),a,b)for n,a,b in zip([ni,nw],masses,highMasses));countGroups.setdefault((parent,child),[]).append((ni,nw))
    tested=0;winnerMasks=[];bestData=None;bestArea=None
    for area,countPairs in sorted(countGroups.items()):
        for ni,nw in countPairs:
            for mi,ci in subsets[0][ni]:
                for mw,cw in subsets[1][nw]:
                    tested+=1
                    if mi&mw or unionCondition and not connected_mask(mi|mw,neighbours):continue
                    cost=base+ci+cw
                    if bestData is None or cost<bestData:bestData=cost;winnerMasks=[(mi,mw)]
                    elif cost==bestData:winnerMasks.append((mi,mw))
        if winnerMasks:bestArea=area;break
    assert winnerMasks # The all-canvas labeling is always permitted.
    layouts=[]
    for mi,mw in winnerMasks:
        a=fixed.copy()
        for k,p in enumerate(points):a[p]=1 if mi>>k&1 else 2 if mw>>k&1 else 0
        layouts.append(a)
    return layouts,{'completeOptimalEnumeration':True,'optimalWitnesses':len(layouts),'sourceMassBoundsFloat':[[float(a),float(b)]for a,b in zip(masses,highMasses)],'exactObjective':[str(v)for v in [*bestArea,bestData]],
      'objective':['immutable-bank AND certain-source-grid single-component constraints','parent EyeUnion area error','child iris/white area error','source reconstruction error'],
      'currentSourceConnectedIrisWhiteUnionConstraints':[*conditions,unionCondition],'sourceCandidateSubsetsEnumerated':checked,'subsetPairsChecked':tested,'UpperLineIncludedInAreaQuota':False,'fixedTargetCount':False,'usesRGBOrLightQ':False,'runtimeGPUImplemented':False}

def tests():
    # Tiny independent brute-force oracle, not a reimplementation trace.
    import itertools
    rng=np.random.default_rng(22);cases=0
    for n in range(1,7):
        a=rng.integers(0,5,(1,n))/8;b=rng.integers(0,5,(1,n))/8;out,info=allocate(a,a,b,b,{},np.zeros((1,n),bool),None);choices=[[0]+([1]if a[0,i]>0 else[])+([2]if b[0,i]>0 else[])for i in range(n)];costs=[]
        for v in itertools.product(*choices):
            i=v.count(1);j=v.count(2);la=sum(map(fraction,a.flat));lb=sum(map(fraction,b.flat));parent=abs(Fraction(i+j)-la-lb);child=abs(Fraction(i)-la)+abs(Fraction(j)-lb);data=sum(1-([max(0,1-float(a[0,k])-float(b[0,k])),float(a[0,k]),float(b[0,k])][p])for k,p in enumerate(v));costs.append((parent,child,fraction(data),v))
        best=min(v[:3]for v in costs);expected={q[3]for q in costs if q[:3]==best};actual={tuple(map(int,v.ravel()))for v in out};assert actual==expected and info['completeOptimalEnumeration'];cases+=1
    # A .6-cell important UNION survives even when each part is below.5.
    a=np.array([[.3]]);out,info=allocate(a,a,a,a,{},np.zeros((1,1),bool),None);assert all(np.count_nonzero(q)==1 for q in out)
    # True zero source/complete Close cannot be resurrected by an area budget.
    z=np.zeros((1,2));out,_=allocate(z,z,z,z,{},z.astype(bool),None);assert len(out)==1 and not out[0].any()
    return {'independentExhaustiveCases':cases,'parentUnionBeatsPerCellPartThreshold':True,'zeroSourceStaysZero':True,'noLineAreaQuota':True}
