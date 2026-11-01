from pathlib import Path
import json,hashlib,shutil,subprocess
HERE=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
DEST=REPO/'experiments/pixel-pipeline/2026-11-01-eye-observer72'
DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
NAMES=['Read72.cs','Post72.cs','Compile72.cs','Capture72.cs','NativeSnapshot72.cs','build72.py','relay72.py','DISK_BEFORE72.json','CURRENT72.json','POST72.json','RESULT72.json','GLOBAL_NAMES66.json','Compile72_REQUEST.json','Compile72_REPLY.json','Compile72_COMPILE_FAILURE1_REQUEST.json','Compile72_COMPILE_FAILURE1_REPLY.json','Read72_REQUEST.json','Read72_REPLY.json','Post72_REQUEST.json','Post72_REPLY.json','publish72.py']
def git(*a):return subprocess.check_output(['git','-C',str(REPO),*a],text=True,encoding='utf-8').strip()
def main():
 assert git('rev-parse','HEAD')=='8d42f12831a4dd14bcbe121d6d3674053a8fa37f'
 assert not git('diff','--cached','--name-only')
 assert not git('diff','--name-only','--',DOC)
 r=json.loads((HERE/'RESULT72.json').read_text());assert r['PlayEntries']==0 and not r['captureInvocationSent'] and all(r['currentChecks'].values())
 base=json.loads((HERE/'DISK_BEFORE72.json').read_text())
 for p,h in base['files'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 DEST.mkdir(exist_ok=False);paths=[]
 for n in NAMES:
  src=HERE/n;dst=DEST/n;shutil.copyfile(src,dst);assert src.read_bytes()==dst.read_bytes();paths.append(dst.relative_to(REPO).as_posix())
 helper=HERE.parent/'boundary-input69/prepare_eye72.py';target=REPO/'experiments/pixel-pipeline/2026-11-01-boundary-input69/prepare_eye72.py';assert not target.exists();shutil.copyfile(helper,target);paths.append(target.relative_to(REPO).as_posix())
 doc=REPO/DOC;before=doc.read_bytes();add=(HERE/'HANDOFF72.txt').read_bytes();assert add not in before
 with doc.open('ab') as f:f.write(add)
 assert doc.read_bytes()==before+add;paths.append(DOC)
 git('add','--',*paths);assert set(git('diff','--cached','--name-only').splitlines())==set(paths);git('diff','--cached','--check')
 msg=HERE/'.commit72.txt';msg.write_text('Prepare bounded eye observer and record MCP approval blocker\n\nPreserve current Edit/dirty29 state. Fix monolithic dynamic namespace assembly without SDK edits; full observer still blocked before execution by SDK unsafe File.Move approval unsupported through MCP. No Play, capture, settings change, Assets import or product change. Record exact failure, current-state and31file SHA comparisons and prepared native PlayerSettings backup contract; no full-native restoration claim.\n',encoding='utf-8');print(git('commit','--file',str(msg)),flush=True)
 assert not git('diff','--cached','--name-only')
 for p,h in base['files'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 out={'commit':git('rev-parse','HEAD'),'files':len(paths),'PlayEntries':0,'captureCalled':False,'baseline31Unchanged':True,'stageEmpty':True,'status':'SDK_APPROVAL_INTERACTION_BLOCKED'};(HERE/'COMMIT72.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
