"""Finite, source-supported JOINT allocation. Pure offline, no RGB modification.

Two explicit lexicographic hypotheses are compared, NOT a tuned weighted sum:
 M: minimise whole-region L1 mass error, then source reconstruction error.
 D: minimise source reconstruction error, subject to the same hard constraints.
No hypothesis is silently selected as the artistic answer.

Curve policy: reachability between the two existing registered upper-arc end
cells, ONLY if both have certain visible pigment support. This reference is a
skin-ring arc, not an authored pigment contour. Testing it does not validate it.
All simple paths are enumerated; equal vertex sets are deduplicated because
fixed cells impose the same allocation constraint. Additional lid components
are allowed: source samples do not establish that all marks form one component.
"""
from pathlib import Path
import itertools,heapq,math,json,time
import numpy as np

EPS=1e-10 # numerical comparison only, not colour/shape tolerance

def neighbours(points,diagonal=False):
    lookup={p:i for i,p in enumerate(points)};result=[]
    shifts=[(-1,0),(1,0),(0,-1),(0,1)]
    if diagonal:shifts += [(-1,-1),(-1,1),(1,-1),(1,1)]
    for y,x in points:result.append([lookup[(y+dy,x+dx)]for dy,dx in shifts if(y+dy,x+dx)in lookup])
    return result

def path_sets(points,eligible,start,end,diagonal=False):
    """Exact simple-path vertex sets, no heuristic truncation."""
    if start not in points or end not in points:return []
    a=points.index(start);b=points.index(end)
    if not eligible[a]or not eligible[b]:return []
    g=neighbours(points,diagonal);sets=set()
    def visit(i,mask):
        if i==b:sets.add(mask);return
        for j in g[i]:
            if eligible[j]and not(mask>>j&1):visit(j,mask|1<<j)
    visit(a,1<<a)
    return sorted(sets,key=lambda x:(x.bit_count(),x))

def count_error(counts,lo,hi):
    return sum(max(0,l-n,n-h)for n,l,h in zip(counts,lo,hi))

def mincost_fixed(domains,mass,counts,fixed,unit=1):
    """Exact integral capacitated assignment via successive shortest paths.
    Source -> part -> cell -> sink. Negative costs use Bellman-Ford; residual
    edges permit JOINT reassignment, never sequential iris/lid protection.
    A fixed path consumes its real cells and its quota before the flow solve.
    """
    n=len(domains);assignment=[-1]*n;remaining=list(counts)
    for i in range(n):
        if fixed>>i&1:
            if 3 not in domains[i]:return None
            assignment[i]=3;remaining[2]-=1
    if min(remaining,default=0)<0:return None
    free=[i for i in range(n)if assignment[i]<0]
    if sum(remaining)>len(free):return None
    nodes=1+3+len(free)+1;s=0;t=nodes-1;g=[[]for _ in range(nodes)];arcs=[]
    def edge(u,v,cap,cost):
        g[u].append([v,len(g[v]),cap,cost]);g[v].append([u,len(g[u])-1,0,-cost]);return g[u][-1]
    for p in range(1,4):edge(s,p,remaining[p-1],0)
    for j,i in enumerate(free):
        v=4+j;edge(v,t,1,0)
        for p in domains[i]:
            if p:arcs.append((i,p,edge(p,v,1,mass[i,0]-mass[i,p])))
    for _ in range(sum(remaining)):
        dist=[math.inf]*nodes;dist[s]=0;prev=[None]*nodes
        for _ in range(nodes-1):
            changed=False
            for u,es in enumerate(g):
                if not math.isfinite(dist[u]):continue
                for j,e in enumerate(es):
                    v,rev,cap,cost=e
                    if cap and dist[u]+cost<dist[v]:dist[v]=dist[u]+cost;prev[v]=(u,j);changed=True
            if not changed:break
        if prev[t]is None:return None
        v=t
        while v!=s:
            u,j=prev[v];e=g[u][j];e[2]-=1;g[v][e[1]][2]+=1;v=u
    def decode():
        out=[3 if fixed>>i&1 else 0 for i in range(n)]
        for i,p,e in arcs:
            if e[2]==0:out[i]=p
        return out
    assignment=decode()
    assert tuple(assignment.count(p)for p in range(1,4))==tuple(counts)
    # All actual solves use exact integer costs derived from the observed
    # binary float inputs. A zero-reduced-cost residual cycle certifies a
    # second optimal assignment. Absence certifies fixed-quota uniqueness.
    second=None;certified=np.asarray(mass).dtype==object
    if certified:
        potential=[0]*nodes
        for _ in range(nodes-1):
            changed=False
            for u,es in enumerate(g):
                for v,rev,cap,cost in es:
                    if cap and potential[u]+cost<potential[v]:potential[v]=potential[u]+cost;changed=True
            if not changed:break
        zero=[[(j,e[0])for j,e in enumerate(es)if e[2]and e[3]+potential[u]-potential[e[0]]==0]for u,es in enumerate(g)]
        state=[0]*nodes;parent={};cycle=None
        def dfs(u):
            nonlocal cycle
            state[u]=1
            for j,v in zero[u]:
                if state[v]==0:
                    parent[v]=(u,j)
                    if dfs(v):return True
                elif state[v]==1:
                    cycle=[(u,j)];q=u
                    while q!=v:uu,jj=parent[q];cycle.append((uu,jj));q=uu
                    return True
            state[u]=2;return False
        for u in range(nodes):
            if state[u]==0 and dfs(u):break
        if cycle:
            for u,j in cycle:e=g[u][j];e[2]-=1;g[e[0]][e[1]][2]+=1
            second=decode();assert second!=assignment
            assert sum(unit-mass[i,p]for i,p in enumerate(second))==sum(unit-mass[i,p]for i,p in enumerate(assignment))
    return {'labels':assignment,'data':sum(unit-mass[i,p]for i,p in enumerate(assignment)), 'second':second,'fixedQuotaUniquenessCertified':certified}

