"""Observed pigment-to-background constraints, not internal AA colour bins.

Support identity is an input. A flank inside any observed pigment support is
not background, and therefore cannot impose a pigment-vs-background order.
Output addresses encode source values, never semantic regions or light Q.
"""
import numpy as np
from audit_polarity76 import luminance

def constraints(rgb,mask,foreground,islands,rows,flanks):
 rgb=np.asarray(rgb,np.uint8);mask=np.asarray(mask,bool);fg=np.asarray(foreground,bool);islands=np.asarray(islands);rows=np.asarray(rows,int);flanks=np.asarray(flanks,int)
 if rgb.shape!=mask.shape+(3,)or fg.shape!=mask.shape or islands.shape!=mask.shape or rows.ndim!=2 or rows.shape[1]!=2 or flanks.shape!=(len(rows),2,2)or(fg&~mask).any():raise ValueError('observed source support/paired profile ABI')
 colours,inv,counts=np.unique(rgb[mask],axis=0,return_inverse=True,return_counts=True);index=np.full(mask.shape,-1,int);index[mask]=inv;y=luminance(colours);orders=set();accepted=[];rejected={'centre-not-observed-pigment':0,'flank-outside-source':0,'flank-inside-pigment':0,'different-source-island':0,'not-a-two-sided-native-extremum':0};height,width=mask.shape
 for row,ends in zip(rows,flanks):
  yy,xx=map(int,row)
  if not(0<=xx<width and 0<=yy<height)or not fg[yy,xx]:rejected['centre-not-observed-pigment']+=1;continue
  if any(x<0 or yy2<0 or x>=width or yy2>=height or not mask[yy2,x]for x,yy2 in ends):rejected['flank-outside-source']+=1;continue
  if any(fg[yy2,x]for x,yy2 in ends):rejected['flank-inside-pigment']+=1;continue
  if any(islands[yy2,x]!=islands[yy,xx]for x,yy2 in ends):rejected['different-source-island']+=1;continue
  a=index[yy,xx];b,c=[index[yy2,x]for x,yy2 in ends];sign=-1 if y[a]<min(y[b],y[c])else 1 if y[a]>max(y[b],y[c])else 0
  if not sign:rejected['not-a-two-sided-native-extremum']+=1;continue
  for other in [b,c]:orders.add((int(a),int(other))if sign<0 else(int(other),int(a)))
  accepted.append((xx,yy,int(ends[0,0]),int(ends[0,1]),int(ends[1,0]),int(ends[1,1]),sign))
 return {'colours':colours,'counts':counts,'index':index,'orders':orders,'accepted':accepted,'rejected':rejected}

def field_ranges(rgb,mask,regions,index,colours):
 # Preserve the observed range of a nonconstant connected field without
 # insisting that every adjacent AA code become a separate colour address.
 y=luminance(colours);n=int(regions.max())+1;lo=np.full(n,np.inf);hi=np.full(n,-np.inf);np.minimum.at(lo,regions[mask],y[index[mask]]);np.maximum.at(hi,regions[mask],y[index[mask]]);ranges=set()
 for k in range(1,n):
  ids=np.unique(index[mask&(regions==k)])
  if not len(ids):continue
  a=int(ids[np.argmin(y[ids])]);b=int(ids[np.argmax(y[ids])])
  if y[a]<y[b]:ranges.add((a,b))
  elif len(ids)>1:ranges.add((int(ids[0]),int(ids[-1])))
 return ranges
