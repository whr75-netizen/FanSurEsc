r"""Exact selected-region/continuous-region incidence for correspondence only.

Reuses511 rational segment intersections and the511 critical-event sweep.
P = positive-winding continuous curve region; M = already selected cells.
A=M\P, D=P\M, I=P&M, O=outside. Nothing here chooses or edits M.
"""
from fractions import Fraction as Q
from collections import defaultdict
import math
from compile_curve511 import parameters,cross,sub,point

def rational(v):return v if isinstance(v,Q)else Q(float(v))
def canonical_rings(rings):
    out=[]
    for ring in rings:
        p=[tuple(rational(v)for v in q)for q in ring]
        while len(p)>3:
            keep=[]
            for i,b in enumerate(p):
                a,c=p[i-1],p[(i+1)%len(p)];v,w=sub(b,a),sub(c,b)
                if cross(v,w)!=0 or v[0]*w[0]+v[1]*w[1]<0:keep.append(b)
            if len(keep)==len(p)or len(keep)<3:break
            p=keep
        at=min(range(len(p)),key=lambda i:p[i]);out.append(p[at:]+p[:at])
    return sorted(out)
def winding(p,edges):
    value=0
    for a,b in edges:
        c=cross(sub(b,a),sub(p,a))
        if a[1]<=p[1]<b[1]and c>0:value+=1
        elif b[1]<=p[1]<a[1]and c<0:value-=1
    return value
class DSU:
    def __init__(self,n):self.p=list(range(n))
    def root(self,x):
        while self.p[x]!=x:self.p[x]=self.p[self.p[x]];x=self.p[x]
        return x
    def union(self,a,b):
        a,b=self.root(a),self.root(b)
        if a!=b:self.p[max(a,b)]=min(a,b)

