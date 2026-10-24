"""Small offline coverage kernel; no Unity renderer, image grid or point samples.

Clip/Subtract follow HeadArea505/508's half-plane partition, using exact rational
arithmetic instead of epsilon deletion. A parabola is enclosed by its chord and
midpoint tangent. Only already-proven alpha-pass domains are accepted.
"""
from dataclasses import dataclass,replace
from fractions import Fraction as Q
import heapq,time

def q(x):return x if isinstance(x,Q) else Q(x)
def point(x,y):return q(x),q(y)
def signed_area(p):return sum((a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:]+p[:1])),Q(0))/2
def area(p):return abs(signed_area(p)) if len(p)>=3 else Q(0)

@dataclass(frozen=True)
class Plane:
    x:Q=Q(0);y:Q=Q(0);c:Q=Q(0)
    def __post_init__(self):
        for name in ['x','y','c']:object.__setattr__(self,name,q(getattr(self,name)))
    def at(self,p):return self.x*p[0]+self.y*p[1]+self.c
    def __sub__(self,b):return Plane(self.x-b.x,self.y-b.y,self.c-b.c)
    def scale(self,k):return Plane(self.x*k,self.y*k,self.c*k)
    def offset(self,k):return Plane(self.x,self.y,self.c+k)

def fit(p,values):
    p=tuple(point(*v)for v in p);values=list(map(q,values))
    ax,ay=p[1][0]-p[0][0],p[1][1]-p[0][1];bx,by=p[2][0]-p[0][0],p[2][1]-p[0][1]
    det=ax*by-ay*bx
    if not det:raise ValueError('Degenerate input triangle')
    dv,dw=values[1]-values[0],values[2]-values[0]
    x=(dv*by-dw*ay)/det;y=(ax*dw-bx*dv)/det
    return Plane(x,y,values[0]-x*p[0][0]-y*p[0][1])

class Kernel:
    def __init__(self,max_fragments=4096):self.clips=0;self.pairs=0;self.max_fragments=max_fragments;self.peak_fragments=0
    def clip(self,p,h,positive=True):
        self.clips+=1
        if not p:return ()
        out=[];a=p[-1];da=h.at(a)*(1 if positive else -1)
        def append(v):
            if not out or out[-1]!=v:out.append(v)
        for b in p:
            db=h.at(b)*(1 if positive else -1)
            if (da>=0)!=(db>=0):
                t=da/(da-db);append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
            if db>=0:append(b)
            a,da=b,db
        if len(out)>1 and out[0]==out[-1]:out.pop()
        return tuple(out) if len(out)>=3 else ()
    @staticmethod
    def edges(p):
        sign=1 if signed_area(p)>0 else -1
        for a,b in zip(p,p[1:]+p[:1]):
            dx,dy=b[0]-a[0],b[1]-a[1]
            if dx or dy:yield Plane(-dy*sign,dx*sign,(dy*a[0]-dx*a[1])*sign)
    def overlap(self,p,mask):
        for edge in self.edges(mask):
            p=self.clip(p,edge)
            if not area(p):return ()
        return p
    def subtract(self,p,mask):
        if not area(mask):return [p]
        result=[];inside=p
        for edge in self.edges(mask):
            outside=self.clip(inside,edge,False)
            if area(outside):result.append(outside)
            inside=self.clip(inside,edge)
            if not area(inside):break
        return result
    def track(self,items):
        self.peak_fragments=max(self.peak_fragments,len(items))
        if len(items)>self.max_fragments:raise InputUnavailable('FRAGMENT_LIMIT')
    def nearest(self,patches):
        result=[]
        for t in patches:
            pieces=[t.polygon]
            for o in patches:
                if o.id==t.id or o.layer!=t.layer:continue
                self.pairs+=1
                mask=self.overlap(t.polygon,o.polygon)
                if not area(mask):continue
                if t.z==o.z:
                    if t.draw==o.draw:raise InputUnavailable('AMBIGUOUS_DRAW_TIE')
                    if o.draw<t.draw:continue
                else:mask=self.clip(mask,t.z-o.z)
                if not area(mask):continue
                pieces=[z for p in pieces for z in self.subtract(p,mask)];self.track(pieces)
            result.extend(replace(t,polygon=p) for p in pieces);self.track(result)
        return result
    def visible(self,patches,target_owner):
        for p in patches:
            if p.passed is None:raise InputUnavailable('ALPHA_PASS_DOMAIN_UNPROVEN:'+p.id)
            if not Q(0)<=p.alpha_lo<=p.alpha_hi<=Q(1):raise ValueError('Opacity bounds')
            if p.passed and p.alpha_lo<=0:raise InputUnavailable('ALPHA_PRESENCE_UNPROVEN:'+p.id)
            if p.projection!='orthographic':raise InputUnavailable('NONAFFINE_PROJECTION')
            turns=[]
            for a,b,c in zip(p.polygon,p.polygon[1:]+p.polygon[:1],p.polygon[2:]+p.polygon[:2]):
                cross=(b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])
                if cross:turns.append(cross>0)
            if turns and len(set(turns))!=1:raise InputUnavailable('NONCONVEX_PATCH_NEEDS_SPLIT:'+p.id)
        patches=[p for p in patches if p.passed and area(p.polygon)]
        if len({p.id for p in patches})!=len(patches):raise InputUnavailable('DUPLICATE_FRAGMENT_ID')
        nearest=self.nearest(patches)
        layers={p.layer for p in nearest if p.kind=='source'}
        if len(layers)>1:raise InputUnavailable('REFERENCE_SUPPORT_FALLBACK_NOT_EXPRESSED')
        result=[]
        for source in nearest:
            if source.kind!='source' or source.owner!=target_owner or not source.front:continue
            pieces=[Weighted(source.polygon,source,Q(1),Q(1))]
            for occluder in nearest:
                if occluder.kind=='source':continue
                mask=self.overlap(source.polygon,occluder.polygon)
                if not area(mask) or source.z==occluder.z:continue  # actual strict '<' depth test
                mask=self.clip(mask,source.z-occluder.z)
                if not area(mask):continue
                lo,hi=(Q(0),Q(0)) if occluder.kind=='body' else (1-occluder.alpha_hi,1-occluder.alpha_lo)
                next_pieces=[]
                for piece in pieces:
                    inside=self.overlap(piece.polygon,mask)
                    next_pieces.extend(replace(piece,polygon=p) for p in self.subtract(piece.polygon,mask))
                    if area(inside) and hi:next_pieces.append(Weighted(inside,source,piece.lo*lo,piece.hi*hi))
                pieces=next_pieces;self.track(pieces)
            result.extend(pieces);self.track(result)
        return result
    def enclosure(self,w,band,left,right):
        source=w.source;u,v=source.u,source.v
        poly=self.clip(w.polygon,u.offset(-left));poly=self.clip(poly,u.scale(-1).offset(right))
        if not area(poly):return Q(0),Q(0),Q(0)
        slope=band.b*(left+right);chord=band.a-band.b*left*right
        mid=(left+right)/2;tangent=band.a-band.b*mid*mid
        low,high=(tangent,chord) if band.b>=0 else (chord,tangent)
        def strip(bottom,top):
            p=self.clip(poly,(v-u.scale(slope)).offset(-bottom-band.down))
            p=self.clip(p,(u.scale(slope)-v).offset(top+band.up))
            return area(p)
        inner=strip(high,low);outer=strip(low,high)
        assert 0<=inner<=outer
        return inner*w.lo,outer*w.hi,(outer-inner)*w.hi

