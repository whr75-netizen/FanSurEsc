"""Geometric active arcs, independent of control segmentation/parameter names.

No selector, weight, colour, temporal-state update or Unity operations here.
"""
import math,itertools
import numpy as np
import active516 as G

EPS=1e-9
def signed_area(p):return .5*sum(G.cross(a,b)for a,b in zip(p,p[1:]+p[:1]))
def simplify(p):
    p=[tuple(map(float,q))for q in p]
    while len(p)>3:
        keep=[]
        for i,b in enumerate(p):
            a,c=p[i-1],p[(i+1)%len(p)];v=G.sub(c,a);w=G.sub(b,a);length=math.hypot(*v)
            collinear=length>EPS and abs(G.cross(v,w))/length<=EPS and sum(x*y for x,y in zip(G.sub(b,a),G.sub(c,b)))>=-EPS
            if not collinear:keep.append(b)
        if len(keep)==len(p)or len(keep)<3:break
        p=keep
    at=min(range(len(p)),key=lambda i:p[i]);return p[at:]+p[:at]
def make_arc(p,lineage=None):
    p=simplify(p);v=np.array(p);b=np.roll(v,-1,axis=0);d=b-v;length=np.linalg.norm(d,axis=1);assert np.all(length>EPS)
    cumulative=np.r_[0,np.cumsum(length)];a=signed_area(p)
    return {'p':v,'b':b,'d':d,'length':length,'cum':cumulative,'total':float(cumulative[-1]),'area':a,'sign':1 if a>0 else-1,'depth':0,'lineage':set(lineage or[]),'visible':True}
def point(arc,u):
    u=float(u)%1.;at=u*arc['total'];i=min(len(arc['p'])-1,int(np.searchsorted(arc['cum'],at,side='right')-1));t=(at-arc['cum'][i])/arc['length'][i]
    return arc['p'][i]+t*arc['d'][i],arc['d'][i]/arc['length'][i]
def inside(q,arc):
    return G.winding(tuple(q),[{'a':tuple(a),'b':tuple(b)}for a,b in zip(arc['p'],arc['b'])])!=0
def depths(arcs):
    for a in arcs:
        q=(a['p'][0]+a['b'][0])*.5;t=a['d'][0]/a['length'][0];normal=np.array([-t[1],t[0]])*a['sign'];q=q+normal*1e-7
        a['depth']=sum(inside(q,b)for b in arcs if b is not a)
    return arcs
def active_arcs(fragments):
    key=lambda p:tuple(round(float(v),8)for v in p)
    outgoing={};incoming={};coords={}
    for i,e in enumerate(fragments):
        a,b=key(e['a']),key(e['b']);coords[a]=tuple(e['a']);coords[b]=tuple(e['b']);outgoing.setdefault(a,[]).append((i,b));incoming.setdefault(b,[]).append((i,a))
    junction={v for v in set(outgoing)|set(incoming)if len(outgoing.get(v,[]))!=1 or len(incoming.get(v,[]))!=1}
    unused=set(range(len(fragments)));arcs=[];reset=[]
    while unused:
        first=min(unused);start=key(fragments[first]['a']);at=start;p=[];lineage=[];seen=set()
        while at not in seen and at not in junction:
            seen.add(at);p.append(coords[at]);index,to=outgoing[at][0];unused.discard(index);e=fragments[index];lineage.extend((int(a),int(b))for a,b,_,_ in e.get('lineages',[[e['ring'],e['segment'],e['t0'],e['t1']]]));at=to
        if at==start and len(p)>=3:arcs.append(make_arc(p,lineage))
        else:
            # Explicit non-manifold/junction event; no guessed connection.
            reset.append({'reason':'JUNCTION_OR_OPEN_ACTIVE_ARC','vertices':len(p)})
            unused.discard(first)
    return depths(arcs),reset
def equal_geometry(a,b):
    return a['sign']==b['sign']and a['p'].shape==b['p'].shape and np.max(abs(a['p']-b['p']),initial=0)<=EPS
