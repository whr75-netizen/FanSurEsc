from pathlib import Path
import sys,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'run';OUT.mkdir(exist_ok=True)
assert not list(OUT.glob('*_REQUEST.json')),'Existing81 execution requires inspection'
OLD=ROOT/'eye-motion78/run';SAFE=ROOT/'eye-motion78/MotionScope78.cs';BASE=ROOT/'apply-capture66';O73=ROOT/'eye-observer73';U=ROOT/'uv-features64'
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
r=(ROOT/'input-smoke80/run/relay76.py').read_text().replace("'VerifyContent80')","'VerifyContent80','Compile81','Capture81','Read81','Post81','Verify81')")
(OUT/'relay76.py').write_bytes(r.encode());(OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
# Reuse the audited no-pointer-replacement proposal. Only real bindings choose keys.
m=SAFE.read_text().replace('MotionScope78','MotionScope81').replace('78','81')
m=m.replace('static Key[] Keys(Vector2 v)', 'System.Collections.Generic.Dictionary<GameInputActionId,Key> bound=new System.Collections.Generic.Dictionary<GameInputActionId,Key>();\n Key[] Keys(Vector2 v)')
m=m.replace('k.Add(Key.W)','k.Add(bound[GameInputActionId.MoveUp])').replace('k.Add(Key.S)','k.Add(bound[GameInputActionId.MoveDown])').replace('k.Add(Key.D)','k.Add(bound[GameInputActionId.MoveRight])').replace('k.Add(Key.A)','k.Add(bound[GameInputActionId.MoveLeft])')
m=m.replace('keyboard.MakeCurrent();Time.captureDeltaTime=Delta;', '''keyboard.MakeCurrent();
  foreach(var id in new[]{GameInputActionId.MoveUp,GameInputActionId.MoveDown,GameInputActionId.MoveLeft,GameInputActionId.MoveRight}){var action=GameInputBindings.GetAction(id);var key=action?.controls.OfType<UnityEngine.InputSystem.Controls.KeyControl>().FirstOrDefault(c=>c.device==keyboard);if(action==null||!action.enabled||key==null)throw new InvalidOperationException("Missing actual keyboard action "+id);bound[id]=key.keyCode;}
  Time.captureDeltaTime=Delta;''')
m=m.replace('priorSettingsJSON=UnityEditor.EditorJsonUtility.ToJson(priorSettings)','priorSettingsJSON=JsonUtility.ToJson(priorSettings)').replace('UnityEditor.EditorJsonUtility.ToJson(priorSettings)==priorSettingsJSON','JsonUtility.ToJson(priorSettings)==priorSettingsJSON')
m=m.replace('native=input','native=input')
(OUT/'MotionScope81.cs').write_bytes(m.encode())
s=(OLD/'Capture78.cs').read_text().replace(str(OLD),str(OUT)).replace('78','81').replace('eye81-','eye81-')
s=s.replace('new MotionScope81(n);','new MotionScope81(n,output);')
s=s.replace(' MotionScope81 motion81;', ''' MotionScope81 motion81;
 UnityEngine.InputSystem.InputSettings settingsBefore81;string settingsJSON81;HideFlags settingsHide81;UnityEngine.InputSystem.InputDevice[] devicesBefore81;bool[] enabledBefore81;UnityEngine.InputSystem.Keyboard keyboardBefore81;
 void InputBackup81(){settingsBefore81=UnityEngine.InputSystem.InputSystem.settings;if(!settingsBefore81||EditorUtility.IsPersistent(settingsBefore81))throw new InvalidOperationException("Live nonpersistent input setting required; no replacement");settingsJSON81=JsonUtility.ToJson(settingsBefore81);settingsHide81=settingsBefore81.hideFlags;devicesBefore81=UnityEngine.InputSystem.InputSystem.devices.ToArray();enabledBefore81=devicesBefore81.Select(d=>d.enabled).ToArray();keyboardBefore81=UnityEngine.InputSystem.Keyboard.current;CreateOnly73.Text(Path.Combine(output,"EDIT_INPUT_BEFORE81.json"),new Obj58{["json"]=settingsJSON81,["nativeId"]=settingsBefore81.GetEntityId().ToString(),["hideFlags"]=settingsHide81.ToString(),["devices"]=new Arr58(devicesBefore81.Select(d=>new Obj58{["id"]=d.deviceId,["layout"]=d.layout,["enabled"]=d.enabled})),["keyboard"]=keyboardBefore81!=null?(Json58)keyboardBefore81.deviceId:null}.ToString());}
 void InputVerify81(){bool alive=settingsBefore81&&System.Object.ReferenceEquals(UnityEngine.InputSystem.InputSystem.settings,settingsBefore81),json=alive&&JsonUtility.ToJson(settingsBefore81)==settingsJSON81,flags=alive&&settingsBefore81.hideFlags==settingsHide81,devices=UnityEngine.InputSystem.InputSystem.devices.Count==devicesBefore81.Length&&devicesBefore81.All(d=>UnityEngine.InputSystem.InputSystem.devices.Contains(d)),enabled=devicesBefore81.Select((d,i)=>d.enabled==enabledBefore81[i]).All(v=>v),keyboard=System.Object.ReferenceEquals(UnityEngine.InputSystem.Keyboard.current,keyboardBefore81);report["editInputRestoration81"]=new Obj58{["sameAliveReference"]=alive,["exactJSON"]=json,["hideFlags"]=flags,["devicesSame"]=devices,["deviceEnabledStates"]=enabled,["keyboardSame"]=keyboard,["nativeId"]=alive?settingsBefore81.GetEntityId().ToString():"destroyed"};if(!alive||!json||!flags||!devices||!enabled||!keyboard)throw new InvalidOperationException("Input restoration mismatch after Play; no extra experiment");}
''')
s=s.replace('oldPlayerBackground=PlayerSettings.runInBackground;nativeBefore=NativeSnapshot73.Backup(Root);','InputBackup81();oldPlayerBackground=PlayerSettings.runInBackground;nativeBefore=NativeSnapshot73.Backup(Root);')
s=s.replace('report["observerRemoved"]=true;if(motion81','InputVerify81();report["observerRemoved"]=true;if(motion81')
# Runtime cached source metadata verification is kept; no buffer swap/reinitialization.
(OUT/'Capture81.cs').write_bytes(s.encode())
deps=[BASE/'Json58Linear66.cs',BASE/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O73/'EyeReadback73.cs',O73/'UnityEyeBuffer70.cs',O73/'CreateOnly73.cs',O73/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',OUT/'MotionScope81.cs']
bundle(deps+[OUT/'Capture81.cs'],OUT/'RUN_Capture81.cs.txt')
c=s.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("81 full normal-motion observer compiled only; no mutation");return;}\n void Prepared81(ExecutionResult result)\n {',1);(OUT/'Compile81.cs').write_bytes(c.encode());bundle(deps+[OUT/'Compile81.cs'],OUT/'RUN_Compile81.cs.txt')
for mode,old,filename in [('Read81','Read80','CURRENT81.json'),('Post81','Post80','POST81.json')]:
 c=(ROOT/'input-smoke80/run'/(old+'.cs')).read_text().replace(str(ROOT/'input-smoke80/run'),str(OUT)).replace('CURRENT80.json',filename).replace('POST80.json',filename);(OUT/(mode+'.cs')).write_bytes(c.encode());bundle([BASE/'Json58Linear66.cs',O73/'CreateOnly73.cs',OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
import re
assert not re.search(r'InputSystem\.settings\s*=(?!=)',s+m),'No settings pointer assignment'
for bad in ['InputSystem.Update(','ownedRest77','SetBlendShapeWeight','File.Move(','File.Delete(','Directory.Delete(','File.WriteAllText(']:assert bad not in s+m,bad
(HERE/'PLAN81.json').write_text(json.dumps({'status':'prepared_not_run','source':'actual77 GPU product, audited smoke80 queue-only input and safe MotionScope78 proposal','samples':{'phase':6,'walk':8,'turn':10},'warmups':{'phase':5,'walk':8},'poseDriver':'normal PlayerMovement.Update/Animator/Gameplay397.Present, no history reset','scope':'same settings object, exact JSON backup before Play and runtime; only transient2 fields, owned virtual keyboard, temporary movement/Animator speeds/captureDelta; normal exit restores','readbacks':'bounded padded eye ROI/samples/counts/records/source geometry; full character only first frame','limits':'one short trajectory, not full gait/long motion/bank coverage; input script repeat mapping verified separately80'},indent=2)+'\n')
print('81 prepared24 frames; no settings setter/clone/manualUpdate or rest-buffer swap')
