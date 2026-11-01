from pathlib import Path
import sys,re,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=ROOT/'eye-motion81/run82';OUT=HERE/'motion85';OUT.mkdir(exist_ok=True)
assert not list(OUT.glob('*_REQUEST.json'))
st=json.loads(sorted((HERE/'run84').glob('STATE84*'))[-1].read_text());assert st['inputProbePassed83']and not st.get('error')and not st.get('restorationError')
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
m=(OLD/'MotionScope82.cs').read_text();assert m.count('#if UNITY_EDITOR')==1;m=m.replace('#if UNITY_EDITOR\n','').replace('#endif\n','');m=m.replace('["actual"]=V(GameInputBindings.ReadMovement()),','["actual"]=V(GameInputBindings.ReadMovement()),["background"]=InputSystem.settings.backgroundBehavior.ToString(),["editorPolicy"]=InputSystem.settings.editorInputBehaviorInPlayMode.ToString(),');(OUT/'MotionScope82.cs').write_bytes(m.encode())
s=(OLD/'Capture82Fixed.cs').read_text();s=re.sub(r'const string Root=@"[^"]+";',lambda _: 'const string Root=@"'+str(OUT)+'";',s,count=1).replace('STATE82-','STATE85-').replace('TRACE82-','TRACE85-').replace('eye82-','eye85-')
s=s.replace('["PlayEntries"]=0,','["revision85"]="83/84 proved missing UNITY_EDITOR symbol; direct Editor-host policy assignment only",["PlayEntries"]=0,');s=s.replace('EditorApplication.isPaused=false;return;}BeginExit();','return;}BeginExit();');(OUT/'Capture85.cs').write_bytes(s.encode())
B=ROOT/'apply-capture66';O=ROOT/'eye-observer73';U=ROOT/'uv-features64';deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',OUT/'MotionScope82.cs']
bundle(deps+[OUT/'Capture85.cs'],OUT/'RUN_Capture85.cs.txt');c=s.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("85 final motion observer, proven policy correction, compiled only");return;}\n void Prepared85(ExecutionResult result)\n {',1);(OUT/'Compile85.cs').write_bytes(c.encode());bundle(deps+[OUT/'Compile85.cs'],OUT/'RUN_Compile85.cs.txt')
for mode,prev,filename in [('Read85','Read82','CURRENT85.json'),('Post85','Post82','POST85.json')]:
 c=(OLD/(prev+'.cs')).read_text().replace(str(OLD),str(OUT)).replace('CURRENT82.json',filename).replace('POST82.json',filename);(OUT/(mode+'.cs')).write_bytes(c.encode());bundle([B/'Json58Linear66.cs',O/'CreateOnly73.cs',OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
c=(OLD/'Verify82.cs').read_text().replace(str(OLD),str(OUT)).replace('VERIFY82.json','VERIFY85.json');(OUT/'Verify85.cs').write_bytes(c.encode());bundle([B/'Json58Linear66.cs',B/'SerializedContent66.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',OUT/'Verify85.cs'],OUT/'RUN_Verify85.cs.txt')
r=(HERE/'run84/relay76.py').read_text().replace("'Verify84')","'Verify84','Read85','Compile85','Capture85','Post85','Verify85')");(OUT/'relay76.py').write_bytes(r.encode());(OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
assert not re.search(r'InputSystem\.settings\s*=(?!=)',s+m)and 'EditorApplication.isPaused=true'not in s and 'InputSystem.Update('not in m
print('85 prepared: original24-frame motion plan, only proven guard fix; no pointer or new setting changes')
