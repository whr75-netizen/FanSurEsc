using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.InputSystem;
using UnityEditor;
using FantasySurvival.Controls;

// Diagnostic visibility only. Keeps all vertex/index bytes and persistent meshes.
// Explicit DrawMesh ignores Renderer.enabled, so suppress only runtime draw ranges.
public sealed class HairDrawScope100:IDisposable{
 readonly NativePlayer395 n;readonly string directory;readonly Dictionary<UnityEngine.Mesh,SubMeshDescriptor[]> meshes=new Dictionary<UnityEngine.Mesh,SubMeshDescriptor[]>();readonly Dictionary<UnityEngine.Mesh,string> hashes=new Dictionary<UnityEngine.Mesh,string>();readonly Dictionary<Renderer,bool> renderers=new Dictionary<Renderer,bool>();
 PlayerMovement movement;Animator animator;InputSettings settings;string settingsJSON;float speed,animatorSpeed,capture;bool started,disposed;int index,last=-1,warm=4;public Exception Failure;
 public Arr58 warmup=new Arr58(),dynamicInput=new Arr58();public string Stage=>index==0?"product77-hair-on":index==1?"product77-hair-off":"product77-hair-restored";public int StageIndex=>index;public bool HasWarmup=>warm>0;public bool Restored{get;private set;}public Obj58 RestoreReport{get;private set;}
 public HairDrawScope100(NativePlayer395 value,string d){n=value;directory=d;}
 static string IndexHash(UnityEngine.Mesh m){using(var bytes=new MemoryStream()){using(var w=new BinaryWriter(bytes,System.Text.Encoding.UTF8,true)){w.Write(m.subMeshCount);for(int i=0;i<m.subMeshCount;i++){var a=m.GetIndices(i);w.Write(a.Length);foreach(int x in a)w.Write(x);}}using(var h=System.Security.Cryptography.SHA256.Create())return BitConverter.ToString(h.ComputeHash(bytes.ToArray())).Replace("-","").ToLowerInvariant();}}
 static bool Equal(SubMeshDescriptor a,SubMeshDescriptor b)=>a.indexStart==b.indexStart&&a.indexCount==b.indexCount&&a.topology==b.topology&&a.baseVertex==b.baseVertex&&a.firstVertex==b.firstVertex&&a.vertexCount==b.vertexCount&&a.bounds==b.bounds;
 public void Start(){
  if(HeadRegion502.Enabled||HairBoundary491.Enabled)throw new InvalidOperationException("100 hair replacement renderer enabled; no guessed suppression of independent cached geometry");
  movement=n.player.GetComponent<PlayerMovement>();animator=n.host.main.motion.animation.target;settings=InputSystem.settings;if(!movement||!animator||!settings)throw new InvalidOperationException("100 live supported actor/input required");
  foreach(var v in new[]{n.host.main,n.host.head}){
   if(!v||v.independentMats.Length!=15||Mathf.RoundToInt(v.independentMats[11].GetFloat("_Auto245Role"))!=11)throw new InvalidOperationException("100 current source renderer/material relation changed");
   foreach(var m in new[]{v.motion.surface.outputs[2].sharedMesh,v.registeredHair,v.otherHair}){
    if(!m||EditorUtility.IsPersistent(m)||!m.isReadable)throw new InvalidOperationException("100 runtime nonpersistent readable hair meshes required; persistent mesh left untouched");
    if(!meshes.ContainsKey(m)){meshes.Add(m,Enumerable.Range(0,m.subMeshCount).Select(m.GetSubMesh).ToArray());hashes.Add(m,IndexHash(m));}
   }
   foreach(var r in new Renderer[]{v.motion.surface.outputs[2].GetComponent<Renderer>(),v.motion.surface.source[2]})if(r&&!renderers.ContainsKey(r)){if(EditorUtility.IsPersistent(r))throw new InvalidOperationException("100 persistent renderer left untouched");renderers.Add(r,r.enabled);}
  }
  settingsJSON=JsonUtility.ToJson(settings);speed=movement.speed;animatorSpeed=animator.speed;capture=Time.captureDeltaTime;
  CreateOnly73.Text(Path.Combine(directory,"HAIR_SCOPE_BEFORE100.json"),new Obj58{["meshes"]=new Arr58(meshes.Select(x=>new Obj58{["id"]=x.Key.GetEntityId().ToString(),["name"]=x.Key.name,["persistent"]=false,["vertices"]=x.Key.vertexCount,["submeshes"]=x.Value.Length,["drawCounts"]=new Arr58(x.Value.Select(d=>d.indexCount)),["indexSHA"]=hashes[x.Key]})),["renderers"]=new Arr58(renderers.Select(x=>new Obj58{["id"]=x.Key.GetEntityId().ToString(),["enabled"]=x.Value})),["speed"]=speed,["animatorSpeed"]=animatorSpeed,["captureDelta"]=capture,["inputId"]=settings.GetEntityId().ToString(),["inputJSON"]=settingsJSON}.ToString());
  started=true;movement.speed=0;animator.speed=0;Time.captureDeltaTime=1f/60;RenderPipelineManager.beginCameraRendering+=BeforeCamera;
 }
 void BeforeCamera(ScriptableRenderContext context,Camera camera){if(disposed||index!=1)return;try{Suppress();}catch(Exception e){Failure=e;}}
 void Suppress(){foreach(var x in meshes){if(!x.Key||x.Key.subMeshCount!=x.Value.Length)throw new InvalidOperationException("100 borrowed runtime hair mesh changed lifetime/topology");for(int i=0;i<x.Value.Length;i++){var d=x.Key.GetSubMesh(i);d.indexCount=0;x.Key.SetSubMesh(i,d,MeshUpdateFlags.DontRecalculateBounds);}}foreach(var r in renderers.Keys)if(r)r.enabled=false;}
 void RestoreHair(){foreach(var x in meshes){if(!x.Key||x.Key.subMeshCount!=x.Value.Length)throw new InvalidOperationException("100 original runtime mesh no longer alive; no replacement");for(int i=0;i<x.Value.Length;i++)x.Key.SetSubMesh(i,x.Value[i],MeshUpdateFlags.DontRecalculateBounds);}foreach(var x in renderers){if(!x.Key)throw new InvalidOperationException("100 original hair renderer destroyed");x.Key.enabled=x.Value;}}
 bool HairRestored()=>meshes.All(x=>x.Key&&x.Value.Select((d,i)=>Equal(d,x.Key.GetSubMesh(i))).All(t=>t)&&IndexHash(x.Key)==hashes[x.Key])&&renderers.All(x=>x.Key&&x.Key.enabled==x.Value);
 public bool Ready(int serial){if(serial==last)return false;last=serial;if(Failure!=null)throw new InvalidOperationException("100 hair range suppression failed",Failure);if(warm>0){warm--;return false;}return true;}
 public Obj58 Snapshot(){if(InputSystem.settings!=settings||JsonUtility.ToJson(settings)!=settingsJSON||GameInputBindings.ReadMovement().sqrMagnitude>1e-8f)throw new InvalidOperationException("100 actual user input changed; no injected input");if(index==1&&meshes.Any(x=>Enumerable.Range(0,x.Key.subMeshCount).Any(i=>x.Key.GetSubMesh(i).indexCount!=0)))throw new InvalidOperationException("100 hair draw ranges not suppressed");if(index!=1&&!HairRestored())throw new InvalidOperationException("100 original draw ranges not restored");return new Obj58{["stage"]=Stage,["index"]=index,["hairDrawSuppressed"]=index==1,["meshCount"]=meshes.Count,["vertexOrIndexBytesErased"]=false,["inputSettingsWrites"]=0,["rendererOriginalStatesPreserved"]=index==1?false:HairRestored()};}
 public bool Advance(){index++;if(index==1){Suppress();warm=2;}else if(index==2){RestoreHair();if(!HairRestored())throw new InvalidOperationException("100 exact hair restoration failed before final control");warm=2;}return index<3;}
 public void Dispose(){if(disposed)return;disposed=true;RenderPipelineManager.beginCameraRendering-=BeforeCamera;if(started){RestoreHair();if(movement)movement.speed=speed;if(animator)animator.speed=animatorSpeed;Time.captureDeltaTime=capture;}Restored=!started||(HairRestored()&&movement&&animator&&InputSystem.settings==settings&&JsonUtility.ToJson(settings)==settingsJSON&&movement.speed==speed&&animator.speed==animatorSpeed&&Time.captureDeltaTime==capture);RestoreReport=new Obj58{["allRestored"]=Restored,["hairDrawRangesExact"]=!started||HairRestored(),["borrowedMeshesDisposed"]=false,["inputSettingsWrites"]=0,["devicesAdded"]=0};}
}
