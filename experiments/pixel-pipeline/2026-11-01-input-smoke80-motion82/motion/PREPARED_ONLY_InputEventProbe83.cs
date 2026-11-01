using System;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

// Prepared diagnostic only. No device/settings creation or mutation and no
// manual Update. Attach to the scope's owned device only; dispose unsubscribes.
public sealed class InputEventProbe83:IDisposable
{
 readonly Keyboard device;readonly Key[] keys;readonly Action<Obj58> sink;
 int entries;bool disposed;
 public InputEventProbe83(Keyboard owned,Key[] requestedKeys,Action<Obj58> boundedSink)
 {device=owned??throw new ArgumentNullException(nameof(owned));keys=requestedKeys;sink=boundedSink;InputSystem.onBeforeUpdate+=Before;InputSystem.onAfterUpdate+=After;InputSystem.onEvent+=Event;InputSystem.onDeviceChange+=Device;}
 Obj58 Row(string stage)=>new Obj58{["stage"]=stage,["frame"]=Time.frameCount,["inputTime"]=InputState.currentTime,["updateType"]=InputState.currentUpdateType.ToString(),["enabled"]=device.enabled,["current"]=Keyboard.current==device,["deviceId"]=device.deviceId};
 void Emit(Obj58 r){if(entries++<64)sink(r);}
 public void Queued(double timestamp){var r=Row("queued-owned-state");r["timestamp"]=timestamp;var a=new Arr58();foreach(var key in keys)a.Add(key.ToString());r["requestedKeys"]=a;Emit(r);}
 void Before(){if(InputState.currentUpdateType!=InputUpdateType.Dynamic)return;Emit(Row("before-Dynamic"));}
 void After(){if(InputState.currentUpdateType!=InputUpdateType.Dynamic)return;var r=Row("after-Dynamic");var a=new Arr58();foreach(var key in keys)a.Add(new Obj58{["key"]=key.ToString(),["pressed"]=device[key].isPressed});r["keys"]=a;Emit(r);}
 void Event(InputEventPtr e,InputDevice d){if(d!=device)return;var r=Row("owned-event-received");r["eventType"]=e.type.ToString();r["eventTime"]=e.time;r["handledOnEntry"]=e.handled;r["bytes"]=e.sizeInBytes;Emit(r);}
 void Device(InputDevice d,InputDeviceChange change){if(d!=device)return;var r=Row("owned-device-change");r["change"]=change.ToString();Emit(r);}
 public void Dispose(){if(disposed)return;disposed=true;InputSystem.onBeforeUpdate-=Before;InputSystem.onAfterUpdate-=After;InputSystem.onEvent-=Event;InputSystem.onDeviceChange-=Device;}
}
