"""Select completed offline source-curve/reader work only; no Unity or app actions."""
from pathlib import Path
import hashlib,json,subprocess,shutil
HERE=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
DEST=REPO/'experiments/pixel-pipeline/2026-11-01-boundary-input69'
NAMES=['schema69.py','run69.py','page69.py','INDEX.html','source_contours70.py','run_contours70.py','test_contours70.py','EyeReadback70.cs','UnityEyeBuffer70.cs','TestEyeReadback70.cs','test_eye70.py','EYE_TEST70.txt','EYE_TEST70.json','NEXT_INPUT70.json','EYE_CALLER70.patch','CURVE_PROJECTION70.npz','ORDERED_SOURCE70.json','CURVE_REPORT70.json','REFERENCE_AMBIGUITY70.json','CONTOUR_TEST70.json','SOURCE_CHAIN70.png','PROJECTED_CHAIN70.png','publish70.py']
def git(*a):return subprocess.check_output(['git','-C',str(REPO),*a],text=True,encoding='utf-8').strip()
def main():
 assert git('rev-parse','HEAD')=='c2c52fa14e91631f66db4c35079b227076f0195c'
 assert not git('diff','--cached','--name-only')
 baseline=json.loads((HERE.parent/'apply-capture66/RESUME68_DISK.json').read_text(encoding='utf-8'))
 for p,h in baseline['files'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 assert json.loads((HERE/'CONTOUR_TEST70.json').read_text())['passed']==14
 assert json.loads((HERE/'EYE_TEST70.json').read_text())['passed']==11
 assert not json.loads((HERE/'CURVE_REPORT70.json').read_text())['curveCorrectionApplied']
 paths=[]
 for name in NAMES:
  src=HERE/name;dst=DEST/name;shutil.copyfile(src,dst);assert src.read_bytes()==dst.read_bytes();paths.append(dst.relative_to(REPO).as_posix())
 python=str(HERE.parents[1]/'full3d-angle/.venv/Scripts/python.exe')
 for script in ['test_contours70.py','test69.py']:
  print(subprocess.check_output([python,'-B','-u','-X','utf8',str(DEST/script)],text=True,encoding='utf-8'),flush=True)
 # Offline tests regenerate only their reports. Include unchanged legacy TEST69
 # only when modified, otherwise preserve the narrowly enumerated path set.
 paths.append('docs/ai/PIXEL_ALBEDO_20261030.md');git('add','--',*paths);assert set(git('diff','--cached','--name-only').splitlines())==set(paths);git('diff','--cached','--check')
 msg=HERE/'.commit70.txt';msg.write_text('Preserve connected source evidence and prepare bounded eye ROI reads\n\nUnify64evidence tiers before ordered path tracing while preserving edge confidence and graph junctions. Keep source curve identity separate from geometry placements and visibility witnesses; no self-smoothed reference or pixel correction. Validate2/3/4step schema and sparse-reference ambiguity. Implement exact48/256byte eye layouts with row-sized typed reads, identity/budget/cancel/failure guards and unapplied direct-host caller patch. Eleven offline C# tests and actual Unity DLL adapter compile pass,14contour tests plus10legacy regressions pass. Record missing reference/sampler/eye inputs and optional nested6xROI contract. No Unity call/import/Play/product change/push.\n',encoding='utf-8');print(git('commit','--file',str(msg)),flush=True)
 assert not git('diff','--cached','--name-only')
 for p,h in baseline['files'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
 receipt={'commit':git('rev-parse','HEAD'),'selectedFiles':len(paths),'baseline31HashesUnchanged':True,'productFilesChanged':0,'newUnityCalls':0,'curveCorrectionApplied':False,'CSharpOfflineTests':11,'contourTests':14,'legacyTests':10,'stageEmpty':True};(HERE/'COMMIT70.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
