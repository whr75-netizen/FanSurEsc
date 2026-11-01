using System;
using System.IO;
using UnityEngine;
using UnityEngine.InputSystem;
using FantasySurvival.Controls;
public sealed class HoldScope99:IDisposable{
 readonly NativePlayer395 native;readonly string directory;PlayerMovement movement;Animator animator;InputSettings settings;string settingsJSON;float speed,animatorSpeed,capture;bool started,disposed;int index,last=-1,warm=4;
 public Arr58 warmup=new Arr58(),dynamicInput=new Arr58();public string Stage=>"actual-two-view";public int StageIndex=>index;public bool HasWarmup=>warm>0;public bool Restored{get;private set;}public Obj58 RestoreReport{get;private set;}
 public HoldScope99(NativePlayer395 n,string d){native=n;directory=d;}
 public void Start(){movement=native.player.GetComponent<PlayerMovement>();animator=native.host.main.motion.animation.target;settings=InputSystem.settings;if(!movement||!animator||!settings)throw new InvalidOperationException("99 supported held actor unavailable");settingsJSON=JsonUtility.ToJson(settings);speed=movement.speed;animatorSpeed=animator.speed;capture=Time.captureDeltaTime;CreateOnly73.Text(Path.Combine(directory,"HOLD_BEFORE99.json"),new Obj58{["speed"]=speed,["animatorSpeed"]=animatorSpeed,["captureDelta"]=capture,["inputJSON"]=settingsJSON,["inputId"]=settings.GetEntityId().ToString()}.ToString());started=true;movement.speed=0;animator.speed=0;Time.captureDeltaTime=1f/60;}
 public bool Ready(int serial){if(serial==last)return false;last=serial;if(warm>0){warm--;return false;}return true;}
 public Obj58 Snapshot(){if(InputSystem.settings!=settings||JsonUtility.ToJson(settings)!=settingsJSON||GameInputBindings.ReadMovement().sqrMagnitude>1e-8f)throw new InvalidOperationException("99 actual input changed; no synthetic input/settings replacement");return new Obj58{["stage"]=Stage,["index"]=index,["inputSettingWrites"]=0,["deltaTime"]=Time.deltaTime,["actualInput"]=new Arr58(0,0),["headJoinOffset"]=new Arr58(native.host.offset.x,native.host.offset.y),["deliveredDelta"]=new Arr58(native.deliveredDelta.x,native.deliveredDelta.y)};}
 public bool Advance(){index++;return index<10;}
 public void Dispose(){if(disposed)return;disposed=true;if(started){if(movement)movement.speed=speed;if(animator)animator.speed=animatorSpeed;Time.captureDeltaTime=capture;}Restored=!started||(movement&&animator&&InputSystem.settings==settings&&settings&&JsonUtility.ToJson(settings)==settingsJSON&&movement.speed==speed&&animator.speed==animatorSpeed&&Time.captureDeltaTime==capture);RestoreReport=new Obj58{["allRestored"]=Restored,["inputSettingWrites"]=0,["devicesAdded"]=0};}
}