def evaluate(arc,u):
    uu=np.asarray(u)%1.;s=uu*arc['total'];i=np.searchsorted(arc['cum'],s,side='right')-1;i=np.clip(i,0,len(arc['p'])-1);t=(s-arc['cum'][i])/arc['length'][i]
    return arc['p'][i]+t[:,None]*arc['d'][i]
def fit_phase(a,b,j):
    phase=b['cum'][j]/b['total'];ka=a['cum']/a['total'];kb=(b['cum']/b['total']-phase)%1.;u=np.unique(np.r_[0,1,ka,kb]);h=np.diff(u)
    p0=evaluate(a,u[:-1]);p1=evaluate(a,u[1:]-1e-15);q0=evaluate(b,u[:-1]+phase);q1=evaluate(b,u[1:]+phase-1e-15)
    ca=np.sum(h[:,None]*(p0+p1)*.5,0);cb=np.sum(h[:,None]*(q0+q1)*.5,0)
    dot=lambda x,y:np.sum(x*y,axis=1)
    cross=lambda x,y:x[:,0]*y[:,1]-x[:,1]*y[:,0]
    ia=np.sum(h*(dot(p0,p0)+dot(p0,p1)+dot(p1,p1))/3)-np.dot(ca,ca)
    ib=np.sum(h*(dot(q0,q0)+dot(q0,q1)+dot(q1,q1))/3)-np.dot(cb,cb)
    d=np.sum(h*(2*dot(p0,q0)+dot(p0,q1)+dot(p1,q0)+2*dot(p1,q1))/6)-np.dot(ca,cb)
    c=np.sum(h*(2*cross(p0,q0)+cross(p0,q1)+cross(p1,q0)+2*cross(p1,q1))/6)-G.cross(ca,cb)
    angle=math.atan2(c,d);co,si=math.cos(angle),math.sin(angle);rotation=np.array([[co,-si],[si,co]]);translation=cb-rotation@ca
    score=max(0.,float(ia+ib-2*math.hypot(d,c)))
    return {'score':score,'R':rotation,'t':translation,'phase':float(phase),'angle':angle}
def fit(a,b):
    if equal_geometry(a,b):return {'score':0.,'R':np.eye(2),'t':np.zeros(2),'phase':0.,'angle':0.,'exactSameGeometry':True,'nearEqualFits':1}
    fits=[fit_phase(a,b,j)for j in range(len(b['p']))];best=min(v['score']for v in fits);close=[v for v in fits if v['score']<=best+1e-8]
    # Equivalent geometric symmetries choose the least global rotation; all tie
    # counts remain explicit. No source control-ID or array-index identity.
    answer=min(close,key=lambda v:(abs(v['angle']),float(np.linalg.norm(v['t'])),v['phase']));return {**answer,'exactSameGeometry':False,'nearEqualFits':len(close)}
