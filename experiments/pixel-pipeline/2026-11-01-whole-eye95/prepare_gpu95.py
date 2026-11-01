from pathlib import Path
import shutil,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'gpu-closed';OUT.mkdir(exist_ok=False);INPUT=OUT/'input';INPUT.mkdir()
for p in (HERE/'final-input-joint').glob('0104-field*.bin'):shutil.copy2(p,INPUT/p.name)
assert len(list(INPUT.glob('*.bin')))==3
s=(ROOT/'native-feature89/FinalGPU89.cs').read_text().replace('ROOT_FINAL89',str(OUT)).replace('INPUT_FINAL89',str(INPUT)).replace('rows.Count==64','rows.Count==3').replace('FINAL_GPU89.json','FINAL_GPU95_CLOSED.json')
s=s.replace('offline; this GPU kernel verifies literal final palette fill only','offline full source-ray joint selector; three separate exact Float32 LUT applications for actual colour/owner/depth schema')
s=s.replace('89 isolated saved-frame finite-palette final fill; no product/Play activation','95 isolated closed-state colour/owner/depth LUT fill; no product or Play activation')
(OUT/'FinalGPU95Closed.cs').write_text(s,encoding='utf-8')
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
bundle([ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'eye-observer73/CreateOnly73.cs',OUT/'FinalGPU95Closed.cs'],OUT/'RUN_FinalGPU95Closed.cs.txt')
relay=(HERE/'capture-scale-correct/relay95.py').read_text().replace("'Verify95B')","'Verify95B','FinalGPU95Closed')");(OUT/'relay95.py').write_text(relay,encoding='utf-8')
print('Prepared one fully resolved evaluated-Closed packet: colour, actual owner, depth. No GPU execution yet.')
