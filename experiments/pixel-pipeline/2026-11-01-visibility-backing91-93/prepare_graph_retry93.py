from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=HERE/'capture93';OUT=HERE/'capture93b';OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
B=ROOT/'apply-capture66';O=ROOT/'eye-observer73';U=ROOT/'uv-features64';base=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs']
s=(OLD/'Capture93.cs').read_text().replace(str(OLD),str(OUT)).replace('eye93-','eye93b-');(OUT/'Capture93B.cs').write_text(s,encoding='utf-8');compile=s.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("93B normal default-renderer path compiled; no Play");return;}\n void Prepared93B(ExecutionResult result)\n {',1);assert 'void Prepared93B'in compile;(OUT/'Compile93B.cs').write_text(compile,encoding='utf-8')
deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',ROOT/'native-feature89/NativeRetarget89.cs',HERE/'GraphSources93.cs',HERE/'MotionScope91.cs']
for mode in['Compile93B','Capture93B']:bundle(deps+[OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
relay=(OLD/'relay93.py').read_text().replace("'CompileFinal93')","'CompileFinal93','Read93B','Compile93B','Capture93B','Post93B','Verify93B')");(OUT/'relay93.py').write_text(relay,encoding='utf-8');(OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
for mode in['Read','Post','Verify']:
 source=(OLD/(mode+'93.cs')).read_text().replace(str(OLD),str(OUT)).replace('CURRENT93.json','CURRENT93B.json').replace('POST93.json','POST93B.json').replace('VERIFY93.json','VERIFY93B.json');(OUT/(mode+'93B.cs')).write_text(source,encoding='utf-8');bundle((base if mode=='Verify'else[B/'Json58Linear66.cs',O/'CreateOnly73.cs'])+[OUT/(mode+'93B.cs')],OUT/('RUN_'+mode+'93B.cs.txt'))
print('Narrow fix matches installed URP GetRenderer fallback; no component creation, no pause change.')
