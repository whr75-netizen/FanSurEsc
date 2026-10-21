from pathlib import Path
import json,struct,hashlib,numpy as np
W=Path(__file__).parent;R=W/'Ray512';assert json.loads((R/'status.json').read_text())['status']=='CAPTURED'
events=json.loads((W/'Walk511/FIRST_STAGE_TRACE511.json').read_text())['candidateVisibleTransitions'];points=sorted({tuple(e['event']['headXY'])for e in events if e['event']['target']==70})
def rd(n):
 b=(R/(n+'.bin')).read_bytes();w,h,_,_=struct.unpack_from('<4i',b);return np.frombuffer(b,'<f4',offset=16).reshape(h,w,4)
def mesh(path):
 b=path.read_bytes();magic,nr=struct.unpack_from('<2i',b);assert magic==512;at=8;out={}
 for _ in range(nr):
  renderer,nv,ns=struct.unpack_from('<3i',b,at);at+=12;v=np.frombuffer(b,'<f4',offset=at,count=nv*5).reshape(nv,5).astype(float);at+=nv*20;ix=[]
  for sm in range(ns):
   ni=struct.unpack_from('<i',b,at)[0];at+=4;ix.append(np.frombuffer(b,'<i4',offset=at,count=ni).reshape(-1,3));at+=ni*4
  out[renderer]={'world':v[:,:3],'uv':v[:,3:],'indices':ix}
 assert at==len(b);return out
def project(points,view,proj):
 a=np.concatenate([np.asarray(points).reshape(-1,3),np.ones((len(np.asarray(points).reshape(-1,3)),1))],axis=1);v=a@view.T;q=v@proj.T;return np.c_[(q[:,0]/q[:,3]*.5+.5)*480,(.5-q[:,1]/q[:,3]*.5)*272,-v[:,2]]
def intersect(m,xy,view,proj,sm,primitive):
 ids=m['indices'][sm][primitive];w=m['world'][ids];s=project(w,view,proj);a,b=s[1,:2]-s[0,:2],s[2,:2]-s[0,:2];den=a[0]*b[1]-a[1]*b[0]
 if abs(den)<1e-12:return None
 v=((xy[0]-s[0,0])*b[1]-(xy[1]-s[0,1])*b[0])/den;t=(a[0]*(xy[1]-s[0,1])-a[1]*(xy[0]-s[0,0]))/den;bar=np.array([1-v-t,v,t]);uv=bar@m['uv'][ids];world=bar@w
 return {'renderer':0 if sm<0 else None,'submesh':int(sm),'primitive':int(primitive),'vertices':ids.tolist(),'barycentric':bar.tolist(),'inside':bool(bar.min()>=-1e-5),'uv':uv.tolist(),'world':world.tolist(),'depth':float(bar@s[:,2]),'screenSignedArea2':float(den)}
def all_hits(m,xy,view,proj):
 sp=project(m['world'],view,proj);hits=[]
 for sm,ids in enumerate(m['indices']):
  tri=sp[ids];a=tri[:,1,:2]-tri[:,0,:2];b=tri[:,2,:2]-tri[:,0,:2];q=np.asarray(xy)-tri[:,0,:2];den=a[:,0]*b[:,1]-a[:,1]*b[:,0];ok=abs(den)>1e-12;v=np.divide(q[:,0]*b[:,1]-q[:,1]*b[:,0],den,out=np.zeros_like(den),where=ok);t=np.divide(a[:,0]*q[:,1]-a[:,1]*q[:,0],den,out=np.zeros_like(den),where=ok);u=1-v-t
  for primitive in np.flatnonzero(ok&(u>=-1e-5)&(v>=-1e-5)&(t>=-1e-5)):
   h=intersect(m,xy,view,proj,sm,int(primitive));h['renderer']=0;hits.append(h)
 return sorted(hits,key=lambda x:x['depth'])
