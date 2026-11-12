from pathlib import Path
import json,sys,numpy as np
from actor_visibility96 import ActorQuery,packet
from selected_light84 import barycentric_uv,geometry
from review_packed93 import ribbon
H=Path(__file__).resolve().parent
def main():
 root=Path(sys.argv[1]);report=json.loads((root/'capture/COMPLETE.json').read_text());assert report['packetComplete']and report['ownedResourcesReleased']and report['restorationChecksPass']and not report['errors'];rows=[]
 for f in report['stream77']['frames']:
  if'actorSource96'not in f:continue
  a,world,wd=packet(root,f);query=ActorQuery(root,f);face=geometry(root/'capture'/f['light84']['sourceGeometryFile']);mesh=next(m for m in query.g['meshes']if m['renderer']==face['renderer']);assert np.array_equal(mesh['v'],face['v'])and np.array_equal(mesh['tri'][face['submesh']],face['tri']);source=[]
  for y,x in np.argwhere(a[4,:,:,3]==1):
   pr=int(a[0,y,x,3])-1;t=face['v'][face['tri'][pr]].astype(float);b=barycentric_uv(t[:,3:5],a[1,y,x,:2]);p=b@t[:,5:7];p[1]=272-p[1];z=float(-(np.r_[b@t[:,:3],1]@query.g['view'].astype(float).T)[2]);hit=query.query(p);source.append({'xy':[int(x),int(y)],'selectedRole':int(a[0,y,x,1]),'selectedPrimitive':pr+1,'CPUFromSameUVDepth':z,'GPUSelectedDepth':float(a[0,y,x,0]),'GPUCPUDepthError':abs(z-float(a[0,y,x,0])),'sourcePointQuery':hit})
  _,_,_,_,anchors,_,_,_=ribbon(root/'capture'/f['ribbon93']['file']);delta=np.array([anchors[2]-anchors[0],-(anchors[3]-anchors[1])]);origin=np.array([f['QROI'][0],272-f['QROI'][1]-f['QROI'][3]]);lines=[]
  for y,x in np.argwhere(a[10,:,:,3]==1):
   p=origin+[x+.5,y+.5]+a[8,y,x,1:3];canon=query.query(p-delta);dest=query.query(p);point=np.floor(np.array(f['nativeOrigin'])+2*(p+f['join']+f['delta'])).astype(int);local=point-np.array(f['sourceFootprint95']['worldFirst']);world_depth=float(wd[local[1],local[0],0])if(local>=0).all()and(local<wd.shape[0]).all()else None;z=float(a[6,y,x,0]);lines.append({'xy':[int(x),int(y)],'edge':int(a[6,y,x,1]),'lineHeadDepth':z,'sourcePoint':(p-delta).tolist(),'destinationPoint':p.tolist(),'canonicalSourceQuery':canon,'destinationQuery':dest,'canonicalOccluderGap':z-canon['hit']['depth']if canon['hit']else None,'destinationOccluderGap':z-dest['hit']['depth']if dest['hit']else None,'rawWorldTileDepth':world_depth,'lineWorldDepth':z+f['depthOffset'],'wholeCellRejected':False})
  rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'allActorMeshes':len(query.g['meshes']),'alphaTexturesVerified':len(query.alpha),'sourceColourPoints':source,'lineQueries':lines})
 out={'CPUFromSameActualCapturedInput':True,'actualFramesWithFullActorInput':len(rows),'selectedSourceUVSamples':sum(len(r['sourceColourPoints'])for r in rows),'maximumSelectedUVDepthError':max((p['GPUCPUDepthError']for r in rows for p in r['sourceColourPoints']),default=None),'sourcePointRoleMismatch':sum(p['sourcePointQuery']['known']and p['sourcePointQuery']['hit']is not None and p['sourcePointQuery']['hit']['role']!=p['selectedRole']for r in rows for p in r['sourceColourPoints']),'lineWitnessesWithCanonicalOccluder':sum(l['canonicalSourceQuery']['known']and l['canonicalOccluderGap']is not None and l['canonicalOccluderGap']>1e-4 for r in rows for l in r['lineQueries']),'rows':rows,'wholeCellCoverageSolved':False};(root/'ACTOR_VISIBILITY96.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items()if k!='rows'}));print(json.dumps([r['lineQueries']for r in rows]))
if __name__=='__main__':main()
