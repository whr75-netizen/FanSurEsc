using System;
using System.Linq;
using System.IO;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using FantasySurvival.Controls;
using FantasySurvival.SceneFlow;

// Temporary virtual GAME input, never OS keyboard/CUA. Normal PlayerMovement.Update
// and Gameplay397.Present remain the only movement/animation/render drivers.
public sealed class MotionScope78:IDisposable
{
 public const int PhaseFrames=6,WalkFrames=8,TurnFrames=10,TotalFrames=24;
 const float Delta=1f/60;
 NativePlayer395 native;PlayerMovement movement;Animator animator;
 InputSettings priorSettings;Keyboard priorKeyboard,keyboard;string backupDirectory;
 InputSettings.BackgroundBehavior priorBackground;
 InputSettings.EditorInputBehaviorInPlayMode priorEditorBehavior;
 float priorSpeed,priorAnimatorSpeed,priorCapture;bool disposed,started,mapEnabled;
 string priorSettingsJSON;int direction,index,warm=5,lastSerial=-1;Vector2 requested;
 public Arr58 warmup=new Arr58();
 static readonly Vector2[]Directions={new Vector2(0,1),new Vector2(1,1),new Vector2(1,0),new Vector2(1,-1),new Vector2(0,-1),new Vector2(-1,-1),new Vector2(-1,0),new Vector2(-1,1)};
 static Key[] Keys(Vector2 v){var k=new System.Collections.Generic.List<Key>();if(v.y>0)k.Add(Key.W);if(v.y<0)k.Add(Key.S);if(v.x>0)k.Add(Key.D);if(v.x<0)k.Add(Key.A);return k.ToArray();}
 public string Stage=>index<PhaseFrames?"phase":index<PhaseFrames+WalkFrames?"walk":"turn";
 public int StageIndex=>index<PhaseFrames?index:index<PhaseFrames+WalkFrames?index-PhaseFrames:index-PhaseFrames-WalkFrames;
 static Arr58 V(Vector2 v)=>new Arr58(v.x,v.y);static Arr58 V(Vector3 v)=>new Arr58(v.x,v.y,v.z);static Arr58 Q(Quaternion v)=>new Arr58(v.x,v.y,v.z,v.w);
 public MotionScope78(NativePlayer395 n,string directory){native=n;backupDirectory=directory;}
 public void Start(){
  if(started)throw new InvalidOperationException("Motion input scope already started");
  movement=native.player.GetComponent<PlayerMovement>();animator=native.host.main.motion.animation.target;
  if(!movement||!movement.isActiveAndEnabled||!animator||!animator.enabled)throw new InvalidOperationException("Normal movement/Animator path unavailable");
  var map=GameInputBindings.GameplayMap;mapEnabled=map!=null&&map.enabled;if(!mapEnabled)throw new InvalidOperationException("Existing gameplay input map is disabled; not enabling it implicitly");
  var shell=PersistentGameplayShell.Instance;Camera camera=shell!=null?shell.PlayerCamera:null;if(!camera||!camera.isActiveAndEnabled)throw new InvalidOperationException("PlayerMovement's actual camera unavailable");
  priorSpeed=movement.speed;priorAnimatorSpeed=animator.speed;priorCapture=Time.captureDeltaTime;priorKeyboard=Keyboard.current;priorSettings=InputSystem.settings;
  if(!priorSettings)throw new InvalidOperationException("InputSettings is missing/destroyed. No implicit default creation or Play retry.");
  if(UnityEditor.EditorUtility.IsPersistent(priorSettings))throw new InvalidOperationException("This narrow proposal does not alter persistent InputSettings assets");
  priorSettingsJSON=UnityEditor.EditorJsonUtility.ToJson(priorSettings);priorBackground=priorSettings.backgroundBehavior;priorEditorBehavior=priorSettings.editorInputBehaviorInPlayMode;
  CreateOnly73.Text(Path.Combine(backupDirectory,"INPUT_BEFORE78.json"),new Obj58{["entityId"]=priorSettings.GetEntityId().ToString(),["path"]=UnityEditor.AssetDatabase.GetAssetPath(priorSettings),["hideFlags"]=priorSettings.hideFlags.ToString(),["json"]=priorSettingsJSON,["background"]=priorBackground.ToString(),["editorBehavior"]=priorEditorBehavior.ToString(),["settingsPointerWillBeReplaced"]=false}.ToString());started=true;
  float best=-2;for(int d=0;d<Directions.Length;d++){float dot=Vector3.Dot(animator.transform.forward,PlayerMovement.CalculateCameraRelativeDirection(Directions[d],camera.transform.rotation));if(dot>best){best=dot;direction=d;}}
  // InputManager.settings DESTROYS the previous HideAndDontSave temporary.
  // Preserve the borrowed pointer; change only backed-up nonpersistent values.
  priorSettings.backgroundBehavior=InputSettings.BackgroundBehavior.IgnoreFocus;
#if UNITY_EDITOR
  priorSettings.editorInputBehaviorInPlayMode=InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;
#endif
  keyboard=InputSystem.AddDevice<Keyboard>("Eye78 isolated movement input");keyboard.MakeCurrent();Time.captureDeltaTime=Delta;
  // Exact amount is a TEST input, derived from the unchanged scene pixel pitch.
  // It is not a feature size/budget or a new product movement default.
  movement.speed=native.host.Cell*.25f/Delta;animator.speed=0;Queue(direction);
 }
 // Queue only. Let the normal runtime Dynamic update consume the event.
 // The explicit Update(InputUpdateType) overload is internal in this package.
 void Queue(int d){requested=Directions[(d+8)%8];InputSystem.QueueStateEvent(keyboard,new KeyboardState(Keys(requested)));}
 public bool Ready(int serial){if(serial==lastSerial)return false;lastSerial=serial;if(warm>0){warmup.Add(new Obj58{["frame"]=Time.frameCount,["serial"]=serial,["stage"]=Stage,["remaining"]=warm,["position"]=V(native.player.position),["rotation"]=Q(animator.transform.rotation),["input"]=V(GameInputBindings.ReadMovement())});warm--;return false;}return true;}
 public Obj58 Snapshot(){
  var input=GameInputBindings.ReadMovement();if(input.sqrMagnitude<=0||Vector2.Dot(input.normalized,requested.normalized)<.999f)throw new InvalidOperationException("Actual gameplay input differs from requested virtual input; no substitution");
  var a=animator.GetCurrentAnimatorStateInfo(0);var n=native;return new Obj58{["stage"]=Stage,["index"]=StageIndex,["requested"]=V(requested),["actualInput"]=V(input),["keys"]=new Arr58(Keys(requested).Select(x=>x.ToString())),["temporaryKeyboardCurrent"]=Keyboard.current==keyboard,["mapEnabled"]=GameInputBindings.GameplayMap.enabled,["playerPosition"]=V(n.player.position),["playerRotation"]=Q(n.player.rotation),["avatarPosition"]=V(animator.transform.position),["avatarRotation"]=Q(animator.transform.rotation),["moveSpeed"]=movement.CurrentMoveSpeed,["requestedSpeed"]=movement.speed,["running"]=movement.IsRunning,["animatorSpeed"]=animator.speed,["locomotion"]=animator.GetFloat(PlayerMovement.LocomotionSpeedParameter),["stateHash"]=a.fullPathHash,["normalizedTime"]=a.normalizedTime,["transition"]=animator.IsInTransition(0),["deltaTime"]=Time.deltaTime,["captureDeltaTime"]=Time.captureDeltaTime,["cellPitch"]=n.host.Cell,["headPivot"]=V(n.host.headPivot),["mainPivot"]=V(n.host.mainPivot),["headJoinOffset"]=new Arr58(n.host.offset.x,n.host.offset.y),["deliveredDelta"]=V(n.deliveredDelta),["worldSerial"]=n.worldSerial,["presentSerial"]=n.presentSerial,["worldView"]=new Arr58(Enumerable.Range(0,16).Select(i=>(double)n.worldView[i])),["worldProjection"]=new Arr58(Enumerable.Range(0,16).Select(i=>(double)n.worldProjection[i])),["useHairRegion502"]=HeadRegion502.Ready,["historyResetRequested"]=n.host.main.motion.resetHistory};
 }
 public bool Advance(){index++;if(index>=TotalFrames)return false;if(index==PhaseFrames){movement.speed=priorSpeed;animator.speed=priorAnimatorSpeed;warm=8;Queue(direction);}else if(index>=PhaseFrames+WalkFrames){int t=index-PhaseFrames-WalkFrames;Queue(t<5?direction+2:direction);}return true;}
 public bool HasWarmup=>warm>0;
 public bool Restored{get;private set;}
 public Obj58 RestoreReport{get;private set;}
 public void Dispose(){if(disposed)return;disposed=true;if(!started){Restored=true;return;}var errors=new Arr58();void Try(Action action){try{action();}catch(Exception e){errors.Add(e.GetType().Name+": "+e.Message);}}
  // Restore borrowed objects first, then retire only the owned virtual device/settings.
  Try(()=>{if(movement)movement.speed=priorSpeed;});Try(()=>{if(animator)animator.speed=priorAnimatorSpeed;});Try(()=>Time.captureDeltaTime=priorCapture);
  var ownedDevice=keyboard;Try(()=>{if(keyboard!=null)InputSystem.QueueStateEvent(keyboard,new KeyboardState());});
  Try(()=>{if(priorSettings){priorSettings.backgroundBehavior=priorBackground;priorSettings.editorInputBehaviorInPlayMode=priorEditorBehavior;}else throw new InvalidOperationException("Borrowed settings disappeared; external backup retained");});Try(()=>{if(ownedDevice!=null)InputSystem.RemoveDevice(ownedDevice);});keyboard=null;Try(()=>{if(priorKeyboard!=null&&InputSystem.devices.Contains(priorKeyboard))priorKeyboard.MakeCurrent();});
  bool settingsSame=false;Try(()=>settingsSame=UnityEditor.EditorJsonUtility.ToJson(priorSettings)==priorSettingsJSON);bool removed=ownedDevice==null||!InputSystem.devices.Contains(ownedDevice);
  bool released=true; // No settings object is created, adopted, replaced or destroyed.
  bool settingsRef=InputSystem.settings==priorSettings,current=Keyboard.current==priorKeyboard,move=!movement||movement.speed==priorSpeed,anim=!animator||animator.speed==priorAnimatorSpeed,time=Time.captureDeltaTime==priorCapture,map=GameInputBindings.GameplayMap.enabled==mapEnabled;
  Restored=errors.Count==0&&settingsRef&&settingsSame&&current&&removed&&released&&move&&anim&&time&&map;
  RestoreReport=new Obj58{["settingsReference"]=settingsRef,["settingsContent"]=settingsSame,["keyboardCurrent"]=current,["ownedDeviceRemoved"]=removed,["ownedSettingsReleased"]=released,["movementSpeed"]=move,["animatorSpeed"]=anim,["captureDelta"]=time,["mapEnabled"]=map,["errors"]=errors,["allRestored"]=Restored};
 }
}
