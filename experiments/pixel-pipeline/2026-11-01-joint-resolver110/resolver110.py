"""Finite reference-point JOINT minimax geometry resolver; NOT product code.

No source-area rounding, RGB cost, label priority, scan-order tie breaker or
fixed glyph count. All parts share ONE cell variable. The explicit hypothesis
is equal geometric importance: minimize maximum source-to-pixel-square and
pixel-corner-to-source distance (pixels). This is a design policy, not recovered
artist intent. Distances describe finite supplied references, not a theorem
about a continuous unobserved surface. Equally optimal layouts stay multiple.

Carrier eligibility is supplied by the geometry/visibility adapter. Its
per-sample footprint records MUST accompany labels to the final compositor.
A label is NEVER evidence that one depth owns the whole square.
"""
import itertools,math,time
import numpy as np

def distances(points,cells):
    q=np.asarray(points,float);c=np.asarray(cells,float)[:,::-1]
    # Reference points -> closed pixel squares. Square corners -> references.
    delta=np.maximum(np.maximum(c[None]-q[:,None],q[:,None]-(c+1)[None]),0)
    omission=np.linalg.norm(delta,axis=2)
    corners=c[:,None]+np.array([[0,0],[1,0],[0,1],[1,1]])
    commission=np.linalg.norm(corners[:,:,None]-q[None,None],axis=3).min(2).max(1)
    return omission,commission

def connected(mask,cells,diagonal):
    wanted={i for i in range(len(cells))if mask>>i&1}
    if not wanted:return False
    lookup={tuple(v):i for i,v in enumerate(cells)};seen={next(iter(wanted))};todo=list(seen)
    shifts=[(-1,0),(1,0),(0,-1),(0,1)]
    if diagonal:shifts += [(-1,-1),(-1,1),(1,-1),(1,1)]
    while todo:
        y,x=cells[todo.pop()]
        for dy,dx in shifts:
            j=lookup.get((y+dy,x+dx))
            if j in wanted and j not in seen:seen.add(j);todo.append(j)
    return seen==wanted

