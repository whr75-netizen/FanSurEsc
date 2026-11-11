"""Create-only28 evidence archive; publish only explicit new experiment files."""
from pathlib import Path
import datetime,hashlib,json,shutil,sys,zipfile
H=Path(__file__).resolve().parent;G=H/'face28'
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 s=json.loads(next((G/'capture-stages').glob('STATE113-*-finished.json')).read_text(encoding='utf-8'));assert s['PlayExited']and not s.get('error')and not s.get('restorationError')
 packet=Path(s['sequencePackets'][0]['output']);files=sorted(p for p in packet.iterdir()if p.is_file())
 z=G/'ACTUAL_STAGE28.zip'
 if not z.exists():
  with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as f:
   for p in files:f.write(p,p.name)
 with zipfile.ZipFile(z)as f:
  assert set(f.namelist())=={p.name for p in files}
  assert all(hashlib.sha256(f.read(p.name)).hexdigest()==sha(p)for p in files)
 ev=G/'CAPTURE_EVIDENCE28.zip';evidence=[]
 for run in ['capture','capture-stages','final-state']:
  evidence.extend((p,run+'/'+p.name)for p in (G/run).iterdir()if p.is_file()and p.suffix in ['.json','.txt','.marker'])
 if not ev.exists():
  with zipfile.ZipFile(ev,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as f:
   for p,name in sorted(evidence):f.write(p,name)
 with zipfile.ZipFile(ev)as f:assert all(hashlib.sha256(f.read(name)).hexdigest()==sha(p)for p,name in evidence)
 baseline=json.loads((H/'RESUME_STATUS.json').read_text(encoding='utf-8'))['userTrackedFiles']
 changed=[p for p,h in baseline.items()if sha(REPO/p)!=h];assert not changed,changed
 status={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'basisCommit':'dc4e915534f4f4deda2df1d0e27fe9674fda801c','implementation':'CPU source-extremum evidence and live same-frame77 stage observer; no new GPU classifier/default change','CPUCounterexamplesPassed':19,'actualPlayEntries':2,'actualFinalStagePackets':1,'initialObservationCallMissing':True,'newKernels':0,'newDispatches':0,'AssetsImports':0,'pending':0,'default77Preserved':True,'userTrackedFilesPreserved':len(baseline),'nativeFinalContentEqual':len(s['nativeComparisons72']),'inputSettingsSameReferenceAndJSON':s['editInputRestoration82']['sameAliveReference']and s['editInputRestoration82']['exactJSON'],'fullFaceRegionAndOutlineCompleted':False,'regionBindingsAdded':0,'blockers':{'permission':'none','algorithm':'Complete source-child boundary/gradient-AA grouping, family sharing and source-derived outline-class producer remain unvalidated. This is not proof that automatic partition is impossible or that new user input is mandatory.','rotation':'The two remaining white cells follow current2.5 AND occlusion policy; changing it is a distinct policy decision, not a fixed colour/crop bug.','memory':'Profiler allocated increase remains; owned readbacks disposed/RT30 does not establish heap/native-root lifetime or leak resolution.'},'actualPacketSourceId':s['sequencePackets'][0]['sourceId'],'actualArchiveFiles':len(files),'actualArchiveSHA256':sha(z),'captureEvidenceSHA256':sha(ev)}
 (G/'STATUS28.json').write_text(json.dumps(status,indent=2),encoding='utf-8',newline='\n')
 selected=[p for p in G.iterdir()if p.is_file()and p.name!='ARCHIVE28.json']+[H/n for n in ['source_features28.py','test_features28.py','prepare_face28.py','review_face28.py','review_turn28.py','final_read28.py','archive_face28.py']]
 # README/analysis are in face28; scripts remain one level above just like the
 # existing snapshot. No product/user file is a publish source.
 target=REPO/'experiments/pixel-pipeline/2026-11-11-resume-argon25'
 manifest={'files':[{'path':str(p.relative_to(H)).replace('\\','/'),'bytes':p.stat().st_size,'SHA256':sha(p)}for p in selected]}
 if '--publish'in sys.argv:
  for p in selected:
   q=target/p.relative_to(H)
   if q.exists():assert sha(q)==sha(p),'Never overwrite a differing snapshot: '+str(q)
   else:q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for row in manifest['files']:assert sha(target/row['path'])==row['SHA256']
  q=target/'face28/ARCHIVE28.json'
  if q.exists():assert json.loads(q.read_text())==manifest
  else:q.write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
 (G/'ARCHIVE28.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
 print(json.dumps({'selectedFiles':len(selected),'rawPacketFiles':len(files),'actualZipBytes':z.stat().st_size,'evidenceZipBytes':ev.stat().st_size,'userTrackedPreserved':len(baseline),'published':'--publish'in sys.argv}))
if __name__=='__main__':main()