def centre(a):return np.sum((a['p']+a['b'])*a['length'][:,None]*.5,axis=0)/a['total']
def match_arcs(old,new):
    matches=[];resets=[]
    oldVisible=[i for i,a in enumerate(old)if a.get('visible',True)];newVisible=[i for i,a in enumerate(new)if a.get('visible',True)]
    if len(oldVisible)!=len(old)or len(newVisible)!=len(new):resets.append({'reason':'EXPLICIT_VISIBILITY_EVENT','oldHidden':len(old)-len(oldVisible),'newHidden':len(new)-len(newVisible)})
    positiveOld=[i for i in oldVisible if old[i]['sign']>0];positiveNew=[j for j in newVisible if new[j]['sign']>0]
    globalFit=fit(old[max(positiveOld,key=lambda i:abs(old[i]['area']))],new[max(positiveNew,key=lambda j:abs(new[j]['area']))])if positiveOld and positiveNew else{'R':np.eye(2),'t':np.zeros(2)}
    kinds=sorted({(a['sign'],a['depth'])for a in old+new})
    for kind in kinds:
        oo=[i for i in oldVisible if(old[i]['sign'],old[i]['depth'])==kind];nn=[j for j in newVisible if(new[j]['sign'],new[j]['depth'])==kind]
        if len(oo)!=len(nn):resets.append({'reason':'GEOMETRIC_COMPONENT_SPLIT_MERGE_OR_BIRTH_DEATH','kind':kind,'old':oo,'new':nn});continue
        if not oo:continue
        pairs={(i,j):fit(old[i],new[j])for i in oo for j in nn};options=[]
        for permutation in itertools.permutations(nn):
            value=0.
            for i,j in zip(oo,permutation):
                motion=centre(new[j])-(globalFit['R']@centre(old[i])+globalFit['t']);value+=pairs[i,j]['score']+float(np.dot(motion,motion))
            options.append((value,permutation))
        options.sort();best=options[0]
        if len(options)>1 and abs(options[1][0]-best[0])<=1e-9:resets.append({'reason':'AMBIGUOUS_GEOMETRIC_ARC_ASSIGNMENT','kind':kind});continue
        matches.extend({'old':i,'new':j,'fit':pairs[i,j]}for i,j in zip(oo,best[1]))
    return matches,resets

def projections(points,arc,directions=None,phase=0.,corridor=False):
    p=np.asarray(points,float);a=arc['p'];d=arc['d'];ll=arc['length']**2;t=np.clip(((p[:,None]-a)*d).sum(2)/ll,0,1);q=a+t[:,:,None]*d
    score=((p[:,None]-q)**2).sum(2);valid=np.ones(score.shape,bool)
    if directions is not None:
        direction=np.asarray(directions,float);valid&=(direction[:,None,:]*d).sum(2)>=-EPS
        if corridor:
            ends=np.array([p-direction*.5,p+direction*.5]);tt=np.clip(((ends[:,:,None,:]-a)*d).sum(3)/ll,0,1);qq=a+tt[:,:,:,None]*d;dist=((ends[:,:,None,:]-qq)**2).sum(3);score=dist.mean(0);valid&=dist.max(0)<=2+EPS
    u=(arc['cum'][:-1]+t*arc['length'])/arc['total'];u=(u-phase)%1.
    n,m=score.shape;order=np.argsort(u,axis=1);cost=np.full((n,m),np.inf);back=np.full((n,m),-1,int)
    cost[0]=np.where(valid[0],score[0],np.inf)
    for i in range(1,n):
        prev=order[i-1];cur=order[i];at=0;best=np.inf;bestId=-1
        for j in cur:
            while at<m and u[i-1,prev[at]]<=u[i,j]+1e-12:
                k=prev[at]
                if cost[i-1,k]<best:best=cost[i-1,k];bestId=k
                at+=1
            if valid[i,j]and bestId>=0:cost[i,j]=score[i,j]+best;back[i,j]=bestId
    j=int(np.argmin(cost[-1]));total=float(cost[-1,j])
    if not math.isfinite(total):return None
    chosen=[j]
    for i in range(n-1,0,-1):j=int(back[i,j]);chosen.append(j)
    chosen=chosen[::-1];rows=np.arange(n);chosen=np.array(chosen);unwrapped=u[rows,chosen]
    if np.any(np.diff(unwrapped)<-1e-10):raise AssertionError('Projection order reversed')
    tangents=d[chosen]/arc['length'][chosen,None]
    return {'q':q[rows,chosen],'u':(unwrapped+phase)%1.,'tangent':tangents,'score':total,'maxFit':float(np.sqrt(score[rows,chosen].max(initial=0))),'segments':chosen,'unwrapped':unwrapped}

