using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.Controls;
using UnityEngine.InputSystem.LowLevel;
using FantasySurvival.Controls;
using FantasySurvival.SceneFlow;

// A bounded normal-game input smoke. No settings pointer assignment, clones,
// manual InputSystem.Update, direct StepMove, render/history reset or GPU reads.
internal class CommandScript:IRunCommand
{
 const string Root=@"ROOT80";
 const int Samples=12; // twice: two Up, two Right, two released frames.
 InputSettings settings;string settingsJson;HideFlags settingsFlags;
 InputSettings.BackgroundBehavior background;InputSettings.EditorInputBehaviorInPlayMode editorBehavior;
 Keyboard previousKeyboard,ownedKeyboard;InputActionAsset actions;string bindingsJson;
 InputDevice[] devices;bool[] devicesEnabled;InputActionMap map;bool mapEnabled;
 Key upKey,rightKey;NativePlayer395 native;PlayerMovement movement;Animator animator;Camera camera;
 Vector3 previousPosition;Quaternion previousFacing;int sampleIndex,lastSerial,dynamicUpdates,armedUpdate;
 Arr58 samples=new Arr58(),updates=new Arr58();Obj58 report;
 GlobalJournal64 journal;Arr58 nativeBefore;
 bool oldBackground,oldPlayerBackground,oldOptions,oldPause,started,exiting,finished,inputStarted;
 EnterPlayModeOptions oldFlags;RenderPipelineAsset oldG,oldQ;float oldTime,oldCapture;int domain,exitTicks,state;
 double start,lastTrace;string output;
 static Arr58 V(Vector2 x)=>new Arr58(x.x,x.y);
 static Arr58 V(Vector3 x)=>new Arr58(x.x,x.y,x.z);
 static Arr58 Q(Quaternion x)=>new Arr58(x.x,x.y,x.z,x.w);
 static Arr58 DeviceRows()=>new Arr58(InputSystem.devices.Select(d=>new Obj58{["id"]=d.deviceId,["layout"]=d.layout,["enabled"]=d.enabled,["native"]=d.native}));
 static Arr58 Scenes(){var a=new Arr58();for(int i=0;i<SceneManager.sceneCount;i++){var s=SceneManager.GetSceneAt(i);a.Add(new Obj58{["path"]=s.path,["dirty"]=s.isDirty,["active"]=s==SceneManager.GetActiveScene()});}return a;}
 static Arr58 Dirty()=>new Arr58(Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o)&&(AssetDatabase.GetAssetPath(o).StartsWith("Assets/")||AssetDatabase.GetAssetPath(o).StartsWith("ProjectSettings/"))).Select(o=>new Obj58{["path"]=AssetDatabase.GetAssetPath(o),["type"]=o.GetType().FullName,["id"]=o.GetEntityId().ToString()}));
 void Save(string stage){report["stage"]=stage;report["utc"]=DateTime.UtcNow.ToString("O");report["samples"]=samples;report["inputUpdates"]=updates;CreateOnly73.Text(Path.Combine(Root,"STATE80-"+(state++).ToString("D3")+"-"+stage+".json"),report.ToString());}
 public void Execute(ExecutionResult result)
 {
  if(File.Exists(Path.Combine(Root,"SMOKE_STARTED80.marker")))throw new IOException("Existing execution must be inspected; no repeat");
  if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required");
  if(Enumerable.Range(0,SceneManager.sceneCount).Select(SceneManager.GetSceneAt).Any(s=>s.isDirty))throw new InvalidOperationException("Unsaved scene requires preservation before smoke");
  settings=InputSystem.settings;if(!settings||EditorUtility.IsPersistent(settings))throw new InvalidOperationException("Live nonpersistent recovered settings required; never replace");
  settingsJson=JsonUtility.ToJson(settings);settingsFlags=settings.hideFlags;background=settings.backgroundBehavior;editorBehavior=settings.editorInputBehaviorInPlayMode;
  if(settings.updateMode!=InputSettings.UpdateMode.ProcessEventsInDynamicUpdate)throw new InvalidOperationException("Normal Dynamic input path required; not changing updateMode");
  previousKeyboard=Keyboard.current;devices=InputSystem.devices.ToArray();devicesEnabled=devices.Select(d=>d.enabled).ToArray();actions=InputSystem.actions;
  if(!actions)throw new InvalidOperationException("Existing project action asset unavailable");bindingsJson=actions.ToJson();
  oldBackground=Application.runInBackground;oldPlayerBackground=PlayerSettings.runInBackground;oldOptions=EditorSettings.enterPlayModeOptionsEnabled;oldFlags=EditorSettings.enterPlayModeOptions;oldPause=EditorApplication.isPaused;oldTime=Time.timeScale;oldCapture=Time.captureDeltaTime;oldG=GraphicsSettings.defaultRenderPipeline;oldQ=QualitySettings.renderPipeline;domain=AppDomain.CurrentDomain.Id;
  output=Path.Combine(Root,"smoke80-"+DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ")+"-"+Guid.NewGuid().ToString("N").Substring(0,8));Directory.CreateDirectory(output);
  report=new Obj58{["sourceId"]=Path.GetFileName(output),["output"]=output,["PlayEntries"]=0,["beforeSettingsId"]=settings.GetEntityId().ToString(),["beforeSettingsJSON"]=settingsJson,["beforeHideFlags"]=settingsFlags.ToString(),["beforeSettingsObjectCount"]=Resources.FindObjectsOfTypeAll<InputSettings>().Length,["beforeDevices"]=DeviceRows(),["beforeKeyboardId"]=previousKeyboard!=null?(Json58)previousKeyboard.deviceId:null,["beforeDirty"]=Dirty(),["beforeScenes"]=Scenes(),["beforeRTCount"]=Resources.FindObjectsOfTypeAll<RenderTexture>().Length,["optionsBefore"]=new Arr58(oldOptions,(int)oldFlags),["timeBefore"]=new Arr58(oldTime,oldCapture,oldPause),["backgroundBefore"]=new Arr58(oldBackground,oldPlayerBackground),["pipelineBefore"]=new Arr58(AssetDatabase.GetAssetPath(oldG),AssetDatabase.GetAssetPath(oldQ)),["settingsPointerReplacementAllowed"]=false,["manualInputUpdateCalls"]=0,["gpuReadbacks"]=0,["plannedSamples"]=Samples};
  CreateOnly73.Text(Path.Combine(output,"INPUT_SETTINGS_BEFORE80.json"),settingsJson);CreateOnly73.Text(Path.Combine(output,"ACTIONS_BEFORE80.json"),bindingsJson);Save("external-backup-before-mutation");
  nativeBefore=NativeSnapshot73.Backup(Root);
  var specs=Json58.Parse(File.ReadAllText(Path.Combine(Root,"GLOBAL_NAMES66.json"))).Select(o=>new GlobalJournal64.Spec{name=(string)o["name"],kind=(string)o["type"]=="Int"?GlobalJournal64.Kind.LegacyInt:(GlobalJournal64.Kind)Enum.Parse(typeof(GlobalJournal64.Kind),(string)o["type"])}).ToArray();
  journal=GlobalJournal64.Snapshot(Path.GetFileName(output),Path.Combine(output,"GLOBALS_BEFORE80.bin"),specs);journal.RequireRecoverable(specs.Select(s=>s.name));foreach(var s in specs)journal.BeforeMutation(s.name);
  CreateOnly73.Text(Path.Combine(Root,"SMOKE_STARTED80.marker"),"Settings reference preserved; one bounded normal-input smoke");
  try{started=true;start=EditorApplication.timeSinceStartup;EditorApplication.update+=Tick;Application.runInBackground=true;EditorSettings.enterPlayModeOptionsEnabled=true;EditorSettings.enterPlayModeOptions=EnterPlayModeOptions.DisableDomainReload;report["PlayEntries"]=1;Save("entering-Play");EditorApplication.EnterPlaymode();result.Log("80 normal-input smoke armed; settings pointer preserved; observer exits/restores");}
  catch(Exception e){report["error"]=e.ToString();BeginExit();}
 }
 Key BoundKey(GameInputActionId id)
 {
  var a=GameInputBindings.GetAction(id);if(a==null||!a.enabled)throw new InvalidOperationException("Existing movement action disabled: "+id);
  var key=a.controls.OfType<KeyControl>().FirstOrDefault(c=>c.device==ownedKeyboard);if(key==null)throw new InvalidOperationException("No actual keyboard binding for "+id+"; no binding overrides");return key.keyCode;
 }
 void StartInput(NativePlayer395 n)
 {
  native=n;movement=n.player.GetComponent<PlayerMovement>();animator=n.host.main.motion.animation.target;var shell=PersistentGameplayShell.Instance;camera=shell!=null?shell.PlayerCamera:null;map=GameInputBindings.GameplayMap;mapEnabled=map!=null&&map.enabled;
  if(!movement||!movement.isActiveAndEnabled||!animator||!camera||!camera.isActiveAndEnabled||!mapEnabled)throw new InvalidOperationException("Normal movement/camera/action map unavailable");
  if(GameInputBindings.ReadMovement()!=Vector2.zero)throw new InvalidOperationException("Existing input already active; not overriding user input");
  if(!settings||!System.Object.ReferenceEquals(InputSystem.settings,settings)||JsonUtility.ToJson(settings)!=settingsJson)throw new InvalidOperationException("Settings changed during Play entry; no overwrite");
  CreateOnly73.Text(Path.Combine(output,"RUNTIME_BEFORE80.json"),new Obj58{["settingsJSON"]=JsonUtility.ToJson(settings),["settingsId"]=settings.GetEntityId().ToString(),["deviceList"]=DeviceRows(),["position"]=V(n.player.position),["rotation"]=Q(animator.transform.rotation),["movementSpeed"]=movement.speed,["animatorSpeed"]=animator.speed,["mapEnabled"]=mapEnabled,["captureDelta"]=Time.captureDeltaTime,["frame"]=Time.frameCount,["serial"]=n.host.main.renderedSerial335}.ToString());
  inputStarted=true;settings.backgroundBehavior=InputSettings.BackgroundBehavior.IgnoreFocus;settings.editorInputBehaviorInPlayMode=InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;
  ownedKeyboard=InputSystem.AddDevice<Keyboard>("Eye80 owned GAME input smoke");ownedKeyboard.MakeCurrent();upKey=BoundKey(GameInputActionId.MoveUp);rightKey=BoundKey(GameInputActionId.MoveRight);if(upKey==rightKey)throw new InvalidOperationException("Actual Up/Right binding conflict");
  report["resolvedUpKey"]=upKey.ToString();report["resolvedRightKey"]=rightKey.ToString();report["ownedKeyboardId"]=ownedKeyboard.deviceId;
  Time.captureDeltaTime=1f/60;previousPosition=n.player.position;previousFacing=animator.transform.rotation;lastSerial=n.host.main.renderedSerial335;InputSystem.onAfterUpdate+=AfterInput;Queue();Save("normal-input-queued");
 }
 Vector2 Requested(){switch((sampleIndex/2)%3){case 0:return Vector2.up;case 1:return Vector2.right;default:return Vector2.zero;}}
 void Queue(){var v=Requested();InputSystem.QueueStateEvent(ownedKeyboard,new KeyboardState(v.y>0?new[]{upKey}:v.x>0?new[]{rightKey}:new Key[0]));armedUpdate=dynamicUpdates;}
 Obj58 ActionRows(){var a=new Obj58();foreach(var id in new[]{GameInputActionId.MoveUp,GameInputActionId.MoveDown,GameInputActionId.MoveLeft,GameInputActionId.MoveRight}){var x=GameInputBindings.GetAction(id);a[id.ToString()]=new Obj58{["enabled"]=x!=null&&x.enabled,["pressed"]=x!=null&&x.IsPressed(),["activeDevice"]=x?.activeControl!=null?(Json58)x.activeControl.device.deviceId:null,["activeControl"]=x?.activeControl?.path,["controls"]=x==null?new Arr58():new Arr58(x.controls.Select(c=>c.path)),["effectivePaths"]=x==null?new Arr58():new Arr58(x.bindings.Select(b=>b.effectivePath))};}return a;}
 void AfterInput(){if(ownedKeyboard==null||exiting||finished)return;var type=InputState.currentUpdateType;if(type==InputUpdateType.Dynamic)dynamicUpdates++;if(updates.Count<100)updates.Add(new Obj58{["frame"]=Time.frameCount,["type"]=type.ToString(),["dynamicCount"]=dynamicUpdates,["sampleIndex"]=sampleIndex,["ownedEnabled"]=ownedKeyboard.enabled,["current"]=Keyboard.current==ownedKeyboard,["upKeyPressed"]=ownedKeyboard[upKey].isPressed,["rightKeyPressed"]=ownedKeyboard[rightKey].isPressed,["actualMovement"]=V(GameInputBindings.ReadMovement()),["actions"]=ActionRows()});}
 void Tick()
 {
  if(finished)return;
  try{
   if(AppDomain.CurrentDomain.Id!=domain)throw new InvalidOperationException("Unexpected domain reload");
   if(exiting){if(!EditorApplication.isPlaying&&!EditorApplication.isPlayingOrWillChangePlaymode&&++exitTicks>=8)Finish();return;}
   if(EditorApplication.timeSinceStartup-start>70)throw new TimeoutException("Bounded smoke timeout; no automatic retry");if(!EditorApplication.isPlaying)return;
   var n=UnityEngine.Object.FindObjectsByType<NativePlayer395>(FindObjectsSortMode.None).FirstOrDefault();var gp=UnityEngine.Object.FindObjectsByType<Gameplay397>(FindObjectsSortMode.None).FirstOrDefault(g=>g.player==n);
   if(n&&!string.IsNullOrEmpty(n.failure))throw new InvalidOperationException(n.failure);
   if(EditorApplication.timeSinceStartup-lastTrace>1){lastTrace=EditorApplication.timeSinceStartup;report["readyTrace"]=new Obj58{["frame"]=Time.frameCount,["nativeReady"]=n&&n.ready,["gameplayConnected"]=gp&&gp.connected,["serial"]=n&&n.host&&n.host.main?n.host.main.renderedSerial335:0};}
   if(EditorApplication.isPaused)throw new InvalidOperationException("Unknown pause; not overriding");if(!n||!n.ready||!gp||!gp.connected||n.host.main.renderedSerial335<=0)return;if(gp.runInputTest)throw new InvalidOperationException("Existing synthetic input test enabled");
   if(!inputStarted){StartInput(n);return;}if(n.host.main.renderedSerial335==lastSerial||dynamicUpdates<=armedUpdate)return;lastSerial=n.host.main.renderedSerial335;
   var request=Requested();var input=GameInputBindings.ReadMovement();var pos=n.player.position;var delta=pos-previousPosition;delta.y=0;var expected=PlayerMovement.CalculateCameraRelativeDirection(request,camera.transform.rotation);float alignment=delta.sqrMagnitude>1e-10f&&expected.sqrMagnitude>0?Vector3.Dot(delta.normalized,expected):0;float beforeAngle=expected.sqrMagnitude>0?Quaternion.Angle(previousFacing,Quaternion.LookRotation(expected,Vector3.up)):0;float afterAngle=expected.sqrMagnitude>0?Quaternion.Angle(animator.transform.rotation,Quaternion.LookRotation(expected,Vector3.up)):0;
   var row=new Obj58{["index"]=sampleIndex,["cycle"]=sampleIndex/6,["frame"]=Time.frameCount,["serial"]=lastSerial,["deltaTime"]=Time.deltaTime,["requested"]=V(request),["actualInput"]=V(input),["keyboardEnabled"]=ownedKeyboard.enabled,["keyboardCurrent"]=Keyboard.current==ownedKeyboard,["upKey"]=ownedKeyboard[upKey].isPressed,["rightKey"]=ownedKeyboard[rightKey].isPressed,["actions"]=ActionRows(),["position"]=V(pos),["deltaXZ"]=V(delta),["expectedWorldDirection"]=V(expected),["directionDot"]=alignment,["expectedStepLength"]=movement.speed*Time.deltaTime,["actualStepLength"]=delta.magnitude,["facingBeforeAngle"]=beforeAngle,["facingAfterAngle"]=afterAngle,["facing"]=Q(animator.transform.rotation),["currentMoveSpeed"]=movement.CurrentMoveSpeed,["movementSpeed"]=movement.speed,["animatorState"]=animator.GetCurrentAnimatorStateInfo(0).fullPathHash,["animatorPhase"]=animator.GetCurrentAnimatorStateInfo(0).normalizedTime,["locomotion"]=animator.GetFloat(PlayerMovement.LocomotionSpeedParameter),["settingsSameReference"]=System.Object.ReferenceEquals(settings,InputSystem.settings),["historyReset"]=n.host.main.motion.resetHistory};samples.Add(row);Save("sample-"+sampleIndex);
   if((input-request).sqrMagnitude>1e-8)throw new InvalidOperationException("Queued key -> actual action mismatch; stop without substitute input");
   if(request.sqrMagnitude>0&&(delta.sqrMagnitude<1e-10||alignment<.99||afterAngle>beforeAngle+.01))throw new InvalidOperationException("Action -> movement/facing mismatch; inspect collisions/focus before further tests");
   if(request.sqrMagnitude==0&&delta.magnitude>1e-4)throw new InvalidOperationException("Released input still moves horizontally");
   previousPosition=pos;previousFacing=animator.transform.rotation;sampleIndex++;if(sampleIndex>=Samples){report["inputSmokePassed"]=true;BeginExit();return;}Queue();
  }catch(Exception e){report["error"]=e.ToString();BeginExit();}
 }
 void ReleaseInput()
 {
  InputSystem.onAfterUpdate-=AfterInput;var errors=new Arr58();void Try(Action a){try{a();}catch(Exception e){errors.Add(e.ToString());}}
  if(inputStarted){Try(()=>{if(!settings||!System.Object.ReferenceEquals(InputSystem.settings,settings))throw new InvalidOperationException("Borrowed settings disappeared/replaced; no replacement attempted");settings.backgroundBehavior=background;settings.editorInputBehaviorInPlayMode=editorBehavior;});}
  var owned=ownedKeyboard;Try(()=>{if(owned!=null&&InputSystem.devices.Contains(owned))InputSystem.RemoveDevice(owned);});ownedKeyboard=null;Try(()=>{if(previousKeyboard!=null&&InputSystem.devices.Contains(previousKeyboard))previousKeyboard.MakeCurrent();});Try(()=>Time.captureDeltaTime=oldCapture);
  report["inputCleanupErrors"]=errors;report["ownedDeviceRemoved"]=owned==null||!InputSystem.devices.Contains(owned);report["settingsBeforePlayExitAlive"]=settings?true:false;report["settingsBeforePlayExitSame"]=System.Object.ReferenceEquals(settings,InputSystem.settings);report["settingsBeforePlayExitExact"]=settings&&JsonUtility.ToJson(settings)==settingsJson;
 }
 void BeginExit(){if(exiting||finished)return;exiting=true;ReleaseInput();Save("normal-Play-exit-requested");if(EditorApplication.isPlaying||EditorApplication.isPlayingOrWillChangePlaymode)EditorApplication.ExitPlaymode();else Finish();}
 void Finish()
 {
  if(finished)return;finished=true;EditorApplication.update-=Tick;InputSystem.onAfterUpdate-=AfterInput;
  try{
   if(started){Application.runInBackground=oldBackground;EditorSettings.enterPlayModeOptionsEnabled=oldOptions;EditorSettings.enterPlayModeOptions=oldFlags;GraphicsSettings.defaultRenderPipeline=oldG;QualitySettings.renderPipeline=oldQ;Time.timeScale=oldTime;Time.captureDeltaTime=oldCapture;EditorApplication.isPaused=oldPause;}
   if(journal!=null){journal.RestoreMarked();var errors=journal.VerifyMarked();report["globalRestoreErrors"]=new Arr58(errors);if(errors.Length>0)throw new InvalidOperationException("Global restoration needs review");journal.ReleaseHandleAfterVerified();}
   bool settingsOK=settings&&System.Object.ReferenceEquals(InputSystem.settings,settings)&&settings.hideFlags==settingsFlags&&JsonUtility.ToJson(settings)==settingsJson;
   report["afterSettingsId"]=settings?settings.GetEntityId().ToString():"destroyed";report["afterSettingsJSON"]=settings?JsonUtility.ToJson(settings):null;report["afterSettingsObjectCount"]=Resources.FindObjectsOfTypeAll<InputSettings>().Length;report["afterDevices"]=DeviceRows();report["afterRTCount"]=Resources.FindObjectsOfTypeAll<RenderTexture>().Length;report["afterDirty"]=Dirty();report["afterScenes"]=Scenes();report["nativeComparisons"]=NativeSnapshot73.Compare(Root,nativeBefore);
   var restore=new Obj58{["settingsReferenceAliveContentHideFlags"]=settingsOK,["devicesSame"]=InputSystem.devices.Count==devices.Length&&devices.All(d=>InputSystem.devices.Contains(d)),["deviceEnabledStatesSame"]=devices.Select((d,i)=>d.enabled==devicesEnabled[i]).All(x=>x),["previousKeyboardCurrent"]=System.Object.ReferenceEquals(previousKeyboard,Keyboard.current),["actionAssetSame"]=System.Object.ReferenceEquals(actions,InputSystem.actions),["actionBindingsSame"]=actions&&actions.ToJson()==bindingsJson,["options"]=EditorSettings.enterPlayModeOptionsEnabled==oldOptions&&EditorSettings.enterPlayModeOptions==oldFlags,["timePause"]=Time.timeScale==oldTime&&Time.captureDeltaTime==oldCapture&&EditorApplication.isPaused==oldPause,["pipeline"]=GraphicsSettings.defaultRenderPipeline==oldG&&QualitySettings.renderPipeline==oldQ,["background"]=Application.runInBackground==oldBackground&&PlayerSettings.runInBackground==oldPlayerBackground,["PlayExited"]=!EditorApplication.isPlaying&&!EditorApplication.isPlayingOrWillChangePlaymode,["observerRemoved"]=true};report["restoration"]=restore;
   foreach(var key in new[]{"settingsReferenceAliveContentHideFlags","devicesSame","deviceEnabledStatesSame","previousKeyboardCurrent","actionAssetSame","actionBindingsSame","options","timePause","pipeline","background","PlayExited"})if(!(bool)restore[key])throw new InvalidOperationException("Restoration mismatch: "+key);
   foreach(Obj58 x in (Arr58)report["nativeComparisons"])if(x["equal"]!=null&&(bool)x["equal"]==false)throw new InvalidOperationException("Native content mismatch: "+(string)x["path"]);
   Save("finished-restored");CreateOnly73.Text(Path.Combine(Root,"RESTORED80.marker"),"Exact settings pointer/content and device/action/options restored");if(report["inputSmokePassed"]!=null&&(bool)report["inputSmokePassed"])CreateOnly73.Text(Path.Combine(Root,"SMOKE_COMPLETE80.marker"),"12 normal input frames/two identical input cycles; not eye/movement-aesthetics validation");
  }catch(Exception e){report["restorationError"]=e.ToString();Save("restoration-incomplete");}
 }
}
