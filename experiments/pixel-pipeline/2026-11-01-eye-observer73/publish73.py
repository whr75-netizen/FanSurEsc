"""Archive this completed experiment only; exclude native-settings backups."""
from pathlib import Path
import json,hashlib,subprocess,shutil
HERE=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');DEST=REPO/'experiments/pixel-pipeline/2026-11-01-eye-observer73';DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
NAMES=['CreateOnly73.cs','EyeReadback73.cs','UnityEyeBuffer70.cs','TestEyeReadback73.cs','NativeSnapshot73.cs','build73.py','relay73.py','Read73.cs','Post73.cs','Compile73.cs','Capture73.cs','analyse73.py','test73.py','publish73.py','CURRENT73.json','POST73.json','DISK_BEFORE73.json','NATIVE_BEFORE73.json','GLOBAL_NAMES66.json','PROTOCOL_TEST73.json','PROTOCOL_TEST73.txt','RESULT73.json','VERIFICATION73.json','VALIDATED_CAPTURE73.json','APPROVAL_SOURCE73.json','CELL_RECORDS73.json','FINAL73.png','EYE73.png','EYE73-nearest20.png','FEATURES73-nearest20.png','INDEX.html','Read73_REQUEST.json','Read73_REPLY.json','Compile73_REQUEST.json','Compile73_REPLY.json','Capture73_REQUEST.json','Capture73_REPLY.json','Post73_REQUEST.json','Post73_REPLY.json']
def git(*a):return subprocess.check_output(['git','-C',str(REPO),*a],text=True,encoding='utf-8').strip()
def main():
 assert git('rev-parse','HEAD')=='042cf7e523112a1a42c496fff7d9f47db509884a';assert not git('diff','--cached','--name-only');assert not git('diff','--name-only','--',DOC)
 r=json.loads((HERE/'RESULT73.json').read_text());v=json.loads((HERE/'VERIFICATION73.json').read_text());assert r['PlayEntries']==1 and all(r['stateChecks'].values()) and v['allDirtyContentsExact'] and v['PlayerSettingsFullBytesEqual'] and v['captureMarkerStillMatchesResult'];assert not r['disk31Changed']
 base=json.loads((HERE/'DISK_BEFORE73.json').read_text());
 for p,h in base['files'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 DEST.mkdir(exist_ok=False);paths=[]
 def copy(src,dst):
  assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert hashlib.sha256(src.read_bytes()).digest()==hashlib.sha256(dst.read_bytes()).digest();paths.append(dst.relative_to(REPO).as_posix())
 for n in NAMES:copy(HERE/n,DEST/n)
 final=sorted(HERE.glob('STATE73-*.json'))[-1];copy(final,DEST/final.name)
 state=json.loads(final.read_text());packet=Path(state['output']);raw=[]
 for src in sorted(packet.iterdir()):
  if src.is_file():copy(src,DEST/packet.name/src.name);raw.append({'name':src.name,'bytes':src.stat().st_size,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
 manifest=DEST/'ARCHIVE73.json';manifest.write_text(json.dumps({'sourceId':state['sourceId'],'rawFiles':raw,'nativeContentBackupsExcluded':True,'archiveMeaning':'actual one-frame experiment, no product integration, importer uncertainty retained'},indent=2)+'\n');paths.append(manifest.relative_to(REPO).as_posix())
 helper=HERE.parent/'boundary-input69/prepare73.py';copy(helper,REPO/'experiments/pixel-pipeline/2026-11-01-boundary-input69/prepare73.py')
 doc=REPO/DOC;before=doc.read_bytes();add=(HERE/'HANDOFF73.txt').read_bytes();assert add not in before
 with doc.open('ab') as f:f.write(add)
 assert doc.read_bytes()==before+add;paths.append(DOC)
 git('add','--',*paths);assert set(git('diff','--cached','--name-only').splitlines())==set(paths);git('diff','--cached','--check')
 msg=HERE/'.commit73.txt';msg.write_text('Capture bounded eye packets with append-only completion markers\n\nNo file moves/deletes/overwrite or approval-settings changes. Thirteen offline protocol tests and full dynamic Unity command compile pass. One normal Play captures actual counts48/records256 eye ROI at frame94; allocator replay exactly matches2iris cells per eye. Normal Edit/options/global restoration,29dirty contents and full PlayerSettings serialization unchanged; one non-dirty native importer unavailable. Preserve input, images and source approval-scope findings; no product eye correction or temporal/art success claim.\n',encoding='utf-8');print(git('commit','--file',str(msg)),flush=True)
 assert not git('diff','--cached','--name-only')
 for p,h in base['files'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 receipt={'commit':git('rev-parse','HEAD'),'files':len(paths),'rawFiles':len(raw),'PlayEntries':1,'dirty29ContentExact':True,'PlayerSettingsFullExact':True,'nativeImporterUnverified':1,'disk31Unchanged':True,'stageEmpty':True,'productChanges':0};
 with (HERE/'COMMIT73.json').open('x') as f:json.dump(receipt,f,indent=2)
 print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