@dataclass(frozen=True)
class Patch:
    id:str;polygon:tuple;z:Plane;u:Plane;v:Plane
    layer:str='source0';kind:str='source';owner:int=2;front:bool=True;draw:int=0
    passed:object=True;alpha_lo:Q=Q(1);alpha_hi:Q=Q(1);projection:str='orthographic'
    def __post_init__(self):
        object.__setattr__(self,'polygon',tuple(point(*v)for v in self.polygon))
        object.__setattr__(self,'alpha_lo',q(self.alpha_lo));object.__setattr__(self,'alpha_hi',q(self.alpha_hi))
@dataclass(frozen=True)
class Weighted:
    polygon:tuple;source:Patch;lo:Q;hi:Q
@dataclass(frozen=True)
class Band:
    a:Q;b:Q;down:Q;up:Q;umin:Q;umax:Q
    def __post_init__(self):
        for name in ['a','b','down','up','umin','umax']:object.__setattr__(self,name,q(getattr(self,name)))
class InputUnavailable(Exception):pass

def solve(patches,band,target_owner=2,tolerance=Q(1,100000),max_leaves=2048):
    start=time.perf_counter();k=Kernel();queue=[];lower=Q(0);upper=Q(0);geometry_gap=Q(0);serial=0;leaves=0;source_lo={};source_hi={}
    try:visible=k.visible(patches,target_owner)
    except InputUnavailable as error:
        return dict(status='UNRESOLVED_INPUT',reason=str(error),lower=None,upper=None,budget=None,seconds=time.perf_counter()-start)
    def add(w,left,right):
        nonlocal lower,upper,geometry_gap,serial,leaves
        # Constant u still covers screen area. At left==right chord==tangent,
        # so the same half-plane clip gives the exact linear-strip result.
        if left>right:return
        lo,hi,ge=k.enclosure(w,band,left,right);lower+=lo;upper+=hi;geometry_gap+=ge;leaves+=1
        name=w.source.id;source_lo[name]=source_lo.get(name,Q(0))+lo;source_hi[name]=source_hi.get(name,Q(0))+hi
        if ge>0:
            serial+=1;heapq.heappush(queue,(-ge,serial,w,left,right,lo,hi,ge))
    for w in visible:
        uv=[w.source.u.at(p) for p in w.polygon]
        add(w,max(band.umin,min(uv)),min(band.umax,max(uv)))
    initial=(lower,upper)
    while geometry_gap>tolerance and queue and leaves<max_leaves:
        _,_,w,left,right,lo,hi,ge=heapq.heappop(queue);lower-=lo;upper-=hi;geometry_gap-=ge;leaves-=1;source_lo[w.source.id]-=lo;source_hi[w.source.id]-=hi
        mid=(left+right)/2;add(w,left,mid);add(w,mid,right)
    nl=int(lower+Q(1,2));nh=int(upper+Q(1,2));accurate=upper-lower<=tolerance
    status='CERTIFIED' if accurate and nl==nh else 'UNRESOLVED_THRESHOLD' if accurate else 'UNRESOLVED_OPACITY' if geometry_gap<=tolerance else 'UNRESOLVED_ACCURACY'
    return dict(status=status,lower=lower,upper=upper,budget=nl if status=='CERTIFIED' else None,
        midpoint=(lower+upper)/2,radius=(upper-lower)/2,tolerance=tolerance,initial=initial,
        leaves=leaves,visibilityFragments=len(visible),clipCalls=k.clips,depthPairs=k.pairs,
        peakVisibilityFragments=k.peak_fragments,geometryGap=geometry_gap,
        bySource={name:dict(lower=source_lo[name],upper=source_hi[name]) for name in source_lo},seconds=time.perf_counter()-start,
        guarantee='Exact rational linear clipping and parabola chord/tangent enclosure, conditional on supplied proven alpha-pass domains/opacity bounds. No epsilon-area deletion or centre samples.')
