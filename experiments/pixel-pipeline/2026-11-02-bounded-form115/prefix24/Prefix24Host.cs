using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEditor;
using UnityEngine.SceneManagement;
using UnityEngine.InputSystem;

namespace Prefix24 {
[Serializable] sealed class State24 {
 public bool Playing,Transition,Compiling,Updating,Paused,Background,PlayerBackground,OptionsEnabled;
 public int Options;
 public string TimeScale,CaptureDelta,Pipeline,QualityPipeline,InputId,InputJson;
 public string[] Scenes,Devices,Dirty,Globals;
}
[Serializable] sealed class Event24 {
 public string Kind,Utc,Kernel,Name,Error;
 public int Stage,Bytes,Pending,Dispatches;
 public bool Done,HasError,Unknown;
}

// Not a renderer or observer. Four independent official commands call Start.
// One command owns one dispatch and its asynchronous readbacks only.
public sealed class Prefix24Host {
 static readonly Dictionary<string,Prefix24Host> Live=new Dictionary<string,Prefix24Host>();
 readonly Dictionary<string,GraphicsBuffer> buffers=new Dictionary<string,GraphicsBuffer>();
 readonly List<AsyncGPUReadbackRequest> requests=new List<AsyncGPUReadbackRequest>();
 readonly List<Blob24> outputs=new List<Blob24>(); readonly StepGate24 gate=new StepGate24();
 sealed class Read24 {public string Name;public GraphicsBuffer Buffer;public int Bytes,Offset;}
 readonly List<Read24> reads=new List<Read24>();
 Case24 data;int stage,mainThread;string dir,kernel,error;byte[] before;ComputeShader shader;
 SynchronizationContext context;Action<string> log;bool finishPosted,terminal;
 static string Id(UnityEngine.Object o)=>o?o.GetEntityId().ToString():"null";
 static string Number(float v)=>v.ToString("R",CultureInfo.InvariantCulture);
 static State24 State(Case24 c){
  var input=InputSystem.settings;if(!input)throw new InvalidOperationException("Existing InputSettings required; no replacement");
  var globals=new List<string>();foreach(var g in c.Globals){string value;
   switch(g.Type){case "Float":value=Number(Shader.GetGlobalFloat(g.Name));break;case "Int":value=Shader.GetGlobalInt(g.Name).ToString(CultureInfo.InvariantCulture);break;
    case "Texture":value=Id(Shader.GetGlobalTexture(g.Name));break;
    case "Vector":var v=Shader.GetGlobalVector(g.Name);value=String.Join(",",new[]{Number(v.x),Number(v.y),Number(v.z),Number(v.w)});break;
    case "Matrix":var m=Shader.GetGlobalMatrix(g.Name);value=String.Join(",",Enumerable.Range(0,16).Select(i=>Number(m[i])));break;
    default:value="UNQUERIED_NO_WRITES:"+g.Type;break;}
   globals.Add(g.Name+"="+value);
  }
  return new State24{Playing=EditorApplication.isPlaying,Transition=EditorApplication.isPlayingOrWillChangePlaymode,Compiling=EditorApplication.isCompiling,Updating=EditorApplication.isUpdating,Paused=EditorApplication.isPaused,
   Background=Application.runInBackground,PlayerBackground=PlayerSettings.runInBackground,OptionsEnabled=EditorSettings.enterPlayModeOptionsEnabled,Options=(int)EditorSettings.enterPlayModeOptions,
   TimeScale=Number(Time.timeScale),CaptureDelta=Number(Time.captureDeltaTime),Pipeline=Id(GraphicsSettings.defaultRenderPipeline),QualityPipeline=Id(QualitySettings.renderPipeline),InputId=Id(input),InputJson=JsonUtility.ToJson(input),
   Scenes=Enumerable.Range(0,SceneManager.sceneCount).Select(i=>{var s=SceneManager.GetSceneAt(i);return s.path+"|"+s.isDirty+"|"+(s==SceneManager.GetActiveScene());}).ToArray(),
   Devices=InputSystem.devices.Select(d=>d.deviceId+"|"+d.layout+"|"+d.enabled).ToArray(),
   Dirty=Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o)).Select(o=>AssetDatabase.GetAssetPath(o)+"|"+o.GetType().FullName+"|"+Id(o)).Where(s=>s.StartsWith("Assets/",StringComparison.Ordinal)||s.StartsWith("ProjectSettings/",StringComparison.Ordinal)).OrderBy(s=>s,StringComparer.Ordinal).ToArray(),
   Globals=globals.ToArray()};
 }
 static void Stable(){if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required");}
 public static void Start(int requestedStage,Action<string> logger){
  Protocol24.Encode=value=>Encoding.UTF8.GetBytes(JsonUtility.ToJson(value));
  Protocol24.Decode=(bytes,type)=>JsonUtility.FromJson(Encoding.UTF8.GetString(bytes),type);
  var job=new Prefix24Host{stage=requestedStage,log=logger??(_=>{})};job.Begin();
 }
 void Begin(){
  // Disk/case checks precede GPU asset loading. Nothing invokes an importer.
  if(stage<1||stage>4)throw new ArgumentOutOfRangeException(nameof(stage));Stable();
  context=SynchronizationContext.Current;mainThread=Thread.CurrentThread.ManagedThreadId;
  if(context==null||context.GetType().FullName!="UnityEngine.UnitySynchronizationContext")throw new InvalidOperationException("Unity main synchronization context required");
  data=Protocol24.LoadCase(CaseLock24.FixtureRoot,CaseLock24.ManifestSha);
  if(stage>1)Protocol24.Previous(data,CaseLock24.ManifestSha,CaseLock24.RunRoot,stage);
  if(SystemInfo.graphicsDeviceType!=GraphicsDeviceType.Direct3D11||!SystemInfo.supportsComputeShaders)throw new InvalidOperationException("Reviewed D3D11 compute context required; no API switch");
  var project=Directory.GetParent(Application.dataPath).FullName;var source=Path.GetFullPath(Path.Combine(project,data.ShaderAssetPath));
  if(data.ShaderAssetPath!="Assets/EUnityValidation01/Direct24Prefix/Prefix24.compute"||!source.StartsWith(Path.Combine(project,"Assets")+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase))throw new IOException("Exact isolated asset required");
  if(Protocol24.Hash(Protocol24.ReadBounded(source,65536))!=data.ShaderSha256)throw new IOException("Unimported/mismatched shader source; no fallback");
  before=Protocol24.Json(State(data));dir=Protocol24.ClaimStage(data,CaseLock24.ManifestSha,CaseLock24.RunRoot,stage);
  Protocol24.Create(Path.Combine(dir,"BEFORE.json"),before);Live.Add(dir,this);
  try{
   if(AssetDatabase.AssetPathToGUID(data.ShaderAssetPath)!=data.ShaderGuid)throw new IOException("Isolated shader identity mismatch");
   var original=AssetDatabase.LoadAssetAtPath<ComputeShader>(data.ShaderAssetPath);if(!original)throw new IOException("Candidate asset is not imported; no fallback");
   shader=UnityEngine.Object.Instantiate(original);shader.hideFlags=HideFlags.DontSave;
   foreach(var name in new[]{"BuildSubsets113","Enumerate113","Reduce113","Write113"}){
    if(!shader.HasKernel(name))throw new IOException("Candidate entrypoint missing");uint x,y,z;shader.GetKernelThreadGroupSizes(shader.FindKernel(name),out x,out y,out z);
    if(x!=(name=="Write113"?8u:64u)||y!=(name=="Write113"?8u:1u)||z!=1)throw new IOException("Thread-group ABI");
   }
   Prepare();int k=shader.FindKernel(kernel);foreach(var b in buffers)shader.SetBuffer(k,b.Key,b.Value);
   shader.SetInts("_CellsSize113",18,8);shader.SetInts("_CurveEyeIds106",2,1);
   Protocol24.CreateJson(Path.Combine(dir,"PREPARED.json"),new Event24{Kind="prepared",Utc=DateTime.UtcNow.ToString("O"),Stage=stage,Kernel=kernel});
   gate.BeforeDispatch();
   // The sole GPU submission site. No callback or finalizer can reach it.
   shader.Dispatch(k,stage==2?32:1,stage==1?2:1,1);
   gate.DispatchReturned();Protocol24.CreateJson(Path.Combine(dir,"SUBMITTED.json"),new Event24{Kind="submitted",Stage=stage,Kernel=kernel,Dispatches=gate.DispatchCalls,Utc=DateTime.UtcNow.ToString("O")});
   gate.BeginReads();
   foreach(var spec in reads){gate.BeforeRead(spec.Name);try{var capture=spec;var request=AsyncGPUReadback.Request(spec.Buffer,spec.Bytes,spec.Offset,r=>Received(capture,r));requests.Add(request);}catch(Exception e){gate.ReadRequestUncertain();error=e.ToString();break;}}
   gate.EndReads();MaybeFinish();log("Prefix24 stage"+stage+" submitted once; no automatic next stage. Read "+dir);
  }catch(Exception e){error=e.ToString();gate.Fail();MaybeFinish();if(!gate.CanRelease&&!terminal)Pending("start-failed-uncertain");log("Prefix24 stopped: "+e.Message);}
 }
 byte[] Input(string name)=>Protocol24.Input(data,CaseLock24.FixtureRoot,name);
 byte[] Prior(string name)=>Protocol24.PreviousBytes(data,CaseLock24.ManifestSha,CaseLock24.RunRoot,stage,name);
 GraphicsBuffer Buffer<T>(string name,T[] array,int stride)where T:struct{
  if(stride!=Protocol24.ExpectedStride<T>()||array.Length<1||(long)array.Length*stride>Protocol24.MaxBlobBytes)throw new IOException("Buffer type/stride/budget");
  var b=new GraphicsBuffer(GraphicsBuffer.Target.Structured,array.Length,stride);buffers.Add(name,b);b.SetData(array);return b;
 }
 void Read(string name,GraphicsBuffer buffer,int bytes,int offset=0){if(bytes<1||offset<0||(long)offset+bytes>(long)buffer.count*buffer.stride||bytes>9216)throw new IOException("Readback bounds");reads.Add(new Read24{Name=name,Buffer=buffer,Bytes=bytes,Offset=offset});}
 void Prepare(){
  kernel=new[]{"BuildSubsets113","Enumerate113","Reduce113","Write113"}[stage-1];
  if(stage==1||stage==4){Buffer("_Cells113",Protocol24.Fours(Input("cells")),16);Buffer("_Frame113",Protocol24.UInts(Input("frame")),16);Buffer("_Points113",Protocol24.UInts(Input("points")),16);}
  if(stage==1){Buffer("_CellTags113",Protocol24.UInts(Input("tags")),16);var b=Buffer("_Subsets113",new Subset24[16384],32);Read("subsets-I",b,2048);Read("subsets-W",b,2048,4096*32);}
  if(stage==2){Buffer("_Frame113",Protocol24.UInts(Input("frame")),16);var a=new Subset24[16384];Array.Copy(Protocol24.Subsets(Prior("subsets-I")),0,a,0,64);Array.Copy(Protocol24.Subsets(Prior("subsets-W")),0,a,4096,64);Buffer("_Subsets113",a,32);Read("groups",Buffer("_Groups113",Protocol24.InvalidGroups(65536),48),32*48);}
  if(stage==3){var a=Protocol24.InvalidGroups(65536);Array.Copy(Protocol24.Groups(Prior("groups")),a,32);Buffer("_Groups113",a,48);Read("best",Buffer("_Best113",Protocol24.Groups(Input("old-best")),48),48);}
  if(stage==4){var best=Protocol24.Groups(Input("old-best"));best[0]=Protocol24.Groups(Prior("best"))[0];Buffer("_Best113",best,48);
   string[] names={"colour","identity","decision","audit"},gpu={"_CurveColour106","_CurveIdentity106","_CurveDecision106","_CurveAudit106"};
   for(int i=0;i<4;i++)Read(names[i],Buffer(gpu[i],Enumerable.Repeat(new F4(-12345.25f,-12345.25f,-12345.25f,-12345.25f),144).ToArray(),16),144*16);
  }
 }
 void Received(Read24 spec,AsyncGPUReadbackRequest request){
  if(terminal)return;
  try{
   bool done=request.done,failed=request.hasError;
   if(!done){error="Readback callback not complete";gate.CompleteRead(spec.Name,false,failed);Pending("callback-incomplete");return;}
   try{
    Protocol24.CreateJson(Path.Combine(dir,"CALLBACK-"+spec.Name+".json"),new Event24{Kind="callback",Name=spec.Name,Stage=stage,Done=done,HasError=failed,Bytes=spec.Bytes,Utc=DateTime.UtcNow.ToString("O")});
    if(failed)throw new IOException("GPU readback error "+spec.Name);
    var bytes=request.GetData<byte>().ToArray();Protocol24.Create(Path.Combine(dir,spec.Name+".bin"),bytes);
    outputs.Add(Protocol24.ValidateOutput(data,stage,spec.Name,bytes));
   }catch(Exception e){error=e.ToString();gate.Fail();}
   finally{gate.CompleteRead(spec.Name,true,failed);}
  }catch(Exception e){error=e.ToString();gate.Fail();}
  MaybeFinish();
 }
 void Pending(string kind){try{Protocol24.CreateJson(Path.Combine(dir,"PENDING-"+Guid.NewGuid().ToString("N")+".json"),new Event24{Kind=kind,Stage=stage,Kernel=kernel,Error=error,Pending=gate.Pending,Dispatches=gate.DispatchCalls,Unknown=gate.Unknown||(gate.DispatchCalls>0&&!gate.CanRelease),Utc=DateTime.UtcNow.ToString("O")});}catch{}}
 void MaybeFinish(){
  if(terminal||finishPosted||!gate.CanRelease)return;
  finishPosted=true;
  if(Thread.CurrentThread.ManagedThreadId==mainThread)Finish();
  else try{context.Post(_=>Finish(),null);}catch(Exception e){error=e.ToString();gate.Fail();Pending("main-finalization-not-scheduled");}
 }
 void Finish(){
  if(terminal)return;if(Thread.CurrentThread.ManagedThreadId!=mainThread){error="Main synchronization context did not return to original thread";gate.Fail();Pending("wrong-finalization-thread");return;}
  if(!gate.CanRelease){finishPosted=false;return;}var failures=new List<string>();
  foreach(var b in buffers.Values)try{b.Dispose();}catch(Exception e){failures.Add(e.ToString());}
  try{if(shader)UnityEngine.Object.DestroyImmediate(shader);}catch(Exception e){failures.Add(e.ToString());}
  bool released=failures.Count==0;byte[] after=null;bool equal=false;
  try{after=Protocol24.Json(State(data));Protocol24.Create(Path.Combine(dir,"AFTER.json"),after);equal=before.SequenceEqual(after);}catch(Exception e){failures.Add(e.ToString());}
  if(!equal||failures.Count>0){gate.Fail();error=(error??"")+"\nState/cleanup verification failed: "+String.Join("\n",failures);}
  gate.MarkFinalized();terminal=true;
  var receipt=new Receipt24{ExecutionKind="gpu-prefix",RunId=data.RunId,Stage=stage,CaseSha256=CaseLock24.ManifestSha,SourceId=data.SourceId,ShaderSha256=data.ShaderSha256,
   DispatchCalls=gate.DispatchCalls,StateEqual=equal,ResourcesReleased=released,BeforeStateSha256=Protocol24.Hash(before),AfterStateSha256=after==null?null:Protocol24.Hash(after),Error=error,Outputs=outputs.ToArray()};
  receipt.Success=gate.CanComplete&&released&&equal&&String.IsNullOrEmpty(error)&&outputs.Count==reads.Count;
  if(receipt.Success)Protocol24.CheckReceipt(data,CaseLock24.ManifestSha,stage,receipt,"gpu-prefix");
  Protocol24.CreateJson(Path.Combine(dir,receipt.Success?"COMPLETE.json":"FAILED.json"),receipt);
  if(released){buffers.Clear();requests.Clear();Live.Remove(dir);} // Never retry failed disposal.
  log("Prefix24 stage"+stage+" terminal; success="+receipt.Success+", no next submission");
 }
}
}
