"""Precision-bounded h-minima markers -> source-native geodesic labelling.

This implements morphological reconstruction by erosion and marker flooding.
The h-minima stage is morphological reconstruction. The subsequent positive
additive graph distance is our diagnostic choice, NOT Beucher's watershed.
It does not join open contour endpoints. A partition is induced by a full graph,
not by treating independently detected edge strokes as closed region outlines.
The only h is a conservative bound on RGB8 half-code derivative uncertainty.
It is not selected by minimising the observed region count. RGB is unchanged.
"""
import heapq
import numpy as np
from graph_regions104 import gaussian


def topography(rgb,mask,sigma=.8):
    rgb=np.asarray(rgb,dtype=float);mask=np.asarray(mask,dtype=bool)
    support=gaussian(mask,sigma)
    signal=gaussian(rgb*mask[...,None],sigma)/np.maximum(support[...,None],1e-30)
    # Central differences, one-sided at support boundaries. The L1 norm of
    # each derivative stencil is <=2, so a half-code input error yields <=1
    # code per channel/axis. A six-component norm is 1-Lipschitz: sqrt(6).
    derivatives=[]
    for axis in (0,1):
        lo=np.take(signal,np.maximum(np.arange(mask.shape[axis])-1,0),axis=axis)
        hi=np.take(signal,np.minimum(np.arange(mask.shape[axis])+1,mask.shape[axis]-1),axis=axis)
        ml=np.take(mask,np.maximum(np.arange(mask.shape[axis])-1,0),axis=axis)
        mh=np.take(mask,np.minimum(np.arange(mask.shape[axis])+1,mask.shape[axis]-1),axis=axis)
        a=np.where(ml[...,None],lo,signal);b=np.where(mh[...,None],hi,signal)
        divisor=(ml.astype(float)+mh.astype(float))[...,None]
        derivatives.append((b-a)/np.maximum(divisor,1))
    magnitude=np.linalg.norm(np.concatenate(derivatives,axis=-1),axis=-1)
    # Canonical 16.16 RGB-code units avoid arithmetic-order-sized minima and
    # rotation-dependent equal-path decisions. Error <= .5/65536 code.
    magnitude=np.rint(magnitude*65536)/65536
    magnitude[~mask]=np.inf
    # A minimum-to-saddle difference has errors at BOTH endpoints. This is a
    # conservative quantisation bound, not a perceptual/art contrast threshold.
    return magnitude,float(np.ceil(2*np.sqrt(6)*65536)/65536)


def neighbours(i,width,height):
    y,x=divmod(i,width)
    if x:yield i-1
    if x+1<width:yield i+1
    if y:yield i-width
    if y+1<height:yield i+width


def reconstruct_erosion(g,mask,h):
    """out[i] = min_j max(g[j]+h, max(g along a valid j->i path))."""
    H,W=mask.shape;n=H*W
    if n>1100000:raise ValueError('native texel budget exceeded')
    valid=mask.ravel();floor=g.ravel();out=floor+h
    queue=[(float(out[i]),int(i))for i in np.flatnonzero(valid)]
    heapq.heapify(queue)
    while queue:
        level,p=heapq.heappop(queue)
        if level!=out[p]:continue
        for q in neighbours(p,W,H):
            if not valid[q]:continue
            candidate=max(level,floor[q])
            if candidate<out[q]:
                out[q]=candidate;heapq.heappush(queue,(candidate,q))
    return out.reshape(H,W)


def minima(g,mask):
    H,W=mask.shape;valid=mask.ravel();z=g.ravel();labels=np.full(H*W,-1,np.int32)
    nextLabel=0;markers=np.full(H*W,-1,np.int32)
    for p in np.flatnonzero(valid):
        if labels[p]>=0:continue
        todo=[int(p)];labels[p]=nextLabel;region=[];minimal=True
        while todo:
            q=todo.pop();region.append(q)
            for r in neighbours(q,W,H):
                if not valid[r]:continue
                if z[r]<z[q]:minimal=False
                elif z[r]==z[q]and labels[r]<0:labels[r]=nextLabel;todo.append(r)
        if minimal:markers[region]=nextLabel
        nextLabel+=1
    unique=np.unique(markers[markers>=0]);result=np.full_like(markers,-1)
    selected=markers>=0;result[selected]=np.searchsorted(unique,markers[selected])
    return result.reshape(H,W),len(unique)


def flood(g,mask,markers,h):
    """Positive additive graph distance, with explicit equal-distance ties.

    Exact different-marker ties are -2, not silently won by coordinate order.
    No missing-source texel is assigned to a region. Seeds retain identity.
    """
    H,W=mask.shape;valid=mask.ravel();z=g.ravel();seed=markers.ravel()
    distance=np.full(H*W,np.iinfo(np.int64).max,np.int64)
    label=np.full(H*W,-1,np.int32);queue=[]
    for p in np.flatnonzero(seed>=0):
        label[p]=seed[p];distance[p]=0
        queue.append((0,int(p)))
    heapq.heapify(queue)
    while queue:
        cost,p=heapq.heappop(queue)
        if cost!=distance[p]:continue
        for q in neighbours(p,W,H):
            if not valid[q]or seed[q]>=0:continue
            edge=65536+int(round(32768*(z[p]+z[q])/h))
            candidate=cost+edge
            if candidate<distance[q]:
                distance[q]=candidate;label[q]=label[p]
                heapq.heappush(queue,(candidate,q))
            elif candidate==distance[q]and label[q]!=label[p]:
                label[q]=-2
    label[~valid]=-1
    return label.reshape(H,W),distance.reshape(H,W)


def segment(rgb,mask,sigma=.8):
    g,h=topography(rgb,mask,sigma);reconstructed=reconstruct_erosion(g,mask,h)
    markers,n=minima(reconstructed,mask)
    labels,_=flood(reconstructed,mask,markers,h)
    return {'labels':labels,'markers':markers,'markerCount':n,'gradient':g,
            'reconstructed':reconstructed,'h':h,'sigma':sigma}
