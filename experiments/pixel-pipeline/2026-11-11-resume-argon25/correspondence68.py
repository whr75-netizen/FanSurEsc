"""Read current evaluated mesh/UV, do not infer visibility from missing centres."""
from pathlib import Path
import json,struct,numpy as np
import review_hull60 as api
from trace_contour40 import geometry
from native_contour42 import coordinates
H=Path(__file__).resolve().parent;G=H/'face68/motion';C=G/'capture'

def read_geometry(path):
 with path.open('rb')as f:
  def integer():return struct.unpack('<i',f.read(4))[0]
  def text():
   size=0;shift=0
   while True:
    n=f.read(1)[0];size|=(n&127)<<shift
    if n<128:break
    shift+=7
   return f.read(size).decode('utf-8')
  assert text()=='all-source68/v1';source=text();model=text();frame=integer();meshes=[]
  for rr in range(integer()):
   assert integer()==rr;n=integer();sm=integer();assert 0<n<100000 and 0<sm<=16
   a=np.frombuffer(f.read(n*28),'<f4').reshape(n,7).copy();ix=[]
   for _ in range(sm):
    count=integer();assert 0<count<1000000 and count%3==0;ix.append(np.frombuffer(f.read(count*4),'<i4').reshape(-1,3).copy())
   meshes.append((a,ix))
  assert not f.read()
 return source,model,frame,meshes

def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['packetComplete']and r['restorationChecksPass'];api.C=C;rows=[];previous=[];previous_frame=None
 previous_join=np.zeros(2)
 for f in r['frames']:
  w=f['QROI'][2];a=api.plane(r,f,'atlas40');b=api.plane(r,f,'ownerReceipts47');owner=api.plane(r,f,'widthOwnerAndLayerAtlas62')[:,2*w:3*w];source,model,frame,meshes=read_geometry(C/f"all-source-frame{f['frame']}.bin");assert source==f['sourceId']and frame==f['frame']and model==f['frameInfo']['model'];face=geometry(C/f'geometry-frame{frame}.bin');view=np.asarray(face['view']);view=view.reshape(4,4,order='F')if view.size==16 else view
  info=f['frameInfo']['nativeComposite42'];q,_,inside=coordinates(f['QROI'],info['joinOffset'],info['nativeOrigin'],info['deliveredDelta']);join=np.array([info['joinOffset'][0],-info['joinOffset'][1]],float);table={x['role']:x for x in f['frameInfo']['integerExterior68']['sourceTable']};current=[];checks=[];transport=[]
  for y,x in np.argwhere(owner[:,:,0]>=100):
   key=owner[y,x].copy();role=int(key[0]-100);tri=int(key[1]-1);row=table[role];vertices,indices=meshes[row['renderer']];ix=indices[row['subMesh']][tri];points=vertices[ix];uv=key[2:];delta=np.stack([points[1,3:5]-points[0,3:5],points[2,3:5]-points[0,3:5]],axis=1).astype(float)
   if np.linalg.det(delta)==0:checks.append({'destinationLocalXY':[int(x),int(y)],'role':role,'primitive':tri+1,'UVTriangleDegenerate':True});continue
   bary2=np.linalg.solve(delta,uv-points[0,3:5]);bary=np.r_[1-bary2.sum(),bary2];p=bary@points[:,:3];head=bary@points[:,5:7];z=-(view@np.r_[p,1])[2];matches=(b[:,2*w:3*w,1]==role)&(b[:,2*w:3*w,3]==tri+1)&(b[:,w:2*w,:2]==uv).all(2)&(a[:,14*w:15*w,2]==1)
   samples=[]
   for sy,sx in np.argwhere(matches):
    observed=np.array([q[sy,sx,0]+.5,272-q[sy,sx,1]-.5]);depth=float(b[sy,sx,2]);samples.append({'originLocalXY':[int(sx),int(sy)],'projectedMinusObservedCellCentre':(head-observed).tolist(),'projectedWithDeclaredJoinMinusObservedCellCentre':(head+join-observed).tolist(),'declaredHeadToMainJoin':join.tolist(),'worldDepthMinusNative':float(z-depth),'worldDepthPlusKnownOffsetMinusNative':float(z+info['depthOffset']-depth)})
   checks.append({'destinationLocalXY':[int(x),int(y)],'role':role,'primitive':tri+1,'sourceUV':uv.tolist(),'barycentric':bary.tolist(),'nativeOriginMatches':samples});current.append({'role':role,'triangle':tri,'barycentric':bary.tolist(),'head':head.tolist()})
  if previous_frame is not None:
   assert frame==previous_frame+1
   for point in previous:
    row=table[point['role']];vertices,indices=meshes[row['renderer']];ix=indices[row['subMesh']][point['triangle']];head=np.asarray(point['barycentric'])@vertices[ix,5:7];transport.append({'role':point['role'],'primitive':point['triangle']+1,'sameSourceBarycentricProjectedDelta':(head-point['head']).tolist(),'sameSourcePointAfterDeclaredMainJoinDelta':(head+join-point['head']-previous_join).tolist(),'visibilityNotInferred':True})
  rows.append({'frame':frame,'sourceId':source,'evaluatedGeometryBytes':(C/f'all-source-frame{frame}.bin').stat().st_size,'origins':checks,'previousSourcePointTransport':transport});previous=current;previous_frame=frame;previous_join=join
 samples=[m for row in rows for o in row['origins']for m in o.get('nativeOriginMatches',[])];summary={'sourcePointCount':len(samples),'maxAbsProjectedAfterDeclaredJoinCellOffset':max(abs(v)for m in samples for v in m['projectedWithDeclaredJoinMinusObservedCellCentre']),'maxAbsDepthAfterDeclaredOffsetError':max(abs(m['worldDepthPlusKnownOffsetMinusNative'])for m in samples),'priorBarycentricPointsTransported':sum(len(row['previousSourcePointTransport'])for row in rows)}
 result={'sourceFrameAndModelExact':True,'currentEvaluatedMeshes':3,'projectionUsesRecordedCurrentGeometry':True,'headToMainXYFromRecordedJoinNotAFit':True,'sameCellSupportIsNotCentreEquality':True,'summary':summary,'rows':rows,'historyFeedbackOrVisibilityProof':False,'GPUCalls':0};(G/'SOURCE_CORRESPONDENCE68.json').write_text(json.dumps(result,indent=2));print(json.dumps({'frames':len(rows),'summary':summary}))
if __name__=='__main__':main()
