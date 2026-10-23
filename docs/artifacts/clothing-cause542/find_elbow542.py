from pathlib import Path
import numpy as np,struct,json
from model542 import load
O=Path(__file__).resolve().parent;R=O.parent/'Common540/FullLoop540';bones,v,bi,bw,indices,tags=load();names=[h for n,h in bones]
upper=[i for i,n in enumerate(names)if n=='LeftUpperArm'];lower=[i for i,n in enumerate(names)if n=='LeftLowerArm'];wu=(bw*np.isin(bi,upper)).sum(axis=1);wl=(bw*np.isin(bi,lower)).sum(axis=1);elbow=(wu>0)&(wl>0)
mapping={};elbowGlobal=[]
for sm,(ids,tg)in enumerate(zip(indices,tags)):
 for pr,(tri,tag)in enumerate(zip(ids,tg)):
  mapping[int(tag[2])]={'sm':sm,'primitive':pr,'part':int(tag[0]),'joint':int(tag[1]),'elbow':bool(elbow[tri].any()),'leftWeight':float((wu[tri]+wl[tri]).mean())}
  if sm==3 and tag[0]==2 and elbow[tri].any():elbowGlobal.append(int(tag[2]))
def read(p):
 b=p.read_bytes();w,h,x,y=struct.unpack_from('<4i',b);a=np.zeros((272,480,4),np.float32);a[y:y+h,x:x+w]=np.frombuffer(b,'<f4',w*h*4,16).reshape(h,w,4);return a
meta=[];before=[];post=[];dark=[];domain=[]
for f in range(81):
 m=read(R/f'{f:03d}_CLOTH_META.bin');a=read(R/f'{f:03d}_CLOTH_PREPARED.bin');b=read(R/f'{f:03d}_CLOTH_POSTLINE.bin');d=(np.max(np.abs(a-b),axis=2)>1e-6)&(a[:,:,3]>.5);e=np.isin(np.rint(abs(m[:,:,3])).astype(int),elbowGlobal)&(np.rint(m[:,:,1])==11);meta.append(m);before.append(a);post.append(b);dark.append(d);domain.append(e)
events=[];coverageEvents=[]
for f in range(1,80):
 cov=(before[f][:,:,3]>.5)&(before[f-1][:,:,3]<.5)&(before[f+1][:,:,3]<.5)&domain[f]
 for y,x in np.argwhere(cov):coverageEvents.append({'frame':f,'xy':[int(x),int(y)],'meta':meta[f][y,x].tolist(),'source':mapping.get(int(round(abs(meta[f][y,x,3]))))})
 changes=dark[f]&~dark[f-1]&~dark[f+1]&domain[f];seen=set()
 for y,x in np.argwhere(changes):
  if(y,x)in seen:continue
  todo=[(int(y),int(x))];seen.add((int(y),int(x)));points=[]
  while todo:
   yy,xx=todo.pop();points.append((xx,yy))
   for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
    p=yy+dy,xx+dx
    if 0<=p[0]<272 and 0<=p[1]<480 and changes[p]and p not in seen:seen.add(p);todo.append(p)
  rows=[]
  for xx,yy in points:
   rows.append({'xy':[xx,yy],'triplet':[{'frame':t,'meta':meta[t][yy,xx].tolist(),'prepared':before[t][yy,xx].tolist(),'postLine':post[t][yy,xx].tolist(),'dark':bool(dark[t][yy,xx]),'source':mapping.get(int(round(abs(meta[t][yy,xx,3]))))}for t in[f-1,f,f+1]]})
  events.append({'frame':f,'bbox':[min(p[0]for p in points),min(p[1]for p in points),max(p[0]for p in points)+1,max(p[1]for p in points)+1],'points':points,'rows':rows})
j={'leftHumanoidBones':[(i,bones[i])for i in upper+lower],'elbowSourceTriangles':len(elbowGlobal),'candidateTransientDarkClusters':events,'coverageABA':coverageEvents,'note':'Observed fixed-cell one-frame dark changes in semantic left elbow domain. Candidates are not all classified as defects; actual contour motion/occlusion must be compared.'};(O/'ELBOW_EVENTS542.json').write_text(json.dumps(j,indent=2));print(json.dumps({'dark':[{k:e[k]for k in ['frame','bbox','points']}for e in events],'coverage':coverageEvents}))