def pixel_loops(mask):
    edges={tuple(e['a'])+tuple(e['b'])for e in G.boundary(mask)};outgoing={}
    for e in edges:outgoing.setdefault(e[:2],[]).append(e)
    dr=lambda e:{(1,0):0,(0,1):1,(-1,0):2,(0,-1):3}[(e[2]-e[0],e[3]-e[1])]
    out=[]
    while edges:
        first=min(edges);at=first;chain=[]
        while True:
            edges.remove(at);chain.append(at)
            if at[2:]==first[:2]:break
            choices=[e for e in outgoing[at[2:]]if e in edges];assert choices
            priority={1:4,0:3,3:2,2:1};at=max(choices,key=lambda e:(priority[(dr(e)-dr(at))%4],e))
        pts=[tuple(e[:2])for e in chain];out.append({'edges':chain,'sign':1 if signed_area(pts)>0 else-1,'area':signed_area(pts)})
    return out
def bind_loop(loop,arc):
    es=loop['edges'];points=np.array([[(e[0]+e[2])*.5,(e[1]+e[3])*.5]for e in es]);dirs=np.array([[e[2]-e[0],e[3]-e[1]]for e in es]);n=len(es)
    # Geometric anchor: closest pixel edge to the canonical curve start, not a
    # control vertex label. All exact tied candidates are evaluated by order DP.
    distances=((points-arc['p'][0])**2).sum(1);minimum=distances.min();starts=np.where(distances<=minimum+1e-9)[0];best=None
    for start in starts:
        index=np.roll(np.arange(n),-int(start));p=projections(points[index],arc,dirs[index],corridor=True)
        if p is not None and(best is None or p['score']<best['projection']['score']-1e-10):best={'indices':index,'projection':p}
    if best is None:return None
    index=best['indices'];p=best['projection'];samples=[]
    for k,i in enumerate(index):samples.append({'q':points[i].tolist(),'direction':dirs[i].tolist(),'reference':p['q'][k].tolist(),'tangent':p['tangent'][k].tolist(),'u':float(p['u'][k]),'edge':es[int(i)]})
    spans=[];run=[]
    for s in samples:
        if run and s['direction']!=run[-1]['direction']:spans.append({'samples':run,'length':len(run)});run=[]
        run.append(s)
    if run:spans.append({'samples':run,'length':len(run)})
    if len(spans)>1 and spans[0]['samples'][0]['direction']==spans[-1]['samples'][0]['direction']:
        first=spans.pop(0);spans[-1]['samples']+=first['samples'];spans[-1]['length']+=first['length']
    return {'spans':spans,'samples':samples,'fit':p['score'],'maxFit':p['maxFit'],'monotone':True}
def bind_full_cycle(mask,arcs):
    assigned={};unsupported=[]
    for loop in pixel_loops(mask):
        candidates=[]
        for i,a in enumerate(arcs):
            if a['sign']!=loop['sign']or not a.get('visible',True):continue
            value=bind_loop(loop,a)
            if value is not None:candidates.append((value['fit'],i,value))
        candidates.sort(key=lambda v:(v[0],v[1]))
        if not candidates:unsupported.append({'reason':'NO_ORDERED_ACTIVE_ARC_FOR_PIXEL_LOOP','area':loop['area']});continue
        score,i,value=candidates[0]
        if i in assigned:unsupported.append({'reason':'MULTIPLE_PIXEL_LOOPS_SHARE_ACTIVE_ARC','arc':i});continue
        assigned[i]=value
    return assigned,unsupported

def segment_cell(a,b,cell):
    lo,hi=0.,1.;v=b-a
    for axis in [0,1]:
        left,right=cell[axis],cell[axis]+1
        if abs(v[axis])<1e-20:
            if a[axis]<left-EPS or a[axis]>right+EPS:return False
        else:
            x,y=(left-a[axis])/v[axis],(right-a[axis])/v[axis];lo=max(lo,min(x,y));hi=min(hi,max(x,y))
            if lo>hi+EPS:return False
    return True