def data_best(domains,mass,fixed,required,unit=1):
    """Exact DP with part-presence mask; count all minimum-data assignments.
    Keeps two witnesses for ties. It does not claim the whole Pareto frontier.
    """
    dp={0:(0,1,(),None)}
    for i,domain in enumerate(domains):
        new={};choices=[3]if fixed>>i&1 else domain
        for mask,(cost,count,path,second)in dp.items():
            for p in choices:
                m=mask|(1<<(p-1)if p else 0);v=cost+unit-mass[i,p];q=path+(p,);old=new.get(m)
                if old is None or v<old[0]:new[m]=(v,count,q,second+(p,)if second else None)
                elif v==old[0]:
                    # Any two witnesses suffice to prove nonuniqueness; count
                    # includes every DP assignment, not just retained witnesses.
                    new[m]=(old[0],old[1]+count,old[2],old[3]or(q if q!=old[2]else second+(p,)if second else None))
        dp=new
    best=None
    for mask,v in dp.items():
        if mask&required!=required:continue
        if best is None or v[0]<best[0]:best=v
        elif v[0]==best[0]:best=(best[0],best[1]+v[1],best[2],best[3]or(v[2]if v[2]!=best[2]else v[3]))
    if best is None:return None
    return {'data':best[0],'labels':list(best[2]),'fixedPathTieCount':best[1],'second':list(best[3])if best[3]else None}

def problem(d,owner,curve,diagonal=False,carrier=False):
    ids=[0]+[i for i,k in enumerate(d['keys'])if k[0]==owner];s=d['support'][ids];mass=d['lower'][ids]
    pts=[tuple(map(int,p))for p in np.argwhere(s[1:].any(0))]
    domains=[[p for p in range(4)if s[p,y,x]]for y,x in pts]
    if carrier:
        # A mathematical relaxation, NOT render-valid eligibility. It isolates
        # same-cell locking from whole-feature relocation. Destination-depth/
        # occlusion and a source-witness transport map are not supplied here.
        active=[0]+[p for p in range(1,4)if s[p].any()]
        domains=[active.copy()for _ in pts]
    values=np.array([[mass[p,y,x]for p in range(4)]for y,x in pts])
    low=d['lower'][ids[1:]].sum((1,2));high=d['upper'][ids[1:]].sum((1,2))
    required=sum(1<<(p-1)for p in range(1,4)if s[p].any())
    seg=d['sourceSegments'][d['sourceSegments'][:,0,3]==owner]
    endpoints=[tuple(map(int,np.floor(q).astype(int)[::-1]))for q in [seg[0,0,:2],seg[-1,1,:2]]]if len(seg)else[]
    paths=path_sets(pts,[3 in x for x in domains],*endpoints,diagonal)if curve and len(endpoints)==2 else[0]
    return {'points':pts,'domains':domains,'values':values,'low':low,'high':high,'lowField':d['lower'][ids[1:]],'highField':d['upper'][ids[1:]],'required':required,'paths':paths,'endpoints':endpoints}

