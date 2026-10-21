"""Partial pixel-edge incidence in the EXISTING exact P/M overlay.

No region is selected here.  Subpieces only describe already selected edges;
one unit edge still supplies one sample to the unchanged atomic edit cost.
Point contacts do not merge faces.  Boundary crossings are recorded separately.
"""
from collections import defaultdict
from fractions import Fraction as Q
import numpy as np
import face518 as F


def contains(p,a,b):
    return F.cross(F.sub(p,a),F.sub(b,a))==0 and all(min(a[k],b[k])<=p[k]<=max(a[k],b[k])for k in[0,1])


def attach_exact_sources(arcs,overlay):
    """Annotate the existing float arcs with the SAME exact overlay geometry.

    The517 geometry array is retained for fitting/cost.  Its rounded rational
    intersection endpoint cannot be tested for exact collinearity.  Recover
    directed cycles from exact active fragments and require a unique match at
    the pre-existing517 EPS; that match never creates a face/region connection.
    """
    import arc517 as A
    edges={(s['a'],s['b'])for s in overlay.source};outgoing=defaultdict(list);incoming=defaultdict(list)
    for a,b in edges:outgoing[a].append(b);incoming[b].append(a)
    assert all(len(outgoing[p])==len(incoming[p])==1 for p in set(outgoing)|set(incoming)),'EXACT_ACTIVE_BOUNDARY_JUNCTION'
    unused=set(edges);cycles=[]
    while unused:
        a,b=min(unused);start=a;points=[]
        while True:
            points.append(a);unused.remove((a,b));a=b
            if a==start:break
            b=outgoing[a][0]
        cycles.append(F.canonical_rings([points])[0])
    matches=[];used=set()
    for ai,arc in enumerate(arcs):
        candidates=[]
        for ci,p in enumerate(cycles):
            v=np.array(p,float)
            if ci not in used and v.shape==arc['p'].shape and np.max(abs(v-arc['p']),initial=0)<=A.EPS:candidates.append((ci,p,float(np.max(abs(v-arc['p']),initial=0))))
        assert len(candidates)==1,('EXACT_SOURCE_CYCLE_MATCH_NOT_UNIQUE',ai,len(candidates),[len(p)for p in cycles],len(arc['p']))
        ci,p,error=candidates[0];used.add(ci);arc['exactP']=p;arc['exactB']=p[1:]+p[:1];matches.append({'arc':ai,'exactSegments':len(p),'maximumSerializationDifference':error})
    assert len(used)==len(cycles)
    return matches


def source_segment(arc,i):
    return [arc['exactP'][i],arc['exactB'][i]]if 'exactP'in arc else[arc['p'][i],arc['b'][i]]