def bind(mask,arcs):
    """Directed span/arc relation with explicit within-cell quantization joins.

    A quantized region may connect an outer source arc with a source hole, or
    close a subpixel neck. Never force a whole pixel loop to one source cycle.
    Every reference join is either geometric continuation or has a common
    logical-cell intersection witness; it is not called physical occlusion.
    """
    assigned={};unsupported=[];cellCache={}
    def candidates(edge):
        p=np.array([(edge[0]+edge[2])*.5,(edge[1]+edge[3])*.5]);direction=np.array([edge[2]-edge[0],edge[3]-edge[1]]);out=[]
        for ai,arc in enumerate(arcs):
            if not arc.get('visible',True):continue
            a,d,ll=arc['p'],arc['d'],arc['length']**2;ends=np.array([p-direction*.5,p+direction*.5]);t=np.clip(((ends[:,None]-a)*d).sum(2)/ll,0,1);q=a+t[:,:,None]*d;dist=((ends[:,None]-q)**2).sum(2)
            ok=(dist.max(0)<=2+EPS)&((direction*d).sum(1)>=-EPS);tm=np.clip(((p-a)*d).sum(1)/ll,0,1)
            for si in np.where(ok)[0]:
                ref=a[si]+tm[si]*d[si];u=(arc['cum'][si]+tm[si]*arc['length'][si])/arc['total']
                out.append({'arc':ai,'segment':int(si),'q':p.tolist(),'direction':direction.tolist(),'edge':tuple(edge),'reference':ref.tolist(),'tangent':(d[si]/arc['length'][si]).tolist(),'u':float(u%1.),'t':float(tm[si]),'fit':float(dist[:,si].mean())})
        return out
    def cells(state,vertex):
        key=(state['arc'],state['segment'],vertex)
        if key not in cellCache:
            x,y=vertex;arc=arcs[state['arc']];s=state['segment'];cellCache[key]={c for c in [(x-1,y-1),(x,y-1),(x-1,y),(x,y)]if segment_cell(arc['p'][s],arc['b'][s],c)}
        return cellCache[key]
    def link(a,b,vertex):
        if a['arc']==b['arc']:
            arc=arcs[a['arc']];sa,sb=a['segment'],b['segment']
            if sa==sb and b['t']>=a['t']-1e-10:return ('CONTINUOUS_ARC',[])
            if sb==(sa+1)%len(arc['p']):
                node=arc['b'][sa]
                if abs(node[0]-vertex[0])<=1+EPS and abs(node[1]-vertex[1])<=1+EPS:return ('CONTINUOUS_ARC_CORNER',[])
        witness=cells(a,vertex)&cells(b,vertex)
        if witness:return ('QUANTIZED_REGION_JOIN',sorted(witness))
        return None
    def better(score,aliases,best):return best is None or score<best[0]-1e-10 or abs(score-best[0])<=1e-10 and aliases<best[1]
    for li,loop in enumerate(pixel_loops(mask)):
        edges=loop['edges'];states=[candidates(e)for e in edges]
        if any(not s for s in states):unsupported.append({'reason':'NO_GEOMETRIC_UNIT_EDGE_CANDIDATE','pixelLoop':li});continue
        links={}
        def connection(i,a,b):
            key=(i,a,b)
            if key not in links:links[key]=link(states[i-1][a],states[i][b],tuple(edges[i][:2]))
            return links[key]
        best=None
        for first in range(len(states[0])):
            costs={first:(states[0][first]['fit'],0)};backs=[]
            for i in range(1,len(states)):
                current={};back={}
                for b,s in enumerate(states[i]):
                    value=None;winner=None
                    for a,(cost,count)in costs.items():
                        con=connection(i,a,b)
                        if con is None:continue
                        score=cost+s['fit'];aliases=count+(con[0]=='QUANTIZED_REGION_JOIN')
                        if better(score,aliases,value):value=(score,aliases);winner=a
                    if value is not None:current[b]=value;back[b]=winner
                costs=current;backs.append(back)
                if not costs:break
            if len(backs)!=len(states)-1 or not costs:continue
            for last,(cost,count)in costs.items():
                close=link(states[-1][last],states[0][first],tuple(edges[0][:2]))
                if close is None:continue
                count+=close[0]=='QUANTIZED_REGION_JOIN'
                if better(cost,count,None if best is None else best[:2]):
                    path=[last];at=last
                    for i in range(len(backs)-1,-1,-1):at=backs[i][at];path.append(at)
                    path=path[::-1];best=(cost,count,path)
        if best is None:unsupported.append({'reason':'NO_CONNECTED_GEOMETRIC_SPAN_PATH','pixelLoop':li});continue
        chosen=[states[i][k]for i,k in enumerate(best[2])];runs=[];run=[];joins=[]
        for i,s in enumerate(chosen):
            con=link(chosen[i-1],s,tuple(edges[i][:2]));assert con is not None
            s={**s,'pixelLoop':li,'connectionFromPrevious':con[0],'joinCellWitness':con[1]}
            if con[0]=='QUANTIZED_REGION_JOIN':joins.append({'atPixelVertex':edges[i][:2],'fromArc':chosen[i-1]['arc'],'toArc':s['arc'],'source':con[0],'cells':con[1]})
            if run and(s['arc']!=run[-1]['arc']or s['direction']!=run[-1]['direction']or con[0]=='QUANTIZED_REGION_JOIN'):
                runs.append(run);run=[]
            run.append(s)
        if run:runs.append(run)
        if len(runs)>1 and runs[0][0]['arc']==runs[-1][0]['arc']and runs[0][0]['direction']==runs[-1][0]['direction']and runs[0][0]['connectionFromPrevious']!='QUANTIZED_REGION_JOIN':runs[-1]+=runs.pop(0)
        for run in runs:
            ai=run[0]['arc'];value=assigned.setdefault(ai,{'spans':[],'samples':[],'fit':0.,'maxFit':0.,'monotone':True,'quantizedJoins':[]})
            value['spans'].append({'samples':run,'length':len(run)});value['samples']+=run;value['fit']+=sum(s['fit']for s in run);value['maxFit']=max(value['maxFit'],max(math.sqrt(s['fit'])for s in run))
        for ai in {s['arc']for s in chosen}:assigned[ai]['quantizedJoins']+=joins
    for value in assigned.values():value['spans'].sort(key=lambda s:(s['samples'][0]['u'],s['samples'][0]['edge']))
    return assigned,unsupported

