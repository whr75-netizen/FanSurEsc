"""One inside-outline correspondence audit; no selector or product changes.

B4(S) is the L1 one-cell inner boundary, not a claim about OwnerLines333.
G8 is the paper's pixel neighbourhood; G4 is a diagnostic alternative only.
"""
from pathlib import Path
from collections import Counter
import hashlib, json
import numpy as np

O=Path(__file__).resolve().parent
W=O.parent
ns={'__file__':str(W/'Feature535/compare535.py')}
exec((W/'Feature535/compare535.py').read_text().split('\nrows = []')[0],ns)
saved,boundaries=ns['saved'],ns['boundaries']

def inner(mask):
    p=np.pad(mask,1,constant_values=False)
    return mask & ~(p[:-2,1:-1]&p[2:,1:-1]&p[1:-1,:-2]&p[1:-1,2:])

def graph(cells,eight):
    ds=[(x,y)for x in[-1,0,1]for y in[-1,0,1]if(x or y)and(eight or abs(x)+abs(y)==1)]
    adj={p:{(p[0]+dx,p[1]+dy)for dx,dy in ds}&cells for p in cells}
    left=set(cells);comps=[]
    while left:
        start=min(left);todo=[start];part=set();left.remove(start)
        while todo:
            p=todo.pop();part.add(p)
            for q in adj[p]&left:left.remove(q);todo.append(q)
        hist=Counter(len(adj[p])for p in part);edges=sum(k*v for k,v in hist.items())//2
        cycle=len(part)>2 and set(hist)=={2}
        path=len(part)>1 and hist[1]==2 and all(k in[1,2]for k in hist)
        comps.append({'vertices':len(part),'edges':edges,'degreeHistogram':dict(sorted(hist.items())),
            'cycleRank':edges-len(part)+1,'singleClosedPath':cycle,'singleOpenPath':path})
    degree=Counter(len(v)for v in adj.values())
    return {'vertices':len(cells),'edges':sum(map(len,adj.values()))//2,
        'components':len(comps),'degreeHistogram':dict(sorted(degree.items())),
        'junctionCells':sum(v for k,v in degree.items()if k>2),'isolatedCells':degree[0],
        'allComponentsSinglePath':all(q['singleClosedPath']or q['singleOpenPath']for q in comps),
        'singleClosedPath':len(comps)==1 and comps[0]['singleClosedPath'],
        'singleOpenPath':len(comps)==1 and comps[0]['singleOpenPath'],
        'componentStats':comps,
        'junctionExamples':[list(p)for p in sorted(adj)if len(adj[p])>2][:12]},adj

def incidence(loops):
    owners={};walks=[]
    for i,r in enumerate(loops):
        walk=[]
        for aa,bb in zip(r,np.roll(r,-1,axis=0)):
            a,b=tuple(map(int,aa)),tuple(map(int,bb));dx,dy=b[0]-a[0],b[1]-a[1]
            assert abs(dx)+abs(dy)==1
            p=a if dx==1 else (a[0]-1,a[1])if dy==1 else(b[0],b[1]-1)if dx==-1 else b
            owners.setdefault(p,set()).add(i)
            if not walk or walk[-1]!=p:walk.append(p)
        if len(walk)>1 and walk[0]==walk[-1]:walk.pop()
        counts=Counter(walk)
        transitions=[max(abs(a[0]-b[0]),abs(a[1]-b[1]))for a,b in zip(walk,walk[1:]+walk[:1])]
        walks.append({'regionLoopID':i,'centreCount':len(walk),'distinctCentres':len(counts),
            'repeatedNonconsecutiveCentres':sum(v-1 for v in counts.values()),
            'allTransitionsWithin8':all(t<=1 for t in transitions),
            'simpleCycle':len(walk)>=3 and len(counts)==len(walk)and all(t==1 for t in transitions),
            'centresXY':[[x+.5,y+.5]for x,y in walk]})
    return {p:v for p,v in owners.items()if len(v)>1},walks

