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
 const string Root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66\retry-background";
 GlobalJournal64 journal;Obj58 report;string output,sourceId;Arr58 planes=new Arr58();
 RenderPipelineAsset oldG,oldQ;float oldTime,oldCapture;bool oldOptions,oldPause,started,exiting,finished;EnterPlayModeOptions oldFlags;double start,lastTelemetry;bool oldBackground;int exitTicks,domain;long readyAllocated;
 static Arr58 V(Vector2 v){return new Arr58(v.x,v.y);}static Arr58 V(Vector3 v){return new Arr58(v.x,v.y,v.z);}static Arr58 V(Vector4 v){return new Arr58(v.x,v.y,v.z,v.w);}static Arr58 M(Matrix4x4 m){return new Arr58(Enumerable.Range(0,16).Select(i=>(double)m[i]));}
 static string SHA(string path){using(var h=SHA256.Create())using(var f=File.OpenRead(path))return BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant();}
 static Obj58 Memory(){return new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["allocated"]=Profiler.GetTotalAllocatedMemoryLong(),["reserved"]=Profiler.GetTotalReservedMemoryLong(),["mono"]=Profiler.GetMonoUsedSizeLong(),["renderTextureCount"]=Resources.FindObjectsOfTypeAll<RenderTexture>().Length};}
 static Arr58 Dirty(){return new Arr58(Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o)).Select(o=>new Obj58{["path"]=AssetDatabase.GetAssetPath(o),["type"]=o.GetType().FullName}));}
 static Arr58 Scenes(){var a=new Arr58();for(int i=0;i<SceneManager.sceneCount;i++){var s=SceneManager.GetSceneAt(i);a.Add(new Obj58{["path"]=s.path,["dirty"]=s.isDirty,["active"]=s==SceneManager.GetActiveScene(),["roots"]=s.rootCount});}return a;}
 void Save(string stage){report["stage"]=stage;report["utc"]=DateTime.UtcNow.ToString("O");report["planes"]=planes;File.WriteAllText(Path.Combine(Root,"CAPTURE_STATE66.json"),report.ToString());}
 public void Execute(ExecutionResult result)
 {
  if(File.Exists(Path.Combine(Root,"CAPTURE_STATE66.json")))throw new InvalidOperationException("Existing capture outcome must be inspected; no repeat");
  sourceId="capture67-"+DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ");output=Path.Combine(Root,sourceId);Directory.CreateDirectory(output);
  report=new Obj58{["sourceId"]=sourceId,["output"]=output,["PlayEntries"]=0,["packetComplete"]=false,["captureContractStatus"]="RAW_INPUT_PENDING_OFFLINE_CORRESPONDENCE",["largestOwnedReadbackBytes"]=0,["simultaneousReadbacks"]=1,["resetHistoryRequestedByObserver"]=false};
  try
  {
   if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required");
   if(Enumerable.Range(0,SceneManager.sceneCount).Select(SceneManager.GetSceneAt).Any(s=>s.isDirty))throw new InvalidOperationException("Scene changed before capture");
   domain=AppDomain.CurrentDomain.Id;oldBackground=Application.runInBackground;oldOptions=EditorSettings.enterPlayModeOptionsEnabled;oldFlags=EditorSettings.enterPlayModeOptions;oldPause=EditorApplication.isPaused;oldTime=Time.timeScale;oldCapture=Time.captureDeltaTime;oldG=GraphicsSettings.defaultRenderPipeline;oldQ=QualitySettings.renderPipeline;
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
   if(EditorApplication.timeSinceStartup-start>70)throw new TimeoutException("Normal-ready timeout; no second Play");
   if(!EditorApplication.isPlaying)return;
   var n=UnityEngine.Object.FindObjectsByType<NativePlayer395>(FindObjectsSortMode.None).FirstOrDefault();
   if(n&&!string.IsNullOrEmpty(n.failure))throw new InvalidOperationException(n.failure);
   var gp=UnityEngine.Object.FindObjectsByType<Gameplay397>(FindObjectsSortMode.None).FirstOrDefault(g=>g.player==n);
   if(EditorApplication.timeSinceStartup-lastTelemetry>.5){lastTelemetry=EditorApplication.timeSinceStartup;File.AppendAllText(Path.Combine(Root,"WAIT_TRACE.jsonl"),new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["frame"]=Time.frameCount,["paused"]=EditorApplication.isPaused,["timeScale"]=Time.timeScale,["background"]=Application.runInBackground,["hasNative"]=n!=null,["nativeReady"]=n&&n.ready,["hasGameplay"]=gp!=null,["connected"]=gp&&gp.connected,["gameplayFailure"]=gp?gp.failure:null,["mainSerial"]=n&&n.host&&n.host.main?n.host.main.renderedSerial335:0}.ToString()+"\n");}
   if(EditorApplication.isPaused)throw new InvalidOperationException("Runtime paused before observer ready; do not override unidentified pause");
   if(!n||!n.ready||!gp||!gp.connected||n.host.main.renderedSerial335<=0)return;
   if(gp.runInputTest)throw new InvalidOperationException("Synthetic input test enabled");
   EditorApplication.isPaused=true;readyAllocated=Profiler.GetTotalAllocatedMemoryLong();report["readyMemory"]=Memory();report["frameIndex"]=Time.frameCount;report["deltaTime"]=Time.deltaTime;report["hostMainRenderSerial"]=n.host.main.renderedSerial335;Save("paused-already-rendered");
   Capture(n,gp);report["afterCaptureReleaseMemory"]=Memory();BeginExit();
  }
  catch(Exception e){report["error"]=e.ToString();BeginExit();}
 }
 void BeginExit(){if(exiting||finished)return;exiting=true;Save("normal-Play-exit-requested");if(EditorApplication.isPlaying||EditorApplication.isPlayingOrWillChangePlaymode){EditorApplication.isPaused=false;EditorApplication.ExitPlaymode();}else Finish();}
 void Finish()
 {
  if(finished)return;finished=true;EditorApplication.update-=Tick;
  try
  {
   if(started){Application.runInBackground=oldBackground;EditorSettings.enterPlayModeOptionsEnabled=oldOptions;EditorSettings.enterPlayModeOptions=oldFlags;GraphicsSettings.defaultRenderPipeline=oldG;QualitySettings.renderPipeline=oldQ;Time.timeScale=oldTime;Time.captureDeltaTime=oldCapture;EditorApplication.isPaused=oldPause;}
   if(journal!=null){journal.RestoreMarked();var errors=journal.VerifyMarked();report["globalRestoreErrors"]=new Arr58(errors);if(errors.Length>0)throw new InvalidOperationException("Global getter restoration failed");journal.ReleaseHandleAfterVerified();}
   report["afterMemory"]=Memory();report["afterDirty"]=Dirty();report["afterScenes"]=Scenes();report["optionsRestored"]=!started||(EditorSettings.enterPlayModeOptionsEnabled==oldOptions&&EditorSettings.enterPlayModeOptions==oldFlags);report["timeRestored"]=!started||(Time.timeScale==oldTime&&Time.captureDeltaTime==oldCapture&&EditorApplication.isPaused==oldPause);report["pipelineRestored"]=!started||(GraphicsSettings.defaultRenderPipeline==oldG&&QualitySettings.renderPipeline==oldQ);
   report["backgroundRestored"]=Application.runInBackground==oldBackground;report["PlayExited"]=!EditorApplication.isPlaying&&!EditorApplication.isPlayingOrWillChangePlaymode;report["observerRemoved"]=true;Save("finished");
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
  using(var w=new BinaryWriter(File.Create(path))){w.Write("aux-mesh67/v1");w.Write(sourceId);w.Write(frame.viewId);w.Write(frame.frameIndex);w.Write(frame.renderSerial);for(int i=0;i<16;i++)w.Write(matrix[i]);var p=mesh.vertices;var uv=mesh.uv;var n=mesh.normals;w.Write(p.Length);foreach(var v in p){w.Write(v.x);w.Write(v.y);w.Write(v.z);}w.Write(n.Length);foreach(var v in n){w.Write(v.x);w.Write(v.y);w.Write(v.z);}w.Write(uv.Length);foreach(var v in uv){w.Write(v.x);w.Write(v.y);}w.Write(mesh.subMeshCount);for(int sm=0;sm<mesh.subMeshCount;sm++){var ix=mesh.GetIndices(sm);w.Write(ix.Length);foreach(int i in ix)w.Write(i);}}
 }
 void Buffer(string name,ComputeBuffer buffer,CpuSourceCapture64.Frame frame)
 {
  if(buffer==null||!buffer.IsValid())return;long size=(long)buffer.count*buffer.stride;if(size>1024*1024)throw new InvalidOperationException("Feature buffer exceeds one MiB");
  using(var w=new BinaryWriter(File.Create(Path.Combine(output,name+".buffer")))){w.Write("buffer67/v1");w.Write(sourceId);w.Write(frame.viewId);w.Write(frame.frameIndex);w.Write(frame.renderSerial);w.Write(buffer.count);w.Write(buffer.stride);if(buffer.stride==4){var data=new uint[buffer.count];buffer.GetData(data);foreach(uint v in data)w.Write(v);}else if(buffer.stride==16){var data=new Vector4[buffer.count];buffer.GetData(data);foreach(var v in data){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}}else throw new InvalidOperationException("Unimplemented feature buffer stride");}
 }
 void Capture(NativePlayer395 n,Gameplay397 gp)
 {
  int serial=n.host.main.renderedSerial335,frameIndex=Time.frameCount;var f=n.host.head?n.host.head:n.host.main;string view=n.host.head?"head":"main";var frame=Frame(f,view,serial);var mainFrame=Frame(n.host.main,"main-final",serial);
  var bindings=new Arr58();foreach(var v in new[]{n.host.main,n.host.head}.Where(v=>v))
  {
   var handles=v.motion.materials.Select(m=>m.GetBuffer("_BodyScope551")).ToArray();if(handles.Any(h=>h.Equals(default(GraphicsBufferHandle)))||handles.Any(h=>!h.Equals(handles[0])))throw new InvalidOperationException("Actual production material scope bindings not coherent");
   bindings.Add(new Obj58{["view"]=v==f?view:"main",["materialCount"]=handles.Length,["handleHash"]=handles[0].GetHashCode(),["allLocalHandlesEqual"]=true});
  }
  report["actualProductionMaterialBindings"]=bindings;Save("production-bindings-verified-before-readback");
  CpuSourceCapture64.WriteCpuGeometry(Path.Combine(output,"evaluated-source.geometry"),frame,f.motion.surface.outputs,f.motion.surface.source);CpuSourceCapture64.WriteCamera(Path.Combine(output,"source.camera"),frame);CpuSourceCapture64.WriteCamera(Path.Combine(output,"main.camera"),mainFrame);
  var roi=MetaAndBounds(frame,f);report["sourceROIBottomLeft"]=new Arr58(roi.x,roi.y,roi.width,roi.height);
  var nativeROI=new RectInt(roi.x*2,roi.y*2,roi.width*2,roi.height*2);if((long)nativeROI.width*nativeROI.height*16>1024*1024)throw new InvalidOperationException("Source ROI too large for bounded plane; no extra readback");
  for(int y=0;y<n.output.rt.height;y+=64)Plane(mainFrame,"final-strip-"+y,n.output,new RectInt(0,y,n.output.rt.width,Math.Min(64,n.output.rt.height-y)),"Native395 current normal output","final linear RGBA");
  foreach(var item in new[]{new{n="unlit-source",t=f.native[0]},new{n="native-normal",t=f.native[1]},new{n="physical",t=f.native[3]},new{n="native-endpoint",t=f.native[5]},new{n="native-uv",t=f.native[6]},new{n="world",t=f.native[7]},new{n="style-class",t=f.style960[3]},new{n="shade-mask",t=f.shadeMask960}})Plane(frame,item.n,item.t,nativeROI,"Native333 / original335 signals","actual producer channels; source/class/mask definitions in code manifest");
  foreach(var item in new[]{new{n="selected-uv",t=f.preparedUV},new{n="source-final",t=f.colour},new{n="source-owner",t=f.owner},new{n="shade-class480",t=f.style480[3]},new{n="shade-mask480",t=f.shadeMask480}})Plane(frame,item.n,item.t,roi,"Prepare333 / RestoreStyle335","selected current logical cell metadata/colour");
  int ex0=480,ey0=272,ex1=0,ey1=0;foreach(var p in f.projectedPivots){int x=Mathf.RoundToInt(p.x),y=271-Mathf.RoundToInt(p.y);ex0=Math.Min(ex0,x-12);ex1=Math.Max(ex1,x+13);ey0=Math.Min(ey0,y-10);ey1=Math.Max(ey1,y+11);}var eyeROI=new RectInt(Math.Max(0,ex0),Math.Max(0,ey0),Math.Min(480,ex1)-Math.Max(0,ex0),Math.Min(272,ey1)-Math.Max(0,ey0));
  report["eyeROIBottomLeft"]=new Arr58(eyeROI.x,eyeROI.y,eyeROI.width,eyeROI.height);
  foreach(int part in new[]{0,1,2,3,4,5,6,7,8,9,10,11,12}){Plane(frame,"eye-"+part+"-rgba",f.layers[part].rgba,eyeROI,"FullFeature367.Eyes part"+part,"actual pre-eye styled RGBA; part10 is clean backing");Plane(frame,"eye-"+part+"-meta",f.layers[part].meta,eyeROI,"FullFeature367.Eyes part"+part,"actual owner/depth metadata");Plane(frame,"eye-"+part+"-uv",f.layers[part].uv,eyeROI,"FullFeature367.Eyes part"+part,"actual source UV");}
  var ph=f.phases[f.phaseIndex];AuxMesh("phase-backing",ph.backing,f.providerMatrix,frame);AuxMesh("phase-face",ph.face,f.providerMatrix,frame);AuxMesh("phase-native-face",ph.nativeFace,f.providerMatrix*ph.nativeFaceMatrix,frame);
  var e=UnityEngine.Object.FindObjectsByType<EyeFeature348>(FindObjectsSortMode.None).FirstOrDefault(x=>x.full==f);
  if(e){Buffer("eye-feature-counts",e.featureCounts19,frame);Buffer("eye-records",e.records,frame);Buffer("eye-lash-geometry",e.lashGeometry590,frame);report["eyeFeature"]=new Obj58{["topologySHA256"]=e.modelTopologySHA256,["styleVersion"]=e.style.version,["roi"]=new Arr58(e.roi.x,e.roi.y,e.roi.width,e.roi.height),["headMatrix"]=M(e.headMatrix),["cropProjection"]=M(e.cropProjection),["featureCountsSkippedByDispatch"]=EyeFeature348.UseIrisSurface582||EyeFeature348.UseLashRegion583,["stableIds"]=new Arr58(e.modelEyes.Select(x=>x.stableId))};}
  report["modeFlags"]=new Obj58{["motionMode"]=f.motion.mode,["poseBins"]=f.motion.poseBins,["phaseIndex"]=f.phaseIndex,["styleEnabled"]=f.styleEnabled,["layeredSurface"]=f.layeredSurface,["shadeLayer"]=f.shadeLayer,["surfaceSteps"]=f.surfaceShadeSteps,["UseIrisSurface582"]=EyeFeature348.UseIrisSurface582,["UseLashRegion583"]=EyeFeature348.UseLashRegion583,["UseClosedLash590"]=EyeFeature348.UseClosedLash590,["oldLayerMode19GetterAvailable"]=false};
  report["sourceView"]=view;report["phaseIndex"]=f.phaseIndex;report["sourceFrame"]=f.motion.sourceFrame;report["evaluatedFrame"]=f.motion.evaluatedFrame;report["sourceViewRenderedSerial335"]=f.renderedSerial335;report["mainRenderedSerial335"]=n.host.main.renderedSerial335;report["renderSerialProducer"]="HeadLocal367.RenderFrame increments public main.renderedSerial335 after normal final pass; per-view counter also recorded, no private Gameplay397 access";
  report["geometryFile"]= "evaluated-source.geometry";report["poseDigest"]=SHA(Path.Combine(output,"evaluated-source.geometry"));report["headOffset"]=new Arr58(n.host.offset.x,n.host.offset.y);report["nativeOrigin"]=new Arr58(n.origin.x,n.origin.y);report["nativeDeliveredDelta"]=V(n.deliveredDelta);report["nativePixelsPerCell"]=n.nativePixelsPerCell;report["sourceColorSpace"]="native[0] unlit texture sample*material factor in linear RT; hardware sRGB sampling per original material";
  report["gDefinition"]=new Obj58{["producerFunction"]="ContinuousSurfaceLight335 (original current product)",["formula"]="lit=ambient+sum(luma(color)*distanceAttenuation*shadow*saturate(.5*dot(N,L)+.5)); available=ambient+sum(luma(color)*distanceAttenuation); g=saturate(lit/available)",["units"]="dimensionless normalized ratio; not absolute irradiance",["classGChannel"]="style-class.g"};
  report["coverageDefinition"]="Native raster-sample presence and alpha are available; exact continuous projected cell area must be computed from captured geometry, not substituted by alpha.";
  report["missingBeforeOfflineBinding"]=new Arr58("native sample to evaluated triangle/barycentric/world/screen correspondence","source UV feature-boundary projection correspondence","six historical backing destinations mapped into this sourceId/state; complete part10 backing planes captured");
  report["lights"]=new Arr58(UnityEngine.Object.FindObjectsByType<Light>(FindObjectsSortMode.None).Select(l=>new Obj58{["type"]=l.type.ToString(),["enabled"]=l.isActiveAndEnabled,["position"]=V(l.transform.position),["forward"]=V(l.transform.forward),["colour"]=new Arr58(l.color.r,l.color.g,l.color.b),["intensity"]=l.intensity,["range"]=l.range,["spotAngle"]=l.spotAngle,["shadowStrength"]=l.shadowStrength}));
  report["frameUnchangedDuringReadback"]=Time.frameCount==frameIndex&&n.host.main.renderedSerial335==serial;if(!(bool)report["frameUnchangedDuringReadback"])throw new InvalidOperationException("Source frame advanced; packet incomplete");
  File.WriteAllText(Path.Combine(output,"RAW_MANIFEST.json"),report.ToString());Save("raw-input-captured-pending-offline-binding");
 }
}
