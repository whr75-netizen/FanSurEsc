from pathlib import Path
import struct,json,math
import numpy as np
O=Path(__file__).resolve().parent;R=O/'Math';REF=O.parent/'Outline533/FullLoop'
class Reader:
 def __init__(self,b):self.b=b;self.i=0
 def n(self):v=struct.unpack_from('<i',self.b,self.i)[0];self.i+=4;return v
 def a(self,d,n):v=np.frombuffer(self.b,d,n,self.i).copy();self.i+=v.nbytes;return v
def read(path,region=True):
 r=Reader(path.read_bytes());curves=[r.a('<f4',r.n()*2).reshape(-1,2)for _ in range(r.n())]
 if not region:return curves
 box=tuple(r.n()for _ in range(4));x,y,w,h=box;a=r.a('<f4',w*h).reshape(h,w);m=r.a('?',w*h).reshape(h,w);assert r.i==len(r.b);return curves,box,a,m
def oldregion(f):
 r=Reader((REF/f'{f:03d}_ALT_REGION.bin').read_bytes());box=tuple(r.n()for _ in range(4));x,y,w,h=box;return box,r.a('<f4',w*h).reshape(h,w),r.a('?',w*h).reshape(h,w)
def cells(box,m):
 x,y,w,h=box;return{(int(xx)+x,int(yy)+y)for yy,xx in np.argwhere(m)}
def area_abs(path):
 # Exact polygon-lobe areas, without normalized projection coordinates.
 p=np.asarray(path,float);a,b=p[0],p[-1];d=b-a
 cross=lambda v:float(d[0]*v[1]-d[1]*v[0])
 def polygon(q):
  q=np.array(q,float);return abs(float(np.sum(q[:,0]*np.roll(q[:,1],-1)-q[:,1]*np.roll(q[:,0],-1))*.5))
 lobes=[];part=[a];prev=a;hprev=0.
 for curr in p[1:]:
  h=cross(curr-a)
  if h*hprev<0:
   q=prev+(curr-prev)*(hprev/(hprev-h));part.append(q);lobes.append(polygon(part));part=[q]
  part.append(curr)
  if h==0 and len(part)>2:lobes.append(polygon(part));part=[curr]
  prev=curr;hprev=h
 if len(part)>2:lobes.append(polygon(part))
 return sum(lobes),lobes
def metrics(arc):
 p=np.asarray(arc,float);d=p[-1]-p[0];dd=np.asarray(d,np.float32);den=np.float32(dd[0]*dd[0]+dd[1]*dd[1]);length=math.sqrt(float(den));v=p-p[0];ss=v@d/length;hs=(d[0]*v[:,1]-d[1]*v[:,0])/length
 area=0.
 for s0,s1,h0,h1 in zip(ss,ss[1:],hs,hs[1:]):
  u,w=abs(h0),abs(h1);area+=(s1-s0)*((u*u+w*w)/(2*(u+w))if h0*h1<0 else(u+w)*.5)
 exact,lobes=area_abs(p)
 return {'arcLength':float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum()),'chordLength':float(np.linalg.norm(d)),'maxPerpendicularError':float(np.max(abs(hs))),'orderedProjection':bool(np.all(np.diff(ss)>=0)),'implementedNormalizedArea':float(area),'independentLobeArea':exact,'absoluteAreaError':abs(area-exact),'lobeAreas':lobes,'h':hs.tolist(),'s':ss.tolist()}
def chord_for(rs,y):
 for ri,r in enumerate(rs):
  for i,a in enumerate(r):
   b=r[(i+1)%len(r)]
   if min(a[1],b[1])<=y<max(a[1],b[1]):
    t=(y-float(a[1]))/(float(b[1])-float(a[1]));x=float(a[0])+t*(float(b[0])-float(a[0]))
    if 198<x<205:return ri,i,a,b,x
 raise RuntimeError('Missing local chord')
rows=[]
for f in[49,50,51]:
 variants={v:read(R/f'{f}_{v}.bin')for v in['source','distance','area']};source=variants['source'][0][0];candidate=variants['area'][0];ri,edge,a,b,x=chord_for(candidate,97.5)
 ia=np.flatnonzero(np.all(source==a,1));ib=np.flatnonzero(np.all(source==b,1));assert len(ia)==len(ib)==1
 start,end=int(ia[0]),int(ib[0]);ids=list(range(start,end+1))if end>=start else list(range(start,len(source)))+list(range(end+1));arc=source[ids]
 distancePoints={tuple(map(float,p))for r in variants['distance'][0]for p in r};skipped=[{'sourceIndex':i,'xy':source[i].tolist(),'retainedByDistance':tuple(map(float,source[i]))in distancePoints}for i in ids[1:-1]]
 samples={}
 for key,(rs,box,areas,mask)in variants.items():
  bx,by,w,h=box;samples[key]={'curvePoints':[len(r)for r in rs],'cells':[{'xy':[201,y],'area':float(areas[y-by,201-bx]),'selected':bool(mask[y-by,201-bx])}for y in range(96,101)]}
 ob,oa,om=oldregion(f);nrs,nb,na,nm=variants['area'];bx,by,w,h=ob;nx,ny,nw,nh=nb
 # Compare only corresponding recorded cells, all complete selected regions.
 replay={'maskSymmetricDifference':len(cells(ob,om)^cells(nb,nm)),'areaMaxErrorOnOriginalBounds':float(np.max(abs(oa-na[by-ny:by-ny+h,bx-nx:bx-nx+w])))}
 rows.append({'frame':f,'sharedInputSourcePoints':len(source),'localAcceptedAreaChord':{'ring':ri,'edge':edge,'a':a.tolist(),'b':b.tolist(),'crossing97_5':x,'sourceArcIndices':ids,'sourceArc':arc.tolist(),'skippedVertices':skipped,'metrics':metrics(arc),'areaBudget':1,'distanceBudget':.09375},'variants':samples,'exactAreaReplayVsRuntime':replay})
equal=[]
for k in[0,1]:
 source=read(R/f'equal{k}_source.bin')[0][0];arc=source[:3]if k==0 else source[:4];a=read(R/f'equal{k}_area.bin')[0][0];d=read(R/f'equal{k}_distance.bin')[0][0]
 equal.append({'variant':k,'sourceArc':arc.tolist(),'metrics':metrics(arc),'sourceClosedArea':float(abs(np.sum(source[:,0]*np.roll(source[:,1],-1)-source[:,1]*np.roll(source[:,0],-1))*.5)),'areaCurve':a.tolist(),'distanceCurve':d.tolist()})
result={'status':'SAME_INPUT_TRANSFORM_REPLAY_COMPLETE','rows':rows,'equalAreaGeometryControls':equal,'equalAreaControlInterpretation':'Two different source height/width distributions with identical0.75 local error and8.75 enclosed area collapse to the same chord under area fit; this is a property of its aggregate objective, not proof that actual frame50 selected an equal-area tie.','noNewRender':True,'noProductPatch':True}
(O/'TRANSFORM_AUDIT534.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'frames':[{'frame':r['frame'],'replay':r['exactAreaReplayVsRuntime'],'skipped':r['localAcceptedAreaChord']['skippedVertices'],'metrics':r['localAcceptedAreaChord']['metrics'],'cell97':{v:r['variants'][v]['cells'][1]for v in r['variants']}}for r in rows],'equal':equal}))
