using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
using UnityEngine.Profiling;

// One normal Play entry, one already-rendered paused input, no RenderPose/re-render/algorithm switch.
internal partial class CommandScript : IRunCommand
{
 const string Root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\joint-lid107\capture-final";
 struct Baseline76 {public Vector4 colour,owner,meta,uv,domain,stamp;}
 bool armed102; LayerZero101 layer102; ForwardCanvas107 forward102;
 bool calibrated89;Exception renderError89;int retargetFrame89=-1;
 Sequence107 motion82;
 UnityEngine.InputSystem.InputSettings settingsBefore82;string settingsJSON82;HideFlags settingsHide82;UnityEngine.InputSystem.InputDevice[] devicesBefore82;bool[] enabledBefore82;UnityEngine.InputSystem.Keyboard keyboardBefore82;
 void InputBackup82(){settingsBefore82=UnityEngine.InputSystem.InputSystem.settings;if(!settingsBefore82||EditorUtility.IsPersistent(settingsBefore82))throw new InvalidOperationException("Live nonpersistent input setting required; no replacement");settingsJSON82=JsonUtility.ToJson(settingsBefore82);settingsHide82=settingsBefore82.hideFlags;devicesBefore82=UnityEngine.InputSystem.InputSystem.devices.ToArray();enabledBefore82=devicesBefore82.Select(d=>d.enabled).ToArray();keyboardBefore82=UnityEngine.InputSystem.Keyboard.current;CreateOnly73.Text(Path.Combine(output,"EDIT_INPUT_BEFORE82.json"),new Obj58{["json"]=settingsJSON82,["nativeId"]=settingsBefore82.GetEntityId().ToString(),["hideFlags"]=settingsHide82.ToString(),["devices"]=new Arr58(devicesBefore82.Select(d=>new Obj58{["id"]=d.deviceId,["layout"]=d.layout,["enabled"]=d.enabled})),["keyboard"]=keyboardBefore82!=null?(Json58)keyboardBefore82.deviceId:null}.ToString());}
 void InputVerify82(){bool alive=settingsBefore82&&System.Object.ReferenceEquals(UnityEngine.InputSystem.InputSystem.settings,settingsBefore82),json=alive&&JsonUtility.ToJson(settingsBefore82)==settingsJSON82,flags=alive&&settingsBefore82.hideFlags==settingsHide82,devices=UnityEngine.InputSystem.InputSystem.devices.Count==devicesBefore82.Length&&devicesBefore82.All(d=>UnityEngine.InputSystem.InputSystem.devices.Contains(d)),enabled=devicesBefore82.Select((d,i)=>d.enabled==enabledBefore82[i]).All(v=>v),keyboard=System.Object.ReferenceEquals(UnityEngine.InputSystem.Keyboard.current,keyboardBefore82);report["editInputRestoration82"]=new Obj58{["sameAliveReference"]=alive,["exactJSON"]=json,["hideFlags"]=flags,["devicesSame"]=devices,["deviceEnabledStates"]=enabled,["keyboardSame"]=keyboard,["nativeId"]=alive?settingsBefore82.GetEntityId().ToString():"destroyed"};if(!alive||!json||!flags||!devices||!enabled||!keyboard)throw new InvalidOperationException("Input restoration mismatch after Play; no extra experiment");}

