from pathlib import Path
import json,numpy as np,hashlib,zipfile
from actor_visibility96 import packet
H=Path(__file__).resolve().parent

def main():
 g=H/'face96';rows=[]
 for name in['probe1','geometry64']:
  root=g/name;r=json.loads((root/'capture/COMPLETE.json').read_text());assert r['Edit']and r['packetComplete']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];assert r['inputSameReferenceAndJSON']and r['globalCount']==74 and not r['globalErrors'];frames=r['stream77']['frames'];assert len(frames)==(1 if name=='probe1'else 64);pal=np.fromfile(root/'capture/RUNTIME_PALETTE89.rgb',np.uint8).reshape(-1,3,3);samples=0
  for i,f in enumerate(frames):
   assert f['ordinal']==i and f['frame']==frames[0]['frame']+i;a,_,_=packet(root,f);known=a[4,:,:,3]==1;family=a[4,:,:,0][known].astype(int)-1;q=a[4,:,:,2][known].astype(int);assert(family>=0).all()and(family<len(pal)).all()and(q>=0).all()and(q<3).all();linear=a[5,:,:,:3][known];encoded=np.where(linear<=.0031308,linear*12.92,1.055*np.power(np.maximum(linear,0),1/2.4)-.055);rgb=np.rint(encoded*255).astype(int);assert np.array_equal(rgb,pal[family,q]);samples+=int(known.sum())
  s=json.loads((root/'post/final/STATE.json').read_text());assert s['Edit']and not s['compiling']and not s['updating']and s['inputJSONExact']and len(s['dirty'])==31 and s['allRTCount']==30 and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0
  rows.append({'run':name,'actualGPUFrames':len(frames),'LUTSamplesExact':samples,'consecutive':name=='geometry64','simulationSeconds':len(frames)/60,'nativeExact':sum(x.get('equal')is True for x in r['nativeChecks']),'nativeUnavailable':[x for x in r['nativeChecks']if x.get('equal')is None],'beforeMemory':r['beforeMemory'],'afterMemory':r['afterMemory'],'postUTC':s['utc'],'Edit':True,'dirty':31,'ownRTMaterialObserver':0,'totalRT':30,'newRunErrors':r['errors']})
 # Snapshot only the15 specifically needed captured alpha files. Preserve
 # original files; no directory-wide archive, deletion or inferred alpha.
 root=g/'geometry64/capture';spec=json.loads((root/'ACTOR_MATERIALS96.json').read_text());assert len(spec['textures'])==15 and all(t['alphaChannelVerified']for t in spec['textures']);manifest=[];archive=root/'ALPHA96.zip'
 if not archive.exists():
  with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9)as z:
   for t in spec['textures']:z.write(root/t['alphaFile'],t['alphaFile'])
 with zipfile.ZipFile(archive)as z:
  assert z.namelist()==[t['alphaFile']for t in spec['textures']]
  for t in spec['textures']:
   raw=(root/t['alphaFile']).read_bytes();assert z.read(t['alphaFile'])==raw;manifest.append({'file':t['alphaFile'],'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'verifiedAlphaByteOffset':t['alphaByteOffset']})
 summary={'actualRuns':rows,'CPUVisibilityTests':12,'CPUHaloTests':4,'sourceAlpha':manifest,'newProductionDefault':False,'nearest95RejectedStill':True,'runtimeJointLineResolverImplemented':False,'worldContinuousVisibilityProven':False,'fullPipelineComplete':False};(g/'SUMMARY96.json').write_text(json.dumps(summary,indent=2));print(json.dumps({'runs':rows,'sourceAlphaFiles':len(manifest),'sourceAlphaArchiveBytes':archive.stat().st_size}))
if __name__=='__main__':main()
