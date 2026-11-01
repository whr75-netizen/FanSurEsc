"""Source UV graph partition, independent of lighting, palettes and screen grids.

Independent implementation of Felzenszwalb/Huttenlocher (2004), Algorithm 1.
No author code is executed/imported. No minimum-size post merge is performed.
4-neighbour connectivity is deliberate: every returned region has a 4-connected
source support. Edge ordering is stable; equal edges do not define a new policy.
RGB8 Gaussian detection signal is never a rendered/output colour. Alpha, source
texel coordinates, material and primitive identity remain separate provenance.
"""
import numpy as np


def gaussian(a, sigma=.8):
    radius=int(np.ceil(3*sigma)); x=np.arange(-radius,radius+1)
    kernel=np.exp(-.5*(x/sigma)**2); kernel/=kernel.sum()
    out=np.asarray(a,dtype=np.float64)
    for axis in (0,1):
        pad=[(0,0)]*out.ndim; pad[axis]=(radius,radius)
        source=np.pad(out,pad,mode='edge'); result=np.zeros_like(out)
        for i,w in enumerate(kernel):
            sl=[slice(None)]*out.ndim; sl[axis]=slice(i,i+out.shape[axis])
            result+=w*source[tuple(sl)]
        out=result
    return out


def graph(rgb, mask, sigma=.8):
    rgb=np.asarray(rgb); mask=np.asarray(mask,dtype=bool)
    if rgb.shape!=(*mask.shape,3): raise ValueError('RGB/mask shape mismatch')
    if mask.size>1100000: raise ValueError('native source texel budget exceeded')
    if sigma<0 or not np.isfinite(sigma): raise ValueError('invalid detection sigma')
    source=rgb.astype(np.float64)
    if sigma:
        support=gaussian(mask,sigma)
        source=gaussian(source*mask[...,None],sigma)/np.maximum(support[...,None],1e-30)
    ids=np.full(mask.shape,-1,np.int32); ids[mask]=np.arange(int(mask.sum()))
    aa=[];bb=[];ww=[]
    for sa,sb in [((slice(None),slice(None,-1)),(slice(None),slice(1,None))),
                  ((slice(None,-1),slice(None)),(slice(1,None),slice(None)))]:
        valid=mask[sa]&mask[sb]
        aa.append(ids[sa][valid]);bb.append(ids[sb][valid])
        ww.append(np.linalg.norm(source[sa][valid]-source[sb][valid],axis=1))
    a=np.concatenate(aa);b=np.concatenate(bb);w=np.concatenate(ww)
    order=np.argsort(w,kind='stable')
    return {'a':a[order],'b':b[order],'w':w[order],'mask':mask,'sigma':sigma,
            'n':int(mask.sum()),'edgeBytes':int(a.nbytes+b.nbytes+w.nbytes)}


def partition(g, k=300.):
    if k<0 or not np.isfinite(k): raise ValueError('invalid observation scale')
    n=g['n']; parent=list(range(n)); size=[1]*n; threshold=[float(k)]*n
    def find(x):
        root=x
        while parent[root]!=root: root=parent[root]
        while parent[x]!=x:
            after=parent[x];parent[x]=root;x=after
        return root
    for a,b,w in zip(g['a'].tolist(),g['b'].tolist(),g['w'].tolist()):
        ra=find(a);rb=find(b)
        if ra!=rb and w<=threshold[ra] and w<=threshold[rb]:
            if size[ra]<size[rb]:ra,rb=rb,ra
            parent[rb]=ra;size[ra]+=size[rb]
            threshold[ra]=w+k/size[ra]
    roots=np.fromiter((find(i)for i in range(n)),dtype=np.int32,count=n)
    _,inverse=np.unique(roots,return_inverse=True)
    labels=np.full(g['mask'].shape,-1,np.int32);labels[g['mask']]=inverse
    return labels


def same_partition(a,b,mask):
    a=a[mask].ravel();b=b[mask].ravel()
    pairs=np.unique(np.column_stack([a,b]),axis=0)
    return len(pairs)==len(np.unique(a))==len(np.unique(b))


def boundary(labels,mask):
    result=np.zeros(mask.shape,bool)
    for sa,sb in [((slice(None),slice(None,-1)),(slice(None),slice(1,None))),
                  ((slice(None,-1),slice(None)),(slice(1,None),slice(None)))]:
        edge=mask[sa]&mask[sb]&(labels[sa]!=labels[sb])
        result[sa]|=edge;result[sb]|=edge
    return result


def stats(labels,mask):
    sizes=np.bincount(labels[mask]);edge=boundary(labels,mask)
    return {'regions':len(sizes),'singletons':int((sizes==1).sum()),
            'regionsUnder8Texels':int((sizes<8).sum()),'boundaryTexels':int(edge.sum()),
            'largestRegions':sorted(sizes.tolist(),reverse=True)[:12]}
