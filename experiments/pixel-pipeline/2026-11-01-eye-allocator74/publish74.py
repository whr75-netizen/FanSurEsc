from pathlib import Path
import json,hashlib,subprocess,shutil
R=Path(__file__).resolve().parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');DEST=REPO/'experiments/pixel-pipeline/2026-11-01-eye-allocator74';DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
NAMES=['allocator74.py','test74.py','run74.py','source_centre74.py','publish74.py','TEST74.json','RESULT74.json','SOURCE_CENTRE74.json','OLD47_COMPARISON1x.png','OLD47_COMPARISON12x.png','CURRENT73_UNCHANGED.png','CURRENT73_UNCHANGED20x.png','INDEX.html']
def git(*a):return subprocess.check_output(['git','-C',str(REPO),*a],text=True,encoding='utf-8').strip()
def main():
 assert git('rev-parse','HEAD')=='5fbfac0ae30d890ed5fa46852d345a17df0792af';assert not git('diff','--cached','--name-only');assert not git('diff','--name-only','--',DOC)
 keys=json.loads((R.parent/'eye-observer73/DISK_BEFORE73.json').read_text())['files'];before={p:hashlib.sha256((REPO/p).read_bytes()).hexdigest() for p in keys}
 assert json.loads((R/'TEST74.json').read_text())['passed']==16;assert not json.loads((R/'RESULT74.json').read_text())['candidateAdopted']
 DEST.mkdir(exist_ok=False);paths=[]
 for n in NAMES:shutil.copyfile(R/n,DEST/n);assert (R/n).read_bytes()==(DEST/n).read_bytes();paths.append((DEST/n).relative_to(REPO).as_posix())
 py=str(R.parents[1]/'full3d-angle/.venv/Scripts/python.exe')
 for script,args in [('run74.py',['--verify']),('source_centre74.py',[])]:print(subprocess.check_output([py,'-B','-u','-X','utf8',str(DEST/script),*args],text=True,encoding='utf-8'),flush=True)
 doc=REPO/DOC;initial=doc.read_bytes();addition=(R/'HANDOFF74.txt').read_bytes();assert addition not in initial
 with doc.open('ab')as f:f.write(addition)
 assert doc.read_bytes()==initial+addition;paths.append(DOC)
 git('add','--',*paths);assert set(git('diff','--cached','--name-only').splitlines())==set(paths);git('diff','--cached','--check')
 msg=R/'.commit74.txt';msg.write_text('Audit eye allocation topology and retain rejected connected-subset candidate\n\nReuse current73 and frozen47/49/52/53 inputs. Conditional fixed-budget connectivity removes6historical diagonal allocations and leaves73 unchanged, but source evidence/centres and lower-like/sclera replacement expose tradeoffs. Sixteen offline tests include temporal counterexample. No art/temporal success, product adoption or Unity call.\n',encoding='utf-8');print(git('commit','--file',str(msg)),flush=True)
 assert not git('diff','--cached','--name-only')
 for p,h in before.items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 receipt={'commit':git('rev-parse','HEAD'),'files':len(paths),'UnityCalls':0,'productChanges':0,'candidateAdopted':False,'disk31UnchangedDuringArchive':True,'stageEmpty':True}
 with (R/'COMMIT74.json').open('x')as f:json.dump(receipt,f,indent=2)
 print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
