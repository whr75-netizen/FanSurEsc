from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=ROOT/'final-eye95/capture-scale-correct'
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
OUT=HERE/'preflight';OUT.mkdir(exist_ok=False)
s=(ROOT/'final-eye95/post-final/Post95Final.cs').read_text().replace(str(ROOT/'final-eye95/post-final/POST95FINAL.json'),str(OUT/'CURRENT96.json')).replace(str(ROOT/'final-eye95/post-final/NATIVE95FINAL.json'),str(OUT/'NATIVE96.json'))
(OUT/'Read96.cs').write_text(s,encoding='utf-8')
bundle([ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'apply-capture66/SerializedContent66.cs',ROOT/'eye-observer73/CreateOnly73.cs',ROOT/'eye-observer73/NativeSnapshot73.cs',OUT/'Read96.cs'],OUT/'RUN_Read96.cs.txt')
relay=(OLD/'relay95.py').read_text().replace("'Verify95B')","'Verify95B','Read96')");(OUT/'relay96.py').write_text(relay,encoding='utf-8')
print('Prepared read-only preflight; no Unity mutation.')
