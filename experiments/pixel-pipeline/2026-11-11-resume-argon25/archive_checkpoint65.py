"""Only completed owned63-65 diagnostics; never stage product/user modifications."""
from pathlib import Path
import json,hashlib,subprocess,sys
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');P='experiments/pixel-pipeline/2026-11-11-resume-argon25';BASE='e17722e5d6750f7e192fd062062ff8d55c416b09'
ROOTS=['prepare_motion63.py','relay63.py','prepare_motion64.py','relay64.py','review_motion64.py','prepare_motion65.py','relay65.py','review_motion65.py','ConsumerRegression65.cs','test_consumers65.py','SelectedShade65.cs','SelectedShadeTests65.cs','prepare_selected65.py','archive_checkpoint65.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8').strip()
def save(p,d):p.write_text(json.dumps(d,indent=2),encoding='utf-8',newline='\n')
def main():
 assert git('rev-parse','HEAD')==BASE and not git('diff','--cached','--name-only')
 user=load(H/'face55/BEFORE_GIT55.json')['user30'];assert len(user)==30 and all(sha(R/p)==v for p,v in user.items())
 disk=load(H/'face55/backup/DISK_BEFORE.json');assert all((R/x['path']).exists()==x['exists'] and(not x['exists']or sha(R/x['path'])==x['sha256'])for x in disk)
 assert (R/'Assets/EUnityValidation01/SourceBoundary60/SourceNativeHull60.compute').read_bytes()==(H/'face62/shaders/SourceNativeHull60.compute').read_bytes()
 for n in [63,64,65]:
  d=load(H/f'face{n}/capture'/('COMPLETE.json'if n==65 else'FAILED.json'))
  assert d['Edit'] and d['restorationChecksPass'] and d['ownedResourcesReleased'] and d['pendingOwners']==0 and not d['errors'] and all(x.get('equal')is not False for x in d['nativeChecks'])
 f=load(H/'face65/post/STATE.json');assert f['Edit'] and f['inputJSONExact'] and f['diagnosticRTs']==f['diagnosticMaterials']==f['commandUpdateObservers']==0 and f['allRTCount']==30 and len(f['dirty'])==31
 a=load(H/'face65/ACTUAL_MOTION65.json');assert a['actualGPUFrames']==6 and a['CPUExactWidthCases']==24 and a['positiveOwnerSamplesAllControls']==358
 c=load(H/'face65/console/REPLY.json')['result'];c=c.get('structuredContent')or next(json.loads(x['text'])for x in c['content']if x.get('type')=='text');assert c['success'] and not c['data']['logs']
 q=load(H/'face65/CPU_SELECTED_SHADE65.json');assert q['tests']==264 and q['observedOrdinaryFaceQ']==240 and q['paletteOutputsCreated']==0
 assert load(H/'face65/CPU_CONSUMERS65.json')['sixOwnersOutOfOrder']
 files=list(ROOTS)
 for n in [63,64,65]:
  for p in(H/f'face{n}').rglob('*'):
   if not p.is_file()or'build'in p.parts or p.name.startswith(('native-before-','native-after-'))or p.name in ['GLOBALS_BEFORE.bin','INPUT_BEFORE.json','INPUT_AFTER.json','REPLY.json','SCHEMA.json','COMMIT65.json','ARCHIVE65.json','COMMIT_BODY65.txt']:continue
   files.append(p.relative_to(H).as_posix())
 rows=[{'path':p,'bytes':(H/p).stat().st_size,'SHA256':sha(H/p)}for p in sorted(set(files))]
 save(H/'face65/ARCHIVE65.json',{'baseCommit':BASE,'files':rows,'user30AndProtected128Exact':True,'product77DefaultChanged':False,'actualGPUFrames':6,'CPUExactCases':24,'fullFaceLUTApplied':False,'longTermStabilityValidated':False})
 if'--publish'in sys.argv:
  for row in rows+[{'path':'face65/ARCHIVE65.json','SHA256':sha(H/'face65/ARCHIVE65.json')}]:
   target=R/P/row['path'];assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((H/row['path']).read_bytes());assert sha(target)==row['SHA256']
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';assert not git('diff','--name-only','--',str(doc));old=doc.read_bytes();add=(H/'face65/HANDOFF_APPEND65.md').read_bytes();assert add not in old;doc.write_bytes(old+add)
 print(json.dumps({'files':len(rows)+1,'bytes':sum(x['bytes']for x in rows),'published':'--publish'in sys.argv,'user30And128Exact':True,'product77DefaultChanged':False}))
 if'--commit'in sys.argv:
  assert'--publish'in sys.argv
  names=[P+'/'+r['path']for r in rows]+[P+'/face65/ARCHIVE65.json','docs/ai/PIXEL_ALBEDO_20261030.md'];assert not set(names).intersection(user)
  subprocess.run(['git','add','--pathspec-from-file=-','--pathspec-file-nul'],cwd=R,input=('\0'.join(names)+'\0').encode('utf-8'),check=True);assert set(git('diff','--cached','--name-only').splitlines())==set(names)
  subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check'],cwd=R,check=True)
  body=H/'face65/COMMIT_BODY65.txt';body.write_text('Validate authored outline motion and recover selected surface shade receipts\n\nFix bounded six-owner readback scheduling without timeout extension or new shader work. Preserve failed63/64 evidence. Six real normal-input frames and24 width cases match CPU RGB/owner/layer; retain original77 and user edits.\n\nAdapt observed selected-surface Q from UV receipt to existing52 supplier;264 CPU checks and31 actual consumer-guard checks. Full-face region/family mapping and stable pixel-art stroke policy remain incomplete; do not promote calibration or thin raster flicker to success.\n',encoding='utf-8')
  print(git('commit','--file',str(body)));assert not git('diff','--cached','--name-only') and all(sha(R/p)==v for p,v in user.items())
  save(H/'face65/COMMIT65.json',{'commit':git('rev-parse','HEAD'),'files':len(names),'product77DefaultChanged':False,'user30Exact':True,'protected128Exact':True,'actualGPUFrames':6,'CPUExactCases':24,'CPUSelectedShadeTests':264,'fullFaceLUTApplied':False,'longTermStabilityValidated':False,'push':False});print((H/'face65/COMMIT65.json').read_text())
if __name__=='__main__':main()
