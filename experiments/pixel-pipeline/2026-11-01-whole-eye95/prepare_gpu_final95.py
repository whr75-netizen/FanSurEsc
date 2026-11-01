"""Prepare frozen seven-frame, three-field LUT replay. Does not execute Unity."""
from pathlib import Path
import shutil,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
OUT=HERE/'gpu-final';OUT.mkdir(exist_ok=False);INPUT=OUT/'input';INPUT.mkdir()
for p in (HERE/'final-input-source-cache').glob('*.bin'):shutil.copy2(p,INPUT/p.name)
assert len(list(INPUT.glob('*.bin')))==21
s=(ROOT/'native-feature89/FinalGPU89.cs').read_text().replace('ROOT_FINAL89',str(OUT)).replace('INPUT_FINAL89',str(INPUT)).replace('rows.Count==64','rows.Count==21').replace('FINAL_GPU89.json','FINAL_GPU95_FINAL.json')
s=s.replace('offline; this GPU kernel verifies literal final palette fill only','offline whole-feature source-ray and source-identity selector; three independent Float32 LUTs: colour, Native395 owner, depth')
s=s.replace('89 isolated saved-frame finite-palette final fill; no product/Play activation','95 seven-frame isolated LUT replay; no product or Play activation')
(OUT/'FinalGPU95Final.cs').write_text(s,encoding='utf-8')
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
bundle([ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'eye-observer73/CreateOnly73.cs',OUT/'FinalGPU95Final.cs'],OUT/'RUN_FinalGPU95Final.cs.txt')
relay=(HERE/'capture-scale-correct/relay95.py').read_text().replace("'Verify95B')","'Verify95B','FinalGPU95Final')")
(OUT/'relay95.py').write_text(relay,encoding='utf-8')
print('Prepared 21 frozen field packets; no Unity execution yet.')
