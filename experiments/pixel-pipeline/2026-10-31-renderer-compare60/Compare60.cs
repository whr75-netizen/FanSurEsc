using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Unity.Collections;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.Experimental.Rendering;

// In-memory command only. No C# Assets import or runtime assembly reload.
internal class CommandScript:IRunCommand {
 const string Root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\renderer-compare60";
 const string Probe="Assets/Editor/RendererCompare60Probe/";
 Obj58 report,before;RenderPipelineAsset oldG,oldQ;float oldTime,oldCapture;bool oldPause,oldOptions;EnterPlayModeOptions oldFlags;
 Dictionary<string,float> floats=new Dictionary<string,float>();Dictionary<string,int> ints=new Dictionary<string,int>();Dictionary<string,Vector4> vectors=new Dictionary<string,Vector4>();Dictionary<string,Matrix4x4> matrices=new Dictionary<string,Matrix4x4>();Dictionary<string,Texture> textures=new Dictionary<string,Texture>();
 bool started,exiting,finished;int exitTicks;double start;int domain;
 List<ComputeBuffer> buffers=new List<ComputeBuffer>();List<Material> materials=new List<Material>();List<ComputeShader> computes=new List<ComputeShader>();
 struct U4 {public uint x,y,z,w;public U4(uint a,uint b,uint c,uint d){x=a;y=b;z=c;w=d;}}
 sealed class Saved {public Full319View335 f;public Material[] legacy,independent;public ComputeShader restore;}
 List<Saved> saved=new List<Saved>();
 Dictionary<int,int> roleDraw=new Dictionary<int,int>();SourcePalette58.Palette[] palettes;RendererFamily59 provider;Json58 registry;uint[] roleFamily=new uint[16];
 void Save(string stage){report["stage"]=stage;report["utc"]=DateTime.UtcNow.ToString("O");File.WriteAllText(Path.Combine(Root,"RESULT60.json"),report.ToString());}
 public void Execute(ExecutionResult result){
  report=new Obj58{["sourceId"]="renderer60-"+DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ"),["mode"]="same-frame hair-only runtime shader/compute clones",["playEntries"]=0,["cleanBackingSixCollected"]=false};
  try{
   before=State58.Read();State58.RequireEdit(before);report["before"]=before;report["memoryBefore"]=State58.Memory();domain=AppDomain.CurrentDomain.Id;
   var expected=Obj58.Parse(File.ReadAllText(Path.Combine(Root,"PREFLIGHT60.json")))["state"];
   bool oldDirtyExact=expected["dirty"].All(o=>before["dirty"].Any(n=>Json58.DeepEquals(o,n)));
   bool oldFilesExact=expected["files"].All(o=>before["files"].Any(n=>Json58.DeepEquals(o,n)));
   var addedDirty=before["dirty"].Where(n=>!expected["dirty"].Any(o=>(string)o["path"]==(string)n["path"])).ToArray();
   // The first attempt stopped before Play. Subsequent disk audit found no
   // source changes; preserve the newly observed loaded Shader as current state.
   bool onlyRecordedShader=addedDirty.All(n=>(string)n["path"]=="Assets/EUnityValidation01/SourceLight329/Shaders/CommonSurface329.shader");
   report["additionalPrePlayDirty"]=new Arr58(addedDirty);report["original24ExactBefore"]=oldDirtyExact;
   if(!oldDirtyExact||!oldFilesExact||!onlyRecordedShader||!Json58.DeepEquals(expected["scenes"],before["scenes"]))throw new InvalidOperationException("Unaccounted state change since preflight; no Play");
   if(UnityEngine.Object.FindObjectsByType<NativePlayer395>(FindObjectsInactive.Include,FindObjectsSortMode.None).Length!=0)throw new InvalidOperationException("Unexpected existing native instance");
   oldOptions=EditorSettings.enterPlayModeOptionsEnabled;oldFlags=EditorSettings.enterPlayModeOptions;oldG=GraphicsSettings.defaultRenderPipeline;oldQ=QualitySettings.renderPipeline;oldTime=Time.timeScale;oldCapture=Time.captureDeltaTime;oldPause=EditorApplication.isPaused;
   foreach(var g in Json58.Parse(File.ReadAllText(Path.Combine(Root,"GLOBAL_NAMES60.json")))){
    string n=(string)g["name"];switch((string)g["type"]){case "Float":floats[n]=Shader.GetGlobalFloat(n);break;case "Int":ints[n]=Shader.GetGlobalInt(n);break;case "Vector":vectors[n]=Shader.GetGlobalVector(n);break;case "Matrix":matrices[n]=Shader.GetGlobalMatrix(n);break;case "Texture":textures[n]=Shader.GetGlobalTexture(n);break;}
   }
   report["globalValueCount"]=floats.Count+ints.Count+vectors.Count+matrices.Count+textures.Count;report["globalBufferBindingsSnapshot"]=false;
   foreach(var n in new[]{"SourcePalette54.hlsl","LegacySignals60.shader","Independent60.shader","RestoreStyle60.compute"})AssetDatabase.ImportAsset(Probe+n,ImportAssetOptions.ForceSynchronousImport);
   var s1=AssetDatabase.LoadAssetAtPath<Shader>(Probe+"LegacySignals60.shader");var s2=AssetDatabase.LoadAssetAtPath<Shader>(Probe+"Independent60.shader");var cs=AssetDatabase.LoadAssetAtPath<ComputeShader>(Probe+"RestoreStyle60.compute");
   if(!s1||!s2||!cs||!s1.isSupported||!s2.isSupported)throw new InvalidOperationException("Candidate shader not available");
   var messages=ShaderUtil.GetShaderMessages(s1).Concat(ShaderUtil.GetShaderMessages(s2)).Select(m=>m.severity+": "+m.message).Concat(ShaderUtil.GetComputeShaderMessages(cs).Select(m=>m.severity+": "+m.message)).ToArray();report["shaderMessages"]=new Arr58(messages);if(messages.Any(m=>m.StartsWith("Error")))throw new InvalidOperationException("Candidate shader compile error");
   var imported=State58.Read();bool sameOriginal=before["dirty"].All(o=>imported["dirty"].Any(n=>Json58.DeepEquals(o,n)));bool onlyOwnedAdded=imported["dirty"].Where(n=>!before["dirty"].Any(o=>(string)o["path"]==(string)n["path"])).All(n=>((string)n["path"]).StartsWith(Probe));if(AppDomain.CurrentDomain.Id!=domain||EditorApplication.isCompiling||!sameOriginal||!onlyOwnedAdded)throw new InvalidOperationException("Import affected domain or original dirty assets");
   report["importStateChanges"]=new Arr58(State58.Changes(before,imported));Save("ready-before-Play");
   start=EditorApplication.timeSinceStartup;EditorApplication.update+=Tick;started=true;
   EditorSettings.enterPlayModeOptionsEnabled=true;EditorSettings.enterPlayModeOptions=EnterPlayModeOptions.DisableDomainReload;
   report["temporaryOptions"]="DisableDomainReload; scene reload enabled";report["playEntries"]=1;Save("entering-Play");EditorApplication.EnterPlaymode();
   result.Log("60 armed single normal Play; observer owns normal exit and option restoration");
  }catch(Exception e){report["error"]=e.ToString();if(started)BeginExit();else Finish();result.Log("60 stopped before Play: "+e.Message);}
 }
 void Tick(){
  if(finished)return;
  try{
   if(AppDomain.CurrentDomain.Id!=domain)throw new InvalidOperationException("Unexpected domain reload");
   if(exiting){if(!EditorApplication.isPlaying&&!EditorApplication.isPlayingOrWillChangePlaymode&&++exitTicks>=8)Finish();return;}
   if(EditorApplication.timeSinceStartup-start>55)throw new TimeoutException("Ready timeout; single Play will exit without another entry");
   if(!EditorApplication.isPlaying)return;
   var n=UnityEngine.Object.FindObjectsByType<NativePlayer395>(FindObjectsSortMode.None).FirstOrDefault();
   if(n&&!string.IsNullOrEmpty(n.failure))throw new InvalidOperationException("Native renderer failure: "+n.failure);
   var gp=UnityEngine.Object.FindObjectsByType<Gameplay397>(FindObjectsSortMode.None).FirstOrDefault(g=>g.player==n);
   if(!n||!n.ready||!gp||!gp.connected)return;
   if(gp.runInputTest)throw new InvalidOperationException("Synthetic input test unexpectedly enabled");
   EditorApplication.isPaused=true;report["frameIndex"]=Time.frameCount;report["deltaTime"]=Time.deltaTime;report["runtimeInputTest"]=gp.runInputTest;report["runtimeReady"]=true;Save("paused-ready");
   Capture(n);BeginExit();
  }catch(Exception e){report["error"]=e.ToString();BeginExit();}
 }
 void BeginExit(){RestoreClones();exiting=true;Save("normal-Play-exit-requested");if(EditorApplication.isPlaying||EditorApplication.isPlayingOrWillChangePlaymode){EditorApplication.isPaused=false;EditorApplication.ExitPlaymode();}else Finish();}
 void RestoreClones(){foreach(var s in saved)if(s.f){s.f.legacySignalsMats=s.legacy;s.f.independentMats=s.independent;s.f.restoreStyle=s.restore;}saved.Clear();foreach(var m in materials)if(m)UnityEngine.Object.DestroyImmediate(m);materials.Clear();foreach(var c in computes)if(c)UnityEngine.Object.DestroyImmediate(c);computes.Clear();foreach(var b in buffers)b.Release();buffers.Clear();}
 void Finish(){
  if(finished)return;finished=true;EditorApplication.update-=Tick;
  try{
   RestoreClones();if(started){EditorSettings.enterPlayModeOptionsEnabled=oldOptions;EditorSettings.enterPlayModeOptions=oldFlags;GraphicsSettings.defaultRenderPipeline=oldG;QualitySettings.renderPipeline=oldQ;Time.timeScale=oldTime;Time.captureDeltaTime=oldCapture;EditorApplication.isPaused=oldPause;
    foreach(var p in floats)Shader.SetGlobalFloat(p.Key,p.Value);foreach(var p in ints)Shader.SetGlobalInt(p.Key,p.Value);foreach(var p in vectors)Shader.SetGlobalVector(p.Key,p.Value);foreach(var p in matrices)Shader.SetGlobalMatrix(p.Key,p.Value);foreach(var p in textures)Shader.SetGlobalTexture(p.Key,p.Value);
   }
   var after=State58.Read();report["after"]=after;report["memoryAfter"]=State58.Memory();report["optionsRestored"]=!started||(EditorSettings.enterPlayModeOptionsEnabled==oldOptions&&EditorSettings.enterPlayModeOptions==oldFlags);report["pipelineRestored"]=!started||(GraphicsSettings.defaultRenderPipeline==oldG&&QualitySettings.renderPipeline==oldQ);report["timeRestored"]=!started||(Time.timeScale==oldTime&&Time.captureDeltaTime==oldCapture&&EditorApplication.isPaused==oldPause);
   report["originalDirtyExact"]=Json58.DeepEquals(before["dirty"],after["dirty"]);report["diskFilesExact"]=Json58.DeepEquals(before["files"],after["files"]);report["buildScenesExact"]=Json58.DeepEquals(before["buildScenes"],after["buildScenes"]);
   report["rtCountBefore"]=before["rtIds"].Count;report["rtCountAfter"]=after["rtIds"].Count;report["allOwnedClonesReleased"]=saved.Count==0&&materials.Count==0&&computes.Count==0&&buffers.Count==0;
   report["sceneEntityIdentityExpectedToChange"]=started;report["newCaptureOrReplayAfterThis"]=false;Save("finished");
  }catch(Exception e){report["restorationError"]=e.ToString();Save("restoration-incomplete");}
 }
 static Color[] Read(RenderTexture t,RectInt? box=null){var r=box??new RectInt(0,0,t.width,t.height);var data=new NativeArray<Color>(r.width*r.height,Allocator.Persistent,NativeArrayOptions.UninitializedMemory);AsyncGPUReadbackRequest request=default;bool sent=false;try{request=AsyncGPUReadback.RequestIntoNativeArray(ref data,t,0,r.x,r.width,r.y,r.height,0,1,TextureFormat.RGBAFloat);sent=true;request.WaitForCompletion();if(request.hasError)throw new InvalidOperationException("60 readback failed: "+t.name);return data.ToArray();}finally{if(sent&&!request.done)request.WaitForCompletion();data.Dispose();}}
 static Arr58 C(Color c){return new Arr58(new[]{c.r,c.g,c.b,c.a});}
 static void Raw(string n,Color[] a){using(var w=new BinaryWriter(File.Create(Path.Combine(Root,n))))foreach(var c in a){w.Write(c.r);w.Write(c.g);w.Write(c.b);w.Write(c.a);}}
 static void PNG(string n,Color[] a,int width,int height){var bytes=new byte[a.Length*4];for(int i=0;i<a.Length;i++){bytes[4*i]=(byte)Mathf.Clamp(Mathf.RoundToInt((float)SourcePalette58.Encode(Math.Max(0,a[i].r))*255),0,255);bytes[4*i+1]=(byte)Mathf.Clamp(Mathf.RoundToInt((float)SourcePalette58.Encode(Math.Max(0,a[i].g))*255),0,255);bytes[4*i+2]=(byte)Mathf.Clamp(Mathf.RoundToInt((float)SourcePalette58.Encode(Math.Max(0,a[i].b))*255),0,255);bytes[4*i+3]=(byte)Mathf.Clamp(Mathf.RoundToInt(a[i].a*255),0,255);}var t=new Texture2D(width,height,TextureFormat.RGBA32,false,false){hideFlags=HideFlags.HideAndDontSave};try{t.LoadRawTextureData(bytes);t.Apply(false,false);File.WriteAllBytes(Path.Combine(Root,n),t.EncodeToPNG());}finally{UnityEngine.Object.DestroyImmediate(t);}}
 ComputeBuffer Buffer(Array a,int stride){var b=new ComputeBuffer(a.Length,stride);buffers.Add(b);b.SetData(a);return b;}
 void Bind(Material m,int family,ComputeBuffer rgb,ComputeBuffer cuts,ComputeBuffer families){m.SetFloat("_SourceFamily60",family+1);m.SetBuffer("_SourcePalette54RGB8",rgb);m.SetBuffer("_SourcePalette54Thresholds",cuts);m.SetBuffer("_SourcePalette54Families",families);}
 Obj58 Pose(NativePlayer395 n){var m=n.host.main.motion;return new Obj58{["frameIndex"]=Time.frameCount,["sourceFrame"]=m.sourceFrame,["evaluatedFrame"]=m.evaluatedFrame,["phaseIndex"]=n.host.main.phaseIndex,["offset"]=new Arr58(new[]{n.host.offset.x,n.host.offset.y}),["origin"]=new Arr58(new[]{n.origin.x,n.origin.y}),["delta"]=new Arr58(new[]{n.deliveredDelta.x,n.deliveredDelta.y}),["cellScale"]=n.nativePixelsPerCell,["geometryHashes"]=new Arr58(m.surface.outputs.Select(o=>{using(var ms=new MemoryStream()){using(var w=new BinaryWriter(ms)){foreach(var v in o.sharedMesh.vertices){w.Write(v.x);w.Write(v.y);w.Write(v.z);}}return State58.Hash(ms.ToArray());}})),["headRegion502"]=HeadRegion502.Enabled,["hairBoundary491"]=HairBoundary491.Enabled};}
 void Capture(NativePlayer395 n){
  var f=n.host.main;var specs=Obj58.Parse(File.ReadAllText(Path.Combine(Path.GetDirectoryName(Root),"renderer-family59","SOURCE_REGISTRY59.json")));registry=specs;
  var ss=specs["bindings"].Select(s=>new RendererFamily59.Spec{rendererOrdinal=(int)s["rendererOrdinal"],subMesh=(int)s["subMesh"],bindingOrdinal=(int)s["bindingOrdinal"],triangleCount=(int)s["triangleCount"],materialId=(int)s["materialId"],sourceFamilyId=(string)s["sourceFamilyId"],meshUVSHA256=(string)s["meshUVSHA256"],indexSHA256=(string)s["indexSHA256"]}).ToArray();provider=new RendererFamily59(f.motion.surface.source,ss);
  if(provider.Draws.Length!=f.legacySignalsMats.Length)throw new InvalidOperationException("Runtime draw/material length mismatch");
  int count=Math.Max(2,f.surfaceShadeSteps);palettes=new SourcePalette58.Palette[ss.Length];var paletteRows=new Arr58();var rgbWords=new List<U4>();var familyWords=new List<U4>();var thresholds=new List<float>();
  for(int d=0;d<ss.Length;d++){
   var draw=provider.Draws[d];int role=Mathf.RoundToInt(f.legacySignalsMats[d].GetFloat("_Auto245Role"));if(roleDraw.ContainsKey(role))throw new InvalidOperationException("Ambiguous runtime material role");roleDraw[role]=d;
   bool scope=role>=11&&role<=14; // Existing renderer semantic scope; not a new model classifier.
   if(!scope){familyWords.Add(new U4(0,0,0,0));continue;}
   roleFamily[role]=(uint)d+1;var bind=specs["bindings"][d];var mesh=f.motion.surface.source[ss[d].rendererOrdinal].sharedMesh;var uv=mesh.uv;var ix=mesh.GetIndices(ss[d].subMesh);var samples=new List<SourcePalette58.Sample>();
   for(int j=0;j<32;j++){int tri=j*(ss[d].triangleCount-1)/31;Vector2 p=(uv[ix[tri*3]]+uv[ix[tri*3+1]]+uv[ix[tri*3+2]])/3;p=Vector2.Scale(p,draw.scale)+draw.offset;Color32 c;Vector2Int texel;string reason;if(!provider.TryReadSourcePoint(d,tri,p,out c,out texel,out reason))throw new InvalidOperationException("Reference source missing: "+reason);samples.Add(new SourcePalette58.Sample{id="d"+d.ToString("D2")+"-t"+tri.ToString("D6"),materialId=ss[d].materialId,primitiveId=(int)bind["gltfPrimitive"],triangle=tri,imageSHA256=(string)bind["imageSHA256"],uv=new[]{(double)p.x,1-(double)p.y},texel=new[]{texel.x,draw.texture.height-1-texel.y},rgba8=new[]{(int)c.r,c.g,c.b,c.a},weight=1});}
   var family=new SourcePalette58.Family{id=ss[d].sourceFamilyId,domainId=ss[d].sourceFamilyId,source=new SourcePalette58.Source{modelSHA256=(string)specs["modelSHA256"],imageSHA256=(string)bind["imageSHA256"],materialId=ss[d].materialId,factorLinear=new[]{(double)draw.factor.r,draw.factor.g,draw.factor.b,draw.factor.a}},samples=samples.ToArray()};
   var reference=SourcePalette58.ExtractReference(family);var settings=new SourcePalette58.Settings{count=count,darkLRatio=.55,darkCRatio=.6,gamma=1,intervalScale=1};var palette=SourcePalette58.MakePalette(reference,settings);palettes[d]=palette;
   int first=rgbWords.Count,cutStart=thresholds.Count;foreach(var colour in palette.rgb8)rgbWords.Add(new U4((uint)colour[0],(uint)colour[1],(uint)colour[2],255));for(int k=0;k<count-1;k++)thresholds.Add((k+.5f)/(count-1));familyWords.Add(new U4((uint)first,(uint)count,(uint)cutStart,(uint)count-1));paletteRows.Add(new Obj58{["draw"]=d,["legacyRole"]=role,["binding"]=bind,["family"]=SourceJson58.Family(family),["reference"]=SourceJson58.Reference(reference),["settings"]=SourceJson58.Settings(settings),["palette"]=SourceJson58.Palette(palette)});
  }
  report["palettes"]=paletteRows;report["scopeClassifier"]="Existing runtime role 11..14; source identity independently validated by full UV/index hashes";report["paletteSettingsAreDiagnostic"]=true;report["surfaceShadeSteps"]=count;report["selectionMapping"]=new Arr58(roleDraw.Select(p=>new Obj58{["role"]=p.Key,["draw"]=p.Value}));
  var rgb=Buffer(rgbWords.ToArray(),16);var cuts=Buffer(thresholds.ToArray(),4);var families=Buffer(familyWords.ToArray(),16);var roles=Buffer(roleFamily,4);
  // Equal, current-frame capture policy for both arms. No resetHistory/RenderPose.
  f.capturePending=true;if(n.host.head)n.host.head.capturePending=true;n.host.RenderFrame();report["controlPose"]=Pose(n);Save("control-rendered");
  var baseFull=Read(n.output.rt);var baseMeta=Read(f.preparedMeta.rt);var baseUV=Read(f.preparedUV.rt);var baseOwner=Read(f.owner.rt);var baseLocal=Read(f.colour.rt);var baseNativeOwner=Read(n.owner.rt);Raw("CONTROL_FULL60.float4",baseFull);Raw("CONTROL_META60.float4",baseMeta);Raw("CONTROL_UV60.float4",baseUV);Raw("CONTROL_OWNER60.float4",baseOwner);Raw("CONTROL_LOCAL60.float4",baseLocal);Raw("CONTROL_NATIVE_OWNER60.float4",baseNativeOwner);PNG("CONTROL_FULL60.png",baseFull,960,544);
  var shader=AssetDatabase.LoadAssetAtPath<Shader>(Probe+"LegacySignals60.shader");var independent=AssetDatabase.LoadAssetAtPath<Shader>(Probe+"Independent60.shader");var original=AssetDatabase.LoadAssetAtPath<ComputeShader>(Probe+"RestoreStyle60.compute");
  foreach(var v in new[]{f,n.host.head}.Where(v=>v)){
   var state=new Saved{f=v,legacy=v.legacySignalsMats,independent=v.independentMats,restore=v.restoreStyle};saved.Add(state);v.legacySignalsMats=(Material[])state.legacy.Clone();v.independentMats=(Material[])state.independent.Clone();
   for(int d=0;d<ss.Length;d++)if(palettes[d]!=null){var m=new Material(state.legacy[d]){shader=shader,hideFlags=HideFlags.HideAndDontSave};materials.Add(m);Bind(m,d,rgb,cuts,families);v.legacySignalsMats[d]=m;var q=new Material(state.independent[d]){shader=independent,hideFlags=HideFlags.HideAndDontSave};materials.Add(q);Bind(q,d,rgb,cuts,families);v.independentMats[d]=q;}
   var cs=UnityEngine.Object.Instantiate(original);cs.hideFlags=HideFlags.HideAndDontSave;computes.Add(cs);int kernel=cs.FindKernel("ApplyShadeBoundary");cs.SetBuffer(kernel,"_RoleFamily60",roles);cs.SetBuffer(kernel,"_SourcePalette54RGB8",rgb);cs.SetBuffer(kernel,"_SourcePalette54Families",families);v.restoreStyle=cs;
  }
  f.capturePending=true;if(n.host.head)n.host.head.capturePending=true;n.host.RenderFrame();report["candidatePose"]=Pose(n);report["poseAndGeometryExact"]=Json58.DeepEquals(report["controlPose"],report["candidatePose"]);Save("candidate-rendered");
  var candidateFull=Read(n.output.rt);var candidateMeta=Read(f.preparedMeta.rt);var candidateUV=Read(f.preparedUV.rt);var candidateOwner=Read(f.owner.rt);var candidateLocal=Read(f.colour.rt);var candidateNativeOwner=Read(n.owner.rt);Raw("CANDIDATE_FULL60.float4",candidateFull);Raw("CANDIDATE_META60.float4",candidateMeta);Raw("CANDIDATE_UV60.float4",candidateUV);Raw("CANDIDATE_OWNER60.float4",candidateOwner);Raw("CANDIDATE_LOCAL60.float4",candidateLocal);Raw("CANDIDATE_NATIVE_OWNER60.float4",candidateNativeOwner);PNG("CANDIDATE_FULL60.png",candidateFull,960,544);
  int x0=480,y0=272,x1=0,y1=0;for(int i=0;i<candidateMeta.Length;i++){int role=Mathf.RoundToInt(candidateMeta[i].g)-1;if(candidateMeta[i].r>0&&role>=0&&role<16&&roleFamily[role]>0){int x=i%480,y=i/480;x0=Math.Min(x0,x);y0=Math.Min(y0,y);x1=Math.Max(x1,x+1);y1=Math.Max(y1,y+1);}}
  if(x0>=x1||y0>=y1)throw new InvalidOperationException("No candidate visible hair provenance");
  var roi=new RectInt(x0,y0,x1-x0,y1-y0);report["hairRectBottomLeft"]=new Arr58(new[]{roi.x,roi.y,roi.width,roi.height});var srcView=n.host.head?n.host.head:f;Vector2Int offset=n.host.head?n.host.offset:Vector2Int.zero;var sr=new RectInt(roi.x-offset.x,roi.y-offset.y,roi.width,roi.height);if(sr.x<0||sr.y<0||sr.xMax>480||sr.yMax>272)throw new InvalidOperationException("Head/source ROI mismatch");
  var sourceClass=Read(srcView.style480[3].rt,sr);var sourceMeta=Read(srcView.motion.raw[5].rt,sr);var sourceUV=Read(srcView.motion.raw[6].rt,sr);var sourceInitial=Read(srcView.style480[0].rt,sr);var sourceMask=Read(srcView.shadeMask480.rt,sr);var map=srcView.actionMap.GetPixels();
  Raw("SELECTED_SOURCE_CLASS60.float4",sourceClass);Raw("SELECTED_SOURCE_META60.float4",sourceMeta);Raw("SELECTED_SOURCE_UV60.float4",sourceUV);Raw("SELECTED_SOURCE_INITIAL60.float4",sourceInitial);Raw("SELECTED_SOURCE_MASK60.float4",sourceMask);
  var cells=new Arr58();int unknown=0,known=0;
  for(int yy=0;yy<roi.height;yy++)for(int xx=0;xx<roi.width;xx++){int i=(roi.y+yy)*480+roi.x+xx,j=yy*roi.width+xx;var meta=candidateMeta[i];int role=Mathf.RoundToInt(meta.g)-1;if(meta.r<=0||role<0||role>=16||roleFamily[role]==0)continue;int draw=roleDraw[role],tri=Mathf.RoundToInt(meta.a)-1;Color32 colour;Vector2Int texel;string reason;bool bound=provider.TryReadSourcePoint(draw,tri,new Vector2(candidateUV[i].r,candidateUV[i].g),out colour,out texel,out reason);if(bound)known++;else unknown++;bool centre=Math.Abs(meta.g-sourceMeta[j].g)<.01&&Math.Abs(meta.a-sourceMeta[j].a)<.01&&Math.Abs(candidateUV[i].r-sourceUV[j].r)<1e-5&&Math.Abs(candidateUV[i].g-sourceUV[j].g)<1e-5;var row=new Obj58{["x"]=roi.x+xx,["yBottom"]=roi.y+yy,["draw"]=draw,["materialId"]=ss[draw].materialId,["triangle"]=tri,["uv"]=new Arr58(new[]{candidateUV[i].r,candidateUV[i].g}),["sourceKnown"]=bound,["sourceFailure"]=reason,["sourceRGBA8"]=bound?new Arr58(new[]{(int)colour.r,colour.g,colour.b,colour.a}):null,["texelUnityBottom"]=bound?new Arr58(new[]{texel.x,texel.y}):null,["owner"]=C(candidateOwner[i]),["selectedMeta"]=C(meta),["centreSourceExact"]=centre,["g"]=centre?(Json58)sourceClass[j].g:null,["q"]=candidateUV[i].b,["centreClass"]=C(sourceClass[j]),["centreInitial"]=C(sourceInitial[j]),["centreMask"]=C(sourceMask[j]),["controlRGBLinear"]=C(baseLocal[i]),["candidateRGBLinear"]=C(candidateLocal[i])};cells.Add(row);}
  report["knownVisibleHairSourceCells"]=known;report["unknownVisibleHairSourceCells"]=unknown;report["cells"]=cells;report["capturePolicy"]="Both arms capturePending=true once, no resetHistory, no RenderPose; static-frame comparison only";report["cleanBackingReason"]="Not collected: this hair-only candidate does not supply a proven source-aligned clean eye backing pass";Save("comparison-captured");
 }
}
