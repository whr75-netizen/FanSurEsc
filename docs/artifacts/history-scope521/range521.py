"""Representation/cost bounds only. Does not build a growing mask bank."""
from pathlib import Path
from collections import deque,Counter
import json,pickle,time,math,hashlib
import numpy as np
import active516 as G,select516 as S
W=G.ROOT;D=W/'State521';D.mkdir(exist_ok=True)
def key(mask):return hashlib.sha256(mask.tobytes()).hexdigest()
def decompose(mask):
    ys,xs=mask.nonzero();x0,y0=int(xs.min())-1,int(ys.min())-1;x1,y1=int(xs.max())+2,int(ys.max())+2;m=mask[y0:y1,x0:x1];outside=np.zeros_like(m);q=deque([(0,0)]);outside[0,0]=True
    while q:
        x,y=q.popleft()
        for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]:
            xx,yy=x+dx,y+dy
            if 0<=xx<m.shape[1]and 0<=yy<m.shape[0]and not m[yy,xx]and not outside[yy,xx]:outside[yy,xx]=True;q.append((xx,yy))
    holes=np.zeros_like(mask);holes[y0:y1,x0:x1]=~m&~outside;return mask|holes,holes
rows=[]
for i in range(81):
    masks=[G.read_mask(i)]+[np.load(W/'Temporal516'/f'eta-{eta}'/f'{i:03d}.npy')for eta in['0.5','1.0','2.0']];outers={};holes={}
    for m in masks:
        u,h=decompose(m);outers[key(u)]=u;holes[key(h)]=h
    us,hs=list(outers.values()),list(holes.values());du=np.logical_or.reduce([u!=us[0]for u in us]);dh=np.logical_or.reduce([h!=hs[0]for h in hs]);cross=[]
    for dy in[-1,0,1]:
        for dx in[-1,0,1]:
            shifted=np.roll(np.roll(dh,dy,axis=0),dx,axis=1);n=int((du&shifted).sum())
            if n:cross.append({'dx':dx,'dy':dy,'links':n,'kind':'SHARED_CELL'if dx==dy==0 else'SPATIAL_8_NEIGHBOUR'})
    bounds,area=S.areas(i);energy=np.array([[S.spatial(u&~h,area,bounds)['total']for h in hs]for u in us]);residual=energy-energy[:,0,None]-energy[0,None,:]+energy[0,0];valid=np.array([[not np.any(h&~u)for h in hs]for u in us]);invalid=int((~valid).sum());q=len(us)*len(hs);nu,nh=int(du.sum()),int(dh.sum());validResidual=0.
    for u in range(len(us)):
        for v in range(u+1,len(us)):
            for h in range(len(hs)):
                for k in range(h+1,len(hs)):
                    if valid[u,h]and valid[u,k]and valid[v,h]and valid[v,k]:validResidual=max(validResidual,abs(energy[u,h]+energy[v,k]-energy[u,k]-energy[v,h]))
    rows.append({'target':i,'wholeCandidatesObserved':len({key(m)for m in masks}),'outerPatternsObserved':len(us),'holeUnionPatternsObserved':len(hs),'jointObservedProjectionDomain':q,'containedJointDomain':int(valid.sum()),'factorLocalValuesIfIndependent':len(us)+len(hs),'jointValuesIfCoupled':q,'instantaneousSpaceEnergyAdditiveResidualMax':float(np.max(abs(residual))),'validRectangleSpaceEnergyCouplingMax':float(validResidual),'outerHoleCouplingLinks':cross,'containmentInvalidCombinations':invalid,'observedVaryingCellsOuter':nu,'observedVaryingCellsHoleUnion':nh,'binaryCombinationsUpperBoundObservedSupport':str(2**(nu+nh)),'scope':'Observed4-proposal projections only; this is not the full admissible search space, geometry/visibility-certified combinations or a new selector.'})

# Actual frozen80 single-cell variables: spatially independent but linked by
# the SAME whole-arc temporal DP and one cell shared with a hole-arc boundary.
with(W/'State520/current-static.pickle').open('rb')as f:good=pickle.load(f)
with(W/'State520/past-held516.pickle').open('rb')as f:bad=pickle.load(f)
edgeArc={}
for state in[good,bad]:
    for ai,b in state['bindings'].items():
        for s in b['samples']:edgeArc.setdefault(tuple(s['edge']),set()).add(ai)
cells=[]
for y,x in zip(*(good['mask']!=bad['mask']).nonzero()):
    x,y=int(x),int(y);es=[(x,y,x+1,y),(x+1,y,x+1,y+1),(x+1,y+1,x,y+1),(x,y+1,x,y)];ids=set()
    for e in es:ids|=edgeArc.get(e,set())|edgeArc.get(e[2:]+e[:2],set())
    cells.append({'xy':[x,y],'affectedCanonicalArcIds':sorted(ids)})
neighbours=[(a['xy'],b['xy'])for n,a in enumerate(cells)for b in cells[n+1:]if max(abs(a['xy'][0]-b['xy'][0]),abs(a['xy'][1]-b['xy'][1]))<=1];assert not neighbours
actual=json.loads((W/'State520/PREFLIGHT520.json').read_text());arcCosts=[{'old':r['old'],'new':r['new'],'oldSpans':r['oldPixelSpans'],'newSpans':r['newPixelSpans'],'raw':r['raw']}for r in actual['recoverDetail']['rows']]
summary={'posesExamined':81,'observedJointDomainMax':max(r['jointObservedProjectionDomain']for r in rows),'observedContainedJointDomainMax':max(r['containedJointDomain']for r in rows),'observedLocalValuesMaxIfIndependent':max(r['factorLocalValuesIfIndependent']for r in rows),'spaceCoupledTargets':[r['target']for r in rows if r['instantaneousSpaceEnergyAdditiveResidualMax']>1e-9 or r['containmentInvalidCombinations']],'softSpaceCoupledOnValidRectangles':[r['target']for r in rows if r['validRectangleSpaceEnergyCouplingMax']>1e-9],'hardContainmentCoupledTargets':[r['target']for r in rows if r['containmentInvalidCombinations']],'maxSpaceResidual':max(r['instantaneousSpaceEnergyAdditiveResidualMax']for r in rows),'maxValidRectangleSpaceCoupling':max(r['validRectangleSpaceEnergyCouplingMax']for r in rows),'observedVaryingOuterCellsMax':max(r['observedVaryingCellsOuter']for r in rows),'observedVaryingHoleCellsMax':max(r['observedVaryingCellsHoleUnion']for r in rows),'frozenCounterexample':{'cells':cells,'spatial8NeighbourPairs':neighbours,'sameCanonicalOuterArcCouplesCells':len([c for c in cells if 0 in c['affectedCanonicalArcIds']]),'arcCosts':arcCosts,'independentBinarySpatialChoices':len(cells),'possibleBinaryCombinationsBeforeJointCorrespondenceAndVisibilityChecks':2**len(cells),'allCombinationsCertified':False},'denseStateCosts':{'q4096Values':4096,'q4096DoubleMatrixBytes':4096**2*8,'q4096FloydScalarTriples':4096**3,'observedq16DoubleMatrixBytes':16**2*8,'observedq16FloydScalarTriples':16**3},'rows':rows,'noNewBankOrSelectorOrProductCode':True,'scope':'Bounds for existing black-box span/state API, not impossibility of every compressed algorithm.'}
(D/'RANGE521.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items()if k not in['rows','frozenCounterexample']},ensure_ascii=False),flush=True);print(json.dumps(summary['frozenCounterexample']),flush=True)