def feasible(domains,clauses,cells,connectivity,limit=None,count_bounds=None):
    """Exact finite CSP, unit propagation + MRV, no heuristic acceptance.
    limit bounds retained witnesses, NOT an optimality claim about unsearched
    solutions. Feasibility may stop at the first witness; enumeration reports
    when incomplete. Candidate order never selects a displayed unique answer.
    """
    result=[];nodes=0;truncated=False
    neighbours={p:[[j for j,b in enumerate(cells)if i!=j and
        (max(abs(a[0]-b[0]),abs(a[1]-b[1]))<=1 if diag else abs(a[0]-b[0])+abs(a[1]-b[1])==1)]for i,a in enumerate(cells)]for p,diag in connectivity.items()}
    def visit(ds):
        nonlocal nodes,truncated
        nodes+=1;ds=list(ds)
        while True:
            changed=False
            if any(not v for v in ds):return
            # Optional exact feasibility diagnostics, NEVER a style count in
            # the default resolver. Used to discover whether a truncated
            # witness set hid other output budgets at the SAME optimal error.
            for p,(lower,upper)in (count_bounds or {}).items():
                fixed=[i for i,v in enumerate(ds)if v==1<<p];possible=[i for i,v in enumerate(ds)if v>>p&1]
                if len(fixed)>upper or len(possible)<lower:return
                if len(fixed)==upper:
                    for i in possible:
                        if i not in fixed:ds[i]&=~(1<<p);changed=True
                elif len(possible)==lower:
                    for i in possible:
                        if ds[i]!=1<<p:ds[i]=1<<p;changed=True
            for p,mask in clauses:
                if any(mask>>i&1 and ds[i]==1<<p for i in range(len(ds))):continue
                candidates=[i for i in range(len(ds))if mask>>i&1 and ds[i]>>p&1]
                if not candidates:return
                if len(candidates)==1:
                    i=candidates[0]
                    if ds[i]!=(1<<p):ds[i]=1<<p;changed=True
            if not changed:break
        # A required part may not be split by cells it can no longer occupy.
        for p in connectivity:
            required=[i for i,v in enumerate(ds)if v==1<<p]
            if len(required)<2:continue
            seen={required[0]};todo=required[:1]
            while todo:
                for j in neighbours[p][todo.pop()]:
                    if ds[j]>>p&1 and j not in seen:seen.add(j);todo.append(j)
            if any(i not in seen for i in required):return
        if all(v.bit_count()==1 for v in ds):
            labels=tuple(v.bit_length()-1 for v in ds)
            if any(not connected(sum(1<<i for i,v in enumerate(labels)if v==p),cells,diag)for p,diag in connectivity.items()):return
            result.append(labels)
            if limit and len(result)>=limit:truncated=True
            return
        # Branch on a still-unsatisfied coverage clause. Positive/negative
        # literal branches partition all assignments exactly. Unlike trying
        # canvas in every cell first, this does not enumerate irrelevant
        # backgrounds before proving source coverage impossible.
        unsatisfied=[]
        for p,mask in clauses:
            if any(mask>>i&1 and ds[i]==1<<p for i in range(len(ds))):continue
            choices=[i for i,v in enumerate(ds)if mask>>i&1 and v>>p&1]
            unsatisfied.append((len(choices),p,choices))
        if unsatisfied:
            _,p,choices=min(unsatisfied,key=lambda v:v[0]);i=max(choices,key=lambda j:sum(pp==p and bool(mm>>j&1)for pp,mm in clauses))
            for value in [1<<p,ds[i]&~(1<<p)]:
                new=ds.copy();new[i]=value;visit(new)
                if truncated:return
            return
        i=min((i for i,v in enumerate(ds)if v.bit_count()>1),key=lambda i:(ds[i].bit_count(),-sum(bool(mask>>i&1)for p,mask in clauses)))
        for p in range(4):
            if ds[i]>>p&1:
                new=ds.copy();new[i]=1<<p;visit(new)
                if truncated:return
    visit(domains)
    return result,{'nodes':nodes,'enumerationComplete':not truncated}

def constraints(cells,eligibility,references,level):
    active=[p for p,q in references.items()if len(q)];dist={p:distances(references[p],cells)for p in active}
    ds=[1|sum(1<<p for p in active if eligibility[i,p]and dist[p][1][i]<=level)for i in range(len(cells))];clauses=set()
    for p in active:
        for row in dist[p][0]:clauses.add((p,sum(1<<i for i in range(len(cells))if ds[i]>>p&1 and row[i]<=level)))
    reduced=[(p,m)for p,m in clauses if not any(pp==p and mm!=m and mm&m==mm for pp,mm in clauses)]
    return ds,reduced

