"""State-bound template placement plus independently tested visibility eligibility.

Input coordinates are top-left logical cells. This is an offline layer adapter,
not a reconstruction of the missing GPU baseline RGBA or complete compositor.
"""
from dataclasses import dataclass
import hashlib,json,math
import numpy as np

@dataclass(frozen=True)
class CachedCell:
    identity:str
    eye:int
    role:int
    reference:tuple
    rgba8:tuple

class StateBoundCluster:
    def __init__(self,source_style_key,state,reference_anchor,cells,style_json=None):
        self.key=source_style_key;self.state=state
        self.style_json=style_json
        self.anchor=np.asarray(reference_anchor,float)
        self.cells=tuple(cells)
        if len({c.identity for c in cells})!=len(cells):raise ValueError('Duplicate source cell identity')
        if len({c.reference for c in cells})!=len(cells):raise ValueError('Overlapping source cells')
    def place(self,key,state,projected_anchor,phase=(0.,0.)):
        if key!=self.key:raise ValueError('Source/style/template binding changed')
        if state!=self.state:raise ValueError('Unregistered pose/lid key form; no open-eye substitution')
        delta=np.asarray(projected_anchor)+phase-self.anchor
        shift=np.floor(delta+.5).astype(int)
        return [dict(cellId=c.identity,eye=c.eye,role=c.role,referenceXY=list(c.reference),
            xy=(np.asarray(c.reference)+shift).tolist(),rgba8=list(c.rgba8))for c in self.cells],shift,delta

def projected_anchor(m):
    """Same projection inputs already used by EyeFeature348; no per-frame readback.

    Invert the saved camera ray basis, not a guessed camera/scale/offset.
    A runtime integration can call full.Project(headMatrix * modelEye.centre).
    """
    xyz=lambda v:np.array([v[k]for k in ('x','y','z')],float)
    head=np.linalg.inv(np.asarray(m['headInverse']).reshape(4,4,order='F'))
    ray=np.column_stack([xyz(m[k])for k in ('rayX','rayY','rayDepth')])
    by_eye={round(c['w']):np.linalg.solve(ray,(head@np.r_[xyz(c),1])[:3]-xyz(m['rayBase']))[:2]for c in m['centres']}
    return np.mean(list(by_eye.values()),axis=0),by_eye

def covered(m):return m[...,0]>0 and m[...,1]>.5 and m[...,3]>1e-6

def known_final_occlusion(d,m,xy,depth):
    """Exact existing final cell hair/brow/body veto. No hair deletion or refill."""
    x,y=xy[0]-m['x'],xy[1]-m['y']
    if depth<=0:return ['no-representative']
    blocks=[]
    for name in ('hair-meta','brow-meta','raw-meta'):
        v=d[name][y,x]
        is_body=8<=round(float(v[1]))<=11
        if covered(v) and v[0]<depth and(name!='raw-meta'or is_body):blocks.append(name)
    return blocks

def representative(d,m,row):
    """Bind cache family to its actual mesh, without fresh normalized Classify.

    Cached iris uses S2 and cached sclera uses S1. They never borrow skin colour
    or one another's colour. Original external skin/lash/hair/brow/body sample
    visibility is retained. Internal iris-vs-sclera role is the registered design
    assignment; it is not recomputed from alpha totals each frame.
    """
    x,y=row['xy'][0]-m['x'],row['xy'][1]-m['y']
    if not(0<=x<m['width']and 0<=y<m['height']):return None
    s=2 if row['role']==1 else 1
    candidates=[];source_count=0;weight_sum=0.;blockers=set()
    for k in range(16):
        xx=x*4+k%4;yy=y*4+3-k//4
        src=d[f'S{s}META'][yy,xx];point=d[f'S{s}POINT'][yy,xx]
        if not(covered(src)and round(float(src[2]))==row['eye']and point[3]>.5):continue
        source_count+=1;weight=float(np.clip(src[3],0,1));depth=float(src[0])
        for name in ('S0META','S3META','S4META','S5META','S6META'):
            o=d[name][yy,xx]
            if not covered(o)or o[0]>=depth:continue
            if name=='S0META' and(round(float(o[2]))!=row['eye']or d['S0POINT'][yy,xx,3]<=.5):continue
            weight*=0 if name=='S6META'else 1-float(np.clip(o[3],0,1))
            blockers.add(name)
        weight_sum+=weight
        if weight>0:candidates.append((((k%4+.5)/4-.5)**2+((k//4+.5)/4-.5)**2,k,depth,weight))
    if not candidates:return dict(support=False,source=s,sourceSamples=source_count,weightSum=weight_sum,sampleBlockers=sorted(blockers))
    distance,k,depth,weight=min(candidates,key=lambda q:(q[0],q[1]))
    return dict(support=True,source=s,sourceSamples=source_count,weightSum=weight_sum,
        sampleBlockers=sorted(blockers),k=k,depth=depth,weight=weight)

def place_visible(cluster,key,state,m,d,final_gate=True):
    if m['blinkWeight']!=0:raise ValueError('Only measured fully open probe state is registered')
    if cluster.style_json is not None and m['styleJson']!=cluster.style_json:raise ValueError('Style cache must be explicitly rebound')
    anchor,centres=projected_anchor(m)
    rows,shift,delta=cluster.place(key,state,anchor)
    for row in rows:
        rep=representative(d,m,row);row['representative']=rep
        blocks=known_final_occlusion(d,m,row['xy'],rep['depth'])if rep and rep.get('support')else ['no-source-support']
        row['knownFinalBlocks']=blocks
        row['visible']=bool(rep and rep.get('support')and(not final_gate or not blocks))
    return rows,shift,anchor,centres

def family_shape(rows,eye,visible_only=False):
    pts=np.array([r['xy']for r in rows if r['eye']==eye and r['role']==1 and(not visible_only or r['visible'])],int)
    if not len(pts):return ()
    return tuple(sorted(map(tuple,pts-pts.min(axis=0))))