def audit(name,mask,box,path=None):
    bm=inner(mask);x0,y0,_,_=box;cells={(int(x)+x0,int(y)+y0)for y,x in np.argwhere(bm)}
    loops,branch=boundaries(mask,box);g8,_=graph(cells,True);g4,adj4=graph(cells,False)
    multi,walks=incidence(loops)
    out={'case':name,'definition':'B4=S minus cells whose four axial neighbours are all in S; outside grid is empty',
        'filledCells':int(mask.sum()),'innerOutlineCells':len(cells),'regionBoundaryLoops':len(loops),
        'regionBoundaryTurnDecisions':branch,'G8':g8,'G4Diagnostic':g4,
        'cellsIncidentToSeveralRegionBoundaryLoops':len(multi),
        'multiLoopIncidence':[{ 'xy':list(p),'loopIDs':sorted(v)}for p,v in sorted(multi.items())],
        'boundaryOrderedCentreWalks':walks,
        'innerOutlineCellsXY':[list(p)for p in sorted(cells)],
        'inputPath':str(path)if path else None,'inputSHA256':hashlib.sha256(path.read_bytes()).hexdigest()if path else None}
    if name=='hole_3x3_wall1':
        assert len(loops)==2 and g4['singleClosedPath'] and multi
        start=min(cells);at=start;prior=None;route=[]
        while True:
            route.append((at[0]+.5,at[1]+.5));nxt=sorted(adj4[at]-({prior}if prior else set()))[0]
            prior,at=at,nxt
            if at==start:break
        q=(1.5,1.5);inside=False
        for a,b in zip(route,route[1:]+route[:1]):
            if(a[1]>q[1])!=(b[1]>q[1])and q[0]<(b[0]-a[0])*(q[1]-a[1])/(b[1]-a[1])+a[0]:inside=not inside
        assert inside and not mask[1,1]
        out['centreCycleAsFillBoundary']={'path':route,'holeCentre':list(q),'strictlyInside':inside,
            'originalFilledAtHoleCentre':False,'wouldWronglyFillHoleIfOnlyThisCycleUsed':True}
    return out

rows=[]
for name,p in [('actual43',W/'Shape532/actual43_baseline.bin'),
               ('actual50',W/'Contour534/Math/50_area.bin'),
               ('normalThin',W/'Shape532/thin0_0_baseline.bin')]:
    _,box,_,mask=saved(p);rows.append(audit(name,mask,box,p))
contact=np.array([[1,0],[0,1]],bool)
rows.append(audit('diagonal_contact_2cells',contact,(0,0,2,2)))
hole=np.ones((3,3),bool);hole[1,1]=False
rows.append(audit('hole_3x3_wall1',hole,(0,0,3,3)))
assert rows[-2]['regionBoundaryLoops']==2 and rows[-2]['G8']['singleOpenPath']
summary={'status':'ONE_UNLABELLED_CENTRE_PATH_NOT_A_GENERAL_LOSSLESS_REGION_ADAPTER',
    'newUnityCalls':0,'newCaptures':0,'newProductCode':False,
    'conditionsForSinglePath':'Under an explicitly fixed adjacency: one component, all degrees2 for a closed path; or exactly two degrees1 and other degrees2 for an open path. Start/orientation still need an anchor.',
    'graphChoiceNotImplicit':'G8 and G4 have different results; do not silently remove diagonals or thin cells to force a path.',
    'minimalLosslessDecision':'Keep labelled oriented region boundary loops and per-edge outer/hole/side ownership authoritative; any centreline outline is a separate graph with branch/dual-incidence labels, not the sole fill boundary.',
    'paperReproduction535':False,
    'noNewSelector':'This audit does not choose a pixel simplification policy or port the paper.',
    'rows':rows}
(O/'CORRESPONDENCE537.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
brief=[{'case':q['case'],'cells':q['filledCells'],'outline':q['innerOutlineCells'],
        'boundaryLoops':q['regionBoundaryLoops'],'G8components':q['G8']['components'],
        'G8junctions':q['G8']['junctionCells'],'G8singlePath':q['G8']['singleClosedPath']or q['G8']['singleOpenPath'],
        'G4components':q['G4Diagnostic']['components'],'G4junctions':q['G4Diagnostic']['junctionCells'],
        'G4singlePath':q['G4Diagnostic']['singleClosedPath']or q['G4Diagnostic']['singleOpenPath'],
        'multiLoopCells':q['cellsIncidentToSeveralRegionBoundaryLoops']}for q in rows]
for b,q in zip(brief,rows):
    b['orderedWalksSimple']=all(v['simpleCycle']for v in q['boundaryOrderedCentreWalks'])
    b['orderedWalkNonconsecutiveRepeats']=sum(v['repeatedNonconsecutiveCentres']for v in q['boundaryOrderedCentreWalks'])
(O/'SUMMARY537.json').write_text(json.dumps({'status':summary['status'],'newUnityCalls':0,'newCaptures':0,'newProductCode':False,
    'cases':brief,'decision':summary['minimalLosslessDecision'],'535isPaperReproduction':False},indent=2),encoding='utf-8')
print(json.dumps(brief))
