"""Compact actual GPU Q receipts, for CPU-only repository regression.

The original 120 lossless atlases remain in the local capture folder. This
fixture preserves all valid source-Q samples and their actual prior-GPU Q,
plus the previous primitive's UV/projected triangle for every mapped sample.
It cannot replace a fresh GPU render or the original full-atlas identity audit.
"""
from pathlib import Path
import sys,json,hashlib,numpy as np
from frame_bytes77 import decode
from selected_light84 import geometry,barycentric_uv
from audit_history85 import source_valid
from shade_history85 import choose,prior_address
H=Path(__file__).resolve().parent

def pack(root):
 c=root/'capture';report=json.loads((c/'COMPLETE.json').read_text());records=[];triangles=[];uvs=[];origins=[];oldxy=[];hashes=[];previous=None
 assert report['restorationChecksPass']and report['ownedResourcesReleased']and not report['errors']
 for f in report['stream77']['frames']:
  w,h=f['QROI'][2:];raw=decode((c/f['compressedFile']).read_bytes(),f['bytes']);assert hashlib.sha256(raw).hexdigest()==f['rawSHA256'];a=np.frombuffer(raw,'<f4').reshape(h,17,w,4).transpose(1,0,2,3);valid=source_valid(a);geo=geometry(c/f['light84']['sourceGeometryFile']);hashes.append({'file':f['compressedFile'],'SHA256':f['rawSHA256'],'sourceId':f['sourceId'],'frame':f['frame']})
  for y,x in np.argwhere(valid):
   mapped=False;oldq=float(a[8,y,x,0]);oldraw=oldq;tri=np.zeros((3,4));origin=np.zeros(4);xy=np.array([-1,-1])
   if previous is not None:
    old,oldf,oldg,oldvalid=previous;pos,why=prior_address(oldg,int(a[9,y,x,3]),a[11,y,x,:2],oldf['QROI'])
    if pos is not None:
     px,py=pos
     if oldvalid[py,px]and np.array_equal(old[9,py,px,1:],a[9,y,x,1:]):
      mapped=True;oldq=float(old[16,py,px,0]);oldraw=float(old[8,py,px,0]);tri=oldg['v'][oldg['tri'][int(a[9,y,x,3])-1],3:7];origin=np.asarray(oldf['QROI']);xy=np.array([px,py])
   records.append([f['frame'],x,y,f['light84']['faceSteps'],a[8,y,x,0],a[8,y,x,1],oldq,a[16,y,x,0],a[16,y,x,1],a[16,y,x,2],mapped,oldraw,a[12,y,x,3]])
   triangles.append(tri);uvs.append(a[11,y,x,:2]);origins.append(origin);oldxy.append(xy)
  previous=a,f,geo,valid
 np.savez_compressed(root/'REPLAY_CASES85.npz',records=np.asarray(records),triangles=triangles,uv=uvs,origin=origins,priorXY=oldxy)
 (root/'REPLAY_PROVENANCE85.json').write_text(json.dumps({'frames':hashes,'validSourceSamples':len(records),'originalAtlasFilesIncludedInRepository':root.name!='pulse120','fullRawAvailableLocally':str(c),'noExpectedQUploadedToGPU':True},indent=2))

def verify(root):
 z=np.load(root/'REPLAY_CASES85.npz');mapped=0;used=0
 for i,r in enumerate(z['records']):
  frame,x,y,levels,q,g,pq,actual,actual_previous,actual_used,is_mapped,oldraw,visible=r
  if is_mapped:
   tri=z['triangles'][i];bc=barycentric_uv(tri[:,:2],z['uv'][i]);assert bc is not None and(bc>=0).all();head=bc@tri[:,2:];origin=z['origin'][i];pixel=np.array([head[0],272-head[1]]);uncertainty=np.finfo(np.float32).eps*32*(1+max(abs(pixel)));assert(np.abs(pixel-np.rint(pixel))>uncertainty).all();local=np.floor(pixel).astype(int)-np.array([origin[0],272-origin[1]-origin[3]]).astype(int);assert np.array_equal(local,z['priorXY'][i]);mapped+=1
   expected,hold=choose(q,g,pq,int(levels))
  else:expected,hold=q,False
  assert expected==actual and pq==actual_previous and hold==bool(actual_used);used+=int(hold)
 result={'actualGPUFrames':len(np.unique(z['records'][:,0])),'validActualSourceSamples':len(z['records']),'mappedPrimitiveUVProjectionCases':mapped,'actualGPUHistoryUses':used,'allQPriorAndUsageExact':True,'currentRenderedRGBChangedByThisCPUCheck':False,'fullRawIdentityAuditReplaced':False};(root/'CPU_REPLAY85.json').write_text(json.dumps(result,indent=2));print(str(root),json.dumps(result))

if __name__=='__main__':
 for root in [H/'face85',H/'face85/pulse120']:
  if '--pack'in sys.argv:pack(root)
  verify(root)
