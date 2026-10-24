from pathlib import Path
import json, struct, csv
import numpy as np
R=Path(__file__).resolve().parent;C=R/'Runtime578/Full170'
j=json.loads((R/'REVIEW578_Full170.json').read_text())
def buf(p):
 b=p.read_bytes();w,h,x,y=struct.unpack_from('<4i',b);return x,y,np.frombuffer(b,'<f4',offset=16).reshape(h,w,4)
out=[]
for p in C.glob('*_ON_EYE_VISIBLE.bin'):
 f=int(p.name[:3]);a=buf(C/f'{f:03}_OFF_EYE_VISIBLE.bin');b=buf(p)
 for yy,xx in np.argwhere(np.any(a[2]!=b[2],axis=2)):
  point=[int(a[0]+xx),int(a[1]+yy)]
  q={'frame':f,'eyeBufferLogicalXY':point,'before':a[2][yy,xx].tolist(),'after':b[2][yy,xx].tolist(),'nearby':{}}
  for kind in ['OFF','ON']:
   q['nearby'][kind]={}
   for label in ['META','FINAL','MASK']:
    ox,oy,data=buf(C/f'{f:03}_{kind}_{label}.bin');x,y=point[0]-ox,point[1]-oy
    q['nearby'][kind][label]=[{'xy':[int(ox+sx),int(oy+sy)],'v':data[sy,sx].tolist()}for sy in range(max(0,y-1),min(data.shape[0],y+2))for sx in range(max(0,x-1),min(data.shape[1],x+2))]
  out.append(q)
for case in out:
 f=case['frame'];x,y=case['eyeBufferLogicalXY'];observations=[]
 for frame in range(max(0,f-1),min(80,f+1)+1):
  rec={'frame':frame,'modes':{}}
  for kind in ['OFF','ON']:
   p=C/f'{frame:03}_{kind}';par=json.loads(Path(str(p)+'_PARAMS.json').read_text());mx=x+par['offsetX'];my=y-par['offsetY']
   z={'mainXY':[mx,my]}
   for label,px,py in [('MASK',x,y),('EYE_VISIBLE',x,y),('META',mx,my)]:
    ox,oy,data=buf(Path(str(p)+'_'+label+'.bin'));z[label]=data[py-oy,px-ox].tolist()
   raw=Path(str(p)+'_AREAS.bin').read_bytes();ax,ay,w,h=struct.unpack_from('<4i',raw);areas=np.frombuffer(raw,'<f4',offset=16).reshape(h,w)
   z['area']=float(areas[y-ay,x-ax]);z['depthOffset']=par['depthOffset'];rec['modes'][kind]=z
  observations.append(rec)
 case['adjacent']=observations
 rays=C/f'{f:03}_ON_FACE_SAME_RAY.csv'
 case['existingSameRayWitness']=[r for r in csv.DictReader(rays.open())if int(r['headX'])==x and int(r['headY'])==y] if rays.exists() else []
 case['families']=list(csv.DictReader((C/f'{f:03}_ON_FAMILIES.tsv').open(),delimiter='\t'))
summary={k:j.get(k)for k in ['poses','faceCoverageChanges','faceChangesMissingSameRayPacket','acceptedPacketsWithOpaqueSkinInFront','acceptedPacketsWithAnyOpaqueFaceInFront','removedHairRevealsFace','sourceFaceRayPackets','outsideParent','outsideEnvelope']}
(R/'EYE_CHANGE578.json').write_text(json.dumps({'summary':summary,'eyeChanges':out},indent=2)+'\n')
print(json.dumps({'summary':summary,'eyeChanges':[{k:v for k,v in x.items()if k!='nearby'}for x in out]}))