def solve(d,owner,curve=False,diagonal=False,carrier=False):
    started=time.perf_counter();p=problem(d,owner,curve,diagonal,carrier);pts,domains,mass=p['points'],p['domains'],p['values'];paths=p['paths']
    if not pts:return {'status':'no-visible-pigment','points':[],'labels':[],'mass':0.,'data':0.,'seconds':time.perf_counter()-started}
    base={'points':pts,'sourceMassLower':p['low'].tolist(),'sourceMassUpper':p['high'].tolist(),'endpoints':p['endpoints'],
          'pathSets':len(paths),'minimumLidPathCells':min((x.bit_count()for x in paths),default=None),'curveReference':'registered skin-ring upper arc; pigment-contour agreement NOT established',
          'sameCellSupportHard':not carrier,'relaxedCarrierIsRenderValid':False if carrier else None}
    if not paths:return base|{'status':'infeasible-curve-support','seconds':time.perf_counter()-started}
    # Preserve exact dyadic values of the frozen numeric inputs. Integer costs
    # remove scan-order/epsilon-dependent ties without choosing a visual style.
    values=list(mass.flat)+list(p['lowField'].flat)+list(p['highField'].flat);unit=max(float(v).as_integer_ratio()[1]for v in values)
    def units(v):a,b=float(v).as_integer_ratio();return a*(unit//b)
    mass=np.array([[units(v)for v in line]for line in mass],dtype=object)
    low=[sum(units(v)for v in field.flat)for field in p['lowField']];high=[sum(units(v)for v in field.flat)for field in p['highField']]
    base['sourceMassLower']=[v/unit for v in low];base['sourceMassUpper']=[v/unit for v in high]
    nmax=[sum(k in domain for domain in domains)for k in range(1,4)]
    combinations=[]
    for counts in itertools.product(*[range(1 if p['required']>>(k-1)&1 else 0,nmax[k-1]+1)for k in range(1,4)]):
        if sum(counts)<=len(pts):combinations.append((count_error([n*unit for n in counts],low,high),counts))
    combinations.sort();best=None;ties=[];tested=0
    for error,counts in combinations:
        if best is not None and error>best['mass']:break
        for path in paths:
            if path.bit_count()>counts[2]:continue
            tested+=1;q=mincost_fixed(domains,mass,counts,path,unit)
            if q is None:continue
            q|={'mass':error,'counts':counts,'pathMask':path}
            candidates=[q['labels']]+([q['second']]if q['second']else[])
            if best is None or error<best['mass']or(error==best['mass']and q['data']<best['data']):best=q;ties=candidates
            elif q['data']==best['data']:
                for x in candidates:
                    if x not in ties:ties.append(x)
    dbest=None;dties=[]
    for path in paths:
        q=data_best(domains,mass,path,p['required'],unit)
        if q is None:continue
        q['mass']=count_error([q['labels'].count(k)*unit for k in range(1,4)],low,high)
        if dbest is None or q['data']<dbest['data']:dbest=q;dties=[q['labels']]+([q['second']]if q['second']else[])
        elif q['data']==dbest['data']:
            for x in [q['labels'],q['second']]:
                if x and x not in dties:dties.append(x)
    if best is None:return base|{'status':'infeasible-presence-and-curve','seconds':time.perf_counter()-started}
    for q in [best,dbest]:
        q['dataExactUnits']=int(q['data']);q['massExactUnits']=int(q['mass']);q['data']/=unit;q['mass']/=unit
    return base|{'status':'exact-optima-under-stated-policy','massFirst':best,'dataFirst':dbest,'massFirstDistinctWitnesses':ties,
       'dataFirstDistinctWitnesses':dties,'massFirstIsUnique':len(ties)==1,'dataFirstIsUnique':len(dties)==1,'exactCostUnitDenominator':unit,
       'equivalentWitnessCountsAreLowerBounds':True,'completeParetoFrontier':False,'flowSubproblems':tested,'seconds':time.perf_counter()-started}

def tests():
    # Exhaustive independent oracle for tiny joint assignment, all count quotas.
    rng=np.random.default_rng(108);checks=0
    for n in range(1,7):
        for case in range(4):
            domains=[[0]+[p for p in range(1,4)if rng.integers(2)]for _ in range(n)];mass=rng.random((n,4));mass/=mass.sum(1)[:,None]
            fixed=next((1<<i for i,x in enumerate(domains)if 3 in x),0)if case%2 else 0
            allq=[x for x in itertools.product(*domains)if all(x[i]==3 for i in range(n)if fixed>>i&1)]
            quotas={tuple(x.count(k)for k in range(1,4))for x in allq}
            for counts in quotas:
                q=mincost_fixed(domains,mass,counts,fixed);ref=min(sum(1-mass[i,p]for i,p in enumerate(x))for x in allq if tuple(x.count(k)for k in range(1,4))==counts)
                assert q and abs(q['data']-ref)<EPS;checks+=1
            for required in range(8):
                q=data_best(domains,mass,fixed,required);feasible=[x for x in allq if all(k in x for k in range(1,4)if required>>(k-1)&1)]
                assert (q is None)==(not feasible)
                if feasible:assert abs(q['data']-min(sum(1-mass[i,p]for i,p in enumerate(x))for x in feasible))<EPS
                checks+=1
    # L corner connects by 4-neighbours, diagonals do not; 8-neighbour variant
    # explicitly differs. Reflections/rotations preserve path-set cardinality.
    for diag in [False,True]:
        points=[(0,0),(1,0),(1,1)];a=path_sets(points,[1,1,1],points[0],points[-1],diag)
        for f in [lambda y,x:(x,-y),lambda y,x:(-y,x),lambda y,x:(y,-x)]:
            q=[f(*x)for x in points];assert len(path_sets(q,[1,1,1],q[0],q[-1],diag))==len(a);checks+=1
    assert not path_sets([(0,0),(1,1)],[1,1],(0,0),(1,1),False)
    assert path_sets([(0,0),(1,1)],[1,1],(0,0),(1,1),True)
    # Exact integer ties: compare cost, count feasibility and uniqueness with
    # independent exhaustive enumeration, including canvas reassignment cycles.
    exactChecks=0
    for n in range(1,7):
        for case in range(3):
            domains=[[0]+[p for p in range(1,4)if rng.integers(2)]for _ in range(n)]
            mass=np.array(rng.integers(0,5,(n,4)),dtype=object);unit=16
            allq=list(itertools.product(*domains));quotas={tuple(x.count(k)for k in range(1,4))for x in allq}
            for counts in quotas:
                feasible=[x for x in allq if tuple(x.count(k)for k in range(1,4))==counts]
                costs=[sum(unit-mass[i,p]for i,p in enumerate(x))for x in feasible];opt=min(costs)
                best=[x for x,v in zip(feasible,costs)if v==opt];q=mincost_fixed(domains,mass,counts,0,unit)
                assert q['data']==opt and(q['second']is None)==(len(best)==1);exactChecks+=1
            q=data_best(domains,mass,0,0,unit);costs=[sum(unit-mass[i,p]for i,p in enumerate(x))for x in allq];opt=min(costs)
            assert q['data']==opt and q['fixedPathTieCount']==costs.count(opt);exactChecks+=1
    # A single source cell containing 30/27/2/5 samples cannot display three
    # labels while also satisfying one-label-per-cell and part nonvanishing.
    mass=np.array([[5,30,27,2]],dtype=object)
    assert data_best([[0,1,2,3]],mass,0,7,64)is None
    # Keeping a 4-cell thin path and a separate iris is feasible, but source
    # mass .4 cannot also be matched within its natural ceil(.4)=1 cell budget.
    points=[(0,i)for i in range(4)]+[(1,1)]
    paths=path_sets(points,[1,1,1,1,0],points[0],points[3]);assert paths and min(x.bit_count()for x in paths)==4
    return {'independentExhaustiveChecks':checks,'exactIntegerCostAndUniquenessChecks':exactChecks,'singleCellThreePartConflict':True,
      'thinPathMassConflict':True,'noUnity':True,'noRGBMath':True}

if __name__=='__main__':print(json.dumps(tests()))
