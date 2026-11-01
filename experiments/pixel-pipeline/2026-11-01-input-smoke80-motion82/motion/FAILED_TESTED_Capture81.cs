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
internal class CommandScript : IRunCommand
{
 const string Root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\eye-motion81\run";
 struct Baseline76 {public Vector4 colour,owner,meta,uv,domain,stamp;}
 MotionScope81 motion81;
 UnityEngine.InputSystem.InputSettings settingsBefore81;string settingsJSON81;HideFlags settingsHide81;UnityEngine.InputSystem.InputDevice[] devicesBefore81;bool[] enabledBefore81;UnityEngine.InputSystem.Keyboard keyboardBefore81;
 void InputBackup81(){settingsBefore81=UnityEngine.InputSystem.InputSystem.settings;if(!settingsBefore81||EditorUtility.IsPersistent(settingsBefore81))throw new InvalidOperationException("Live nonpersistent input setting required; no replacement");settingsJSON81=JsonUtility.ToJson(settingsBefore81);settingsHide81=settingsBefore81.hideFlags;devicesBefore81=UnityEngine.InputSystem.InputSystem.devices.ToArray();enabledBefore81=devicesBefore81.Select(d=>d.enabled).ToArray();keyboardBefore81=UnityEngine.InputSystem.Keyboard.current;CreateOnly73.Text(Path.Combine(output,"EDIT_INPUT_BEFORE81.json"),new Obj58{["json"]=settingsJSON81,["nativeId"]=settingsBefore81.GetEntityId().ToString(),["hideFlags"]=settingsHide81.ToString(),["devices"]=new Arr58(devicesBefore81.Select(d=>new Obj58{["id"]=d.deviceId,["layout"]=d.layout,["enabled"]=d.enabled})),["keyboard"]=keyboardBefore81!=null?(Json58)keyboardBefore81.deviceId:null}.ToString());}
 void InputVerify81(){bool alive=settingsBefore81&&System.Object.ReferenceEquals(UnityEngine.InputSystem.InputSystem.settings,settingsBefore81),json=alive&&JsonUtility.ToJson(settingsBefore81)==settingsJSON81,flags=alive&&settingsBefore81.hideFlags==settingsHide81,devices=UnityEngine.InputSystem.InputSystem.devices.Count==devicesBefore81.Length&&devicesBefore81.All(d=>UnityEngine.InputSystem.InputSystem.devices.Contains(d)),enabled=devicesBefore81.Select((d,i)=>d.enabled==enabledBefore81[i]).All(v=>v),keyboard=System.Object.ReferenceEquals(UnityEngine.InputSystem.Keyboard.current,keyboardBefore81);report["editInputRestoration81"]=new Obj58{["sameAliveReference"]=alive,["exactJSON"]=json,["hideFlags"]=flags,["devicesSame"]=devices,["deviceEnabledStates"]=enabled,["keyboardSame"]=keyboard,["nativeId"]=alive?settingsBefore81.GetEntityId().ToString():"destroyed"};if(!alive||!json||!flags||!devices||!enabled||!keyboard)throw new InvalidOperationException("Input restoration mismatch after Play; no extra experiment");}

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
 void Arm76(NativePlayer395 n){native=n;probeEye=n.host.headEyes;if(!probeEye||!n.host.headEnabled)throw new InvalidOperationException("Head deferred path required");oldShader=probeEye.candidateShader;if(!NativeSource77.Build(probeEye,out var nativeData77,out var components77,out string reason77))throw new InvalidOperationException(reason77);if(nativeData77.Length*16L>1024*1024)throw new InvalidOperationException("Native metadata transfer exceeds one MiB");borrowedRest77=probeEye.restTriangles;var activeHeader77=new Vector4[1];borrowedRest77.GetData(activeHeader77,0,0,1);report["productCacheBeforeObserver77"]=activeHeader77[0].w;report["headMainRestDistinct77"]=!System.Object.ReferenceEquals(probeEye.restTriangles,n.host.mainEyes.restTriangles);report["productShaderSHA77"]=SHA(AssetDatabase.GetAssetPath(oldShader));report["productHelperSHA77"]=SHA("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/NativeCacheGPU77.hlsl");if(activeHeader77[0].w!=77)throw new InvalidOperationException("Actual product source cache was not initialized before observer");expectedRest77=nativeData77;report["restBufferReplaced81"]=false;
 report["nativeSource77"]=new Obj58{["bufferBytes"]=nativeData77.Length*16L,["topologySHA256"]=probeEye.modelTopologySHA256,["components"]=new Arr58(components77.Select(c=>new Obj58{["label"]=c.label,["eyeId"]=c.eyeId,["upper"]=c.upper,["meanRest"]=V(c.meanRest),["normalizedV"]=c.normalizedV,["triangles"]=c.triangles})),["productDefaultChanged"]=true};
report["actualRuntimeProductShaderPath"]=AssetDatabase.GetAssetPath(oldShader);probeShader=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/BaselineProbe77GPU.compute"));probeShader.hideFlags=HideFlags.DontSave;
 var r=probeEye.roi;probeROI=new RectInt(Math.Max(0,r.x-12),Math.Max(0,272-r.y-r.height-12),r.width+24,r.height+24);if(probeROI.xMax>480||probeROI.yMax>272)throw new InvalidOperationException("Probe near grid boundary");probeBuffer=new ComputeBuffer(probeROI.width*probeROI.height,96);probeVisits=new ComputeBuffer(1,4);probeVisits.SetData(new uint[1]);int k=probeShader.FindKernel("Evaluate");probeShader.SetBuffer(k,"_Baseline76",probeBuffer);probeShader.SetBuffer(k,"_ProbeVisits76",probeVisits);probeShader.SetInts("_ProbeROI76",probeROI.x,probeROI.y,probeROI.width,probeROI.height);probeEye.candidateShader=probeShader;armedSerial=n.host.main.renderedSerial335;RenderPipelineManager.beginCameraRendering+=CameraBegin76;motion81=new MotionScope81(n,output);motion81.Start();report["movementPlan81"]="6 frozen-pose quarter-cell steps,8 walking frames after8 warmup,10 normal turn frames; one Play, no history reset";
 }
 void Release76(){RenderPipelineManager.beginCameraRendering-=CameraBegin76;motion81?.Dispose();report["motionRestoration81"]=motion81?.RestoreReport;if(probeEye&&oldShader)probeEye.candidateShader=oldShader;report["borrowedRestReferenceUntouched81"]=probeEye&&probeEye.restTriangles==borrowedRest77;report["borrowedRestDisposedByObserver81"]=false;probeBuffer?.Dispose();probeBuffer=null;probeVisits?.Dispose();probeVisits=null;if(probeShader)UnityEngine.Object.DestroyImmediate(probeShader);probeShader=null;report["ownedProbeReleased76"]=true;}
 string sequenceDirectory,sequenceId;Arr58 packetList76=new Arr58();int captured76,previousFrame76=-1;
 GlobalJournal64 journal;Arr58 nativeBefore;bool oldPlayerBackground;Obj58 report;string output,sourceId;int stateSequence;Arr58 planes=new Arr58();
 RenderPipelineAsset oldG,oldQ;float oldTime,oldCapture;bool oldOptions,oldPause,started,exiting,finished;EnterPlayModeOptions oldFlags;double start,lastTelemetry;bool oldBackground;int exitTicks,domain;long readyAllocated;
 static Arr58 V(Vector2 v){return new Arr58(v.x,v.y);}static Arr58 V(Vector3 v){return new Arr58(v.x,v.y,v.z);}static Arr58 V(Vector4 v){return new Arr58(v.x,v.y,v.z,v.w);}static Arr58 M(Matrix4x4 m){return new Arr58(Enumerable.Range(0,16).Select(i=>(double)m[i]));}
 static string SHA(string path){using(var h=SHA256.Create())using(var f=File.OpenRead(path))return BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant();}
 static Obj58 Memory(){return new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["allocated"]=Profiler.GetTotalAllocatedMemoryLong(),["reserved"]=Profiler.GetTotalReservedMemoryLong(),["mono"]=Profiler.GetMonoUsedSizeLong(),["renderTextureCount"]=Resources.FindObjectsOfTypeAll<RenderTexture>().Length};}
 static Arr58 Dirty(){return new Arr58(Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o)).Select(o=>new Obj58{["path"]=AssetDatabase.GetAssetPath(o),["type"]=o.GetType().FullName}));}
 static Arr58 Scenes(){var a=new Arr58();for(int i=0;i<SceneManager.sceneCount;i++){var s=SceneManager.GetSceneAt(i);a.Add(new Obj58{["path"]=s.path,["dirty"]=s.isDirty,["active"]=s==SceneManager.GetActiveScene(),["roots"]=s.rootCount});}return a;}
 void Save(string stage){report["stage"]=stage;report["utc"]=DateTime.UtcNow.ToString("O");report["planes"]=planes;CreateOnly73.Text(Path.Combine(Root,"STATE81-"+(stateSequence++).ToString("D4")+"-"+stage+".json"),report.ToString());}

 public void Execute(ExecutionResult result)
 {
  if(File.Exists(Path.Combine(Root,"CAPTURE_STARTED76.json")))throw new InvalidOperationException("Existing capture outcome must be inspected; no repeat");CreateOnly73.Text(Path.Combine(Root,"CAPTURE_STARTED76.json"),"one approved observer invocation");
  sourceId="eye81-"+DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ")+"-"+Guid.NewGuid().ToString("N").Substring(0,8);output=Path.Combine(Root,sourceId);if(Directory.Exists(output))throw new IOException("Unique output required");Directory.CreateDirectory(output);
  report=new Obj58{["sourceId"]=sourceId,["output"]=output,["PlayEntries"]=0,["packetComplete"]=false,["captureContractStatus"]="RAW_INPUT_PENDING_OFFLINE_CORRESPONDENCE",["largestOwnedReadbackBytes"]=0,["simultaneousReadbacks"]=1,["resetHistoryRequestedByObserver"]=false};
  try
  {
   if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required");
   if(Enumerable.Range(0,SceneManager.sceneCount).Select(SceneManager.GetSceneAt).Any(s=>s.isDirty))throw new InvalidOperationException("Scene changed before capture");
   InputBackup81();oldPlayerBackground=PlayerSettings.runInBackground;nativeBefore=NativeSnapshot73.Backup(Root);domain=AppDomain.CurrentDomain.Id;oldBackground=Application.runInBackground;oldOptions=EditorSettings.enterPlayModeOptionsEnabled;oldFlags=EditorSettings.enterPlayModeOptions;oldPause=EditorApplication.isPaused;oldTime=Time.timeScale;oldCapture=Time.captureDeltaTime;oldG=GraphicsSettings.defaultRenderPipeline;oldQ=QualitySettings.renderPipeline;
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
   if(!probeShader&&EditorApplication.timeSinceStartup-start>70)throw new TimeoutException("Normal-ready timeout; no repeat");if(probeShader&&EditorApplication.timeSinceStartup-start>240)throw new TimeoutException("Bounded24-frame observation budget exhausted; normal exit");
   if(!EditorApplication.isPlaying)return;
   var n=UnityEngine.Object.FindObjectsByType<NativePlayer395>(FindObjectsSortMode.None).FirstOrDefault();
   if(n&&!string.IsNullOrEmpty(n.failure))throw new InvalidOperationException(n.failure);
   var gp=UnityEngine.Object.FindObjectsByType<Gameplay397>(FindObjectsSortMode.None).FirstOrDefault(g=>g.player==n);
   if(EditorApplication.timeSinceStartup-lastTelemetry>.5){lastTelemetry=EditorApplication.timeSinceStartup;CreateOnly73.Text(Path.Combine(Root,"TRACE81-"+Guid.NewGuid().ToString("N")+".json"),new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["frame"]=Time.frameCount,["paused"]=EditorApplication.isPaused,["focused"]=Application.isFocused,["timeScale"]=Time.timeScale,["background"]=Application.runInBackground,["hasNative"]=n!=null,["nativeEnabled"]=n&&n.enabled,["nativeActive"]=n&&n.gameObject.activeInHierarchy,["nativeWarmup"]=n?n.warmup:-1,["nativeReady"]=n&&n.ready,["nativeFailure"]=n?n.failure:null,["hasGameplay"]=gp!=null,["gameplayActive"]=gp&&gp.activateGameplay,["connected"]=gp&&gp.connected,["gameplayFailure"]=gp?gp.failure:null,["mainSerial"]=n&&n.host&&n.host.main?n.host.main.renderedSerial335:0}.ToString()+"\n");}
   if(EditorApplication.isPaused)throw new InvalidOperationException("Runtime paused before observer ready; do not override unidentified pause");
   if(!n||!n.ready||!gp||!gp.connected||n.host.main.renderedSerial335<=0)return;
   if(gp.runInputTest)throw new InvalidOperationException("Synthetic input test enabled");
   if(!probeShader){EditorApplication.isPaused=true;Arm76(n);Save("probe-armed-on-live-head-next-normal-frame");EditorApplication.isPaused=false;return;}
   if(n.host.main.renderedSerial335<=armedSerial)return;
   if(!motion81.Ready(n.host.main.renderedSerial335)){armedSerial=n.host.main.renderedSerial335;report["motionWarmup81"]=motion81.warmup;return;}
   EditorApplication.isPaused=true;readyAllocated=Profiler.GetTotalAllocatedMemoryLong();report["readyMemory"]=Memory();report["frameIndex"]=Time.frameCount;report["deltaTime"]=Time.deltaTime;report["hostMainRenderSerial"]=n.host.main.renderedSerial335;Save("paused-already-rendered");
   if(previousFrame76>=0&&Time.frameCount!=previousFrame76+1)throw new InvalidOperationException("Observed frames are not consecutive");
   if(captured76==0){sequenceDirectory=output;sequenceId=sourceId;}
   sourceId=sequenceId+"-frame"+Time.frameCount;output=Path.Combine(sequenceDirectory,"frame-"+Time.frameCount);if(Directory.Exists(output))throw new IOException("Unique frame output required");Directory.CreateDirectory(output);planes=new Arr58();report["sourceId"]=sourceId;report["output"]=output;report["sequenceId"]=sequenceId;
   report["motion81"]=motion81.Snapshot();report["motionWarmup81"]=motion81.warmup;
   VerifySourceCache77();report["gpuSourceCache77"]=cacheReport77;Capture(n,gp);report["afterCaptureReleaseMemory"]=Memory();previousFrame76=Time.frameCount;captured76++;packetList76.Add(new Obj58{["sourceId"]=sourceId,["output"]=output,["frame"]=Time.frameCount,["serial"]=n.host.main.renderedSerial335,["deltaTime"]=Time.deltaTime,["testStage81"]=motion81.Stage,["stageIndex81"]=motion81.StageIndex});report["sequencePackets"]=packetList76;
   if(motion81.Advance()){if(motion81.HasWarmup)previousFrame76=-1;armedSerial=n.host.main.renderedSerial335;EditorApplication.isPaused=false;return;}BeginExit();
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
   report["backgroundRestored"]=Application.runInBackground==oldBackground;report["PlayExited"]=!EditorApplication.isPlaying&&!EditorApplication.isPlayingOrWillChangePlaymode;InputVerify81();report["observerRemoved"]=true;if(motion81!=null&&!motion81.Restored)throw new InvalidOperationException("Input/movement scope restoration failed; see motionRestoration81");Save("finished");
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
  long bytes=(long)roi.width*roi.height*16;report["largestOwnedReadbackBytes"]=Math.Max((long)report["largestOwnedReadbackBytes"],bytes);Save("capturing-"+name);
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

 void Capture(NativePlayer395 n,Gameplay397 gp)
 {
  int serial=n.host.main.renderedSerial335,frameIndex=Time.frameCount;var f=n.host.head;var e=n.host.headEyes;
  if(!f||!e||e!=probeEye||e.candidateShader!=probeShader)throw new InvalidOperationException("Actual head probe binding changed");
  var frame=Frame(f,"head",serial);var mainFrame=Frame(n.host.main,"main-final",serial);
  var roi=new RectInt(e.roi.x,272-e.roi.y-e.roi.height,e.roi.width,e.roi.height);
  if(!probeROI.Contains(roi.min)||!probeROI.Contains(roi.max-Vector2Int.one))throw new InvalidOperationException("Actual eye ROI left probe bounds");
  var visits=new uint[1];probeVisits.GetData(visits);if(visits[0]<1||visits[0]>4)throw new InvalidOperationException("Unexpected Evaluate dispatch visits");
  var rows=new Baseline76[probeROI.width*probeROI.height];probeBuffer.GetData(rows);
  foreach(var b in rows)if(b.stamp.z!=frameIndex||b.stamp.w!=serial-1)throw new InvalidOperationException("Baseline frame/serial stamp mismatch");
  using(var w=new BinaryWriter(new FileStream(Path.Combine(output,"baseline76.buffer"),FileMode.CreateNew,FileAccess.Write,FileShare.Read)))
  {w.Write("baseline76/v1");w.Write(sourceId);w.Write(frame.viewId);w.Write(frameIndex);w.Write(serial);w.Write(probeROI.x);w.Write(probeROI.y);w.Write(probeROI.width);w.Write(probeROI.height);w.Write(96);foreach(var b in rows)foreach(var v in new[]{b.colour,b.owner,b.meta,b.uv,b.domain,b.stamp}){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}}
  report["baseline76"]=new Obj58{["file"]="baseline76.buffer",["roiBottomLeft"]=new Arr58(probeROI.x,probeROI.y,probeROI.width,probeROI.height),["stride"]=96,["visits"]=visits[0],["producer"]="actual Evaluate entry before record writes; last deferred dispatch",["frameIndex"]=frameIndex,["mainSerial"]=serial,["allStampsVerified"]=true};
  report["largestOwnedReadbackBytes"]=Math.Max((long)report["largestOwnedReadbackBytes"],rows.Length*96L);
  FrozenOriginal76(e,frame);
  var sampleROI=new RectInt(0,0,e.roi.width*4,e.roi.height*4);
  for(int s=0;s<7;s++)
  {
   Plane(frame,"S"+s+"-meta",e.samples[s].meta,sampleROI,"EyeRenderer367.Samples current 4x","depth / role / stable eye ID / coverage");
   if(s>3)continue;
   Plane(frame,"S"+s+"-point",e.samples[s].point,sampleROI,"EyeRenderer367.Samples current 4x","rest head xyz / valid");
   Plane(frame,"S"+s+"-uv",e.samples[s].uv,sampleROI,"EyeRenderer367.Samples current 4x","source UV / primitive");
   Plane(frame,"S"+s+"-rgba",e.samples[s].rgba,sampleROI,"EyeRenderer367.Samples current 4x","source linear colour / alpha");
  }
  Plane(frame,"S3-shade",e.samples[3].shade,sampleROI,"EyeRenderer367.Samples current 4x","actual eyeline shade inputs");
  var ident=new PixelReadback70.Identity{source=sourceId,view="head",frame=frameIndex,serial=serial};
  var gpuROI=PixelReadback70.Readback.FromTopLeft(e.roi.x,e.roi.y,e.roi.width,e.roi.height);
  Func<PixelReadback70.Identity> now=()=>new PixelReadback70.Identity{source=sourceId,view="head",frame=Time.frameCount,serial=n.host.main.renderedSerial335};
  if(EyeFeature348.UseIrisSurface582||EyeFeature348.UseLashRegion583)throw new InvalidOperationException("Counts producer inactive; not an equivalent LayerMode19 input");
  PixelReadback70.Readback.Counts(output,"eye-counts76.bin",new PixelReadback70.UnityEyeBuffer(e.featureCounts19),ident,gpuROI,now,()=>exiting||finished);
  PixelReadback70.Readback.Records(output,"eye-records76.bin",new PixelReadback70.UnityEyeBuffer(e.records),ident,gpuROI,now,()=>exiting||finished);
  foreach(var item in new[]{new{n="head-final",t=f.colour},new{n="head-owner",t=f.owner},new{n="old-eye-owner",t=f.eyeOwner},new{n="old-intrinsic",t=f.intrinsic},new{n="old-eye-audit",t=f.eyeAudit},new{n="base-rgba",t=f.layers[8].rgba},new{n="base-meta",t=f.layers[8].meta},new{n="backing-rgba",t=f.layers[10].rgba},new{n="backing-meta",t=f.layers[10].meta},new{n="hair-meta",t=f.layers[6].meta},new{n="brow-meta",t=f.layers[7].meta}})Plane(frame,item.n,item.t,probeROI,"current deferred head graph","named channel; no guessed backing");
  int scale81=n.nativePixelsPerCell;Vector2 delta81=n.deliveredDelta;var origin81=n.origin;var shift81=n.host.offset;
  int nx81=Math.Max(0,(int)Math.Floor(origin81.x+(probeROI.x+shift81.x+delta81.x)*scale81)-2),ny81=Math.Max(0,(int)Math.Floor(origin81.y+(probeROI.y+shift81.y+delta81.y)*scale81)-2);
  int ex81=Math.Min(n.output.rt.width,(int)Math.Ceiling(origin81.x+(probeROI.xMax+shift81.x+delta81.x)*scale81)+2),ey81=Math.Min(n.output.rt.height,(int)Math.Ceiling(origin81.y+(probeROI.yMax+shift81.y+delta81.y)*scale81)+2);if(ex81<=nx81||ey81<=ny81)throw new InvalidOperationException("Final eye ROI outside native canvas");var nativeROI81=new RectInt(nx81,ny81,ex81-nx81,ey81-ny81);
  report["nativeEyeROI81"]=new Arr58(nx81,ny81,nativeROI81.width,nativeROI81.height);report["nativePresentation81"]=new Obj58{["cellScale"]=scale81,["origin"]=new Arr58(origin81.x,origin81.y),["delta"]=V(delta81),["headJoinOffset"]=new Arr58(shift81.x,shift81.y)};
  foreach(var target81 in new[]{new{n="native-eye-rgba",t=n.output},new{n="native-eye-cell",t=n.cellID},new{n="native-eye-owner",t=n.owner},new{n="native-eye-depth",t=n.depthAudit}})Plane(mainFrame,target81.n,target81.t,nativeROI81,"Native395.Present actual current final ROI","final RGBA/cell/owner/depth; explicit origin/delta/cellScale");
  if(captured76==0)for(int y=0;y<n.output.rt.height;y+=64)Plane(mainFrame,"final-strip-"+y,n.output,new RectInt(0,y,n.output.rt.width,Math.Min(64,n.output.rt.height-y)),"Native395 normal output","final linear RGBA");
  CpuSourceCapture64.WriteCpuGeometry(Path.Combine(output,"evaluated-source.geometry"),frame,f.motion.surface.outputs,f.motion.surface.source);CpuSourceCapture64.WriteCamera(Path.Combine(output,"source.camera"),frame);CpuSourceCapture64.WriteCamera(Path.Combine(output,"main.camera"),mainFrame);
  var ph=f.phases[f.phaseIndex];AuxMesh("phase-native-face",ph.nativeFace,f.providerMatrix*ph.nativeFaceMatrix,frame);
  report["eyeFeature"]=new Obj58{["roiTopLeft"]=new Arr58(e.roi.x,e.roi.y,e.roi.width,e.roi.height),["headMatrix"]=M(e.headMatrix),["inverse"]=new Arr58(f.eyeInverse.Select(x=>M(x))),["planes"]=new Arr58(f.eyePlanes.Select(x=>V(x))),["rayBase"]=V(f.rayBase),["rayX"]=V(f.rayX),["rayY"]=V(f.rayY),["rayDepth"]=V(f.rayDepth),["centres"]=new Arr58(e.centres.Select(x=>V(x))),["axesX"]=new Arr58(e.axesX.Select(x=>V(x))),["axesY"]=new Arr58(e.axesY.Select(x=>V(x))),["topologySHA256"]=e.modelTopologySHA256,["styleVersion"]=e.style.version,["upper"]=V(e.style.upper),["lower"]=V(e.style.lower),["irisRadii"]=V(e.style.irisRadii),["catchU"]=V(e.style.catchU),["catchV"]=V(e.style.catchV),["irisOffset"]=e.style.irisOffset,["irisPower"]=e.style.irisPower,["modelEyes"]=new Arr58(e.modelEyes.Select(x=>new Obj58{["id"]=x.stableId,["centre"]=V(x.centre),["axisX"]=V(x.axisX),["axisY"]=V(x.axisY),["measuredRadii"]=V(x.measuredRadii),["closedBoundary"]=new Arr58(x.closedBoundary)}))};
  report["modeFlags"]=new Obj58{["UseIrisSurface582"]=EyeFeature348.UseIrisSurface582,["UseLashRegion583"]=EyeFeature348.UseLashRegion583,["UseClosedLash590"]=EyeFeature348.UseClosedLash590,["phaseIndex"]=f.phaseIndex};
  report["frameIndex"]=frameIndex;report["mainSerial"]=serial;report["sourceFrame"]=f.motion.sourceFrame;report["evaluatedFrame"]=f.motion.evaluatedFrame;
  report["frameUnchangedDuringReadback"]=Time.frameCount==frameIndex&&n.host.main.renderedSerial335==serial;if(!(bool)report["frameUnchangedDuringReadback"])throw new InvalidOperationException("Frame changed during reads");
  report["packetComplete"]=true;CreateOnly73.Text(Path.Combine(output,"RAW_MANIFEST.json"),report.ToString());
  CreateOnly73.Text(Path.Combine(output,"RAW_COMPLETE76.marker"),SHA(Path.Combine(output,"RAW_MANIFEST.json")));Save("actual-pre348-and-individual-samples-complete");
 }

}
