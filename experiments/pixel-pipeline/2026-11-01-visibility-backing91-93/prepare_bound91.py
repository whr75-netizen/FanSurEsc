from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=HERE/'capture91';OUT=HERE/'capture91b';IMP=HERE/'import91b'
OUT.mkdir(exist_ok=False);IMP.mkdir(exist_ok=False)
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
B=ROOT/'apply-capture66';O=ROOT/'eye-observer73';U=ROOT/'uv-features64';base=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs']
importSource=(HERE/'import91/Import91.cs').read_text().replace(str(HERE/'import91'),str(IMP));(IMP/'Import91B.cs').write_text(importSource,encoding='utf-8')
for mode in ['PreImport91B','Import91B']:bundle(base+[IMP/'Import91B.cs'],IMP/('RUN_'+mode+'.cs.txt'))
relay=(OLD/'relay91.py').read_text().replace("'Verify91')","'Verify91','PreImport91B','Import91B','Read91B','Compile91B','Capture91B','Post91B','Verify91B')")
for folder in [OUT,IMP]:(folder/'relay91.py').write_text(relay,encoding='utf-8')
(OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
s=(OLD/'Capture91.cs').read_text().replace(str(OLD),str(OUT)).replace('eye91-','eye91b-');(OUT/'Capture91B.cs').write_text(s,encoding='utf-8');c=s.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("91B compile-only; no Play");return;}\n void Prepared91B(ExecutionResult result)\n {',1);assert 'void Prepared91B'in c;(OUT/'Compile91B.cs').write_text(c,encoding='utf-8')
deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',ROOT/'native-feature89/NativeRetarget89.cs',HERE/'CurrentRasters91.cs',HERE/'MotionScope91.cs']
for mode in ['Compile91B','Capture91B']:bundle(deps+[OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
for mode in ['Read','Post','Verify']:
 oldname=mode+'91';newname=mode+'91B';source=(OLD/(oldname+'.cs')).read_text().replace(str(OLD),str(OUT)).replace('CURRENT91.json','CURRENT91B.json').replace('POST91.json','POST91B.json').replace('VERIFY91.json','VERIFY91B.json');(OUT/(newname+'.cs')).write_text(source,encoding='utf-8');bundle((base if mode=='Verify'else[B/'Json58Linear66.cs',O/'CreateOnly73.cs'])+[OUT/(newname+'.cs')],OUT/('RUN_'+newname+'.cs.txt'))
print('Prepared actual ambient-input A/B with unbound group0, bound group1/backing; no execution.')
