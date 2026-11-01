from pathlib import Path
import json,hashlib,subprocess,shutil,sys
R=Path(__file__).resolve().parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');DEST=REPO/'experiments/pixel-pipeline/2026-11-01-whole-eye75';DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
NAMES=['joint75.py','test75.py','audit75.py','publish75.py','RESULT75.json','TEST75.json','SOURCE_FLOW75.json','SOURCE_BANK75.png','SOURCE_BANK75-nearest24.png','INDEX.html']
def git(*a):return subprocess.check_output(['git','-C',str(REPO),*a],text=True,encoding='utf-8').strip()
def main():
 assert git('rev-parse','HEAD')=='bc9d00ac77a918788fc661bdcad3fae5ac007b87';assert not git('diff','--cached','--name-only');assert not git('diff','--name-only','--',DOC)
 keys=json.loads((R.parent/'eye-observer73/DISK_BEFORE73.json').read_text())['files'];before={p:hashlib.sha256((REPO/p).read_bytes()).hexdigest()for p in keys};result=json.loads((R/'RESULT75.json').read_text());assert not result['jointCandidateRendered']and result['newUnityCalls']==0;assert json.loads((R/'TEST75.json').read_text())['passed']==10
 for src in result['bankSources']:assert hashlib.sha256(Path(src['path']).read_bytes()).hexdigest()==src['sha256']
 DEST.mkdir(exist_ok=False);paths=[]
 for n in NAMES:shutil.copyfile(R/n,DEST/n);assert (R/n).read_bytes()==(DEST/n).read_bytes();paths.append((DEST/n).relative_to(REPO).as_posix())
 sys.path.insert(0,str(DEST));from joint75 import hall
 for row in result['current73ConditionalCapacity']:
  ds={k:set(map(tuple,v))for k,v in row['domains'].items()};assert hall(ds,row['allBankCellsVisibleDemand'])==row['capacityUnderActualPostClassifyCounts']
 doc=REPO/DOC;old=doc.read_bytes();add=(R/'HANDOFF75.txt').read_bytes();assert add not in old
 with doc.open('ab')as f:f.write(add)
 assert doc.read_bytes()==old+add;paths.append(DOC)
 git('add','--',*paths);assert set(git('diff','--cached','--name-only').splitlines())==set(paths);git('diff','--cached','--check')
 msg=R/'.commit75.txt';msg.write_text('Restore eye colour-bank provenance and audit whole-eye constraints\n\nDecode actual Template assets and match20 reference cells plus10 current GPU Own samples at RGB8. Separate colour atlas/state geometry from complete visible keyforms, and cached identity from visible occupancy. Joint Hall capacity and raw/count/S0 ablations show why freezing counts as source support blocks all12 cases. No S0 removal, fabricated lid/state, full joint candidate or Unity call. Ten offline constraint tests pass; retain exact missing contract/observation scope.\n',encoding='utf-8');print(git('commit','--file',str(msg)),flush=True)
 assert not git('diff','--cached','--name-only')
 for p,h in before.items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 receipt={'commit':git('rev-parse','HEAD'),'files':len(paths),'UnityCalls':0,'productChanges':0,'newJointRGB':False,'disk31Unchanged':True,'stageEmpty':True}
 with(R/'COMMIT75.json').open('x')as f:json.dump(receipt,f,indent=2)
 print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
