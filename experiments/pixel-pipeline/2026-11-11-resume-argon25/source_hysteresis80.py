"""Grow only existing fine-scale line evidence from cross-scale source seeds.

No invented endpoints or gap filling. Component membership is confidence
propagation, not semantic colour-family identity. Junctions remain junctions.
"""
import numpy as np

def linked(allowed,seeds):
 a=np.asarray(allowed,bool);s=np.asarray(seeds,bool)
 if a.shape!=s.shape or a.ndim!=2 or (s&~a).any():raise ValueError('source seeds must be admitted line evidence')
 seen=np.zeros(a.shape,bool);out=np.zeros_like(seen);h,w=a.shape;components=[]
 for y,x in np.argwhere(a):
  if seen[y,x]:continue
  todo=[(int(y),int(x))];seen[y,x]=True;members=[];strong=False
  while todo:
   yy,xx=todo.pop();members.append((yy,xx));strong|=bool(s[yy,xx])
   for dy,dx in[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
    y2,x2=yy+dy,xx+dx
    if 0<=y2<h and 0<=x2<w and a[y2,x2]and not seen[y2,x2]:seen[y2,x2]=True;todo.append((y2,x2))
  if strong:
   q=np.array(members);out[q[:,0],q[:,1]]=True;components.append(q)
 return out,components
