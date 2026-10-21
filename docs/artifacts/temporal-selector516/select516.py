"""Offline single-selector prototype. Current cut is an initial proposal only.

One objective: unchanged area/Potts perimeter + eta*.14 * motion-conditioned
span edit. No downstream mask filter or RGB history. Novel packet support is
reported as unverified; it cannot pass the runtime gate by geometry alone.
"""
from pathlib import Path
import json,struct,math,time,collections,sys,hashlib
import numpy as np
import active516 as G,span516 as S
from context516 import signature,previous_for

OUT=G.OUTPUT; IN=G.INPUT
MODEL=Path('C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets/EUnityValidation01/HeadRegion502/Resources/HeadCurve511.bytes')
MODEL_SIGNATURE=hashlib.sha256(MODEL.read_bytes()).hexdigest()
WEIGHTS=[(1,0,float(np.float32(.14)*np.float32(.58578644))),(0,1,float(np.float32(.14)*np.float32(.58578644))),(1,1,float(np.float32(.14)*np.float32(.29289322))),(-1,1,float(np.float32(.14)*np.float32(.29289322)))]
N8=[(dx,dy,w)for dx,dy,w in WEIGHTS]+[(-dx,-dy,w)for dx,dy,w in WEIGHTS]
def key(e):return tuple(e['a'])+tuple(e['b'])
def channel(e):return(e['ring'],e['segment'])
def inside_edge(k):
    x,y,u,v=k;dx,dy=u-x,v-y
    return[int(math.floor((x+u-dy)*.5)),int(math.floor((y+v+dx)*.5))]
def cell_edges(x,y):return[(x,y,x+1,y),(x+1,y,x+1,y+1),(x+1,y+1,x,y+1),(x,y+1,x,y)]
def reverse(k):return(k[2],k[3],k[0],k[1])
def areas(i):
    b=(IN/f'{i:03d}_areas.bin').read_bytes();x,y,w,h=struct.unpack_from('<4i',b);a=np.frombuffer(b,'<f4',offset=16).reshape(h,w).copy();return(x,y,w,h),a
def spatial(mask,a,bounds):
    x,y,w,h=bounds;m=mask[y:y+h,x:x+w];fill=np.float32(1)-a
    unary=float(np.where(m,fill,a).sum(dtype=np.float64));per=0.
    for dx,dy,weight in WEIGHTS:
        if dx>=0:p,q=m[:h-dy,:w-dx],m[dy:,dx:]
        else:p,q=m[:h-dy,-dx:],m[dy:,:w+dx]
        per+=int((p!=q).sum())*weight
    return {'area':unary,'perimeter':per,'total':unary+per}
def delta_spatial(mask,a,bounds,x,y):
    bx,by,w,h=bounds;old=bool(mask[y,x]);aa=float(a[y-by,x-bx]);fill=float(np.float32(1)-np.float32(aa));delta=aa-fill if old else fill-aa
    for dx,dy,weight in N8:
        other=bool(mask[y+dy,x+dx]);delta+=weight*((not old)!=other)-weight*(old!=other)
    return delta
def groups(desc):
    spans,invalid=G.spans(list(desc.values()));assert not invalid
    d={}
    for s in spans:d.setdefault(channel(s),[]).append(s)
    return d

def loop_quality(mask):
    es={key(e)for e in G.boundary(mask)};adj={}
    for e in es:adj.setdefault(e[:2],[]).append(e)
    loops=[]
    def dr(e):
        d=(e[2]-e[0],e[3]-e[1]);return{(1,0):0,(0,1):1,(-1,0):2,(0,-1):3}[d]
    while es:
        first=min(es);at=first;points=[]
        while True:
            if at not in es:raise AssertionError('Open boundary')
            es.remove(at);points.append(at);end=at[2:]
            if end==first[:2]:break
            candidates=[e for e in adj[end]if e in es];assert candidates
            scores={1:4,0:3,3:2,2:1};at=max(candidates,key=lambda e:(scores[(dr(e)-dr(at))%4],e))
        loops.append(points)
    nonmono=0;runCount=0;extrema=0
    for edges in loops:
        runs=[]
        for e in edges:
            d=dr(e)
            if runs and runs[-1][0]==d:runs[-1][1]+=1
            else:runs.append([d,1])
        if len(runs)>1 and runs[0][0]==runs[-1][0]:runs[0][1]+=runs[-1][1];runs.pop()
        runCount+=len(runs)
        slopes=[];quadrant=None
        for k in range(len(runs)):
            d,n=runs[k];dd,nn=runs[(k+1)%len(runs)]
            if d%2==dd%2:continue
            horizontal=(d,n)if d%2==0 else(dd,nn);vertical=(dd,nn)if d%2==0 else(d,n);q=(horizontal[0],vertical[0])
            ratio=horizontal[1]/vertical[1]
            if q!=quadrant:slopes=[];quadrant=q;extrema+=1
            slopes.append(ratio)
            if len(slopes)>=3 and(slopes[-1]-slopes[-2])*(slopes[-2]-slopes[-3])<-1e-12:nonmono+=1
    return {'dualBoundaryEdges':sum(len(e)for e in loops),'collinearRuns':runCount,'stairRatioReversalsDiagnostic':nonmono,'monotoneBlocksDiagnostic':extrema,'regionBoundaryLoops':len(loops),'metricScope':'closed dual-grid run diagnostic, not paper Eq4 or an aesthetic pass'}