class Overlay:
    def __init__(self,rings,mask,domain,whole=False):
        self.rings=canonical_rings(rings);self.edges=[(a,b)for r in self.rings for a,b in zip(r,r[1:]+r[:1])if a!=b]
        self.mask=mask;self.domain=tuple(map(int,domain));self.whole=whole;self.faces=[];self.bands=[];self.source=[];self.pixel=[];self.common=[]
        x0,y0,x1,y1=self.domain;levels={Q(y)for y in range(y0,y1+1)}
        relevant=[e for e in self.edges if max(e[0][0],e[1][0])>=x0 and min(e[0][0],e[1][0])<=x1 and max(e[0][1],e[1][1])>=y0 and min(e[0][1],e[1][1])<=y1]
        for a,b in relevant:
            for q in[a,b]:
                if y0<q[1]<y1:levels.add(q[1])
            if a[0]!=b[0]:
                for x in range(x0,x1+1):
                    t=(Q(x)-a[0])/(b[0]-a[0]);y=a[1]+t*(b[1]-a[1])
                    if 0<t<1 and y0<y<y1:levels.add(y)
        for i,(a,b)in enumerate(relevant):
            for c,d in relevant[i+1:]:
                for t,u in parameters(a,b,c,d):
                    p=point(a,b,t)
                    if x0<=p[0]<=x1 and y0<p[1]<y1:levels.add(p[1])
        self.levels=sorted(levels)
        for lo,hi in zip(self.levels,self.levels[1:]):
            mid=(lo+hi)/2;lines={}
            def add(slope,intercept,source=None,grid=None):
                x=slope*mid+intercept
                if x0<=x<=x1:
                    key=(slope,intercept);entry=lines.setdefault(key,{'a':slope,'b':intercept,'source':set(),'grid':grid})
                    if source is not None:entry['source'].add(source)
                    if grid is not None:entry['grid']=grid
            for x in range(x0,x1+1):add(Q(0),Q(x),grid=x)
            for si,(a,b)in enumerate(self.edges):
                if a[1]!=b[1]and min(a[1],b[1])<mid<max(a[1],b[1]):
                    slope=(b[0]-a[0])/(b[1]-a[1]);add(slope,a[0]-slope*a[1],source=si)
            ordered=sorted(lines.values(),key=lambda l:l['a']*mid+l['b'])
            assert all(self.X(a,mid)<self.X(b,mid)for a,b in zip(ordered,ordered[1:])),'Unsplit equal crossings'
            band=[]
            for left,right in zip(ordered,ordered[1:]):
                centre=(self.X(left,mid)+self.X(right,mid))/2;cell=(math.floor(centre),math.floor(mid));inside=winding((centre,mid),self.edges)>0;selected=bool(mask.get(cell,False));tag='I'if inside and selected else'A'if selected else'D'if inside else'O'
                area=(hi-lo)*(self.X(right,lo)-self.X(left,lo)+self.X(right,hi)-self.X(left,hi))/2;assert area>0
                f={'id':len(self.faces),'lo':lo,'hi':hi,'left':left,'right':right,'P':inside,'M':selected,'tag':tag,'area':area,'cell':cell,'cut':left['grid']==x0 or right['grid']==x1 or lo==y0 and self.X(right,lo)>self.X(left,lo)or hi==y1 and self.X(right,hi)>self.X(left,hi)}
                self.faces.append(f);band.append(f['id'])
            self.bands.append(band)
        n=len(self.faces);self.changed=DSU(n);self.positive=DSU(n);self.negative=DSU(n);self.selected=DSU(n)
        for band in self.bands:
            for ia,ib in zip(band,band[1:]):
                a,b=self.faces[ia],self.faces[ib];line=a['right'];p=(self.X(line,a['lo']),a['lo']);q=(self.X(line,a['hi']),a['hi']);self.adjacency(a,b,p,q,axis='V',sourceIds=line['source'])
        for above,below in zip(self.bands,self.bands[1:]):
            y=self.faces[above[0]]['hi'];ia=ib=0
            while ia<len(above)and ib<len(below):
                a,b=self.faces[above[ia]],self.faces[below[ib]];al,ar=self.X(a['left'],y),self.X(a['right'],y);bl,br=self.X(b['left'],y),self.X(b['right'],y);lo,hi=max(al,bl),min(ar,br)
                if hi>lo:
                    source={k for k,(p,q)in enumerate(self.edges)if p[1]==q[1]==y and min(p[0],q[0])<=lo and max(p[0],q[0])>=hi}
                    self.adjacency(a,b,(lo,y),(hi,y),axis='H',sourceIds=source)
                if ar<=br:ia+=1
                if br<=ar:ib+=1
        self.components={};self.pixelOwners=defaultdict(set)
        for f in self.faces:
            if f['tag']not in['A','D']:continue
            root=self.changed.root(f['id']);c=self.components.setdefault(root,{'tag':f['tag'],'faces':[],'area':Q(0),'cells':set(),'cut':False,'sourceBoundary':[],'pixelBoundary':[],'sourceRegions':set(),'selectedRegions':set(),'negativeRegions':set()})
            c['faces'].append(f['id']);c['area']+=f['area'];c['cells'].add(f['cell']);c['cut']|=f['cut']
        for s in self.source:
            for fid in s['changeFaces']:
                c=self.components[self.changed.root(fid)];c['sourceBoundary'].append(s);inside=self.faces[s['insideP']];c['sourceRegions'].add(self.positive.root(inside['id']))
        for s in self.pixel:
            for fid in s['changeFaces']:
                root=self.changed.root(fid);c=self.components[root];c['pixelBoundary'].append(s);inside=self.faces[s['insideM']];c['selectedRegions'].add(self.selected.root(inside['id']));self.pixelOwners[s['edge']].add(root)
        for f in self.faces:
            if f['tag']in['A','D']:
                c=self.components[self.changed.root(f['id'])]
                if f['P']:c['sourceRegions'].add(self.positive.root(f['id']))
                else:c['negativeRegions'].add(self.negative.root(f['id']))
                if f['M']:c['selectedRegions'].add(self.selected.root(f['id']))
        self.cellAreas=defaultdict(Q)
        for f in self.faces:
            if f['P']:self.cellAreas[f['cell']]+=f['area']
    @staticmethod
    def X(line,y):return line['a']*y+line['b']
    def adjacency(self,a,b,p,q,axis,sourceIds):
        assert p!=q
        if a['tag']==b['tag']:self.changed.union(a['id'],b['id'])
        if a['P']and b['P']:self.positive.union(a['id'],b['id'])
        if not a['P']and not b['P']:self.negative.union(a['id'],b['id'])
        if a['M']and b['M']:self.selected.union(a['id'],b['id'])
        changes=[f['id']for f in[a,b]if f['tag']in['A','D']]
        if a['P']!=b['P']:
            assert sourceIds,'Positive-winding boundary without source edge'
            if axis=='V':u,v=(p,q)if a['P']else(q,p)
            else:u,v=(q,p)if a['P']else(p,q)
            self.source.append({'a':u,'b':v,'sourceIds':sorted(sourceIds),'changeFaces':changes,'insideP':a['id']if a['P']else b['id']})
        if a['M']!=b['M']:
            if axis=='V':
                assert p[0]==q[0]and p[0].denominator==1;xx=int(p[0]);yy=math.floor((p[1]+q[1])/2);edge=(xx,yy,xx,yy+1)if a['M']else(xx,yy+1,xx,yy);u,v=(p,q)if a['M']else(q,p)
            else:
                assert p[1]==q[1]and p[1].denominator==1;yy=int(p[1]);xx=math.floor((p[0]+q[0])/2);edge=(xx+1,yy,xx,yy)if a['M']else(xx,yy,xx+1,yy);u,v=(q,p)if a['M']else(p,q)
            self.pixel.append({'a':u,'b':v,'edge':edge,'changeFaces':changes,'insideM':a['id']if a['M']else b['id']})
        if a['P']!=b['P']and a['M']!=b['M']:
            self.common.append({'a':p,'b':q,'sameFilledSide':a['P']==a['M'],'pixelEdge':self.pixel[-1]['edge'],'sourceIds':sorted(sourceIds)})
    def summary(self):
        out=[]
        for root,c in sorted(self.components.items()):
            out.append({'id':root,'tag':c['tag'],'areaExact':str(c['area']),'area':float(c['area']),'cells':sorted(c['cells']),'analysisCutOpen':c['cut'],'sourceBoundaryCount':len(c['sourceBoundary']),'pixelBoundaryCount':len(c['pixelBoundary']),'sourceRegions':sorted(c['sourceRegions']),'selectedRegions':sorted(c['selectedRegions']),'negativeRegions':sorted(c['negativeRegions'])})
        return {'domain':self.domain,'wholeDomainWithOutsidePadding':self.whole,'criticalBands':len(self.bands),'atomicFaces':len(self.faces),'components':out,'directSharedBoundaryFragments':len([s for s in self.common if s['sameFilledSide']]),'newMaskChosen':False,'connectivity':'exact positive-length shared face boundaries; point-only contact is not adjacency'}
    def candidate_components(self,edge,segment):
        a,b=[tuple(rational(x)for x in p)for p in segment];out=set()
        for root in self.pixelOwners[tuple(edge)]:
            for record in self.components[root]['sourceBoundary']:
                c,d=record['a'],record['b']
                if cross(sub(b,a),sub(d,c))!=0 or cross(sub(c,a),sub(b,a))!=0:continue
                axis=0 if abs(b[0]-a[0])>=abs(b[1]-a[1])else 1
                if min(max(a[axis],b[axis]),max(c[axis],d[axis]))>max(min(a[axis],b[axis]),min(c[axis],d[axis]))and sum(x*y for x,y in zip(sub(b,a),sub(d,c)))>0:out.add(root)
        return out
    def relate(self,edgeA,edgeB,visibility=True,sourceA=None,sourceB=None):
        a,b=tuple(edgeA),tuple(edgeB);shared=self.pixelOwners[a]&self.pixelOwners[b];witness=[]
        candidateA=self.candidate_components(a,sourceA)if sourceA is not None else None;candidateB=self.candidate_components(b,sourceB)if sourceB is not None else None
        if candidateA is not None:shared&=candidateA
        if candidateB is not None:shared&=candidateB
        for root in sorted(shared):
            c=self.components[root];owners=c['selectedRegions'];witness.append({'component':root,'kind':'SELECTOR_ADDED_FACE_JOIN'if c['tag']=='A'else'SELECTOR_REMOVED_FACE_RELATION','tag':c['tag'],'areaExact':str(c['area']),'cells':sorted(c['cells']),'sourceBoundaryCount':len(c['sourceBoundary']),'sourceRegions':sorted(c['sourceRegions']),'selectedRegions':sorted(owners),'outputRegionMerged':c['tag']=='A'and len(owners)==1})
        incident=a[2:]==b[:2]or b[2:]==a[:2];ownerA={self.selected.root(s['insideM'])for s in self.pixel if s['edge']==a};ownerB={self.selected.root(s['insideM'])for s in self.pixel if s['edge']==b};sameOwner=bool(ownerA&ownerB)
        def contains(p,u,v):return cross(sub(p,u),sub(v,u))==0 and all(min(u[k],v[k])<=p[k]<=max(u[k],v[k])for k in[0,1])
        commonA=[s for s in self.common if s['pixelEdge']==a and s['sameFilledSide']];commonB=[s for s in self.common if s['pixelEdge']==b and s['sameFilledSide']]
        vertex=a[2:]if a[2:]==b[:2]else b[2:]if b[2:]==a[:2]else None
        direct=vertex is not None and any(contains(vertex,s['a'],s['b'])for s in commonA)and any(contains(vertex,s['a'],s['b'])for s in commonB)
        graph=bool(witness)or direct;joined=incident and sameOwner and graph;visible=joined if visibility is True else False if visibility is False or not joined else None
        return {'graphRelation':graph,'boundaryPathJoin':joined,'pixelEdgesIncident':incident,'sameSelectedRegion':sameOwner,'directSharedBoundary':direct,'witness':witness,'candidateSourceAComponents':sorted(candidateA)if candidateA is not None else None,'candidateSourceBComponents':sorted(candidateB)if candidateB is not None else None,'visibleCorrespondenceAccepted':visible,'visibilityReason':'CURRENT_OWNER_ELIGIBLE'if visibility is True else'CURRENT_FRONT_OWNER'if visibility is False else'VISIBILITY_UNVERIFIED','maskChanged':False}

def mask_from_array(array):return{(int(x),int(y)):True for y,x in zip(*array.nonzero())}
def auto_domain(rings,mask):
    p=[q for r in rings for q in r];xs=[q[0]for q in p]+[x for x,y in mask]+[x+1 for x,y in mask];ys=[q[1]for q in p]+[y for x,y in mask]+[y+1 for x,y in mask]
    return(math.floor(min(xs))-1,math.floor(min(ys))-1,math.ceil(max(xs))+1,math.ceil(max(ys))+1)
