"""Curve-conditioned joint visibility; no unconditional part protection.
All three source parts compete at the same original pigment witness. A curve
candidate may replace an allocated iris/white only when lid's lower visible
contribution strictly exceeds every other part/canvas upper contribution.
Unordered depth ties are intervals, not array-order priorities.
"""
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'live-curve106'))
from curve_reference106 import intersects,distance
F=np.float32

def contributions(layers,visibility,y,x):
    lo=visibility[1:4,y,x,0].copy();hi=visibility[1:4,y,x,1].copy();z=layers[1:4,1,y,x,0].copy()
    lower=lo.copy();upper=hi.copy();canvasLo=F(1);canvasHi=F(1)
    for p in range(3):
        canvasLo=F(canvasLo*F(1-hi[p]));canvasHi=F(canvasHi*F(1-lo[p]))
        for q in range(3):
            if p==q or z[q]<=0 or hi[q]<=0:continue
            if z[q]<F(z[p]-F(3e-5)):
                lower[p]=F(lower[p]*F(1-hi[q]));upper[p]=F(upper[p]*F(1-lo[q]))
            elif abs(F(z[q]-z[p]))<=F(3e-5):lower[p]=F(lower[p]*F(1-hi[q]))
    return np.r_[lower,canvasLo],np.r_[upper,canvasHi]

def cell(segments,layers,vis,colour,identity,decision,x,y,scale=4):
    touched={int(round(s[0,3]))for s in segments if intersects(s[0,:2],s[1,:2],[x,y])}
    if not touched:return colour.copy(),identity.copy(),decision.copy(),np.zeros(4,np.float32)
    bestD=np.finfo(np.float32).max;bestA=F(-1);chosen=None;tied=False;supported=set();raw=False;blocked=False;unknown=False
    for yy in range(y*scale,y*scale+scale):
        for xx in range(x*scale,x*scale+scale):
            v=vis[3,yy,xx];owner=int(round(layers[3,1,yy,xx,2]))
            if v[0]<=0 or v[0]!=v[1]or owner not in touched:continue
            raw=True;lo,hi=contributions(layers,vis,yy,xx)
            if not(lo[2]>max(hi[0],hi[1],hi[3])):
                blocked|=any(lo[q]>hi[2]for q in [0,1,3]);unknown|=not any(lo[q]>hi[2]for q in [0,1,3]);continue
            supported.add(owner);point=np.array([xx+.5,yy+.5],np.float32)/F(scale)
            d=min(distance(point,s[0,:2],s[1,:2])for s in segments if round(s[0,3])==owner);alpha=lo[2]
            if d<bestD or(d==bestD and alpha>bestA):bestD=d;bestA=alpha;chosen=(yy,xx,owner);tied=False
            elif d==bestD and alpha==bestA and chosen is not None:
                if not np.array_equal(layers[3,0,yy,xx,:3],layers[3,0,chosen[0],chosen[1],:3]):tied=True
    flag=4 if chosen is None and raw and blocked and not unknown else-4 if chosen is None and raw else-1 if chosen is None else-3 if len(supported)>1 else-2 if tied else 3
    audit=np.array([flag,int(raw),0,float(bestD)if chosen is not None else 0],np.float32)
    if flag!=3:return colour.copy(),identity.copy(),decision.copy(),audit
    yy,xx,owner=chosen;out=layers[3,0,yy,xx].copy();out[3]=1
    ids=np.array([6,owner,layers[3,1,yy,xx,0],layers[3,3,yy,xx,2]],np.float32)
    dec=np.array([6,107,*decision[2:]],np.float32);audit[2]=yy*layers.shape[3]+xx+1
    return out,ids,dec,audit

def apply(segments,layers,vis,colour,identity,decision,scale=4):
    h,w=layers.shape[2:4];out=colour.copy();ids=identity.copy();dec=decision.copy();audit=np.zeros_like(dec)
    assert scale in [4,8]and h%scale==0 and w%scale==0 and len(colour)==(h//scale)*(w//scale)
    for y in range(h//scale):
        for x in range(w//scale):
            k=y*(w//scale)+x;out[k],ids[k],dec[k],audit[k]=cell(segments,layers,vis,colour[k],identity[k],decision[k],x,y,scale)
    return out,ids,dec,audit

def tests():
    a=np.zeros((4,5,4,4,4),np.float32);v=np.zeros((4,4,4,4),np.float32);s=np.array([[[.1,.2,5,1],[.9,.2,5,1]]],np.float32)
    a[3,0,0,0]=[.2,.1,.08,1];a[3,1,0,0]=[5,7,1,1];a[3,3,0,0,2]=1;v[3,0,0,:2]=1
    c=np.array([[.1,.4,.7,1]],np.float32);i=np.array([[1,1,6,1]],np.float32);d=np.array([[1,0,0,0]],np.float32)
    out,ids,_,audit=apply(s,a,v,c,i,d);assert audit[0,0]==3 and ids[0,0]==6
    a[1,0,0,0]=c[0];a[1,1,0,0]=[4,2,1,1];v[1,0,0,:2]=1
    out,ids,_,audit=apply(s,a,v,c,i,d);assert audit[0,0]==4 and np.array_equal(out,c)
    a[1,1,0,0,0]=5
    out,ids,_,audit=apply(s,a,v,c,i,d);assert audit[0,0]==-4 and np.array_equal(out,c)
    v[1,0,0]=0;v[3,0,0,:2]=0
    out,ids,_,audit=apply(s,a,v,c,i,d);assert audit[0,0]==-1 and np.array_equal(out,c)
    return {'foregroundLidCanReplacePriorIris':True,'foregroundIrisNotOverwritten':True,'depthTieNotArrayOrder':True,'noUnsupportedFill':True}
if __name__=='__main__':print(tests())
