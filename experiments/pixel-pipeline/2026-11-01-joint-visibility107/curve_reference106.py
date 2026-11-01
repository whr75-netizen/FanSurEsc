"""CPU reference for the live curve kernel; no target pose or cell budget."""
import numpy as np
F=np.float32

def intersects(a,b,p):
    a=np.asarray(a,dtype=np.float32);b=np.asarray(b,dtype=np.float32);p=np.asarray(p,dtype=np.float32)
    lo=F(0);hi=F(1);d=b-a
    for axis in (0,1):
        if d[axis]==0:
            if a[axis]<p[axis]or a[axis]>p[axis]+1:return False
        else:
            x=F((p[axis]-a[axis])/d[axis]);y=F((p[axis]+1-a[axis])/d[axis])
            lo=F(max(lo,min(x,y)));hi=F(min(hi,max(x,y)))
    return hi>=lo and np.dot(d,d)>0

def distance(p,a,b):
    d=b-a;den=F(max(F(np.dot(d,d)),F(1e-30)));t=F(np.clip(F(np.dot(p-a,d))/den,0,1));r=a+F(t)*d-p
    return F(np.dot(r,r))

def cell(segments,layers,vis,colour,identity,decision,x,y):
    touched={int(round(s[0,3]))for s in segments if intersects(s[0,:2],s[1,:2],[x,y])}
    if not touched:return colour.copy(),identity.copy(),decision.copy(),np.zeros(4,np.float32),-1
    bestD=np.finfo(np.float32).max;bestA=F(-1);chosen=None;tied=False;supported=set()
    for yy in range(y*4,y*4+4):
        for xx in range(x*4,x*4+4):
            v=vis[3,yy,xx];owner=int(round(layers[3,1,yy,xx,2]))
            if v[0]<=0 or v[0]!=v[1]or owner not in touched:continue
            supported.add(owner);p=np.array([xx+.5,yy+.5],np.float32)*F(.25)
            d=min(distance(p,s[0,:2],s[1,:2])for s in segments if round(s[0,3])==owner);alpha=v[0]
            if d<bestD or(d==bestD and alpha>bestA):bestD=d;bestA=alpha;chosen=(yy,xx,owner);tied=False
            elif d==bestD and alpha==bestA and chosen is not None:
                if not np.array_equal(layers[3,0,yy,xx,:3],layers[3,0,chosen[0],chosen[1],:3]):tied=True
    audit=np.array([1,int(chosen is not None),0,float(bestD)if chosen is not None else 0],np.float32)
    role=round(float(identity[0]));flag=2 if role in(1,4)else-1 if chosen is None else-3 if len(supported)>1 else-2 if tied else 3
    audit[0]=flag
    if flag!=3:return colour.copy(),identity.copy(),decision.copy(),audit,-1
    yy,xx,owner=chosen;out=layers[3,0,yy,xx].copy();out[3]=1
    ident=np.array([6,owner,layers[3,1,yy,xx,0],layers[3,3,yy,xx,2]],np.float32)
    dec=np.array([6,106,*decision[2:]],np.float32);audit[2]=yy*layers.shape[3]+xx+1
    return out,ident,dec,audit,yy*layers.shape[3]+xx

def apply(segments,layers,vis,colour,identity,decision):
    h,w=layers.shape[2:4];out=colour.copy();ids=identity.copy();dec=decision.copy();audit=np.zeros_like(dec)
    for y in range(h//4):
        for x in range(w//4):
            k=y*(w//4)+x;out[k],ids[k],dec[k],audit[k],_=cell(segments,layers,vis,colour[k],identity[k],decision[k],x,y)
    return out,ids,dec,audit

def tests():
    layers=np.zeros((4,5,8,8,4),np.float32);v=np.zeros((4,8,8,4),np.float32)
    segment=np.array([[[.1,.2,5,1],[1.8,.2,5,1]]],np.float32)
    for x in range(8):layers[3,0,0,x]=[.2,.1,.08,1];layers[3,1,0,x]=[5,7,1,1];layers[3,3,0,x,2]=1;v[3,0,x,:2]=1
    c=np.zeros((4,4),np.float32);i=c.copy();d=c.copy();a,ids,dd,audit=apply(segment,layers,v,c,i,d)
    assert(audit[:,0]==3).sum()==2 and(ids[:,0]==6).sum()==2
    i[0]=[1,1,5,1];c[0]=[.1,.4,.7,1]
    a,ids,dd,audit=apply(segment,layers,v,c,i,d);assert audit[0,0]==2 and np.array_equal(a[0],c[0])and np.array_equal(ids[0],i[0])
    v[:]=0;a,ids,dd,audit=apply(segment,layers,v,c,i,d);assert(audit[:,0]==-1).sum()==1 and(ids[:,0]==6).sum()==0
    long=np.array([[[.1,.2],[2.8,.2]]],np.float32)
    assert sum(intersects(*long[0],[x,0])for x in range(4))>sum(intersects(*segment[0,:,:2],[x,0])for x in range(4))
    return {'liveGeometryChangesSupport':True,'irisWhiteProtected':True,'noUnsupportedFill':True,'noPixelBudget':True}
if __name__=='__main__':print(tests())