class Selector:
    def __init__(self,i,previous,eta):
        self.i=i;self.eta=eta;self.beta=float(np.float32(.14))*eta
        projection=json.loads((IN/f'{i:03d}_ALT_projection.json').read_text())
        self.signature=signature(MODEL_SIGNATURE,projection['headProjection'],projection['headView'],'Rig|Walk_Loop')
        self.previous,self.contextReason=previous_for(self.signature,previous)
        self.bounds,self.area=areas(i);doc=json.loads((IN/f'{i:03d}_curves.json').read_text());self.rings=[[(v['x'],v['y'])for v in r['points']]for r in doc['curves']]
        audit=json.loads((OUT/f'{i:03d}_ACTIVE.json').read_text());self.active=audit['active']
        self.packets={(p['x'],p['y']):p for p in json.loads((IN/f'{i:03d}_packets.json').read_text())['packets']}
        for ref in json.loads((IN/f'{i:03d}_ALT_bodyrefs512.json').read_text())['references']:
            k=(ref['x'],ref['y'])
            if k in self.packets:self.packets[k]['bodyForeground']=ref['kind']in[1,2]and ref['depth']<ref['hairDepth']-.0001
        self.mask=G.read_mask(i).copy();self.original=self.mask.copy();self.cache={};self.desc={}
        for e in G.boundary(self.mask):
            d=self.describe(key(e));assert d is not None,('Invalid initial cut',i,e)
            self.desc[key(e)]=d
        self.groupEdges={}
        for k,d in self.desc.items():self.groupEdges.setdefault(channel(d),{})[k]=d
        self.groupSpans=groups(self.desc);self.costs={};self.operations=[];self.rejected=collections.Counter();self.evaluations=0
        if self.previous:
            for ch in set(self.previous['spans'])|set(self.groupSpans):self.costs[ch]=self.cost(ch,self.groupSpans.get(ch,[]))
        self.initialT=sum(self.costs.values());self.initialSpatial=spatial(self.mask,self.area,self.bounds)
    def describe(self,k):
        if k not in self.cache:
            e={'a':list(k[:2]),'b':list(k[2:]),'inside':inside_edge(k)};d=G.descriptor(e,self.active,self.rings,self.packets)
            # Geometry-only novel-packet candidates may participate offline,
            # but their chosen result cannot pass runtime validation as known.
            if not d.get('geometryValid',False)or d.get('bodyForeground',False):self.cache[k]=None
            else:d['valid']=True;self.cache[k]=d
        return self.cache[k]
    def cost(self,ch,spans,trace=False):
        if not self.previous:return 0. if not trace else{'raw':0.,'operations':[]}
        result=S.channel_cost(self.previous['spans'].get(ch,[]),spans,self.rings,self.previous['active'],self.active,ch,trace)
        return result if trace else result['raw']
    def proposal(self,x,y):
        removed=[];added=[]
        for k in cell_edges(x,y):
            inv=reverse(k)
            if self.mask[y,x]:
                if k in self.desc:removed.append(k)
                else:added.append(inv)
            else:
                if inv in self.desc:removed.append(inv)
                else:added.append(k)
        ds=[]
        for k in added:
            d=self.describe(k)
            if d is None:self.rejected['INVALID_GEOMETRY_OR_KNOWN_FOREGROUND']+=1;return None
            ds.append((k,d))
        affected={channel(self.desc[k])for k in removed}|{channel(d)for k,d in ds}
        changed={ch:dict(self.groupEdges.get(ch,{}))for ch in affected}
        for k in removed:changed[channel(self.desc[k])].pop(k)
        for k,d in ds:changed[channel(d)][k]=d
        spanGroups={};newCosts={}
        for ch,d in changed.items():
            spanGroups[ch]=groups(d).get(ch,[]);newCosts[ch]=self.cost(ch,spanGroups[ch])
        dt=sum(newCosts[ch]-self.costs.get(ch,0.)for ch in affected)
        dspace=delta_spatial(self.mask,self.area,self.bounds,x,y);self.evaluations+=1
        return {'xy':[x,y],'removed':removed,'added':ds,'groups':changed,'spans':spanGroups,'costs':newCosts,'deltaSpatial':dspace,'deltaTemporal':dt,'deltaObjective':dspace+self.beta*dt}
    def solve(self):
        start=time.perf_counter();bx,by,w,h=self.bounds
        if self.previous:
            for iteration in range(256):
                best=None
                for y in range(by+1,by+h-1):
                    for x in range(bx+1,bx+w-1):
                        # A flip with no nearby current boundary can only add
                        # an isolated shape. Such births are still considered
                        # if their source cell has nonzero continuous area.
                        if not self.mask[y,x]and self.area[y-by,x-bx]==0 and not any(self.mask[y+dy,x+dx]for dx,dy,_ in N8):continue
                        p=self.proposal(x,y)
                        if p is not None and p['deltaObjective']<-1e-9 and(best is None or p['deltaObjective']<best['deltaObjective']-1e-12):best=p
                if best is None:break
                x,y=best['xy'];self.mask[y,x]=not self.mask[y,x]
                for k in best['removed']:self.desc.pop(k)
                for k,d in best['added']:self.desc[k]=d
                self.groupEdges.update(best['groups']);self.groupSpans.update(best['spans']);self.costs.update(best['costs'])
                self.operations.append({k:best[k]for k in ['xy','deltaSpatial','deltaTemporal','deltaObjective']})
            else:raise RuntimeError('Local search did not terminate within diagnostic cap; not a pass')
        final=spatial(self.mask,self.area,self.bounds);temporal=sum(self.costs.values());deltaObj=final['total']-self.initialSpatial['total']+self.beta*(temporal-self.initialT)
        assert deltaObj<=1e-7
        newFill=np.argwhere(self.mask&~self.original);removed=np.argwhere(self.original&~self.mask)
        unknown=[list(map(int,[x,y]))for y,x in zip(*np.where(self.mask))if(x,y)not in self.packets]
        error=[d['squaredFit']for d in self.desc.values()]
        traceKeys=set(self.groupSpans)|(set(self.previous['spans'])if self.previous else set())
        traces={str(ch):self.cost(ch,self.groupSpans.get(ch,[]),True)for ch in traceKeys}
        row={'target':self.i,'eta':self.eta,'beta':self.beta,'contextReason':self.contextReason,'initialSpatial':self.initialSpatial,'finalSpatial':final,'initialRawTemporal':self.initialT,'finalRawTemporal':temporal,'objectiveDelta':deltaObj,'localMoves':self.operations,'newFillXY':[[int(x),int(y)]for y,x in newFill],'removedXY':[[int(x),int(y)]for y,x in removed],'selectedNovelPacketUnknownXY':unknown,'boundaryFitRMS':math.sqrt(sum(error)/len(error))if error else 0.,'boundaryFitMax':math.sqrt(max(error,default=0.)),'quality':loop_quality(self.mask),'evaluations':self.evaluations,'rejected':dict(self.rejected),'seconds':time.perf_counter()-start,'traces':traces}
        return row,{'spans':self.groupSpans,'active':self.active,'rings':self.rings,'signature':self.signature},self.mask

