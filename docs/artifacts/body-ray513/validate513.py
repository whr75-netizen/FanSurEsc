from pathlib import Path
import json,struct,hashlib,numpy as np
from PIL import Image
W=Path(__file__).parent;R=W/'Compare513';analysis=json.loads((R/'ANALYSIS513.json').read_text());rows=[]
def rd(p,n):
 b=(R/(p+'_'+n+'.bin')).read_bytes();w,h,_,_=struct.unpack_from('<4i',b);return np.frombuffer(b,'<f4',offset=16).reshape(h,w,4)
def meshes(path):
 b=path.read_bytes();magic,n=struct.unpack_from('<2i',b);assert magic==512;at=8;out={}
 for _ in range(n):
  r,nv,ns=struct.unpack_from('<3i',b,at);at+=12;v=np.frombuffer(b,'<f4',offset=at,count=nv*5).reshape(nv,5).astype(float);at+=nv*20;ix=[]
  for sm in range(ns):
   ni=struct.unpack_from('<i',b,at)[0];at+=4;ix.append(np.frombuffer(b,'<i4',offset=at,count=ni).reshape(-1,3));at+=ni*4
  out[r]=(v,ix)
 assert at==len(b);return out
points=sorted({tuple(t['event']['headXY'])for t in json.loads((W/'Walk511/FIRST_STAGE_TRACE511.json').read_text())['candidateVisibleTransitions']if t['event']['target']==70})
for a in analysis['rows']:
 p=f"{a['capture']:03d}";pose=a['pose'];ox,oy=pose['offset'];cfg=json.loads((R/(p+'_ALT_projection.json')).read_text());view=np.array(cfg['headView']).reshape(4,4);geom=meshes(R/(p+'_ALT.raymesh'));body,ix=geom[0];world=body[:,:3];uvw=body[:,3:];camera=np.c_[world,np.ones(len(world))]@view.T
 baseMask=rd(p,'BASE_MASK');mask=rd(p,'MASK');refs=json.loads((R/(p+'_ALT_bodyrefs512.json')).read_text())['references'];packets=json.loads((R/(p+'_packets.json')).read_text())['packets'];packetBy={(v['x'],v['y']):v for v in packets};refBy={(v['x'],v['y']):v for v in refs};errors=[];maxDepth=0;maxUV=0;maxBary=0;counts={}
 for ref in refs:
  x,y=ref['x'],ref['y'];kind=ref['kind'];counts[kind]=counts.get(kind,0)+1;packet=packetBy[(x,y)]
  if mask[y,x,3]!=kind or np.float32(mask[y,x,2])!=np.float32(ref['depth']):errors.append([x,y,'mask-reference'])
  if any(ref['sampleWorld'][k]!=packet['world'][k]for k in ['x','y','z']):errors.append([x,y,'source-world'])
  if kind==3:continue
  ids=ix[ref['submesh']][ref['primitive']];t=camera[ids];pw=np.array([packet['world'][k]for k in ['x','y','z']]+[1.]);q=view@pw;u=t[1,:2]-t[0,:2];v=t[2,:2]-t[0,:2];det=u[0]*v[1]-u[1]*v[0];z=q[:2]-t[0,:2];bb=(z[0]*v[1]-z[1]*v[0])/det;cc=(u[0]*z[1]-u[1]*z[0])/det;bar=np.array([1-bb-cc,bb,cc]);depth=-bar@t[:,2];uv=bar@uvw[ids];be=max(abs(bar-np.array([ref['barycentric'][k]for k in ['x','y','z']])));de=abs(depth-ref['depth']);ue=max(abs(uv-np.array([ref['uv'][k]for k in ['x','y']])));maxDepth=max(maxDepth,de);maxUV=max(maxUV,ue);maxBary=max(maxBary,be)
  if bar.min()<-.00002 or de>3e-6 or ue>2e-6 or be>2e-6:errors.append([x,y,'triangle-ray',float(de),float(ue),float(be)])
  if kind==2 and ref['depth']<packet['depth']-.0001:errors.append([x,y,'uncertain-foreground'])
 before=rd(p,'BASE_META');after=rd(p,'ALT_META');rgbBefore=rd(p,'BASE_FINAL');rgbAfter=rd(p,'ALT_FINAL');changed=np.any(abs(rgbBefore-rgbAfter)>1e-5,axis=2);roleChanged=(before[:,:,1]!=after[:,:,1])&((before[:,:,0]>0)|(after[:,:,0]>0));locations=[]
 for my,mx in np.argwhere(roleChanged):
  x,y=int(mx-ox),int(my+oy);reference=refBy.get((x,y));locations.append({'headXY':[x,y],'mainXY':[int(mx),int(my)],'beforeRole':int(round(float(before[my,mx,1]))),'afterRole':int(round(float(after[my,mx,1]))),'bodyReference':reference})
 event=[]
 for x,y in points:
  my,mx=y-oy,x+ox;ref=refBy[(x,y)];packet=packetBy[(x,y)];event.append({'headXY':[x,y],'beforeRole':int(round(float(before[my,mx,1]))),'afterRole':int(round(float(after[my,mx,1]))),'reference':ref,'bodyMinusHairDepthSameRay':ref['depth']-packet['depth']})
 comparison={}
 for field in ['RAW','RAWUV','HAIR','HAIRUV','NATIVE','PREPARED','MRAW','MRAWUV','MNATIVE','MNATIVEUV','MNATIVEWORLD','MCANON','MCENTRE','MAP']:
  aa=rd(p,'BASE_'+field);bb=rd(p,'ALT_'+field);different=aa.view('<u4')!=bb.view('<u4');comparison[field]={'floatBitDifferences':int(different.sum()),'maxAbsoluteDelta':float(np.max(abs(aa-bb)))}
 row={'target':a['target'],'maskRGBitDifference':int((baseMask[:,:,:2].copy().view('<u4')!=mask[:,:,:2].copy().view('<u4')).sum()),'referenceCount':len(refs),'packetCount':len(packets),'referenceKinds':counts,'referenceErrors':errors,'maxBodyRayDepthError':float(maxDepth),'maxBodyRayUVError':float(maxUV),'maxBodyRayBaryError':float(maxBary),'bodyAndHairGeometryPairBitEqual':(R/(p+'_BASE.raymesh')).read_bytes()==(R/(p+'_ALT.raymesh')).read_bytes(),'projectionPairEqual':json.loads((R/(p+'_BASE_projection.json')).read_text())==cfg,'sourceBuffers':comparison,'headEvents':event,'changedOwnership':locations,'finalAlphaCellDifference':int((rgbBefore[:,:,3]!=rgbAfter[:,:,3]).sum()),'sameRoleColourCounts':{k:len(v)for k,v in a['sameRoleColourDifferenceYX'].items()},'sameSourceColourCounts':{k:len(v)for k,v in a['sameSurfaceColourDifferenceYX'].items()},'eyeFaceRoleCountsEqual':all(a['roles']['original'][str(role)]==a['roles']['candidate'][str(role)]for role in range(1,8))}
 pngB=np.array(Image.open(R/(p+'_BASE.png')).convert('RGB'));pngA=np.array(Image.open(R/(p+'_ALT.png')).convert('RGB'));pngDiff=np.any(pngA!=pngB,axis=2);coverage=(before[:,:,0]>0)|(after[:,:,0]>0);coverage2=np.repeat(np.repeat(coverage,2,0),2,1)
 row['screenPNG']={'changedPixelsInsideCharacter':int((pngDiff&coverage2).sum()),'changedPixelsOutsideCharacter':int((pngDiff&~coverage2).sum()),'ownershipChangeBlocks':[{'mainXY':q['mainXY'],'maxByteDelta':int(np.max(abs(pngA[2*q['mainXY'][1]:2*q['mainXY'][1]+2,2*q['mainXY'][0]:2*q['mainXY'][0]+2].astype(int)-pngB[2*q['mainXY'][1]:2*q['mainXY'][1]+2,2*q['mainXY'][0]:2*q['mainXY'][0]+2].astype(int))))}for q in locations]}
 rows.append(row)
