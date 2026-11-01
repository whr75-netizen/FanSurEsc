from pathlib import Path
import sys,json,hashlib,subprocess
HERE=Path(__file__).resolve().parent;OUT=HERE/'run';OUT.mkdir(exist_ok=True)
assert not list(OUT.glob('*_REQUEST.json')),'Inspect existing execution before rebuilding'
ROOT=HERE.parent;OLD=ROOT/'eye-input-recovery79/run';BASE=ROOT/'apply-capture66';O73=ROOT/'eye-observer73'
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
r=(OLD/'relay76.py').read_text(encoding='utf-8').replace("'Verify79')","'Verify79','Read80','Compile80','Smoke80','Post80')")
(OUT/'relay76.py').write_bytes(r.encode())
for mode,stem,name in [('Read80','Read77','CURRENT80.json'),('Post80','Post77','POST80.json')]:
 code=(OLD/(stem+'.cs')).read_text(encoding='utf-8').replace(str(OLD),str(OUT)).replace('CURRENT79.json',name).replace('POST79.json',name)
 code=code.replace('  var report=new Obj58', '''  var settings80=UnityEngine.InputSystem.InputSystem.settings;
  if(!settings80)throw new InvalidOperationException("InputSettings native object unavailable; no implicit replacement");
  var input80=new Obj58{["nativeId"]=settings80.GetEntityId().ToString(),["json"]=JsonUtility.ToJson(settings80),["alive"]=settings80?true:false,["hideFlags"]=settings80.hideFlags.ToString(),["path"]=AssetDatabase.GetAssetPath(settings80),["persistent"]=EditorUtility.IsPersistent(settings80),["devices"]=new Arr58(UnityEngine.InputSystem.InputSystem.devices.Select(d=>new Obj58{["id"]=d.deviceId,["layout"]=d.layout,["enabled"]=d.enabled,["native"]=d.native})),["keyboardCurrent"]=UnityEngine.InputSystem.Keyboard.current!=null?(Json58)UnityEngine.InputSystem.Keyboard.current.deviceId:null};
  var report=new Obj58''').replace('["dirty"]=dirty,["scenes"]=scenes','["dirty"]=dirty,["scenes"]=scenes,["input"]=input80')
 (OUT/(mode+'.cs')).write_bytes(code.encode());bundle([BASE/'Json58Linear66.cs',O73/'CreateOnly73.cs',OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
(OUT/'GLOBAL_NAMES66.json').write_bytes((ROOT/'eye-motion78/run/GLOBAL_NAMES66.json').read_bytes())
print('Prepared read-only80 preflight')
