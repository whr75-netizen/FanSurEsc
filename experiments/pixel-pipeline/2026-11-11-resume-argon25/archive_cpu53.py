"""Preserve only CPU52/53 candidates; no Unity, process control, import or GPU calls."""
from pathlib import Path
import hashlib,json,subprocess,sys,zipfile
H=Path(__file__).resolve().parent
R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
P='experiments/pixel-pipeline/2026-11-11-resume-argon25'
BASE='c61afbe6d8bdf680fca59d5dbcf058683df597a6'
ROOTS=['ResolvedShade52.cs','ResolvedShade52.hlsl','StageTests52.cs','prepare_stage52.py','CurveHistoryIndexed53.cs','HistoryIndexTests53.cs','test_index53.py','archive_cpu53.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf-8').strip()
def save(p,d):p.write_text(json.dumps(d,indent=2),encoding='utf-8',newline='\n')
def main():
 assert git('rev-parse','HEAD')==BASE and not git('diff','--cached','--name-only')
 user=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert len(user)==30 and all(sha(R/p)==s for p,s in user.items())
 a=json.loads((H/'face52/CPU_STAGE52.json').read_text());b=json.loads((H/'face53/CPU_INDEX53.json').read_text())
 assert a['assertionGroups']==10 and a['actualFaceBindings']==0 and not a['shaderCompiledOrImported']
 assert b['fullObservableResultEqual'] and b['savedActual12FrameReplayExact'] and b['oldScopeLifecycleGroups']==13
 old=json.loads((H/'face45/ACTUAL_HISTORY45.json').read_text())
 with zipfile.ZipFile(H/'face50/ACTUAL_PACKETS45_49.zip')as z:assert hashlib.sha256(z.read('face45/ACTUAL_INPUT45.bin')).hexdigest()==old['fixtureSHA256']
 for name,expected in [('CurveHistory45.cs',b['sourceHash']['baseline']),('CurveCarrier43.cs',b['sourceHash']['carrierUnchanged'])]:assert sha(H/name)==expected
 assert not(H/'face49/capture/COMPLETE.json').exists() and not(H/'face49/capture/FAILED.json').exists()
 report={'baseCommit':BASE,'user30Equal':True,'existing45andCarrier43Unchanged':True,'product77Changed':False,'existing45RTsNotTouched':True,'currentRTReadPerformed':False,'GPUOrUnityRequests':0,'restartOrSave':0,'52CPUGroups':10,'53LifecycleGroups':13,'53Queries':b['indexed']['queries'],'53Saved12FrameReplayExact':True,'semanticFaceRegionResolved':False,'runtimeHistoryFeedbackImplemented':False}
 save(H/'face53/PRESERVATION53.json',report)
 files=sorted(set(ROOTS+[p.relative_to(H).as_posix()for n in [52,53]for p in(H/f'face{n}').rglob('*')if p.is_file()and'build'not in p.parts and p.name not in ['ARCHIVE53.json','COMMIT53.json','COMMIT_BODY53.txt']]))
 rows=[{'path':p,'bytes':(H/p).stat().st_size,'SHA256':sha(H/p)}for p in files];save(H/'face53/ARCHIVE53.json',{'baselineCommit':BASE,'files':rows,'GPUExecuted':False,'product77Changed':False})
 if '--publish'in sys.argv:
  for row in rows+[{'path':'face53/ARCHIVE53.json','SHA256':sha(H/'face53/ARCHIVE53.json')}]:
   dst=R/P/row['path'];assert not dst.exists(),'Do not overwrite existing snapshot '+row['path'];dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((H/row['path']).read_bytes());assert sha(dst)==row['SHA256']
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';assert not git('diff','--name-only','--',str(doc));oldDoc=doc.read_bytes();add=(H/'face53/HANDOFF_APPEND53.md').read_bytes();assert add not in oldDoc;doc.write_bytes(oldDoc+add)
  assert all(sha(R/p)==s for p,s in user.items())
 print(json.dumps({'files':len(rows)+1,'bytes':sum(x['bytes']for x in rows),'published':'--publish'in sys.argv,'GPUOrUnityCalls':0,'user30Equal':True}))
 if '--commit'in sys.argv:
  assert '--publish'in sys.argv;names=[P+'/'+r['path']for r in rows]+[P+'/face53/ARCHIVE53.json','docs/ai/PIXEL_ALBEDO_20261030.md'];assert not set(names).intersection(user)
  git('add','--',*names);assert set(git('diff','--cached','--name-only').splitlines())==set(names)
  subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check'],cwd=R,check=True)
  body=H/'face53/COMMIT_BODY53.txt';body.write_text('Validate same-stage palette metadata and index source-history correspondence\n\nRequire exact scope and applied-Q agreement for confirmed LUT inputs; preserve unresolved face semantics. Compare indexed source correspondence with the original on2056 queries and12 saved frames, preserving current occlusion and ambiguous ties. Record concrete resource-drain and unsaved-state requirements.\n\nCPU-only candidates; no Unity/GPU/import/save/restart, product77 changes or push.\n',encoding='utf-8');print(git('commit','--file',str(body)))
  assert not git('diff','--cached','--name-only') and all(sha(R/p)==s for p,s in user.items())
  save(H/'face53/COMMIT53.json',{'commit':git('rev-parse','HEAD'),'files':len(names),'user30Equal':True,'product77Changed':False,'GPUOrUnityCalls':0,'existing45ResourcesNotTouched':True,'push':False});print((H/'face53/COMMIT53.json').read_text())
if __name__=='__main__':main()
