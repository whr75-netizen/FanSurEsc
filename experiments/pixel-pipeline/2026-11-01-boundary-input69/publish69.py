"""Selectively archive only this offline candidate; no Unity, Desktop or remote actions."""
from pathlib import Path
import hashlib,json,subprocess,shutil
HERE=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
DEST=REPO/'experiments/pixel-pipeline/2026-11-01-boundary-input69'
def git(*a):return subprocess.check_output(['git','-C',str(REPO),*a],text=True,encoding='utf-8').strip()
def main():
 assert git('rev-parse','HEAD')=='8f47ac86c1fb08fa788a5cba188487db4faa08c3'
 assert not git('diff','--cached','--name-only')
 baseline=json.loads((HERE.parent/'apply-capture66/RESUME68_DISK.json').read_text(encoding='utf-8'))
 for p,h in baseline['files'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 result=json.loads((HERE/'RESULT69.json').read_text());assert not result['adopted'] and result['acceptedOutputChanges']==0 and not result['referenceGate']['passesNonRegression']
 tests=json.loads((HERE/'TEST69.json').read_text());assert tests['passed']==10
 sources=sorted(p for p in HERE.iterdir() if p.is_file() and p.suffix in ['.py','.json','.npz','.png','.html'] and p.name!='COMMIT69.json');assert len(sources)<30 and sum(p.stat().st_size for p in sources)<16*1024*1024
 DEST.mkdir(exist_ok=True);paths=[]
 for src in sources:
  dst=DEST/src.name;shutil.copyfile(src,dst);assert src.read_bytes()==dst.read_bytes();paths.append(dst.relative_to(REPO).as_posix())
 # Verify imports, archived packet paths and actual source API references from the snapshot.
 print(subprocess.check_output([str(HERE.parents[1]/'full3d-angle/.venv/Scripts/python.exe'),'-B','-u','-X','utf8',str(DEST/'test69.py')],text=True,encoding='utf-8'),flush=True)
 paths.append('docs/ai/PIXEL_ALBEDO_20261030.md');git('add','--',*paths);assert set(git('diff','--cached','--name-only').splitlines())==set(paths);git('diff','--cached','--check')
 msg=HERE/'.commit69.txt';msg.write_text('Audit source-bound shade boundaries and reject tangent regression\n\nUse the saved frame94 packet only. Distinguish post-eye UV provenance from shade Q, retain64uncertain source contours as soft evidence and verify current UV/index/source hashes. Compare both diagonal area interpolants under source-local connection witnesses; preserve unknown support. Candidate changes2cells and improves reference position but worsens tangent cost, so keep original accepted output. Record actual silhouette/overlap counterexamples and observer48/256byte readback gaps. Ten offline regressions pass including rotations, thin stripe, hole, source split, schema rejection and archived snapshot imports. No Unity call, product integration, new palette or art-success claim.\n',encoding='utf-8');print(git('commit','--file',str(msg)),flush=True)
 assert not git('diff','--cached','--name-only')
 for p,h in baseline['files'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 receipt={'commit':git('rev-parse','HEAD'),'selectedFiles':len(paths),'baseline31HashesUnchanged':True,'productFilesChanged':0,'newUnityCalls':0,'adopted':False,'stageEmpty':True};(HERE/'COMMIT69.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
