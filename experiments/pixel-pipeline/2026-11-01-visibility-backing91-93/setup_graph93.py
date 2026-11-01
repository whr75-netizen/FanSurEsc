from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=HERE/'capture91b';OUT=HERE/'capture93';OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
B=ROOT/'apply-capture66';O=ROOT/'eye-observer73';U=ROOT/'uv-features64'
s=(OLD/'Capture91B.cs').read_text().replace(str(OLD),str(OUT)).replace('eye91b-','eye93-').replace('STATE91-','STATE93-').replace('TRACE91-','TRACE93-').replace('CurrentRasters91','GraphSources93').replace('current91.Render();','current91.AssertRendered();');(OUT/'Capture93.cs').write_text(s,encoding='utf-8');compile=s.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("93 in-graph source compile-only; no Play");return;}\n void Prepared93(ExecutionResult result)\n {',1);assert 'void Prepared93'in compile;(OUT/'Compile93.cs').write_text(compile,encoding='utf-8')
deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',ROOT/'native-feature89/NativeRetarget89.cs',HERE/'GraphSources93.cs',HERE/'MotionScope91.cs']
for mode in['Compile93','Capture93']:bundle(deps+[OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
relay=(HERE/'capture92/relay92.py').read_text().replace("'Verify92')","'Verify92','Read93','Compile93','Capture93','Post93','Verify93')");(OUT/'relay93.py').write_text(relay,encoding='utf-8');(OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
for mode in['Read','Post','Verify']:
 source=(OLD/(mode+'91B.cs')).read_text().replace(str(OLD),str(OUT)).replace('CURRENT91B.json','CURRENT93.json').replace('POST91B.json','POST93.json').replace('VERIFY91B.json','VERIFY93.json');(OUT/(mode+'93.cs')).write_text(source,encoding='utf-8');bundle(([B/'Json58Linear66.cs',B/'SerializedContent66.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs']if mode=='Verify'else[B/'Json58Linear66.cs',O/'CreateOnly73.cs'])+[OUT/(mode+'93.cs')],OUT/('RUN_'+mode+'93.cs.txt'))
print('Prepared same original8frame Close test; public EnqueuePass with explicit graph shadow inputs. No persistent renderer feature/Assets changes.')