rows=[]
for path in sorted(R.glob('*_pose.json')):
 p=path.name[:3];pose=json.loads(path.read_text());target=int((R/(p+'_target.txt')).read_text());cfg=json.loads((R/(p+'_ALT_projection.json')).read_text());geom=mesh(R/(p+'_ALT.raymesh'));mv=np.array(cfg['mainView']).reshape(4,4);hv=np.array(cfg['headView']).reshape(4,4);mp=np.array(cfg['mainProjection']).reshape(4,4);hp=np.array(cfg['headProjection']).reshape(4,4);ox,oy=pose['offset'];packets=json.loads((R/(p+'_packets.json')).read_text())['packets'];raw=rd(p+'_ALT_MRAW');rawuv=rd(p+'_ALT_MRAWUV');native=rd(p+'_ALT_MNATIVE');nu=rd(p+'_ALT_MNATIVEUV');nw=rd(p+'_ALT_MNATIVEWORLD');canon=rd(p+'_ALT_MCANON');centre=rd(p+'_ALT_MCENTRE');amap=rd(p+'_ALT_MAP');fmeta=rd(p+'_ALT_META')
 row={'target':target,'phase':pose['phase'],'pose':pose,'configuration':cfg,'points':[]}
 # Compare this diagnostic run's head projection with the already captured same-target511 pose.
 oldp=next(q.name[:3]for q in (W/'Walk511').glob('*_target.txt')if int(q.read_text())==target);old=(W/'Walk511'/(oldp+'.hairgeom')).read_bytes();nv=struct.unpack_from('<i',old)[0];oldsp=np.frombuffer(old,'<f4',count=nv*3,offset=8).reshape(nv,3);newsp=project(geom[2]['world'],hv,hp);delta=newsp-oldsp
 row['prior511ProjectionDifference']={'medianXYZ':np.median(delta,axis=0).tolist(),'rangeXYZ':np.ptp(delta,axis=0).tolist(),'maxAbsoluteXYZ':np.max(abs(delta),axis=0).tolist()}
 for x,y in points:
  mx,my=x+ox,y-oy;packet=next(q for q in packets if q['x']==x and q['y']==y);a=amap[my,mx];added=a[0]>.5 and a[3]>.5
  if added:
   sx,sy=np.rint(a[1:3]).astype(int);bodyraw=native[sy,sx];bodyuv=nu[sy,sx];bodycanon=canon[sy,sx];bodyworld=nw[sy,sx,:3];samplekind='native';sample=[int(sx),int(sy)];bodyxy=project([bodyworld],mv,mp)[0,:2]
  else:
   bodyraw=raw[my,mx];bodyuv=rawuv[my,mx];bodycanon=centre[my,mx];bodyxy=np.array([mx+.5,my+.5]);bodyworld=None;samplekind='centre';sample=[mx,my]
  bodyrole=int(round(float(bodyraw[1])));sm=bodyrole-8;prim=int(round(float(bodyraw[3])))-1
  if not(0<=sm<len(geom[0]['indices'])):raise RuntimeError('Body role does not map to declared body material: '+str(bodyraw))
  hworld=np.array([packet['world'][k]for k in ['x','y','z']]);hproj=project([hworld],mv,mp)[0];display=np.array([mx+.5,my+.5]);source=intersect(geom[0],bodyxy,mv,mp,sm,prim)
  source['renderer']=0;source['gpuUVError']=float(np.max(abs(np.array(source['uv'])-bodyuv[:2])));source['gpuDepthError']=abs(source['depth']-float(bodyraw[0]));source['gpuWorldError']=None if bodyworld is None else float(np.linalg.norm(np.array(source['world'])-bodyworld))
  hitHead=all_hits(geom[0],hproj[:2],mv,mp);hitDisplay=all_hits(geom[0],display,mv,mp)
  for hit in hitHead+hitDisplay:hit['bodyMinusHairDepth']=hit['depth']-float(hproj[2])
  q={'headXY':[x,y],'displayMainXY':[mx,my],'mask':rd(p+'_MASK')[y,x,:2].tolist(),'finalRole':int(round(float(fmeta[my,mx,1]))),'headPacket':packet,'headPacketMainProjected':hproj.tolist(),'headProjectedMinusDisplayRay':(hproj[:2]-display).tolist(),'bodyPrepareAction':a.tolist(),'bodySelectedSampleKind':samplekind,'bodySelectedSampleXY':sample,'bodySelectedSampleProjected':bodyxy.tolist(),'bodyRaw':bodyraw.tolist(),'bodyRawUV':bodyuv.tolist(),'bodyCanonical':bodycanon.tolist(),'actualBodySurfaceAtGPUSelectedRay':source,'selectedBodyTriangleAtHeadRay':intersect(geom[0],hproj[:2],mv,mp,sm,prim),'selectedBodyTriangleAtDisplayRay':intersect(geom[0],display,mv,mp,sm,prim),'allBodyAtHeadRay':hitHead[:12],'allBodyAtDisplayRay':hitDisplay[:12],'GPUComparedBodyMinusHairDepth':float(bodycanon[0]-hproj[2]),'headDepthTransformError':float(hproj[2]-packet['depth']-cfg['depthOffset'])}
  row['points'].append(q)
 rows.append(row)
out={'status':'ACTUAL_THREE_POSE_SAME_RAY_TRIANGLE_EVIDENCE; ALPHA_CULL_VALIDATION_PENDING','rows':rows,'limits':['Different source rays and designed region ownership must not be conflated.','All-body hits currently include backfaces/alpha holes until material checks.','Previous511 projection differences are reported explicitly; no phase matching by assumption.'],'runtimeChanged':False}
(R/'RAY_ANALYSIS512.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{'target':r['target'],'oldProjection':r['prior511ProjectionDifference'],'points':[{'xy':q['headXY'],'role':q['finalRole'],'sample':q['bodySelectedSampleKind'],'sampleXY':q['bodySelectedSampleProjected'],'headXY':q['headPacketMainProjected'],'delta':q['headProjectedMinusDisplayRay'],'bodyActualPrimitive':[q['actualBodySurfaceAtGPUSelectedRay']['submesh'],q['actualBodySurfaceAtGPUSelectedRay']['primitive']],'bodyGPUError':[q['actualBodySurfaceAtGPUSelectedRay']['gpuUVError'],q['actualBodySurfaceAtGPUSelectedRay']['gpuDepthError']],'comparedMargin':q['GPUComparedBodyMinusHairDepth'],'headRayHits':[{'sm':h['submesh'],'tri':h['primitive'],'dz':h['bodyMinusHairDepth'],'cross':h['screenSignedArea2'],'uv':h['uv']}for h in q['allBodyAtHeadRay'][:3]]}for q in r['points']]}for r in rows]))
