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
 const string Root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\input-event83\run84";
 struct Baseline76 {public Vector4 colour,owner,meta,uv,domain,stamp;}
 MotionScope83 motion83;Arr58 probeRows83=new Arr58();
 UnityEngine.InputSystem.InputSettings settingsBefore83;string settingsJSON83;HideFlags settingsHide83;UnityEngine.InputSystem.InputDevice[] devicesBefore83;bool[] enabledBefore83;UnityEngine.InputSystem.Keyboard keyboardBefore83;
 void InputBackup83(){settingsBefore83=UnityEngine.InputSystem.InputSystem.settings;if(!settingsBefore83||EditorUtility.IsPersistent(settingsBefore83))throw new InvalidOperationException("Live nonpersistent input setting required; no replacement");settingsJSON83=JsonUtility.ToJson(settingsBefore83);settingsHide83=settingsBefore83.hideFlags;devicesBefore83=UnityEngine.InputSystem.InputSystem.devices.ToArray();enabledBefore83=devicesBefore83.Select(d=>d.enabled).ToArray();keyboardBefore83=UnityEngine.InputSystem.Keyboard.current;CreateOnly73.Text(Path.Combine(output,"EDIT_INPUT_BEFORE83.json"),new Obj58{["json"]=settingsJSON83,["nativeId"]=settingsBefore83.GetEntityId().ToString(),["hideFlags"]=settingsHide83.ToString(),["devices"]=new Arr58(devicesBefore83.Select(d=>new Obj58{["id"]=d.deviceId,["layout"]=d.layout,["enabled"]=d.enabled})),["keyboard"]=keyboardBefore83!=null?(Json58)keyboardBefore83.deviceId:null}.ToString());}
 void InputVerify83(){bool alive=settingsBefore83&&System.Object.ReferenceEquals(UnityEngine.InputSystem.InputSystem.settings,settingsBefore83),json=alive&&JsonUtility.ToJson(settingsBefore83)==settingsJSON83,flags=alive&&settingsBefore83.hideFlags==settingsHide83,devices=UnityEngine.InputSystem.InputSystem.devices.Count==devicesBefore83.Length&&devicesBefore83.All(d=>UnityEngine.InputSystem.InputSystem.devices.Contains(d)),enabled=devicesBefore83.Select((d,i)=>d.enabled==enabledBefore83[i]).All(v=>v),keyboard=System.Object.ReferenceEquals(UnityEngine.InputSystem.Keyboard.current,keyboardBefore83);report["editInputRestoration83"]=new Obj58{["sameAliveReference"]=alive,["exactJSON"]=json,["hideFlags"]=flags,["devicesSame"]=devices,["deviceEnabledStates"]=enabled,["keyboardSame"]=keyboard,["nativeId"]=alive?settingsBefore83.GetEntityId().ToString():"destroyed"};if(!alive||!json||!flags||!devices||!enabled||!keyboard)throw new InvalidOperationException("Input restoration mismatch after Play; no extra experiment");}

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
 void Arm76(NativePlayer395 n){native=n;probeEye=n.host.headEyes;if(!probeEye||!n.host.headEnabled)throw new InvalidOperationException("Head deferred path required");oldShader=probeEye.candidateShader;if(!NativeSource77.Build(probeEye,out var nativeData77,out var components77,out string reason77))throw new InvalidOperationException(reason77);if(nativeData77.Length*16L>1024*1024)throw new InvalidOperationException("Native metadata transfer exceeds one MiB");borrowedRest77=probeEye.restTriangles;var activeHeader77=new Vector4[1];borrowedRest77.GetData(activeHeader77,0,0,1);report["productCacheBeforeObserver77"]=activeHeader77[0].w;report["headMainRestDistinct77"]=!System.Object.ReferenceEquals(probeEye.restTriangles,n.host.mainEyes.restTriangles);report["productShaderSHA77"]=SHA(AssetDatabase.GetAssetPath(oldShader));report["productHelperSHA77"]=SHA("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/NativeCacheGPU77.hlsl");if(activeHeader77[0].w!=77)throw new InvalidOperationException("Actual product source cache was not initialized before observer");expectedRest77=null;report["restBufferReplaced83"]=false;
 report["nativeSource77"]=new Obj58{["bufferBytes"]=nativeData77.Length*16L,["topologySHA256"]=probeEye.modelTopologySHA256,["components"]=new Arr58(components77.Select(c=>new Obj58{["label"]=c.label,["eyeId"]=c.eyeId,["upper"]=c.upper,["meanRest"]=V(c.meanRest),["normalizedV"]=c.normalizedV,["triangles"]=c.triangles})),["productDefaultChanged"]=true};
report["actualRuntimeProductShaderPath"]=AssetDatabase.GetAssetPath(oldShader);probeShader=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/BaselineProbe77GPU.compute"));probeShader.hideFlags=HideFlags.DontSave;
 var r=probeEye.roi;probeROI=new RectInt(Math.Max(0,r.x-12),Math.Max(0,272-r.y-r.height-12),r.width+24,r.height+24);if(probeROI.xMax>480||probeROI.yMax>272)throw new InvalidOperationException("Probe near grid boundary");probeBuffer=new ComputeBuffer(probeROI.width*probeROI.height,96);probeVisits=new ComputeBuffer(1,4);probeVisits.SetData(new uint[1]);int k=probeShader.FindKernel("Evaluate");probeShader.SetBuffer(k,"_Baseline76",probeBuffer);probeShader.SetBuffer(k,"_ProbeVisits76",probeVisits);probeShader.SetInts("_ProbeROI76",probeROI.x,probeROI.y,probeROI.width,probeROI.height);probeEye.candidateShader=probeShader;armedSerial=n.host.main.renderedSerial335;RenderPipelineManager.beginCameraRendering+=CameraBegin76;motion83=new MotionScope83(n,output);motion83.Start();report["movementPlan83"]="Input only: exact80 Up/Right/release first6 queue-each-frame, second6 queue-on-transition. Normal speeds, no eye capture.";
 }
 void Release76(){RenderPipelineManager.beginCameraRendering-=CameraBegin76;motion83?.Dispose();report["motionRestoration83"]=motion83?.RestoreReport;if(probeEye&&oldShader)probeEye.candidateShader=oldShader;report["borrowedRestReferenceUntouched83"]=probeEye&&probeEye.restTriangles==borrowedRest77;report["borrowedRestDisposedByObserver83"]=false;probeBuffer?.Dispose();probeBuffer=null;probeVisits?.Dispose();probeVisits=null;if(probeShader)UnityEngine.Object.DestroyImmediate(probeShader);probeShader=null;report["ownedProbeReleased76"]=true;}
 string sequenceDirectory,sequenceId;Arr58 packetList76=new Arr58();int captured76,previousFrame76=-1;
 GlobalJournal64 journal;Arr58 nativeBefore;bool oldPlayerBackground;Obj58 report;string output,sourceId;int stateSequence;Arr58 planes=new Arr58();
 RenderPipelineAsset oldG,oldQ;float oldTime,oldCapture;bool oldOptions,oldPause,started,exiting,finished;EnterPlayModeOptions oldFlags;double start,lastTelemetry;bool oldBackground;int exitTicks,domain;long readyAllocated;
 static Arr58 V(Vector2 v){return new Arr58(v.x,v.y);}static Arr58 V(Vector3 v){return new Arr58(v.x,v.y,v.z);}static Arr58 V(Vector4 v){return new Arr58(v.x,v.y,v.z,v.w);}static Arr58 M(Matrix4x4 m){return new Arr58(Enumerable.Range(0,16).Select(i=>(double)m[i]));}
 static string SHA(string path){using(var h=SHA256.Create())using(var f=File.OpenRead(path))return BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant();}
 static Obj58 Memory(){return new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["allocated"]=Profiler.GetTotalAllocatedMemoryLong(),["reserved"]=Profiler.GetTotalReservedMemoryLong(),["mono"]=Profiler.GetMonoUsedSizeLong(),["renderTextureCount"]=Resources.FindObjectsOfTypeAll<RenderTexture>().Length};}
 static Arr58 Dirty(){return new Arr58(Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o)).Select(o=>new Obj58{["path"]=AssetDatabase.GetAssetPath(o),["type"]=o.GetType().FullName}));}
 static Arr58 Scenes(){var a=new Arr58();for(int i=0;i<SceneManager.sceneCount;i++){var s=SceneManager.GetSceneAt(i);a.Add(new Obj58{["path"]=s.path,["dirty"]=s.isDirty,["active"]=s==SceneManager.GetActiveScene(),["roots"]=s.rootCount});}return a;}
 void Save(string stage){report["stage"]=stage;report["utc"]=DateTime.UtcNow.ToString("O");report["planes"]=planes;CreateOnly73.Text(Path.Combine(Root,"STATE84-"+(stateSequence++).ToString("D4")+"-"+stage+".json"),report.ToString());}

 public void Execute(ExecutionResult result)
 {
  if(File.Exists(Path.Combine(Root,"CAPTURE_STARTED76.json")))throw new InvalidOperationException("Existing capture outcome must be inspected; no repeat");CreateOnly73.Text(Path.Combine(Root,"CAPTURE_STARTED76.json"),"one approved observer invocation");
  sourceId="eye84-"+DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ")+"-"+Guid.NewGuid().ToString("N").Substring(0,8);output=Path.Combine(Root,sourceId);if(Directory.Exists(output))throw new IOException("Unique output required");Directory.CreateDirectory(output);
  report=new Obj58{["sourceId"]=sourceId,["output"]=output,["revision84"]="Only removed UNITY_EDITOR guard around existing planned policy assignment; added read-only policy getters",["PlayEntries"]=0,["packetComplete"]=false,["captureContractStatus"]="RAW_INPUT_PENDING_OFFLINE_CORRESPONDENCE",["largestOwnedReadbackBytes"]=0,["simultaneousReadbacks"]=1,["resetHistoryRequestedByObserver"]=false};
  try
  {
   if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required");
   if(Enumerable.Range(0,SceneManager.sceneCount).Select(SceneManager.GetSceneAt).Any(s=>s.isDirty))throw new InvalidOperationException("Scene changed before capture");
   InputBackup83();oldPlayerBackground=PlayerSettings.runInBackground;nativeBefore=NativeSnapshot73.Backup(Root);domain=AppDomain.CurrentDomain.Id;oldBackground=Application.runInBackground;oldOptions=EditorSettings.enterPlayModeOptionsEnabled;oldFlags=EditorSettings.enterPlayModeOptions;oldPause=EditorApplication.isPaused;oldTime=Time.timeScale;oldCapture=Time.captureDeltaTime;oldG=GraphicsSettings.defaultRenderPipeline;oldQ=QualitySettings.renderPipeline;
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
   if(EditorApplication.timeSinceStartup-lastTelemetry>.5){lastTelemetry=EditorApplication.timeSinceStartup;CreateOnly73.Text(Path.Combine(Root,"TRACE84-"+Guid.NewGuid().ToString("N")+".json"),new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["frame"]=Time.frameCount,["paused"]=EditorApplication.isPaused,["focused"]=Application.isFocused,["timeScale"]=Time.timeScale,["background"]=Application.runInBackground,["hasNative"]=n!=null,["nativeEnabled"]=n&&n.enabled,["nativeActive"]=n&&n.gameObject.activeInHierarchy,["nativeWarmup"]=n?n.warmup:-1,["nativeReady"]=n&&n.ready,["nativeFailure"]=n?n.failure:null,["hasGameplay"]=gp!=null,["gameplayActive"]=gp&&gp.activateGameplay,["connected"]=gp&&gp.connected,["gameplayFailure"]=gp?gp.failure:null,["mainSerial"]=n&&n.host&&n.host.main?n.host.main.renderedSerial335:0}.ToString()+"\n");}
   if(EditorApplication.isPaused)throw new InvalidOperationException("Runtime paused before observer ready; do not override unidentified pause");
   if(!n||!n.ready||!gp||!gp.connected||n.host.main.renderedSerial335<=0)return;
   if(gp.runInputTest)throw new InvalidOperationException("Synthetic input test enabled");
   if(!probeShader){Arm76(n);Save("probe-armed-on-live-head-next-normal-frame");return;}
   if(n.host.main.renderedSerial335<=armedSerial)return;
   if(!motion83.Ready(n.host.main.renderedSerial335)){armedSerial=n.host.main.renderedSerial335;report["motionWarmup83"]=motion83.warmup;report["dynamicInput83"]=motion83.dynamicInput;return;}
   var observation=motion83.ObserveProbe83();probeRows83.Add(observation);report["inputProbe83"]=probeRows83;report["events83"]=motion83.events83;report["dynamicInput83"]=motion83.dynamicInput;Save("input-probe-"+motion83.ProbeIndex);
   if(!motion83.ProbeMatches83)throw new InvalidOperationException("Same80 input/order failed in motion observer; stop without image capture or extra state changes");
   if(motion83.AdvanceProbe83()){armedSerial=n.host.main.renderedSerial335;return;}report["inputProbePassed83"]=true;BeginExit();
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
   report["backgroundRestored"]=Application.runInBackground==oldBackground;report["PlayExited"]=!EditorApplication.isPlaying&&!EditorApplication.isPlayingOrWillChangePlaymode;InputVerify83();report["observerRemoved"]=true;if(motion83!=null&&!motion83.Restored)throw new InvalidOperationException("Input/movement scope restoration failed; see motionRestoration83");Save("finished");
  }
  catch(Exception e){report["restorationError"]=e.ToString();Save("restoration-incomplete");}
 }
}
