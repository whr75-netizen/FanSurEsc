"""Archive recovery evidence only; never submits save/exit/restart/GPU work."""
from pathlib import Path
import hashlib,json,subprocess,sys
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');P='experiments/pixel-pipeline/2026-11-11-resume-argon25'
BASE='c362a87501f98aafac9e643782f2736631ad49ba'
ROOTS=['BackupRestart54.cs.txt','SaveRestart54.cs.txt','SaveProject54.cs.txt','SaveProjectReviewed54.cs.txt','InspectDirty54.cs.txt','ExportNative54.cs.txt','ReadStopped54.cs.txt','relay54.py','console54.py','relay33.py','audit_recovery54.py','archive_recovery54.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8').strip()
def save(p,d):p.write_text(json.dumps(d,indent=2),encoding='utf-8',newline='\n')
def main():
 assert git('rev-parse','HEAD')==BASE and not git('diff','--cached','--name-only')
 a=json.loads((H/'face54/AUDIT54.json').read_text());assert a['native47BackupsAndContentsExact']and a['disk128BackupsAndCurrentFilesExact']and not a['all31SavedProven']and not a['normalExitRequested']and a['newGlobalSaveDeniedBeforeProcess']
 user=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert len(user)==30 and all(sha(R/p)==s for p,s in user.items())
 files=ROOTS[:]
 for p in(H/'face54').rglob('*'):
  if not p.is_file()or'build'in p.parts or'disk'in p.parts or p.name.startswith('native-before-')or p.name in ['ARCHIVE54.json','COMMIT54.json','COMMIT_BODY54.txt','SCHEMA.json','GLOBALS_BEFORE.bin','INPUT_BEFORE.json']:continue
  files.append(p.relative_to(H).as_posix())
 files=sorted(set(files));rows=[{'path':p,'bytes':(H/p).stat().st_size,'SHA256':sha(H/p)}for p in files]
 save(H/'face54/ARCHIVE54.json',{'baseCommit':BASE,'files':rows,'actualUserContentBackupsRemainInWorkspace':True,'backupLocation':str(H/'face54/backup'),'globalSaveDeniedNotExecuted':True,'exitRestartGPUExecuted':False})
 if'--publish'in sys.argv:
  for row in rows+[{'path':'face54/ARCHIVE54.json','SHA256':sha(H/'face54/ARCHIVE54.json')}]:
   target=R/P/row['path']
   if target.exists():
    assert row['path']=='relay33.py';old=subprocess.check_output(['git','show',BASE+':'+P+'/relay33.py'],cwd=R);assert target.read_bytes().replace(b'\r\n',b'\n')==old.replace(b'\r\n',b'\n')
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((H/row['path']).read_bytes());assert sha(target)==row['SHA256']
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';assert not git('diff','--name-only','--',str(doc));old=doc.read_bytes();add=(H/'face54/HANDOFF_APPEND54.md').read_bytes();assert add not in old;doc.write_bytes(old+add)
  assert all(sha(R/p)==s for p,s in user.items())
 print(json.dumps({'files':len(rows)+1,'bytes':sum(x['bytes']for x in rows),'published':'--publish'in sys.argv,'user30Equal':True,'saveCompletionUnproven':True,'exitRestartGPU':0}))
 if'--commit'in sys.argv:
  assert'--publish'in sys.argv;names=[P+'/'+r['path']for r in rows]+[P+'/face54/ARCHIVE54.json','docs/ai/PIXEL_ALBEDO_20261030.md'];assert not set(names).intersection(user)
  git('add','--',*names);assert set(git('diff','--cached','--name-only').splitlines())==set(names)
  subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check'],cwd=R,check=True)
  body=H/'face54/COMMIT_BODY54.txt';body.write_text('Preserve authorized save preparation and exact blocked restart state\n\nBack up47 native snapshots and128 original files; record31 returned targeted GUID saves without claiming persistence. Preserve global-save denial before process launch, unsupported persistent-object export and final Edit/input/native/resource checks. Keep restart and GPU work unexecuted while save scope requires a decision.\n\nOnly diagnostics and handoff are committed; user30 and product77 remain unchanged. No push.\n',encoding='utf-8');print(git('commit','--file',str(body)))
  assert not git('diff','--cached','--name-only')and all(sha(R/p)==s for p,s in user.items())
  save(H/'face54/COMMIT54.json',{'commit':git('rev-parse','HEAD'),'files':len(names),'user30Equal':True,'product77Changed':False,'SaveAssetsExecuted':False,'normalExitRequested':False,'reopenExecuted':False,'GPUExecuted':False,'push':False});print((H/'face54/COMMIT54.json').read_text())
if __name__=='__main__':main()
