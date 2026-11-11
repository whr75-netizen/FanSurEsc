"""Select only29 code/evidence and its unreferenced shader assets. No deletion."""
from pathlib import Path
import hashlib,json,shutil,sys,zipfile
H=Path(__file__).resolve().parent;G=H/'face29';REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');DEST=REPO/'experiments/pixel-pipeline/2026-11-11-resume-argon25'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 run=json.loads(next((G/'run').glob('STATE113-*-finished.json')).read_text(encoding='utf-8'));assert run['PlayExited']and not run.get('restorationError')and not run['packetComplete']
 baseline=json.loads((H/'RESUME_STATUS.json').read_text(encoding='utf-8'))['userTrackedFiles'];assert all(sha(REPO/p)==v for p,v in baseline.items())
 records=[]
 for name in ['import','fixed-import','class-import','run','post-failed-read']:
  for p in (G/name).iterdir():
   if not p.is_file()or p.suffix not in ['.json','.txt','.marker']:continue
   if p.name.startswith(('before-native-','after-native-')):continue
   records.append((p,name+'/'+p.name))
 zip_path=G/'EVIDENCE29.zip'
 if not zip_path.exists():
  with zipfile.ZipFile(zip_path,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
   for p,name in sorted(records):z.write(p,name)
 with zipfile.ZipFile(zip_path)as z:assert all(hashlib.sha256(z.read(name)).hexdigest()==sha(p)for p,name in records)
 status={'basisCommit':'3a64d1a3cf4586d28d389d0f7e0e52849f62d57e','CPURegionChecks':16,'sourceRegionAdopted':False,'actualPlayEntries':1,'actualCompletedPackets':0,'newClassifyDispatchRecorded':False,'firstError':'canonical DenseNative grid mistaken for physical ROI in SourceOutline29.Record','secondaryError':'URP ZBinningJob NativeArray job-lifetime safety error after graph recording aborted','currentReadUTC':'2026-11-11T08:20:32.4955262Z','currentRead':'PID28080 Edit,not compiling/paused/transitioning/updating; Responding=true','newDeviceResetLoggedAfterRootError':False,'furtherPlayGPUHeld':True,'pending':0,'physicalCorrectionCPUCompiled':True,'physicalCorrectionAssetsApplied':False,'sourceShaderOnlyImportsCompleted':2,'default77Preserved':True,'originalTracked30ByteHashesEqual':True,'restorationLimits':['clean AssetImporter lifecycle1 unavailable;46/47 comparable project native objects equal','Two added path-empty Editor internal objects not backed up; project dirty list and scene equal','OS private commit increased3.777GiB across noncontrolled times; leak/root cause not established'],'unreferencedAssets':'Assets/EUnityValidation01/SourceBoundary29 (shader+compute+meta), no Assets C#','latestCode':'face29/physical-fix/SourceOutline29.cs; proposed shader, CPU_PHYSICAL29.json; not original failed runner','serverDenial':False}
 status['restorationLimits'][2]='OS commit peak+3.777GiB receded to+181.53MiB over initial by08:40:43UTC; noncontrolled time windows; leak/root cause not established'
 status['latestOSUTC']='2026-11-11T08:40:43.1236080Z';status['latestOSResponding']=True
 (G/'STATUS29.json').write_text(json.dumps(status,indent=2),encoding='utf-8',newline='\n')
 scripts=['SourceOutline29.cs','prepare_source29.py','import_source29.py','import_class29.py','affine_support29.py','test_affine29.py','review_support29.py','prepare_physical29.py','archive_source29.py']
 selected=[H/n for n in scripts]+[p for p in G.iterdir()if p.is_file()and p.name!='ARCHIVE29.json']+[p for p in (G/'physical-fix').iterdir()if p.is_file()and p.suffix in ['.cs','.shader','.txt','.json','.patch']]
 rows=[]
 for p in selected:
  raw=p.read_bytes()
  if p.suffix in ['.json','.txt','.py','.cs','.shader','.compute','.md','.patch']:
   fixed=raw.replace(b'\r\n',b'\n')
   if fixed!=raw:p.write_bytes(fixed)
  row={'path':p.relative_to(H).as_posix(),'SHA256':sha(p),'bytes':p.stat().st_size};rows.append(row)
  if '--publish'in sys.argv:
   q=DEST/row['path']
   if q.exists():assert sha(q)==row['SHA256'],'Different existing file; never overwrite: '+str(q)
   else:q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 assets=[]
 folder=REPO/'Assets/EUnityValidation01/SourceBoundary29'
 for p in [folder.with_suffix('.meta'),*sorted(folder.iterdir())]:
  assert p.is_file()and p.suffix in ['.meta','.shader','.compute']
  assets.append({'path':p.relative_to(REPO).as_posix(),'SHA256':sha(p),'bytes':p.stat().st_size})
 result={'files':rows,'ownNewAssets':assets,'evidenceFiles':len(records),'rawNativeSettingsIntentionallyNotCopied':True,'packetComplete':False}
 raw=json.dumps(result,indent=2).encode('utf-8');(G/'ARCHIVE29.json').write_bytes(raw)
 if '--publish'in sys.argv:
  p=DEST/'face29/ARCHIVE29.json'
  if p.exists():assert p.read_bytes()==raw
  else:p.write_bytes(raw)
  assert all(sha(DEST/row['path'])==row['SHA256']for row in rows)
 print(json.dumps({'experimentFiles':len(rows)+1,'newAssets':len(assets),'evidenceFiles':len(records),'zipBytes':zip_path.stat().st_size,'published':'--publish'in sys.argv,'userTracked30Unchanged':True,'newGPUExecution':False}))
if __name__=='__main__':main()
