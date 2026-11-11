"""Archive only completed55-57 evidence and owned observer code. Never drives Unity."""
from pathlib import Path
import hashlib,json,subprocess,sys
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');P='experiments/pixel-pipeline/2026-11-11-resume-argon25';BASE='38f397e981f53967c21de0aa9742460c26b78a01'
ROOTS=['relay55.py','QuitCheck55.cs.txt','ReadReopened55.cs.txt','console55.py','FailureCompletion56.cs','FailureCompletionTests56.cs','prepare_capture56.py','relay56.py','console56.py','prepare_capture57.py','relay57.py','review_domain57.py','ReadFinal57.cs.txt','final57.py','CheckInput57.cs.txt','input_check57.py','archive_restart57.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,indent=2),encoding='utf-8',newline='\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8').strip()
def main():
 assert git('rev-parse','HEAD')==BASE and not git('diff','--cached','--name-only')
 user=load(H/'face55/BEFORE_GIT55.json')['user30'];assert len(user)==30 and all(sha(R/p)==v for p,v in user.items())
 rows=load(H/'face55/backup/DISK_BEFORE.json');assert len(rows)==128
 changes=[x['path']for x in rows if(R/x['path']).exists()!=x['exists']or(x['exists']and sha(R/x['path'])!=x['sha256'])];assert not changes
 before=load(H/'face55/project-save-reviewed/RESULT.json');close=load(H/'face55/close/RESULT.json');reopen=load(H/'face55/reopened/STATE.json');failed=load(H/'face56/capture/FAILED.json');done=load(H/'face57/capture/COMPLETE.json');final=load(H/'face57/final/STATE.json');inputcheck=load(H/'face57/input-check/STATE.json');analysis=load(H/'face57/analysis/ACTUAL_DOMAIN57.json')
 assert before['APIreturned']and before['nativeContentsSame']and before['inputSame']and not before['diskChanges']and before['foreignPackageSourceBytesUnchanged']
 assert close['exitedWithin10Seconds']and not close['forcedTermination']and reopen['loadedNativeCompared']==44 and reopen['inputJSONExact']and all(x['equal'] is not False for x in reopen['nativeChecks'])
 assert failed['restorationChecksPass']and failed['ownedResourcesReleased']and not failed['packetComplete']
 assert done['restorationChecksPass']and done['ownedResourcesReleased']and not done['errors']and done['pendingOwners']==0 and len(done['frames'])==1 and all(x['equal'] is True for x in done['nativeChecks'])
 assert final['Edit']and final['diagnosticRTs']==final['diagnosticMaterials']==final['commandUpdateObservers']==0 and final['allRTCount']==30
 assert inputcheck['inputJSONExact']and inputcheck['sameHideFlags']and not inputcheck['InputSettingsAssignment']and analysis['ordinaryGeometryPass']and analysis['ordinaryCarrierClaims']==45
 console=load(H/'face57/console/REPLY.json')['result'];c=console.get('structuredContent')or next(json.loads(x['text'])for x in console['content']if x.get('type')=='text');assert c['success']and not c['data']['logs']
 audit={'baseCommit':BASE,'standardSaveExecutedOnce':True,'normalExitConfirmed':True,'forceKill':False,'oldPID':close['pid'],'newPID':load(H/'face55/reopen/LAUNCHED.json')['pid'],'protected128BytesEqual':True,'user30BytesEqual':True,'reopened44NativeExact':True,'reopenedNativeNotLoaded':3,'final45NativeExact':True,'inputReceiptSchemaCorrectedReadExact':True,'diagnosticRTMaterialObservers':[0,0,0],'actualSourceFrames':1,'failed56Preserved':True,'finalConsoleErrors':0,'candidateVisualAdopted':False,'product77Changed':False,'fullFacePaletteWidthHistoryComplete':False,'forceGC':False,'memoryAllocatedDeltaMiB':{str(n):round((d['afterMemory']['allocated']-d['beforeMemory']['allocated'])/1048576,5)for n,d in[(56,failed),(57,done)]},'memoryCounterIsNotPhysicalWSOrLeakProof':True,'rawBackupsRemainInWorkspace':str(H/'face55/backup')}
 save(H/'face57/AUDIT55_57.json',audit)
 files=ROOTS[:]
 for n in[55,56,57]:
  for p in(H/f'face{n}').rglob('*'):
   if not p.is_file()or any(part in['build','disk','foreign-source']for part in p.parts)or p.name.startswith(('native-before-','native-after-'))or p.name in['GLOBALS_BEFORE.bin','INPUT_BEFORE.json','INPUT_AFTER.json','Editor55.log','COMMIT57.json','ARCHIVE57.json','COMMIT_BODY57.txt','REPLY.json','SCHEMA.json']:continue
   files.append(p.relative_to(H).as_posix())
 files=sorted(set(files));manifest=[{'path':p,'bytes':(H/p).stat().st_size,'SHA256':sha(H/p)}for p in files];save(H/'face57/ARCHIVE57.json',{'baseCommit':BASE,'files':manifest,'rawUserNativeAndOriginalDiskBackupsExcluded':True})
 if'--publish'in sys.argv:
  for row in manifest+[{'path':'face57/ARCHIVE57.json','SHA256':sha(H/'face57/ARCHIVE57.json')}]:
   dest=R/P/row['path'];assert not dest.exists()or sha(dest)==row['SHA256'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((H/row['path']).read_bytes());assert sha(dest)==row['SHA256']
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';assert not git('diff','--name-only','--',str(doc));old=doc.read_bytes();add=(H/'face57/HANDOFF_APPEND57.md').read_bytes();assert add not in old;doc.write_bytes(old+add)
  assert all(sha(R/p)==v for p,v in user.items())
 print(json.dumps({'files':len(manifest)+1,'bytes':sum(x['bytes']for x in manifest),'published':'--publish'in sys.argv,'audit':audit}))
 if'--commit'in sys.argv:
  assert'--publish'in sys.argv;names=[P+'/'+r['path']for r in manifest]+[P+'/face57/ARCHIVE57.json','docs/ai/PIXEL_ALBEDO_20261030.md'];assert not set(names).intersection(user)
  git('add','--',*names);assert set(git('diff','--cached','--name-only').splitlines())==set(names)
  subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check'],cwd=R,check=True)
  body=H/'face57/COMMIT_BODY57.txt';body.write_text('Resume native source-domain capture after verified normal Editor restart\n\nRecord one newly authorized standard save, exact serialized/disk preservation, normal same-project restart and zero retained diagnostic resources. Fix the observer to wait for the completed second main camera render while retaining fail-closed GPU completion and cleanup.\n\nPreserve failed56 and actual57 raw evidence: 45 ordinary carriers pass geometry; 27 eye-domain cells stay separate; native composite matches CPU bytes. Keep the over-dark chin contour unadopted and full-face palette/width/history explicitly incomplete. Correct the final input receipt-schema check without overwriting its original failed evidence.\n\nOnly owned diagnostics and handoff are committed. User30/product77 unchanged; no push.\n',encoding='utf-8')
  print(git('commit','--file',str(body)));assert not git('diff','--cached','--name-only')and all(sha(R/p)==v for p,v in user.items())
  save(H/'face57/COMMIT57.json',{'commit':git('rev-parse','HEAD'),'files':len(names),'user30Equal':True,'product77Changed':False,'standardSaveExecuted':True,'normalRestartExecuted':True,'actualGPUCapture57Complete':True,'candidateAdopted':False,'push':False});print((H/'face57/COMMIT57.json').read_text())
if __name__=='__main__':main()
