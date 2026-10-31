"""Small exhaustive joint glyph allocation; no Unity/product dependencies.

The target glyphs come from an existing Template and an observed source part.
All parts are mandatory; no colour/area vote deletes one. Correction radius is
an exposed diagnostic budget, not a universal eye-size or art-quality constant.
"""
from itertools import product
import copy
import numpy as np

def connected_components(points):
    left=set(map(tuple,points));groups=[]
    while left:
        todo=[left.pop()];g=set(todo)
        while todo:
            x,y=todo.pop()
            for p in[(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if p in left:left.remove(p);g.add(p);todo.append(p)
        groups.append(g)
    return groups

def source_distance(p,path):
    p=np.array(p,float);poly=np.array(path['points'],float)
    if path.get('region'):
        inside=False;x,y=p
        for a,b in zip(poly,np.roll(poly,-1,axis=0)):
            if(a[1]>y)!=(b[1]>y)and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
        if inside:return 0.
    a=poly if path.get('closed')else poly[:-1];b=np.roll(poly,-1,axis=0)if path.get('closed')else poly[1:];d=b-a
    t=np.clip(np.sum((p-a)*d,axis=1)/np.maximum(np.sum(d*d,axis=1),1e-30),0,1)
    return float(np.linalg.norm(p-a-t[:,None]*d,axis=1).min())

def glyph_signature(rows):
    points=np.array([r['xy']for r in rows]);origin=points.min(axis=0)
    return tuple(sorted((r['id'],r['part'],tuple(np.array(r['xy'])-origin),tuple(r['rgba8']))for r in rows))

def enumerate_joint(glyphs,source_paths,budget,external,source_visible):
    """Simultaneous rigid-part alternatives, source/curve error and exact audit.

    All parts use the same displacement set. No iris-first/lid-first rule is
    present. Glyph-internal adjacency, colours and identities remain exact.
    source_visible is per frozen frame/token; external tests destination depth.
    Original external occlusion can never be rescued by moving a token.
    """
    parts=sorted(glyphs)
    moves=[(x,y)for x in range(-budget,budget+1)for y in range(-budget,budget+1)if abs(x)+abs(y)<=budget]
    original=[r for p in parts for r in glyphs[p]]
    original_components=len(connected_components([r['xy']for r in original]))
    original_centres={p:np.mean([r['xy']for r in glyphs[p]],axis=0)for p in parts}
    original_box=np.ptp([r['xy']for r in original],axis=0)+1
    trials=[];feasible=[]
    for shifts in product(moves,repeat=len(parts)):
        mapped={p:np.array(t,int)for p,t in zip(parts,shifts)};rows=[];violations=[]
        for p in parts:
            for src in glyphs[p]:
                r=copy.deepcopy(src);r['xy']=(np.array(src['xy'])+mapped[p]).tolist();r['partShift']=mapped[p].tolist();rows.append(r)
        at={}
        for r in rows:at.setdefault(tuple(r['xy']),[]).append(r['id'])
        clashes=[dict(xy=list(xy),ids=ids)for xy,ids in at.items()if len(ids)>1]
        if clashes:violations.append('internal part collision')
        if len(connected_components([r['xy']for r in rows]))!=original_components:violations.append('whole glyph connectivity changed')
        centres={p:original_centres[p]+mapped[p]for p in parts}
        if 'upper-lid'in centres and 'iris'in centres and centres['upper-lid'][1]>centres['iris'][1]:violations.append('upper-lid moved below iris centre')
        # Actual hair/brow/body remains a hard visibility constraint. A hidden
        # source token is not moved to a visible destination to refill the eye.
        blocked=[]
        for r in rows:
            for frame,visibility in source_visible.items():
                if visibility[r['id']]:
                    veto=external(frame,r,r['xy'])
                    if veto:blocked.append(dict(frame=frame,id=r['id'],xy=r['xy'],veto=veto))
        if blocked:violations.append('would hide an originally visible source token behind external layer')
        # Per-PART normalization avoids forcing all displacement into the small
        # lid merely because it has fewer pixels. No RGB average is used.
        movement=float(sum(np.dot(t,t)for t in mapped.values()))
        curve=0.
        for p in parts:
            path=source_paths.get(p)
            if path is not None:
                curve+=float(np.mean([source_distance(np.array(r['xy'])+[.75,.25],path)**2 for r in rows if r['part']==p]))
        relative=float(sum(np.dot(mapped[a]-mapped[b],mapped[a]-mapped[b])for i,a in enumerate(parts)for b in parts[i+1:]))
        box=np.ptp([r['xy']for r in rows],axis=0)+1
        box_growth=int(np.prod(box)-np.prod(original_box))
        objective=(movement,curve,relative,box_growth,tuple(map(tuple,shifts)))
        entry=dict(shifts={p:mapped[p].tolist()for p in parts},movementPerPart=movement,curveError=curve,
            relativeCentreError=relative,boundingAreaChange=box_growth,collisions=clashes,externalBlocks=blocked,
            violations=violations,feasible=not violations)
        trials.append(entry)
        if not violations:feasible.append((objective,entry,rows))
    feasible.sort(key=lambda q:q[0])
    return dict(budgetL1Cells=budget,partTargetCounts={p:len(glyphs[p])for p in parts},
        enumerated=len(trials),feasible=len(feasible),trials=trials,
        selected=feasible[0][1]if feasible else None,rows=feasible[0][2]if feasible else [],
        pareto=[v[1]for v in feasible[:8]])