out={'status':'ACTUAL_THREE_PAIR_SOURCE_RAY_CORRECTION_VALIDATION','rows':rows,'fixture':json.loads((W/'JOIN_FIXTURE512.json').read_text()),'maskRGBitDifferences':sum(r['maskRGBitDifference']for r in rows),'referenceErrors':sum(len(r['referenceErrors'])for r in rows),'sameRayGeometryErrorMax':max(r['maxBodyRayDepthError']for r in rows),'outside':analysis['outsideTotals'],'packetMismatchTotal':analysis['packetMismatchTotal'],'allPairedPoseLight':analysis['allPoseLightMatched'],'gif':analysis['gif'],'gifSHA256':hashlib.sha256(Path(analysis['gif']['path']).read_bytes()).hexdigest(),'limits':['Three adjacent actual poses, not16 intervals or a full loop.','Front-body behavior tested in actual GPU join kernel; a live hand-crossing animation is not covered by these Walk poses.','Correction applies only511 hair/body source-ray visibility; existing face/eye/world comparison contracts remain separate and unmodified.','No packet performance optimization or new allocation benchmark.']}
(R/'VALIDATION513.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['rows','limits']}));print(json.dumps([{'target':r['target'],'kinds':r['referenceKinds'],'depthError':r['maxBodyRayDepthError'],'UVError':r['maxBodyRayUVError'],'sameRoleColour':r['sameRoleColourCounts'],'sameSourceColour':r['sameSourceColourCounts'],'faceCountsEqual':r['eyeFaceRoleCountsEqual'],'alphaDifference':r['finalAlphaCellDifference'],'changedRoles':[[v['headXY'],v['beforeRole'],v['afterRole']]for v in r['changedOwnership']],'events':r['headEvents'],'sourceBufferDifferenceCounts':{k:v['floatBitDifferences']for k,v in r['sourceBuffers'].items()}}for r in rows]))
