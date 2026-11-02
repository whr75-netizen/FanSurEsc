"""Source-COMPONENT loss ablation of22, not fixed pixel minimums.

Whole active source components are an identity criterion before area error.
One output cell may cover several source IDs/components if its SAME-FRAME
support proves that overlap. No absent component is revived. A component with
no eligible below-boundary destination remains explicitly unrepresented.
No RGB, Q, external hair or screen-history enters canonical allocation.
"""
import sys
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent;P22=R/'argon22-boundary'if(R/'argon22-boundary').exists()else R/'2026-11-01-argon22-boundary';sys.path.insert(0,str(P22))
from interior22 import fraction,interval_error,connected_mask
from aperture22 import component_count

def solve(lowI,highI,lowW,highW,rows,lineCarrier,componentBits,activeBits,component_first):
    h,w=lowI.shape;fixed=np.zeros((h,w),np.int8);points=[]
    for y,x in np.ndindex((h,w)):
        b=rows.get(x)
        if b is not None and y==b:fixed[y,x]=3 if lineCarrier[y,x]else-1
        if (b is None or y>b)and(lowI[y,x]>0 or lowW[y,x]>0):points.append((y,x))
    lookup={p:k for k,p in enumerate(points)};neighbors=[sum(1<<lookup[q]for q in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]if q in lookup)for y,x in points];lo=[lowI,lowW];hi=[highI,highW];mass=[sum(map(fraction,v.flat))for v in lo];upper=[sum(map(fraction,v.flat))for v in hi];allCanvas=sum(fraction(lowI[p])+fraction(lowW[p])for p in points);subsets=[];componentChecks=[];checked=[]
    for part in [0,1]:
        candidates=[k for k,p in enumerate(points)if lo[part][p]>0];assert len(candidates)<=20,'Exact offline budget exceeded; no truncated accepted answer'
        # Every bit is a connected original bank component. Impose current
        # connectivity only when its certain current support is connected.
        bitMasks=[]
        for bit in range(int(activeBits[part]).bit_length()):
            if not(activeBits[part]>>bit&1):continue
            raw=(componentBits[part]&(1<<bit))>0
            if len(component_count(raw,False))==1:bitMasks.append(sum(1<<k for k,p in enumerate(points)if raw[p]))
        table={};componentChecks.append(len(bitMasks))
        for s in range(1<<len(candidates)):
            mask=sum(1<<k for j,k in enumerate(candidates)if s>>j&1)
            if any(not connected_mask(mask&scope,neighbors)for scope in bitMasks):continue
            bits=0;cost=0
            for k in candidates:
                if mask>>k&1:
                    p=points[k];bits|=int(componentBits[part][p]);cost+=1-fraction(lowI[p])-fraction(lowW[p])-fraction(lo[part][p])
            missing=(int(activeBits[part])&~bits).bit_count();table.setdefault((s.bit_count(),missing),[]).append((mask,cost,bits))
        subsets.append(table);checked.append(1<<len(candidates))
    levels={}
    for (ni,mi)in subsets[0]:
        for(nw,mw)in subsets[1]:
            loss=mi+mw;parent=interval_error(fraction(ni+nw),sum(mass),sum(upper));child=sum(interval_error(fraction(n),a,b)for n,a,b in zip([ni,nw],mass,upper));obj=(loss,parent,child)if component_first else(parent,child,loss);levels.setdefault(obj,[]).append(((ni,mi),(nw,mw)))
    best=None;winners=[];tried=0
    for level,pairs in sorted(levels.items()):
        for ki,kw in pairs:
            for mi,ci,bi in subsets[0][ki]:
                for mw,cw,bw in subsets[1][kw]:
                    tried+=1
                    if mi&mw:continue
                    cost=allCanvas+ci+cw
                    if best is None or cost<best:best=cost;winners=[(mi,mw,bi,bw)]
                    elif cost==best:winners.append((mi,mw,bi,bw))
        if winners:break
    out=[]
    for mi,mw,bi,bw in winners:
        a=fixed.copy()
        for k,p in enumerate(points):a[p]=1 if mi>>k&1 else 2 if mw>>k&1 else 0
        out.append(a)
    return out,{'componentFirst':component_first,'exactObjective':[str(v)for v in (*level,best)],'objectiveOrder':['source component loss','parent area error','child area error','source reconstruction error']if component_first else['parent area error','child area error','source component loss','source reconstruction error'],'allOptimalSolutionsEnumerated':True,'optima':len(out),'enumeratedCandidateSubsets':checked,'subsetPairsCompared':tried,'sourceConnectivityConstraints':componentChecks,'activeComponents':list(map(int,activeBits)),'representedComponents':[[bi,bw]for mi,mw,bi,bw in winners],'constantPixelMinimum':False,'UpperLineAreaQuota':False,'externalHairAffectsCanonicalShape':False,'RGBOrQInObjective':False,'runtimeGPUImplementation':False}