 Vector4[] expectedRest77;Obj58 cacheReport77;
 void VerifySourceCache77(){
  if(cacheReport77!=null)return;var e=probeEye;var actual=new Vector4[borrowedRest77.count];borrowedRest77.GetData(actual);int offset=(int)e.triangleRanges[6].x,nativeCount=(int)e.triangleRanges[6].y;
  bool xyzSame=true;for(int i=0;i<actual.Length;i++)if(actual[i].x!=expectedRest77[i].x||actual[i].y!=expectedRest77[i].y||actual[i].z!=expectedRest77[i].z)xyzSame=false;
  if(!xyzSame||actual[0].w!=77)throw new InvalidOperationException("GPU source cache failed or altered source XYZ");
  var labels=new Arr58();for(int t=0;t<nativeCount;t++)labels.Add((int)actual[offset+3*t].w);var groups=new Arr58();
  foreach(int cid in Enumerable.Range(0,nativeCount).Select(t=>(int)actual[offset+3*t].w).Distinct()){
   int root=Math.Abs(cid)-1;groups.Add(new Obj58{["label"]=cid,["eyeId"]=(int)actual[21+4*root].w,["meanRest"]=new Arr58(actual[22+4*root].w,actual[23+4*root].w,actual[24+4*root].w),["triangles"]=Enumerable.Range(0,nativeCount).Count(t=>(int)actual[offset+3*t].w==cid)});
  }
  cacheReport77=new Obj58{["header"]=actual[0].w,["sourceXYZUnchanged"]=xyzSame,["cpuInjectedMetadata"]=false,["components"]=groups,["nativeTriangleLabels"]=labels,["oneReadbackBytes"]=actual.Length*16L};expectedRest77=null;
 }
 ComputeBuffer borrowedRest77;
 EyeFeature348 probeEye;ComputeShader probeShader,oldShader;ComputeBuffer probeBuffer,probeVisits;RectInt probeROI;NativePlayer395 native;int armedSerial;
 void CameraBegin76(ScriptableRenderContext context,Camera camera){if(!native||!probeShader||camera!=native.host.headCamera)return;probeShader.SetInt("_ProbeFrame76",Time.frameCount);probeShader.SetInt("_ProbeSerialBefore76",native.host.main.renderedSerial335);probeVisits.SetData(new uint[1]);}
 void Arm76(NativePlayer395 n){native=n;probeEye=n.host.headEyes;if(!probeEye||!n.host.headEnabled)throw new InvalidOperationException("102 current head path required");oldShader=probeEye.candidateShader;borrowedRest77=probeEye.restTriangles;layer102=new LayerZero101(probeEye,@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\renderer-family59\SOURCE_REGISTRY59.json");forward102=new ForwardCanvas107(probeEye,layer102,@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\native-feature89\REGISTRATION89.json",Path.Combine(output,"REGISTRATION_CURRENT102.json"));calibrated89=true;armed102=true;report["runtimeProduct77Shader"]=AssetDatabase.GetAssetPath(oldShader);report["runtimeProduct77ShaderSHA"]=SHA(AssetDatabase.GetAssetPath(oldShader));report["noExperimental98or99"]=true;report["forwardComputeSHA102"]=SHA("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye102.compute");report["selectionHierarchy102"]="eye union vs canvas, then child coverage, unique source depth only for exact part ties";}
 void Release76(){forward102?.Dispose();report["forward102Disposed"]=forward102==null||forward102.Disposed;layer102?.Dispose();report["layer102Disposed"]=layer102==null||layer102.Disposed;motion82?.Dispose();report["motionRestoration82"]=motion82?.RestoreReport;report["borrowedRestReferenceUntouched82"]=probeEye&&probeEye.restTriangles==borrowedRest77;report["borrowedRestDisposedByObserver82"]=false;report["ownedProbeReleased76"]=true;}
 string sequenceDirectory,sequenceId;Arr58 packetList76=new Arr58();int captured76,previousFrame76=-1;
 GlobalJournal64 journal;Arr58 nativeBefore;bool oldPlayerBackground;Obj58 report;string output,sourceId;int stateSequence;Arr58 planes=new Arr58();
 RenderPipelineAsset oldG,oldQ;float oldTime,oldCapture;bool oldOptions,oldPause,started,exiting,finished;EnterPlayModeOptions oldFlags;double start,lastTelemetry;bool oldBackground;int exitTicks,domain;long readyAllocated;
 static Arr58 V(Vector2 v){return new Arr58(v.x,v.y);}static Arr58 V(Vector3 v){return new Arr58(v.x,v.y,v.z);}static Arr58 V(Vector4 v){return new Arr58(v.x,v.y,v.z,v.w);}static Arr58 M(Matrix4x4 m){return new Arr58(Enumerable.Range(0,16).Select(i=>(double)m[i]));}
 static string SHA(string path){using(var h=SHA256.Create())using(var f=File.OpenRead(path))return BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant();}
 static Obj58 Memory(){return new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["allocated"]=Profiler.GetTotalAllocatedMemoryLong(),["reserved"]=Profiler.GetTotalReservedMemoryLong(),["mono"]=Profiler.GetMonoUsedSizeLong(),["renderTextureCount"]=Resources.FindObjectsOfTypeAll<RenderTexture>().Length};}
 static Arr58 Dirty(){return new Arr58(Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o)).Select(o=>new Obj58{["path"]=AssetDatabase.GetAssetPath(o),["type"]=o.GetType().FullName}));}
 static Arr58 Scenes(){var a=new Arr58();for(int i=0;i<SceneManager.sceneCount;i++){var s=SceneManager.GetSceneAt(i);a.Add(new Obj58{["path"]=s.path,["dirty"]=s.isDirty,["active"]=s==SceneManager.GetActiveScene(),["roots"]=s.rootCount});}return a;}
 void Save(string stage){report["stage"]=stage;report["utc"]=DateTime.UtcNow.ToString("O");report["planes"]=planes;CreateOnly73.Text(Path.Combine(Root,"STATE107-"+(stateSequence++).ToString("D4")+"-"+stage+".json"),report.ToString());}

 public void Execute(ExecutionResult result)
 {
  if(File.Exists(Path.Combine(Root,"CAPTURE_STARTED76.json")))throw new InvalidOperationException("Existing capture outcome must be inspected; no repeat");CreateOnly73.Text(Path.Combine(Root,"CAPTURE_STARTED76.json"),"one approved observer invocation");
  sourceId="eye107-"+DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ")+"-"+Guid.NewGuid().ToString("N").Substring(0,8);output=Path.Combine(Root,sourceId);if(Directory.Exists(output))throw new IOException("Unique output required");Directory.CreateDirectory(output);
  report=new Obj58{["sourceId"]=sourceId,["output"]=output,["revision86"]="106 current deformed source curve, same-input GPU102 comparison; product77 unchanged",["PlayEntries"]=0,["packetComplete"]=false,["captureContractStatus"]="RAW_INPUT_PENDING_OFFLINE_CORRESPONDENCE",["largestOwnedReadbackBytes"]=0,["simultaneousReadbacks"]=1,["resetHistoryRequestedByObserver"]=false};
  try
  {
   if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required");
   if(Enumerable.Range(0,SceneManager.sceneCount).Select(SceneManager.GetSceneAt).Any(s=>s.isDirty))throw new InvalidOperationException("Scene changed before capture");
   InputBackup82();oldPlayerBackground=PlayerSettings.runInBackground;nativeBefore=NativeSnapshot73.Backup(Root);domain=AppDomain.CurrentDomain.Id;oldBackground=Application.runInBackground;oldOptions=EditorSettings.enterPlayModeOptionsEnabled;oldFlags=EditorSettings.enterPlayModeOptions;oldPause=EditorApplication.isPaused;oldTime=Time.timeScale;oldCapture=Time.captureDeltaTime;oldG=GraphicsSettings.defaultRenderPipeline;oldQ=QualitySettings.renderPipeline;
   report["beforeMemory"]=Memory();report["beforeDirty"]=Dirty();report["beforeScenes"]=Scenes();report["domain"]=domain;report["optionsBefore"]=new Arr58(oldOptions,(int)oldFlags);report["pipelineBefore"]=new Arr58(AssetDatabase.GetAssetPath(oldG),AssetDatabase.GetAssetPath(oldQ));
   var specs=Json58.Parse(File.ReadAllText(Path.Combine(Root,"GLOBAL_NAMES66.json"))).Select(o=>new GlobalJournal64.Spec{name=(string)o["name"],kind=(string)o["type"]=="Int"?GlobalJournal64.Kind.LegacyInt:(GlobalJournal64.Kind)Enum.Parse(typeof(GlobalJournal64.Kind),(string)o["type"])}).ToArray();
   journal=GlobalJournal64.Snapshot(sourceId,Path.Combine(output,"GLOBALS_BEFORE.bin"),specs);journal.RequireRecoverable(specs.Select(s=>s.name));foreach(var s in specs)journal.BeforeMutation(s.name);
   report["globalBackupSHA256"]=journal.backupSHA256;report["globalBackupVerified"]=journal.externalVerified;report["globalCount"]=specs.Length;report["globalBufferWrites"]=0;
   start=EditorApplication.timeSinceStartup;EditorApplication.update+=Tick;started=true;Save("ready-before-Play");
   Application.runInBackground=true;report["backgroundBefore"]=oldBackground;report["temporaryRunInBackground"]=true;EditorSettings.enterPlayModeOptionsEnabled=true;EditorSettings.enterPlayModeOptions=EnterPlayModeOptions.DisableDomainReload;report["PlayEntries"]=1;Save("entering-Play");EditorApplication.EnterPlaymode();
   result.Log("67 single normal Play armed; observer owns normal exit/restore, no repeated rendering");
  }
  catch(Exception e){report["error"]=e.ToString();if(started)BeginExit();else Finish();result.Log("67 stopped: "+e.Message);}
 }
 void Tick()
 {
  if(finished)return;
  try
  {
   if(AppDomain.CurrentDomain.Id!=domain)throw new InvalidOperationException("Unexpected domain reload");
   if(exiting){if(!EditorApplication.isPlaying&&!EditorApplication.isPlayingOrWillChangePlaymode&&++exitTicks>=8)Finish();return;}
   if(!armed102&&EditorApplication.timeSinceStartup-start>70)throw new TimeoutException("Normal-ready timeout; no repeat");if(armed102&&EditorApplication.timeSinceStartup-start>240)throw new TimeoutException("Bounded9-state forward eye/actual evaluated Close budget exhausted; normal exit");
   if(!EditorApplication.isPlaying)return;
   var n=UnityEngine.Object.FindObjectsByType<NativePlayer395>(FindObjectsSortMode.None).FirstOrDefault();
   if(n&&!string.IsNullOrEmpty(n.failure))throw new InvalidOperationException(n.failure);
   var gp=UnityEngine.Object.FindObjectsByType<Gameplay397>(FindObjectsSortMode.None).FirstOrDefault(g=>g.player==n);
   if(EditorApplication.timeSinceStartup-lastTelemetry>.5){lastTelemetry=EditorApplication.timeSinceStartup;CreateOnly73.Text(Path.Combine(Root,"TRACE107-"+Guid.NewGuid().ToString("N")+".json"),new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["frame"]=Time.frameCount,["paused"]=EditorApplication.isPaused,["focused"]=Application.isFocused,["timeScale"]=Time.timeScale,["background"]=Application.runInBackground,["hasNative"]=n!=null,["nativeEnabled"]=n&&n.enabled,["nativeActive"]=n&&n.gameObject.activeInHierarchy,["nativeWarmup"]=n?n.warmup:-1,["nativeReady"]=n&&n.ready,["nativeFailure"]=n?n.failure:null,["hasGameplay"]=gp!=null,["gameplayActive"]=gp&&gp.activateGameplay,["connected"]=gp&&gp.connected,["gameplayFailure"]=gp?gp.failure:null,["mainSerial"]=n&&n.host&&n.host.main?n.host.main.renderedSerial335:0}.ToString()+"\n");}
   if(EditorApplication.isPaused)throw new InvalidOperationException("Runtime paused before observer ready; do not override unidentified pause");
   if(!n||!n.ready||!gp||!gp.connected||n.host.main.renderedSerial335<=0)return;
   if(gp.runInputTest)throw new InvalidOperationException("Synthetic input test enabled");
   if(!armed102){Arm76(n);Save("probe-armed-on-live-head-next-normal-frame");return;}
   if(renderError89!=null)throw new InvalidOperationException("Same-head-camera retarget failed",renderError89);
   if(!calibrated89)return;
   if(motion82==null){motion82=new Sequence107(n,output);motion82.Start();armedSerial=n.host.main.renderedSerial335;report["sourceCaptureTiming89"]="endCameraRendering for the exact head camera, current source light context";return;}
   if(n.host.main.renderedSerial335<=armedSerial)return;

   if(!motion82.Ready(n.host.main.renderedSerial335)){armedSerial=n.host.main.renderedSerial335;report["motionWarmup82"]=motion82.warmup;report["dynamicInput82"]=motion82.dynamicInput;return;}
   if(!motion82.CaptureThis){if(!motion82.Advance()){BeginExit();return;}armedSerial=n.host.main.renderedSerial335;return;}
   readyAllocated=Profiler.GetTotalAllocatedMemoryLong();report["readyMemory"]=Memory();report["frameIndex"]=Time.frameCount;report["deltaTime"]=Time.deltaTime;report["hostMainRenderSerial"]=n.host.main.renderedSerial335;Save("already-rendered-main-thread-readback");
   report["conditionalCaptureFrameGap95"]=previousFrame76<0?0:Time.frameCount-previousFrame76;
   if(captured76==0){sequenceDirectory=output;sequenceId=sourceId;}
   sourceId=sequenceId+"-frame"+Time.frameCount;output=Path.Combine(sequenceDirectory,"frame-"+Time.frameCount);if(Directory.Exists(output))throw new IOException("Unique frame output required");Directory.CreateDirectory(output);planes=new Arr58();report["sourceId"]=sourceId;report["output"]=output;report["sequenceId"]=sequenceId;
   report["motion82"]=motion82.Snapshot();report["motionWarmup82"]=motion82.warmup;report["dynamicInput82"]=motion82.dynamicInput;
   Capture(n,gp);report["afterCaptureReleaseMemory"]=Memory();previousFrame76=Time.frameCount;captured76++;packetList76.Add(new Obj58{["sourceId"]=sourceId,["output"]=output,["frame"]=Time.frameCount,["serial"]=n.host.main.renderedSerial335,["deltaTime"]=Time.deltaTime,["testStage82"]=motion82.Stage,["stageIndex82"]=motion82.StageIndex});report["sequencePackets"]=packetList76;
   if(motion82.Advance()){if(motion82.HasWarmup)previousFrame76=-1;armedSerial=n.host.main.renderedSerial335;return;}BeginExit();
  }
  catch(Exception e){report["error"]=e.ToString();BeginExit();}
 }
 void BeginExit(){if(exiting||finished)return;exiting=true;Release76();Save("normal-Play-exit-requested");if(EditorApplication.isPlaying||EditorApplication.isPlayingOrWillChangePlaymode){EditorApplication.isPaused=false;EditorApplication.ExitPlaymode();}else Finish();}
 void Finish()
 {
  if(finished)return;finished=true;EditorApplication.update-=Tick;
  try
  {
   if(started){Application.runInBackground=oldBackground;EditorSettings.enterPlayModeOptionsEnabled=oldOptions;EditorSettings.enterPlayModeOptions=oldFlags;GraphicsSettings.defaultRenderPipeline=oldG;QualitySettings.renderPipeline=oldQ;Time.timeScale=oldTime;Time.captureDeltaTime=oldCapture;EditorApplication.isPaused=oldPause;}
   if(journal!=null){journal.RestoreMarked();var errors=journal.VerifyMarked();report["globalRestoreErrors"]=new Arr58(errors);if(errors.Length>0)throw new InvalidOperationException("Global getter restoration failed");journal.ReleaseHandleAfterVerified();}
   report["nativeComparisons72"]=nativeBefore==null?new Arr58():NativeSnapshot73.Compare(Root,nativeBefore);report["playerSettingsRunInBackgroundRestored"]=PlayerSettings.runInBackground==oldPlayerBackground;report["afterMemory"]=Memory();report["afterDirty"]=Dirty();report["afterScenes"]=Scenes();report["optionsRestored"]=!started||(EditorSettings.enterPlayModeOptionsEnabled==oldOptions&&EditorSettings.enterPlayModeOptions==oldFlags);report["timeRestored"]=!started||(Time.timeScale==oldTime&&Time.captureDeltaTime==oldCapture&&EditorApplication.isPaused==oldPause);report["pipelineRestored"]=!started||(GraphicsSettings.defaultRenderPipeline==oldG&&QualitySettings.renderPipeline==oldQ);
   report["backgroundRestored"]=Application.runInBackground==oldBackground;report["PlayExited"]=!EditorApplication.isPlaying&&!EditorApplication.isPlayingOrWillChangePlaymode;InputVerify82();report["observerRemoved"]=true;if(motion82!=null&&!motion82.Restored)throw new InvalidOperationException("Input/movement scope restoration failed; see motionRestoration82");Save("finished");
  }
  catch(Exception e){report["restorationError"]=e.ToString();Save("restoration-incomplete");}
 }
 CpuSourceCapture64.Frame Frame(Full319View335 f,string view,int serial)
 {
  var cam=f.motion.camera;return new CpuSourceCapture64.Frame{sourceId=sourceId,viewId=view,frameIndex=Time.frameCount,renderSerial=serial,phaseIndex=f.phaseIndex,renderedSource=f.motion.sourceFrame,evaluatedFrame=f.motion.evaluatedFrame,
   view=cam.worldToCameraMatrix,projection=cam.projectionMatrix,effectiveProjection=f.effectiveProjection,gpuProjection=GL.GetGPUProjectionMatrix(cam.projectionMatrix,true),gpuEffectiveProjection=GL.GetGPUProjectionMatrix(f.effectiveProjection,true),viewport=new Vector4(cam.pixelRect.x,cam.pixelRect.y,cam.pixelRect.width,cam.pixelRect.height),clipShift=f.motion.clipShift,nativeShift=f.nativeShift,logicalSize=new Vector2Int(480,272),nativeSize=new Vector2Int(960,544),subsampleProducer="Native333 and Probe331 SV_Position pixel-centres; nativeShift and raw/effective projection recorded separately",activeModeFlags="current FullFeature/EyeRenderer flags exported in metadata"};
 }
 void Plane(CpuSourceCapture64.Frame frame,string name,RTHandle texture,RectInt roi,string producer,string channel)
 {
  if(Profiler.GetTotalAllocatedMemoryLong()-readyAllocated>256L*1024*1024)throw new InvalidOperationException("Capture-only allocation exceeded 256MiB; stop additional reads");
  string file=name+".plane";CpuSourceCapture64.WriteOwnedPlane(Path.Combine(output,file),frame,texture.rt,roi,producer,channel,"linear RGBAFloat; channel-specific noncolour values remain raw","RT memory bottom-left; source raster SV_Position convention recorded by projection");
  planes.Add(new Obj58{["file"]=file,["sourceId"]=sourceId,["viewId"]=frame.viewId,["frameIndex"]=frame.frameIndex,["renderSerial"]=frame.renderSerial,["textureSize"]=new Arr58(texture.rt.width,texture.rt.height),["roiBottomLeft"]=new Arr58(roi.x,roi.y,roi.width,roi.height),["producer"]=producer,["channel"]=channel});
  long bytes=(long)roi.width*roi.height*16;report["largestOwnedReadbackBytes"]=Math.Max((long)report["largestOwnedReadbackBytes"],bytes);
 }
 RectInt MetaAndBounds(CpuSourceCapture64.Frame frame,Full319View335 f)
 {
  int minX=480,minY=272,maxX=0,maxY=0;
  for(int y=0;y<272;y+=64)
  {
   int height=Math.Min(64,272-y);var roi=new RectInt(0,y,480,height);string name="source-meta-strip-"+y;
   Plane(frame,name,f.preparedMeta,roi,"Prepare333.Prepare","selected depth/role/side/primitive metadata");
   // Re-read only the streamed file, not GPU memory; no full-plane duplicate.
   using(var r=new BinaryReader(File.OpenRead(Path.Combine(output,name+".plane"))))
   {
    r.ReadInt32();r.ReadInt32();r.ReadString();r.ReadString();r.ReadInt32();r.ReadInt32();for(int s=0;s<4;s++)r.ReadString();for(int s=0;s<6;s++)r.ReadInt32();
    for(int i=0;i<480*height;i++){float depth=r.ReadSingle(),role=r.ReadSingle();r.ReadSingle();r.ReadSingle();if(depth>0&&role>0){int x=i%480,yy=y+i/480;minX=Math.Min(minX,x);maxX=Math.Max(maxX,x+1);minY=Math.Min(minY,yy);maxY=Math.Max(maxY,yy+1);}}
   }
  }
  if(minX>=maxX||minY>=maxY)throw new InvalidOperationException("No visible source metadata");
  minX=Math.Max(0,minX-2);minY=Math.Max(0,minY-2);maxX=Math.Min(480,maxX+2);maxY=Math.Min(272,maxY+2);
  return new RectInt(minX,minY,maxX-minX,maxY-minY);
 }
 void AuxMesh(string name,UnityEngine.Mesh mesh,Matrix4x4 matrix,CpuSourceCapture64.Frame frame)
 {
  if(!mesh)return;string path=Path.Combine(output,name+".mesh");
  using(var w=new BinaryWriter(new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.Read))){w.Write("aux-mesh67/v1");w.Write(sourceId);w.Write(frame.viewId);w.Write(frame.frameIndex);w.Write(frame.renderSerial);for(int i=0;i<16;i++)w.Write(matrix[i]);var p=mesh.vertices;var uv=mesh.uv;var n=mesh.normals;w.Write(p.Length);foreach(var v in p){w.Write(v.x);w.Write(v.y);w.Write(v.z);}w.Write(n.Length);foreach(var v in n){w.Write(v.x);w.Write(v.y);w.Write(v.z);}w.Write(uv.Length);foreach(var v in uv){w.Write(v.x);w.Write(v.y);}w.Write(mesh.subMeshCount);for(int sm=0;sm<mesh.subMeshCount;sm++){var ix=mesh.GetIndices(sm);w.Write(ix.Length);foreach(int i in ix)w.Write(i);}}
 }
 void Buffer(string name,ComputeBuffer buffer,CpuSourceCapture64.Frame frame)
 {
  if(buffer==null||!buffer.IsValid())return;long size=(long)buffer.count*buffer.stride;if(size>1024*1024)throw new InvalidOperationException("Feature buffer exceeds one MiB");
  using(var w=new BinaryWriter(new FileStream(Path.Combine(output,name+".buffer"),FileMode.CreateNew,FileAccess.Write,FileShare.Read))){w.Write("buffer67/v1");w.Write(sourceId);w.Write(frame.viewId);w.Write(frame.frameIndex);w.Write(frame.renderSerial);w.Write(buffer.count);w.Write(buffer.stride);if(buffer.stride==4){var data=new uint[buffer.count];buffer.GetData(data);foreach(uint v in data)w.Write(v);}else if(buffer.stride==16){var data=new Vector4[buffer.count];buffer.GetData(data);foreach(var v in data){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}}else throw new InvalidOperationException("Unimplemented feature buffer stride");}
 }
 void FrozenOriginal76(EyeFeature348 e,CpuSourceCapture64.Frame frame){
  using(var owned=new ComputeBuffer(probeROI.width*probeROI.height,256)){
   var cmd=CommandBufferPool.Get("76 frozen original, owned record output only");
   try{
var v=e.full;var cs=probeShader;int k=0;void T(string n,RTHandle t)=>cmd.SetComputeTextureParam(cs,k,n,t.rt);for(int stage19=1;stage19<2;stage19++){if(stage19==0&&(EyeFeature348.UseIrisSurface582||EyeFeature348.UseLashRegion583))continue;k=cs.FindKernel("OriginalEvaluate76");cmd.SetComputeBufferParam(cs,k,"_FeatureCounts19",e.featureCounts19);cmd.SetComputeIntParam(cs,"_UseHairRegion502",HeadRegion502.Ready?1:0);cmd.SetComputeIntParam(cs,"_UseIrisSurface582",EyeFeature348.UseIrisSurface582?1:0);cmd.SetComputeIntParam(cs,"_UseLashRegion583",EyeFeature348.UseLashRegion583?1:0);cmd.SetComputeIntParam(cs,"_UseClosedLash590",EyeFeature348.UseClosedLash590?1:0);for(int i=0;i<7;i++){var s=e.samples[i];T("_S"+i+"RGBA",s.rgba);T("_S"+i+"META",s.meta);T("_S"+i+"POINT",s.point);T("_S"+i+"UV",s.uv);}T("_S3Shade",e.samples[3].shade);cmd.SetComputeIntParam(cs,"_EyeLayerView348",v.surfaceLayerView);T("_BaseRGBA",v.layers[8].rgba);T("_BaseMETA",v.layers[8].meta);T("_BackingRGBA",v.layers[10].rgba);T("_BackingMETA",v.layers[10].meta);T("_HairRGBA",v.layers[6].rgba);T("_HairMETA",v.layers[6].meta);T("_BrowRGBA",v.layers[7].rgba);T("_BrowMETA",v.layers[7].meta);T("_RawMETA",v.motion.raw[5]);T("_RawUV",v.motion.raw[6]);T("_PostLine",v.postLine);T("_BaselineColour348",v.colour);T("_BaselineOwner348",v.owner);T("_BaselineMeta348",v.preparedMeta);T("_BaselineUV348",v.preparedUV);T("_BaselineDomain348",v.domain);cmd.SetComputeBufferParam(cs,k,"_RecordsWrite348",owned);cmd.SetComputeBufferParam(cs,k,"_Baseline76",probeBuffer);cmd.SetComputeBufferParam(cs,k,"_LashGeometry590",e.lashGeometry590);
  T("_OldEyeOwner",v.eyeOwner);T("_OldIntrinsic",v.intrinsic);cmd.SetComputeMatrixParam(cs,"_WorldToHead348",e.headMatrix.inverse);cmd.SetComputeIntParams(cs,"_ROI348",e.roi.x,272-e.roi.y-e.roi.height,e.roi.width,e.roi.height);cmd.SetComputeVectorArrayParam(cs,"_Centres348",e.centres);cmd.SetComputeVectorArrayParam(cs,"_AxesX348",e.axesX);cmd.SetComputeVectorArrayParam(cs,"_AxesY348",e.axesY);cmd.SetComputeVectorParam(cs,"_UpperLower348",new Vector4(e.style.upper.x,e.style.upper.y,e.style.lower.x,e.style.lower.y));cmd.SetComputeVectorParam(cs,"_Iris348",new Vector4(e.style.irisRadii.x,e.style.irisRadii.y,e.style.irisOffset,e.style.irisPower));cmd.SetComputeVectorParam(cs,"_Catch348",new Vector4(e.style.catchU.x,e.style.catchU.y,e.style.catchV.x,e.style.catchV.y));cmd.SetComputeVectorParam(cs,"_FaceLidShade348",e.faceLidShadeEndpoint);cmd.SetComputeBufferParam(cs,k,"_RestTriangles348",e.restTriangles);cmd.SetComputeVectorArrayParam(cs,"_TriangleRanges348",e.triangleRanges);cmd.SetComputeTextureParam(cs,k,"_TemplateRGBA",v.templateRGBA);cmd.SetComputeTextureParam(cs,k,"_TemplateRole",v.templateRole);
  for(int i=0;i<2;i++){cmd.SetComputeMatrixParam(cs,"_Inverse348_"+i,v.eyeInverse[i]);cmd.SetComputeVectorParam(cs,"_Plane348_"+i,v.eyePlanes[i]);var b=v.calibration.eyes[i].referenceBounds;cmd.SetComputeIntParams(cs,"_ColourBounds348_"+i,Mathf.FloorToInt(b.x)-1,Mathf.FloorToInt(b.y)-1,Mathf.CeilToInt(b.z)+1,Mathf.CeilToInt(b.w)+1);}cmd.SetComputeVectorParam(cs,"_RayBase348",v.rayBase);cmd.SetComputeVectorParam(cs,"_RayX348",v.rayX);cmd.SetComputeVectorParam(cs,"_RayY348",v.rayY);cmd.SetComputeVectorParam(cs,"_RayDepth348",v.rayDepth);if(stage19==0)cmd.DispatchCompute(cs,k,(e.roi.width+7)/8,(e.roi.height+7)/8,2);else cmd.DispatchCompute(cs,k,(probeROI.width+7)/8,(probeROI.height+7)/8,1);}

    Graphics.ExecuteCommandBuffer(cmd);
   }finally{CommandBufferPool.Release(cmd);}
   var rows=new PixelReadback70.Pixel348[probeROI.width*probeROI.height];owned.GetData(rows);
   using(var w=new BinaryWriter(new FileStream(Path.Combine(output,"original76.buffer"),FileMode.CreateNew,FileAccess.Write,FileShare.Read))){
    w.Write("original76/v1");w.Write(sourceId);w.Write(frame.viewId);w.Write(frame.frameIndex);w.Write(frame.renderSerial);w.Write(probeROI.x);w.Write(probeROI.y);w.Write(probeROI.width);w.Write(probeROI.height);w.Write(256);
    foreach(var r in rows)foreach(var v in new[]{r.colour,r.owner,r.intrinsic,r.visible,r.histA,r.histB,r.surface,r.pigment,r.audit,r.domain,r.bary,r.globalOwner,r.preparedMeta,r.preparedUV,r.control,r.supportMeta}){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}
   }
  }
  report["frozenOriginal76"]=new Obj58{["sameFrame"]=Time.frameCount==frame.frameIndex&&native.host.main.renderedSerial335==frame.renderSerial,["actualCountsAndSampleBindings"]=true,["ownedOutputBytes"]=probeROI.width*probeROI.height*256,["borrowedTexturesWritten"]=0};
 }

 Vector4[] JointSlice107(string name,GraphicsBuffer b,int start,int count){long bytes=(long)count*b.stride;if(b.stride!=16||start<0||count<0||start+count>b.count||bytes>2*1024*1024)throw new InvalidOperationException("107 bounded source readback");var a=new Vector4[count];b.GetData(a,0,start,count);using(var w=new BinaryWriter(new FileStream(Path.Combine(output,name+".f32"),FileMode.CreateNew))){w.Write(count);w.Write(16);foreach(var v in a){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}}return a;}
 void JointBuffer102(string name,GraphicsBuffer b){JointSlice107(name,b,0,b.count);}
 void Curves106(){var c=forward102.Curves;var a=new SourceCurves106.Segment[c.Count];c.Buffer.GetData(a);bool same=a.Length==c.Segments.Length;using(var w=new BinaryWriter(new FileStream(Path.Combine(output,"curve-segments106.f32"),FileMode.CreateNew))){w.Write(a.Length);w.Write(32);for(int i=0;i<a.Length;i++){same&=a[i].a.Equals(c.Segments[i].a)&&a[i].b.Equals(c.Segments[i].b);foreach(var v in new[]{a[i].a,a[i].b}){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}}}report["curveCPUUploadEqualsGPU106"]=same;if(!same)throw new InvalidOperationException("107 curve upload/input mismatch");}
 void Evidence107(string prefix,LiveSurface107 source,int width,int height,bool detailed){
  int n=width*height;var witness=JointSlice107(prefix+"-skin-query-proof",source.Engine.Evidence107,n*6,n*2);
  if(!detailed)return;var ls=JointSlice107(prefix+"-lid-layers-proof",source.Engine.Layers,n*15,n*5);var triangles=new System.Collections.Generic.Dictionary<int,bool>();
  for(int at=0;at<n;at++){int hit=Mathf.RoundToInt(witness[at*2].x)-1;if(hit>=0)triangles[hit]=true;int primitive=Mathf.RoundToInt(ls[n*3+at].z);if(primitive>0)triangles[source.Engine.PartTriangle107(3,primitive)]=true;}
  CreateOnly73.Text(Path.Combine(output,prefix+"-query-geometry107.json"),new Obj58{["sameSourceId"]=sourceId,["frame"]=Time.frameCount,["triangles"]=new Arr58(triangles.Keys.OrderBy(x=>x).Select(x=>source.Engine.TriangleEvidence107(x))),["witnessKind"]="nearest encountered positive-alpha blocker before existing opaque traversal termination; not claimed global nearest"}.ToString());
 }
 void Capture(NativePlayer395 n,Gameplay397 gp){
  forward102.AssertRendered();int serial=n.host.main.renderedSerial335,frameIndex=Time.frameCount;var h=n.host.head;var e=n.host.headEyes;
  if(e!=probeEye||e.candidateShader!=oldShader)throw new InvalidOperationException("107 product77 binding changed");
  var hf=Frame(h,"product77-control-and-isolated-live107",serial);var r=e.roi;var hr=new RectInt(Math.Max(0,r.x-12),Math.Max(0,272-r.y-r.height-20),r.width+24,r.height+40);
  report["renderPath107"]="actual live joint107, same-input102 and106; product77 remains default";report["sourceSkin102"]=layer102.Source.Info;report["forward102"]=forward102.Info;report["forwardComputeSHA107"]=SHA("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye107.compute");
  report["grid102"]=new Obj58{["headROI"]=new Arr58(hr.x,hr.y,hr.width,hr.height),["eyeTopLeftROI"]=new Arr58(r.x,r.y,r.width,r.height),["headToMainOffset"]=new Arr58(n.host.offset.x,n.host.offset.y),["sampleScale"]=4,["denseSampleScale107"]=8,["headView"]=M(h.motion.camera.worldToCameraMatrix),["headProjection"]=M(h.effectiveProjection),["queryPhysicalView107"]=M(h.motion.camera.worldToCameraMatrix),["queryPhysicalProjection107"]=M(h.motion.camera.projectionMatrix),["queryOrthographic107"]=h.motion.camera.orthographic};
  Plane(hf,"H-product77-final",h.colour,hr,"product77 unchanged","control only");
  for(int i=0;i<4;i++){
   var c=layer102.Fields[i];Plane(hf,"L0-"+new[]{"RGBA","META","UV","LIGHT"}[i],c,new RectInt(0,0,c.rt.width,c.rt.height),"native source graph","full-face region palette pending");
   foreach(int variant in new[]{0,1,2}){var f=(variant==0?forward102.BaselineFields:variant==1?forward102.LegacyFields:forward102.Fields)[i];Plane(hf,new[]{"B-","C-","F-"}[variant]+new[]{"EyeRGBA","EyeOwner","FinalRGBA","FinalOwner"}[i],f,new RectInt(0,0,f.rt.width,f.rt.height),new[]{"same-input GPU102","same-input GPU106","actual live joint GPU107"}[variant],"source-local joint visibility then external hair");}
  }
  foreach(var t in new[]{new{n="rgba",t=e.samples[4].rgba},new{n="meta",t=e.samples[4].meta}})Plane(hf,"S4-"+t.n,t.t,new RectInt(0,0,t.t.rt.width,t.t.rt.height),"current physical hair samples","same-sample alpha/depth; no eye allocation feedback");
  foreach(var row in new[]{new{n="rgba",i=0},new{n="meta",i=1},new{n="rest",i=2},new{n="uv",i=3}}){var t=forward102.DenseNative.Handles96[3][row.i];Plane(hf,"D-lid-"+row.n,t,new RectInt(0,0,t.rt.width,t.rt.height),"same-frame8x native joint source","actual107 source pigment and depth; no invented fill");}
  foreach(int part in new[]{1,2}){var t=forward102.DenseNative.Handles96[part][1];Plane(hf,"D-part"+part+"-meta",t,new RectInt(0,0,t.rt.width,t.rt.height),"same-frame8x joint source geometry","actual107 same-sample depth competition");}
  JointBuffer102("canonical-colour",forward102.Source.Engine.Colour);JointBuffer102("canonical-identity",forward102.Source.Engine.Identity);JointBuffer102("canonical-decision",forward102.Source.Engine.Decisions);JointBuffer102("canonical-layers",forward102.Source.Engine.Layers);JointBuffer102("canonical-visibility",forward102.Source.Engine.Visibility);
  for(int i=0;i<4;i++){JointBuffer102("curve-"+new[]{"colour","identity","decision","audit"}[i],forward102.Results[i]);JointBuffer102("legacy106-"+new[]{"colour","identity","decision","audit"}[i],forward102.LegacyResults[i]);}Curves106();
  int dw=forward102.DenseNative.currentWidth,dh=forward102.DenseNative.currentHeight;JointSlice107("dense-lid-visibility",forward102.DenseSource.Engine.Visibility,dw*dh*3,dw*dh);
  JointSlice107("dense-three-part-visibility",forward102.DenseSource.Engine.Visibility,dw*dh,dw*dh*3);report["jointInputSampleScale107"]=8;report["diagnosticAndMainBufferBytes107"]=forward102.DenseSource.Engine.OwnedBytes+forward102.Source.Engine.OwnedBytes;
  bool detailed=motion82.Stage.Contains("blink")&&motion82.StageIndex==1||motion82.Stage=="closed-turn"&&motion82.StageIndex==4;
  Evidence107("normal",forward102.Source,forward102.Source.Engine.Width,forward102.Source.Engine.Height,detailed);Evidence107("dense",forward102.DenseSource,dw,dh,detailed);
  report["frameIndex"]=frameIndex;report["mainSerial"]=serial;report["sourceFrame"]=h.motion.sourceFrame;report["evaluatedFrame"]=h.motion.evaluatedFrame;report["forwardFrame"]=forward102.RenderedFrame;report["frameUnchangedDuringReadback"]=Time.frameCount==frameIndex&&n.host.main.renderedSerial335==serial;
  if(!(bool)report["frameUnchangedDuringReadback"])throw new InvalidOperationException("107 capture crossed source frame");report["packetComplete"]=true;report["planes"]=planes;CreateOnly73.Text(Path.Combine(output,"RAW_MANIFEST.json"),report.ToString());CreateOnly73.Text(Path.Combine(output,"RAW_COMPLETE76.marker"),SHA(Path.Combine(output,"RAW_MANIFEST.json")));Save("joint-visibility107-capture-complete");
 }

}

