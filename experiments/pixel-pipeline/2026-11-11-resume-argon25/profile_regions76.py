"""Explicit new hypothesis, not accepted semantic segmentation.

Frozen105 parent partition lost weak pigment. Fit71 line evidence proposes a
source-local FWHM strip, rasterized by positive-area square/strip intersection.
Only original native texels with a positive observed foreground-direction
residual can enter. This does not invent RGB or connect arbitrary endpoints.
Every resulting component is retained, including one-texel components. If this
still oversegments or loses paint, reject it instead of adjusting thresholds.
"""
import numpy as np

def support(rgb,mask,rows,fit,nx,ny,px,py):
 h,w=mask.shape;result=np.zeros((h,w),bool);source=np.full((h,w),-1,np.int32);score=np.full((h,w),-np.inf)
 for j in np.flatnonzero(fit['lineWins']):
  y,x=rows[j];n=np.array([nx[y,x],ny[y,x]],float);t=np.array([-n[1],n[0]]);centre=np.array([px[y,x],py[y,x]],float)+fit['lineOffset'][j]*n;r=fit['lineSigma'][j]*np.sqrt(2*np.log(2));extent=r*abs(n)+.5*abs(t)+.5;lo=np.floor(centre-extent).astype(int);hi=np.ceil(centre+extent).astype(int);amp=fit['lineAmplitude'][j];base=fit['lineBase'][j]
  for yy in range(max(0,lo[1]),min(h-1,hi[1])+1):
   for xx in range(max(0,lo[0]),min(w-1,hi[0])+1):
    if not mask[yy,xx]:continue
    d=np.array([xx,yy])-centre;dn=d@n;dt=d@t
    if abs(dn)>=r+.5*abs(n).sum()or abs(dt)>=.5+.5*abs(t).sum()or(abs(d)>=extent).any():continue
    # Native residual, not fitted output colour. Core detector confidence is
    # already separate; small positive AA residuals are not deleted as noise.
    baseline=base[0]+base[1]*(dn+fit['lineOffset'][j]);evidence=(rgb[yy,xx]-baseline)@amp
    if evidence<=0:continue
    result[yy,xx]=True
    strength=float(np.linalg.norm(amp));canonical=(int(y),int(x));old=source[yy,xx]
    if strength>score[yy,xx]or(strength==score[yy,xx]and(old<0 or canonical<tuple(rows[old]))):score[yy,xx]=strength;source[yy,xx]=j
 return result,source

def children(parent,mask,foreground):
 h,w=mask.shape;labels=parent.copy();next_label=int(parent[mask].max())+1;components=[];seen=np.zeros(mask.shape,bool)
 for y,x in np.argwhere(mask&foreground):
  if seen[y,x]:continue
  p=parent[y,x];todo=[(int(y),int(x))];seen[y,x]=True;coords=[]
  while todo:
   yy,xx=todo.pop();coords.append((yy,xx))
   for dy,dx in[(0,1),(0,-1),(1,0),(-1,0)]:
    y2,x2=yy+dy,xx+dx
    if 0<=y2<h and 0<=x2<w and mask[y2,x2]and foreground[y2,x2]and not seen[y2,x2]and parent[y2,x2]==p:seen[y2,x2]=True;todo.append((y2,x2))
  q=np.asarray(coords);labels[q[:,0],q[:,1]]=next_label;components.append({'label':next_label,'parent':int(p),'coords':q});next_label+=1
 return labels,components

def original_references(rgb,mask,labels,components,source,rows):
 result={};child={c['label']:c for c in components}
 for label in np.unique(labels[mask]):
  coords=np.argwhere(mask&(labels==label))
  if label in child:
   ids=source[coords[:,0],coords[:,1]];ids=ids[ids>=0];seeds=rows[np.unique(ids)]
   # A real native centre pixel is the colour source; fitted baseline/ink is
   # never supplied to the palette. Choose an observed medoid, no RGB average.
   seeds=seeds[mask[seeds[:,0],seeds[:,1]]]
   if not len(seeds):raise ValueError('child without original colour sample')
   colours=rgb[seeds[:,0],seeds[:,1]];median=np.median(colours,axis=0);at=int(np.argmin(((colours-median)**2).sum(1)));y,x=seeds[at]
  else:
   colours=rgb[coords[:,0],coords[:,1]].astype(np.uint8);code=colours[:,0].astype(np.int64)*65536+colours[:,1].astype(np.int64)*256+colours[:,2];values,counts=np.unique(code,return_counts=True);value=values[np.argmax(counts)];at=np.flatnonzero(code==value)[0];y,x=coords[at]
  result[int(label)]={'texel':[int(x),int(y)],'RGB8':rgb[y,x].astype(int).tolist(),'parent':int(child[label]['parent'])if label in child else None}
 return result
