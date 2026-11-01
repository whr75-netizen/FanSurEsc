"""Archive only completed offline visibility evidence and existing handoff."""
from pathlib import Path
import subprocess,json,hashlib,shutil
HERE=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
DEST=REPO/'experiments/pixel-pipeline/2026-11-01-boundary-input69'
NAMES=['opaque_visibility71.py','test_visibility71.py','run_visibility71.py','VISIBILITY_TEST71.json','VISIBILITY71.json','OPAQUE_SEGMENTS71.npz','OPAQUE_SAMPLES71.json','REPRESENTATIVE_VISIBILITY71.json','OPAQUE_LINE71.png','publish71.py']
DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
def git(*a):return subprocess.check_output(['git','-C',str(REPO),*a],text=True,encoding='utf-8').strip()
def main():
 assert git('rev-parse','HEAD')=='ed807fa889ae05ac7559eb9c3196476eab4df3fb'
 assert not git('diff','--cached','--name-only')
 assert not git('diff','--name-only','--',DOC),'Existing handoff changed; inspect before merging'
 baseline=json.loads((HERE.parent/'apply-capture66/RESUME68_DISK.json').read_text(encoding='utf-8'))
 for p,h in baseline['files'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 result=json.loads((HERE/'VISIBILITY71.json').read_text());assert result['newUnityCalls']==0 and not result['curveCorrectionApplied'];assert json.loads((HERE/'VISIBILITY_TEST71.json').read_text())['passed']==10
 paths=[]
 for name in NAMES:
  src=HERE/name;dst=DEST/name;assert not dst.exists();shutil.copyfile(src,dst);assert src.read_bytes()==dst.read_bytes();paths.append(dst.relative_to(REPO).as_posix())
 doc=REPO/DOC;before=doc.read_bytes();addition=(HERE/'HANDOFF71.txt').read_bytes();assert b'## '+ '\uac00\ub9bc71'.encode() not in before
 with doc.open('ab') as f:f.write(addition)
 assert doc.read_bytes()==before+addition;paths.append(DOC)
 git('add','--',*paths);assert set(git('diff','--cached','--name-only').splitlines())==set(paths);git('diff','--cached','--check')
 msg=HERE/'.commit71.txt';msg.write_text('Audit continuous opaque visibility from captured source geometry\n\nPartition projected source segments by all evaluated source triangles and depth crossings. Compare1734 actual GPU samples without hiding28 opaque-model disagreements, preserve per-interval uncertainty and actual alpha/cull limits. Ten analytic offline tests pass. No pixel correction, new candidate, Unity call, import, Play or product change.\n',encoding='utf-8');print(git('commit','--file',str(msg)),flush=True)
 assert not git('diff','--cached','--name-only')
 for p,h in baseline['files'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 receipt={'commit':git('rev-parse','HEAD'),'selectedFiles':len(paths),'baseline31HashesUnchanged':True,'productFilesChanged':0,'UnityCalls':0,'tests':10,'pixelCorrection':False,'stageEmpty':True};(HERE/'COMMIT71.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