def solve(cells,eligibility,references,connectivity=None,witness_limit=128):
    started=time.perf_counter();connectivity=connectivity or {};active=sorted(p for p,q in references.items()if len(q))
    if not active:return {'status':'no-visible-reference','labels':[0]*len(cells),'solutions':[],'errorPixels':0,'enumerationComplete':True}
    if not len(cells):return {'status':'no-certain-visible-carrier','solutions':[],'activeBeforeExternalHair':active,'historyCannotRestoreAnIneligiblePart':True}
    dist={p:distances(references[p],cells)for p in active}
    levels=np.unique(np.concatenate([x.ravel()for p in active for x in dist[p]]));totalNodes=0;calls=0
    def at(level,limit):
        nonlocal totalNodes,calls
        ds=[1|sum(1<<p for p in active if eligibility[i,p]and dist[p][1][i]<=level)for i in range(len(cells))]
        clauses=set()
        for p in active:
            for row in dist[p][0]:
                mask=sum(1<<i for i in range(len(cells))if ds[i]>>p&1 and row[i]<=level)
                if not mask:return [],{'nodes':0,'enumerationComplete':True}
                clauses.add((p,mask))
        # Subsumption is logical equivalence, not majority filtering.
        reduced=[(p,m)for p,m in clauses if not any(pp==p and mm!=m and mm&m==mm for pp,mm in clauses)]
        q,info=feasible(ds,reduced,cells,{p:d for p,d in connectivity.items()if p in active},limit);totalNodes+=info['nodes'];calls+=1
        return q,info
    lo=0;hi=len(levels)-1;winner=None
    if not at(float(levels[hi]),1)[0]:return {'status':'infeasible-carrier-or-topology','active':active,'seconds':time.perf_counter()-started}
    while lo<hi:
        mid=(lo+hi)//2;q,_=at(float(levels[mid]),1)
        if q:hi=mid
        else:lo=mid+1
    solutions,info=at(float(levels[lo]),witness_limit)
    assert solutions
    return {'status':'sampled-minimax-geometric-optima','errorPixels':float(levels[lo]),'previousThresholdInfeasible':float(levels[lo-1])if lo else None,
        'solutions':[list(v)for v in solutions],'uniqueCertified':len(solutions)==1 and info['enumerationComplete'],'enumerationComplete':info['enumerationComplete'],
        'witnesses':len(solutions),'solverCalls':calls,'nodes':totalNodes,'seconds':time.perf_counter()-started,'active':active,
        'countsAreOutputsNotConstraints':True,'policy':'equal per-feature geometric error, finite points/square corners; not author intent'}

def metrics(cells,labels,references):
    out={}
    for p,q in references.items():
        if not len(q):continue
        a,b=distances(q,cells);take=np.array(labels)==p
        out[str(p)]={'count':int(take.sum()),'sourceToSquares':float(a[:,take].min(1).max())if take.any()else None,
          'cornersToSource':float(b[take].max())if take.any()else None,'components4':component_count(take,cells,False),'components8':component_count(take,cells,True)}
    return out

def component_count(take,cells,diag):
    wanted={tuple(cells[i])for i in np.where(take)[0]};n=0
    while wanted:
        todo=[wanted.pop()];n+=1
        while todo:
            y,x=todo.pop()
            for q in list(wanted):
                if (max(abs(y-q[0]),abs(x-q[1]))==1 if diag else abs(y-q[0])+abs(x-q[1])==1):wanted.remove(q);todo.append(q)
    return n

def tests():
    # Exact complete enumeration oracle; not implementation-mirroring tests.
    cases=0;rng=np.random.default_rng(110)
    for n in range(1,7):
        cells=[(0,i)for i in range(n)]
        for _ in range(4):
            e=np.c_[np.ones(n,bool),rng.integers(0,2,(n,3)).astype(bool)];refs={p:np.array([[i+.5,.5]for i in range(n)if e[i,p]])for p in range(1,4)};refs={p:q for p,q in refs.items()if len(q)}
            q=solve(cells,e,refs,witness_limit=None);allv=list(itertools.product(*[[p for p in range(4)if e[i,p]]for i in range(n)]));costs=[]
            for labels in allv:
                mm=metrics(cells,labels,refs)
                costs.append(max((max(x['sourceToSquares'],x['cornersToSource'])if x['count']else math.inf for x in mm.values()),default=0))
            best=min(costs);expected={v for v,c in zip(allv,costs)if c==best}
            if not math.isfinite(best):assert q['status']=='infeasible-carrier-or-topology'
            elif refs:assert q['errorPixels']==best and set(map(tuple,q['solutions']))==expected
            cases+=1
    # An impossible carrier, and current blink/occlusion removing ALL source.
    e=np.array([[1,1,0,0]],bool);assert solve([(0,0)],e,{2:np.array([[.5,.5]])})['status']=='infeasible-carrier-or-topology'
    assert solve([(0,0)],e,{})['status']=='no-visible-reference'
    return {'independentExhaustiveCases':cases,'infeasibleCarrierRejected':True,'absentPartsCannotBeReanimated':True,'noRGBOrMassRounding':True}