def transport(binding,oldArc,newArc,fit):
    samples=[s for span in binding['spans']for s in span['samples']]
    # Reorder to geometric arc parameter before applying a monotone curve map.
    order=sorted(range(len(samples)),key=lambda i:samples[i]['u']);oldRef=np.array([samples[i]['reference']for i in order]);oldTan=np.array([samples[i]['tangent']for i in order])
    if fit['exactSameGeometry']:
        mapped=oldRef;newTan=oldTan;score=0.
    else:
        transformed=oldRef@fit['R'].T+fit['t'];direction=oldTan@fit['R'].T
        p=projections(transformed,newArc,direction,phase=fit['phase'],corridor=False)
        if p is None:return None
        mapped=p['q'];newTan=p['tangent'];score=p['score']
    predicted=[None]*len(samples)
    for at,index in enumerate(order):
        s=samples[index];a=np.array(s['tangent']);b=newTan[at];co=float(np.dot(a,b));si=G.cross(a,b);v=np.array(s['q'])-s['reference'];r=np.array([co*v[0]-si*v[1],si*v[0]+co*v[1]])
        predicted[index]=(mapped[at]+r).tolist()
    out=[];offset=0
    for span in binding['spans']:
        out.append({'length':span['length'],'points':predicted[offset:offset+span['length']]});offset+=span['length']
    return {'spans':out,'curveMapFit':float(score),'maxPredictedMovement':max((math.dist(s['q'],q)for s,q in zip(samples,predicted)),default=0.)}
