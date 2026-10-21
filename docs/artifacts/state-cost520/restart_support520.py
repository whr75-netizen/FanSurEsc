"""Inspect a tempting restricted bank; never treat it as a valid selector.

Combining outer envelopes and holes here tests state representation/support
only. New combinations are NOT certified for geometry/depth/physical visibility.
"""
from collections import deque
import itertools,json,hashlib
import numpy as np
import active516 as G
D=G.ROOT/'State520';events=json.loads((G.ROOT/'Region519/GEOMETRY_EVENT_INTERVALS519.json').read_text());rows=[]
def hashmask(m):return hashlib.sha256(m.tobytes()).hexdigest()
def regions(mask):
    ys,xs=np.where(mask);x0,y0=max(0,int(xs.min())-1),max(0,int(ys.min())-1);x1,y1=min(480,int(xs.max())+2),min(272,int(ys.max())+2);m=mask[y0:y1,x0:x1];outside=np.zeros_like(m);queue=deque([(0,0)]);outside[0,0]=True
    while queue:
        x,y=queue.popleft()
        for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]:
            xx,yy=x+dx,y+dy
            if 0<=xx<m.shape[1]and 0<=yy<m.shape[0]and not m[yy,xx]and not outside[yy,xx]:outside[yy,xx]=True;queue.append((xx,yy))
    holes=np.zeros_like(mask);holes[y0:y1,x0:x1]=~m&~outside;return mask|holes,holes
for e in events['rows']:
    i=e['target'];masks=[G.read_mask(i)]+[np.load(G.ROOT/'Temporal516'/f'eta-{eta}'/f'{i:03d}.npy')for eta in['0.5','1.0','2.0']];outer={};holes={};seen={hashmask(m)for m in masks}
    for m in masks:
        u,h=regions(m);outer[hashmask(u)]=u;holes[hashmask(h)]=h
    missing=[]
    for uk,u in outer.items():
        for hk,h in holes.items():
            if np.any(h&~u):continue
            combo=u&~h;key=hashmask(combo)
            if key not in seen:missing.append({'outerSHA256':uk,'holesSHA256':hk,'combinationSHA256':key,'pixelCounts':{'outer':int(u.sum()),'holes':int(h.sum()),'combined':int(combo.sum())},'physicalAndSourceEligibility':'UNVERIFIED'})
    rows.append({'target':i,'sourceGeometryEvent':e['events'],'existingWholeMasks':len(seen),'outerAlternatives':len(outer),'holeAlternatives':len(holes),'missingStructurallyContainedCombinations':missing,'counterexampleScope':'Whole-drawing bank is not proven closed for component-only marginal restart. Structural containment is not a visibility/admissibility pass.'})
out={'checkedTargets':[r['target']for r in rows],'rows':rows,'existingSelectorStateRepresentation':'select516.Selector.solve returns one previous spans/active/rings/signature; it retains no values for nonwinning alternatives.','proposed4MaskReuseBankNotAdopted':True,'newSelectionOrTemporalWalkRun':False,'newUnityCalls':0,'missingCombinationEvents':[r['target']for r in rows if r['missingStructurallyContainedCombinations']]}
(D/'RESTART_SUPPORT520.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'missingCombinationEvents':out['missingCombinationEvents'],'counts':[{'target':r['target'],'outer':r['outerAlternatives'],'holes':r['holeAlternatives'],'missing':len(r['missingStructurallyContainedCombinations'])}for r in rows],'bankAdopted':False}))
