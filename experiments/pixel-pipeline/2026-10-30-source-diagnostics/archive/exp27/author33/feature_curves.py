"""Small own implementation of fixed-endpoint, tangent-constrained cubic fitting.
Read Schneider1990/FitCurves.c; external source is not executed/imported.
This module is not the full Superpixelator pixel-span optimizer.
"""
import numpy as np
def unit(v):
    n=np.linalg.norm(v);return v/n if n else v
def evaluate(c,u):
    u=np.asarray(u);return (1-u)[...,None]**3*c[0]+3*(1-u)[...,None]**2*u[...,None]*c[1]+3*(1-u)[...,None]*u[...,None]**2*c[2]+u[...,None]**3*c[3]
def derivatives(c,u):
    u=np.asarray(u);a=3*np.diff(c,axis=0);b=2*np.diff(a,axis=0)
    first=(1-u)[...,None]**2*a[0]+2*(1-u)[...,None]*u[...,None]*a[1]+u[...,None]**2*a[2];second=(1-u)[...,None]*b[0]+u[...,None]*b[1];return first,second
def fit(points,tolerance=.25):
    p=np.asarray(points,float)
    if len(p)<2:return []
    def generate(q,u,left,right):
        b1=3*u*(1-u)**2;b2=3*u*u*(1-u);a=np.stack([b1[:,None]*left,b2[:,None]*right],axis=2).reshape(-1,2);base=((1-u)**3+b1)[:,None]*q[0]+(b2+u**3)[:,None]*q[-1];alpha=np.linalg.lstsq(a,(q-base).reshape(-1),rcond=None)[0]
        if (alpha<=0).any():return None
        return np.array([q[0],q[0]+alpha[0]*left,q[-1]+alpha[1]*right,q[-1]])
    def recurse(q,left,right):
        if len(q)==2:
            length=np.linalg.norm(q[-1]-q[0])/3;return [np.array([q[0],q[0]+left*length,q[-1]+right*length,q[-1]])]
        lengths=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))];u=lengths/lengths[-1];c=generate(q,u,left,right);split=len(q)//2
        for iteration in range(5):
            if c is None:break
            error=np.sum((evaluate(c,u)-q)**2,axis=1);split=int(np.argmax(error))
            if error[split]<=tolerance*tolerance:return [c]
            if iteration==4 or error[split]>4*tolerance*tolerance:break
            values=evaluate(c,u);first,second=derivatives(c,u);delta=values-q;den=np.sum(first*first+delta*second,axis=1)
            if (abs(den[1:-1])<1e-14).any():break
            uu=u.copy();uu[1:-1]-=np.sum(delta[1:-1]*first[1:-1],axis=1)/den[1:-1]
            if (np.diff(uu)<=0).any() or (uu<0).any() or (uu>1).any():break
            u=uu;c=generate(q,u,left,right)
        split=max(1,min(len(q)-2,split));centre=unit(q[split-1]-q[split+1]);return recurse(q[:split+1],left,centre)+recurse(q[split:],-centre,right)
    return recurse(p,unit(p[1]-p[0]),unit(p[-2]-p[-1]))
def sample_curves(curves,spacing=.05):
    points=[]
    for c in curves:
        count=max(8,int(np.linalg.norm(np.diff(c,axis=0),axis=1).sum()/spacing)+1);p=evaluate(c,np.linspace(0,1,count));points.extend(p if not points else p[1:])
    return np.asarray(points)
def marching_paths(field,valid,colour,level,blocked,spacing=.5,origin=(0,0)):
    """Single shared isoline, half-logical-pixel input spacing. Endpoints shared exactly.
    Ambiguous saddle cells are left unconnected; they are fixed topology boundaries.
    """
    h,w=field.shape;edges=[]
    for y in range(h-1):
        for x in range(w-1):
            corners=[(x,y),(x+1,y),(x+1,y+1),(x,y+1)]
            if not all(valid[yy,xx] for xx,yy in corners):continue
            if len({int(colour[yy,xx]) for xx,yy in corners})!=1:continue
            crossings=[];bad=False
            for j in range(4):
                a,b=corners[j],corners[(j+1)%4];key=tuple(sorted((a,b)))
                if key in blocked:bad=True;break
                ga,gb=field[a[1],a[0]],field[b[1],b[0]]
                if (ga>=level)==(gb>=level):continue
                t=(level-ga)/(gb-ga);point=(np.array(a)+(np.array(b)-a)*t)*spacing+origin;crossings.append((key,point))
            if not bad and len(crossings)==2:edges.append(crossings)
    adjacency={};positions={}
    for i,e in enumerate(edges):
        for key,point in e:positions[key]=point;adjacency.setdefault(key,[]).append(i)
    seen=set();paths=[]
    # Degree!=2 endpoints/T nodes are never bridged by fitting.
    starts=sorted(adjacency,key=lambda k:(len(adjacency[k])==2,k))
    for start in starts:
        for index in adjacency[start]:
            if index in seen:continue
            nodes=[start];at=start;edge=index
            while edge not in seen:
                seen.add(edge);e=edges[edge];nextkey=e[1][0] if e[0][0]==at else e[0][0];nodes.append(nextkey)
                if nextkey==start or len(adjacency[nextkey])!=2:break
                options=[i for i in adjacency[nextkey] if i not in seen]
                if not options:break
                at=nextkey;edge=options[0]
            paths.append({'points':np.array([positions[k] for k in nodes]),'closed':nodes[-1]==nodes[0],'nodes':nodes})
    return paths
def winding(poly,points):
    """Signed closed-polygon crossing count, endpoints' common chord cancels in differences."""
    points=np.asarray(points);out=np.zeros(len(points),dtype=int)
    for a,b in zip(poly,np.vstack([poly[1:],poly[:1]])):
        cross=(b[0]-a[0])*(points[:,1]-a[1])-(b[1]-a[1])*(points[:,0]-a[0]);out+=((a[1]<=points[:,1])&(b[1]>points[:,1])&(cross>0));out-=((a[1]>points[:,1])&(b[1]<=points[:,1])&(cross<0))
    return out
def bilinear(field,p):
    # p in logical cells, input nodes at half-cell spacing.
    q=p*2;x=int(np.floor(q[0]));y=int(np.floor(q[1]));x=np.clip(x,0,field.shape[1]-2);y=np.clip(y,0,field.shape[0]-2);tx=np.clip(q[0]-x,0,1);ty=np.clip(q[1]-y,0,1);return (1-tx)*(1-ty)*field[y,x]+tx*(1-ty)*field[y,x+1]+tx*ty*field[y+1,x+1]+(1-tx)*ty*field[y+1,x]