class BoundaryIncidence:
    def __init__(self,overlay):
        self.overlay=overlay;self.pieces=defaultdict(list);self.supportCache={};self.rawCount=len(overlay.pixel)
        for s in overlay.pixel:
            e=s['edge'];direction=(e[2]-e[0],e[3]-e[1]);axis=0 if direction[0]else 1
            t0=(s['a'][axis]-e[axis])/direction[axis];t1=(s['b'][axis]-e[axis])/direction[axis]
            assert 0<=t0<t1<=1
            roots=tuple(sorted({overlay.changed.root(fid)for fid in s['changeFaces']}))
            inside=overlay.faces[s['insideM']];owner=overlay.selected.root(inside['id'])
            tags=tuple(sorted({overlay.components[r]['tag']for r in roots}))
            # No changed face means a coincident P/M boundary.  A+D on the
            # same fragment means opposite filled sides, not a common owner.
            kind='COMMON'if not tags else 'OPPOSED'if tags==('A','D')else tags[0]
            self.pieces[e].append({'a':s['a'],'b':s['b'],'t0':t0,'t1':t1,'roots':roots,'selectedOwner':owner,'kind':kind})
        self.crossings=[]
        for e,raw in list(self.pieces.items()):
            raw.sort(key=lambda s:s['t0']);out=[]
            for p in raw:
                if out and out[-1]['t1']==p['t0']and all(out[-1][k]==p[k]for k in['roots','selectedOwner','kind']):
                    out[-1]={**out[-1],'b':p['b'],'t1':p['t1']}
                else:out.append(dict(p))
            assert out[0]['t0']==0 and out[-1]['t1']==1,(e,out)
            assert all(a['t1']==b['t0']and a['b']==b['a']for a,b in zip(out,out[1:])),e
            assert sum((p['t1']-p['t0']for p in out),Q(0))==1
            assert len({p['selectedOwner']for p in out})==1,e
            for a,b in zip(out,out[1:]):
                point=a['b'];sources=[s for s in overlay.source if contains(point,s['a'],s['b'])]
                # A/D incidence can change only at an already computed active
                # P-boundary intersection.  No near-neighbour join is added.
                assert sources,('INCIDENCE_CHANGE_WITHOUT_SOURCE_CROSSING',e,point)
                self.crossings.append({'edge':e,'point':point,'from':a['kind'],'to':b['kind'],'sourceFragments':len(sources)})
            self.pieces[e]=out

    def at(self,edge,t):
        return[p for p in self.pieces[tuple(edge)]if p['t0']<=t<=p['t1']]

    def candidate_support(self,edge,segment):
        e=tuple(edge);key=(e,tuple(tuple(float(v)for v in p)for p in segment))
        if key in self.supportCache:return self.supportCache[key]
        centre=self.at(e,Q(1,2));roots={r for p in centre for r in p['roots']}
        owners=self.overlay.candidate_components(e,segment)&roots
        common=any(p['kind']=='COMMON'for p in centre)
        a,b=[tuple(F.rational(v)for v in p)for p in segment]
        direct=False
        if common:
            for p in centre:
                if p['kind']!='COMMON':continue
                c,d=p['a'],p['b']
                if F.cross(F.sub(b,a),F.sub(d,c))!=0 or F.cross(F.sub(c,a),F.sub(b,a))!=0:continue
                axis=0 if abs(b[0]-a[0])>=abs(b[1]-a[1])else 1
                if min(max(a[axis],b[axis]),max(c[axis],d[axis]))>max(min(a[axis],b[axis]),min(c[axis],d[axis]))and sum(x*y for x,y in zip(F.sub(b,a),F.sub(d,c)))>0:direct=True
        result={'accepted':bool(owners)or direct,'centreRoots':sorted(roots),'candidateCentreRoots':sorted(owners),'directCommon':direct}
        self.supportCache[key]=result;return result

    def relate(self,edgeA,edgeB,visibility=True,sourceA=None,sourceB=None):
        a,b=tuple(edgeA),tuple(edgeB)
        if b[2:]==a[:2]and a[2:]!=b[:2]:
            a,b=b,a;sourceA,sourceB=sourceB,sourceA
        incident=a[2:]==b[:2]
        pa=self.at(a,Q(1))[-1];pb=self.at(b,Q(0))[0]
        shared=set(pa['roots'])&set(pb['roots']);same=pa['selectedOwner']==pb['selectedOwner']
        supportA=self.candidate_support(a,sourceA)if sourceA is not None else None
        supportB=self.candidate_support(b,sourceB)if sourceB is not None else None
        anchors=(supportA is None or supportA['accepted'])and(supportB is None or supportB['accepted'])
        vertex=tuple(Q(v)for v in a[2:]);sourceVertex=incident and any(contains(vertex,s['a'],s['b'])for s in self.overlay.source)
        direct=pa['kind']==pb['kind']=='COMMON'and sourceVertex
        # An exact source-boundary crossing can change the endpoint incidence;
        # it does NOT union two changed faces or two selected components.
        boundaryTransition=sourceVertex and (pa['kind']!=pb['kind'])
        structural=bool(shared)or direct or boundaryTransition
        joined=incident and same and structural and anchors
        witness=[{'component':r,'tag':self.overlay.components[r]['tag'],'areaExact':str(self.overlay.components[r]['area']),'sourceRegions':sorted(self.overlay.components[r]['sourceRegions']),'selectedRegions':sorted(self.overlay.components[r]['selectedRegions'])}for r in sorted(shared)]
        if direct or boundaryTransition:witness.append({'kind':'EXACT_SOURCE_BOUNDARY_VERTEX','point':vertex,'from':pa['kind'],'to':pb['kind']})
        return {'graphRelation':structural,'boundaryPathJoin':joined,'pixelEdgesIncident':incident,'sameSelectedRegion':same,'directSharedBoundary':direct,'exactSourceBoundaryTransition':boundaryTransition,'witness':witness,'endpointKinds':[pa['kind'],pb['kind']],'unitCentreSupport':[supportA,supportB],'visibleCorrespondenceAccepted':joined if visibility is True else False if visibility is False or not joined else None,'visibilityReason':'CURRENT_OWNER_ELIGIBLE'if visibility is True else'CURRENT_FRONT_OWNER'if visibility is False else'VISIBILITY_UNVERIFIED','maskChanged':False}

    def record(self,edge):
        return[{'a':p['a'],'b':p['b'],'interval':[p['t0'],p['t1']],'kind':p['kind'],'changedComponents':p['roots'],'selectedOwner':p['selectedOwner']}for p in self.pieces[tuple(edge)]]

    def summary(self):
        counts=[len(p)for p in self.pieces.values()]
        return {'unitEdges':len(counts),'rawSweepFragments':self.rawCount,'normalizedPartialPieces':sum(counts),'splitUnitEdges':sum(n>1 for n in counts),'maxPiecesPerUnit':max(counts,default=0),'sourceBoundaryCrossings':len(self.crossings),'pieceKinds':{k:sum(p['kind']==k for ps in self.pieces.values()for p in ps)for k in['A','D','COMMON','OPPOSED']},'exactLengthPerUnit':'1','editCostSamplesPerUnit':1,'newSelection':False}