def main():
    eta=float(sys.argv[1])if len(sys.argv)>1 else 1.;last=int(sys.argv[2])if len(sys.argv)>2 else 80
    root=OUT/('eta-'+str(eta));root.mkdir(exist_ok=True);previous=None;rows=[];start=time.perf_counter()
    for i in range(last+1):
        selector=Selector(i,previous,eta);row,previous,mask=selector.solve();np.save(root/f'{i:03d}.npy',mask)
        (root/f'{i:03d}.json').write_text(json.dumps(row,separators=(',',':'))+'\n');rows.append({k:v for k,v in row.items()if k not in ['traces','localMoves']})
        if i%5==0:print(json.dumps({'eta':eta,'frame':i,'moves':len(row['localMoves']),'seconds':row['seconds'],'newUnknown':len(row['selectedNovelPacketUnknownXY'])}),flush=True)
    result={'mode':'OFFLINE_CAUSAL_SINGLE_SELECTOR_PROTOTYPE','eta':eta,'beta':float(np.float32(.14))*eta,'frames':len(rows),'seconds':time.perf_counter()-start,'rows':rows,'paperEq5':False,'runtimePass':False,'novelPacketCount':sum(len(r['selectedNovelPacketUnknownXY'])for r in rows),'newUnityCapture':False}
    (root/'RESULT516.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='rows'}),flush=True)
if __name__=='__main__':main()
