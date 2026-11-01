from pathlib import Path
import sys,re,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=HERE/'run';OUT=HERE/'run84';OUT.mkdir(exist_ok=True)
assert not list(OUT.glob('*_REQUEST.json'));assert json.loads((OLD/'SYMBOL83.json').read_text())['UNITY_EDITOR']is False
assert all(x['equal']is True for x in json.loads((OLD/'VERIFY83.json').read_text())['nativeComparisons'])
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
m=(OLD/'MotionScope83.cs').read_text();assert m.count('#if UNITY_EDITOR')==1;m=m.replace('#if UNITY_EDITOR\n','').replace('#endif\n','');(OUT/'MotionScope83.cs').write_bytes(m.encode())
p=(OLD/'InputEventProbe83.cs').read_text().replace('["updateType"]=InputState.currentUpdateType.ToString(),','["updateType"]=InputState.currentUpdateType.ToString(),["settingsId"]=InputSystem.settings.GetEntityId().ToString(),["background"]=InputSystem.settings.backgroundBehavior.ToString(),["editorPolicy"]=InputSystem.settings.editorInputBehaviorInPlayMode.ToString(),');(OUT/'InputEventProbe83.cs').write_bytes(p.encode())
s=(OLD/'Probe83.cs').read_text();s=re.sub(r'const string Root=@"[^"]+";',lambda _: 'const string Root=@"'+str(OUT)+'";',s,count=1).replace('STATE83-','STATE84-').replace('TRACE83-','TRACE84-').replace('eye83-','eye84-');s=s.replace('["PlayEntries"]=0,','["revision84"]="Only removed UNITY_EDITOR guard around existing planned policy assignment; added read-only policy getters",["PlayEntries"]=0,');(OUT/'Probe84.cs').write_bytes(s.encode())
B=ROOT/'apply-capture66';O=ROOT/'eye-observer73';U=ROOT/'uv-features64';deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',OUT/'InputEventProbe83.cs',OUT/'MotionScope83.cs']
bundle(deps+[OUT/'Probe84.cs'],OUT/'RUN_Probe84.cs.txt');c=s.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("84 guard-only input routing correction compiled only");return;}\n void Prepared84(ExecutionResult result)\n {',1);(OUT/'Compile84.cs').write_bytes(c.encode());bundle(deps+[OUT/'Compile84.cs'],OUT/'RUN_Compile84.cs.txt')
for mode,prev,filename in [('Read84','Read83','CURRENT84.json'),('Post84','Post83','POST84.json')]:
 c=(OLD/(prev+'.cs')).read_text().replace(str(OLD),str(OUT)).replace('CURRENT83.json',filename).replace('POST83.json',filename);(OUT/(mode+'.cs')).write_bytes(c.encode());bundle([B/'Json58Linear66.cs',O/'CreateOnly73.cs',OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
c=(OLD/'Verify83.cs').read_text().replace(str(OLD),str(OUT)).replace('VERIFY83.json','VERIFY84.json');(OUT/'Verify84.cs').write_bytes(c.encode());bundle([B/'Json58Linear66.cs',B/'SerializedContent66.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',OUT/'Verify84.cs'],OUT/'RUN_Verify84.cs.txt')
r=(OLD/'relay76.py').read_text().replace("'Symbol83')","'Symbol83','Compile84','Read84','Probe84','Post84','Verify84')");(OUT/'relay76.py').write_bytes(r.encode());(OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
assert not re.search(r'InputSystem\.settings\s*=(?!=)',s+m+p)
print('84 prepared: exact83 input/order, guard-only fix, runtime policy readback')
