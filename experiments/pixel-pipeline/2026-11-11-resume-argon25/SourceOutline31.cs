// REVIEW CANDIDATE ONLY: not imported, loaded, or executed by the CPU tests.
using System;using System.IO;using System.Linq;using System.Collections.Generic;
using UnityEditor;using UnityEngine;using UnityEngine.Rendering;using UnityEngine.Rendering.Universal;using UnityEngine.Rendering.RenderGraphModule;
namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {
public sealed class SourceOutline31:ScriptableRenderPass,IDisposable {
 readonly EyeFeature348 eye;readonly Camera camera;readonly string packet,viewKey,model,topology,cameraIdentity;
 readonly Material[][] originals,depthMats;readonly Material[] qOriginals,qMats;readonly Material ink,pigment;readonly ComputeShader classify;
 readonly List<RTHandle> owned=new List<RTHandle>();readonly MaterialVersion31[] versions;
 readonly int renderer,submesh,pigmentSubmesh,kernel;readonly float width;readonly Vector4 sourceInk;
 readonly object failureSync=new object();Exception failure;
 Submission31 submission;bool stopped,recorded,releaseAttempted;
 UnityEngine.Mesh[] meshes;Matrix4x4[] matrices;Matrix4x4 vp,qvp,view;int frame,generation=1;
 public readonly RTHandle[] Fields=new RTHandle[8],QFields=new RTHandle[5];
 public RTHandle Classification{get;private set;}RTHandle depth,qDepth;
 public RectInt ROI{get;private set;}public RectInt QROI{get;private set;}
 public Camera Camera=>camera;public bool Disposed{get;private set;}
 public string ViewIdentity=>cameraIdentity;
 public bool CanRelease=>submission==null||submission.CanRelease;
 public bool CanUsePixels=>!Disposed&&!stopped&&submission!=null&&submission.CanUsePixels&&Failure==null;
 public int CapturedFrame=>frame;public string FrameKey{get;private set;}
 public Matrix4x4 PhysicalGPUVP=>vp;public Matrix4x4 QGPUVP=>qvp;public Vector2 QFullRasterOrigin{get;private set;}
 public Exception Failure{get{Exception e;lock(failureSync){e=failure;}return e??(submission!=null&&submission.HasError?new InvalidOperationException("31 invalid completion receipt; output blocked"):null);}}
 public string QStage=>"initial quantized source light; before spatial Q correction";
 sealed class Data{public SourceOutline31 owner;public int stage;}
 sealed class MaterialVersion31 {
  readonly Material material;readonly int crc;readonly Texture[] textures;readonly uint[] updates;readonly Hash128[] imageHashes;
  public MaterialVersion31(Material m){material=m;crc=m.ComputeCRC();textures=m.GetTexturePropertyNames().Select(m.GetTexture).ToArray();updates=textures.Select(t=>t?t.updateCount:0).ToArray();imageHashes=textures.Select(t=>t?t.imageContentsHash:default).ToArray();}
  public void Require(){if(!material||material.ComputeCRC()!=crc)throw new InvalidOperationException("31 source material generation changed");var now=material.GetTexturePropertyNames().Select(material.GetTexture).ToArray();if(!now.SequenceEqual(textures))throw new InvalidOperationException("31 source texture identity changed");for(int i=0;i<textures.Length;i++)if(textures[i]&&(textures[i].updateCount!=updates[i]||textures[i].imageContentsHash!=imageHashes[i]))throw new InvalidOperationException("31 source texture contents changed");}
 }
 public SourceOutline31(EyeFeature348 e,string bindingPath,string registryPath,string sourcePacket){
  if(String.IsNullOrEmpty(sourcePacket))throw new ArgumentException("source packet");
  eye=e;camera=e.full.motion.camera;packet=sourcePacket;cameraIdentity=camera.GetEntityId().ToString();viewKey=cameraIdentity+"/"+e.GetEntityId()+"/"+Guid.NewGuid().ToString("N");topology=e.modelTopologySHA256;
  renderPassEvent=RenderPassEvent.AfterRenderingTransparents;
  // These are execution-time capability gates. This constructor is never run by CPU compilation.
  if(!SystemInfo.supportsAsyncGPUReadback||SystemInfo.supportedRenderTargetCount<5)throw new NotSupportedException("31 requires asynchronous readback and five MRTs; no fallback");
  var b=Json58.Parse(File.ReadAllText(bindingPath));var registry=Json58.Parse(File.ReadAllText(registryPath));model=(string)registry["modelSHA256"];
  if(model!=(string)b["modelSHA256"])throw new InvalidOperationException("31 model binding mismatch");
  renderer=(int)b["nativeBinding"]["rendererOrdinal"];submesh=(int)b["nativeBinding"]["subMesh"];
  var p=registry["bindings"].Where(v=>(int)v["rendererOrdinal"]==renderer&&(int)v["gltfPrimitive"]==6).ToArray();if(p.Length!=1)throw new InvalidOperationException("31 registered native pigment domain missing");pigmentSubmesh=(int)p[0]["subMesh"];
  var o=b["finiteOutlineColourInput"];if((string)o["widthMode"]!="worldCoordinates"||(double)o["lightingMix"]!=0)throw new InvalidOperationException("31 unsupported source outline mode");
  width=(float)(double)o["widthMetres"];var rgb=o["linearRGB"].Values<float>().ToArray();sourceInk=new Vector4(rgb[0],rgb[1],rgb[2],1);
  originals=e.full.motion.surface.source.Select(v=>v.sharedMaterials).ToArray();qOriginals=e.full.legacySignalsMats.ToArray();
  if(originals.Sum(v=>v.Length)!=qOriginals.Length)throw new InvalidOperationException("31 source/Q material graph mismatch");
  versions=originals.SelectMany(v=>v).Concat(qOriginals).Select(v=>new MaterialVersion31(v)).ToArray();depthMats=new Material[originals.Length][];qMats=new Material[qOriginals.Length];
  try{
   var shader=AssetDatabase.LoadAssetAtPath<Shader>("Assets/EUnityValidation01/SourceBoundary31/SourceOutline31.shader");var qShader=AssetDatabase.LoadAssetAtPath<Shader>("Assets/EUnityValidation01/SourceBoundary31/QMeta31.shader");var cs=AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/SourceBoundary31/LineClass31.compute");
   if(!shader||!qShader||!cs||!shader.isSupported||!qShader.isSupported)throw new InvalidOperationException("31 review shaders are intentionally unapplied; no runtime fallback");
   classify=UnityEngine.Object.Instantiate(cs);kernel=classify.FindKernel("Classify31");classify.GetKernelThreadGroupSizes(kernel,out uint tx,out uint ty,out uint tz);if(tx!=8||ty!=8||tz!=1)throw new InvalidOperationException("31 classifier ABI must be8x8x1");
   for(int r=0;r<originals.Length;r++){depthMats[r]=new Material[originals[r].Length];for(int sm=0;sm<originals[r].Length;sm++)depthMats[r][sm]=Clone(originals[r][sm],shader);}
   for(int i=0;i<qMats.Length;i++)qMats[i]=Clone(qOriginals[i],qShader);
   ink=Clone(originals[renderer][submesh],shader);ink.SetFloat("_OutlineWidth",width);ink.SetVector("_SourceOutline29",sourceInk);pigment=Clone(originals[renderer][pigmentSubmesh],shader);
   if(pigment.FindPass("SourcePigment29")!=2)throw new InvalidOperationException("31 physical pigment ABI missing");
  }catch{TryReleaseOwned();throw;}
 }
 static Material Clone(Material m,Shader shader)=>new Material(m){shader=shader,hideFlags=HideFlags.DontSave,name="31 owned diagnostic material"};
 void Fail(Exception error){lock(failureSync){if(failure==null)failure=error;}submission?.Fail();}
 RTHandle Target(int w,int h,bool z=false,bool uav=false){var t=z?RTHandles.Alloc(w,h,depthBufferBits:DepthBits.Depth32,name:"31 owned depth"):RTHandles.Alloc(w,h,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:uav,filterMode:FilterMode.Point,name:"31 owned source field");owned.Add(t);return t;}
 void Prepare(){
  var f=eye.full;if(f.motion.camera!=camera||eye.modelTopologySHA256!=topology)throw new InvalidOperationException("31 view/model invalidated");
  foreach(var v in versions)v.Require();
  for(int r=0;r<originals.Length;r++)if(!f.motion.surface.source[r].sharedMaterials.SequenceEqual(originals[r]))throw new InvalidOperationException("31 source material identity changed");
  if(!f.legacySignalsMats.SequenceEqual(qOriginals))throw new InvalidOperationException("31 Q material identity changed");
  meshes=f.motion.surface.outputs.Select(v=>v.sharedMesh).ToArray();matrices=f.motion.surface.outputs.Select(v=>v.transform.localToWorldMatrix).ToArray();
  if(meshes.Length!=originals.Length)throw new InvalidOperationException("31 renderer graph changed");for(int r=0;r<meshes.Length;r++)if(!meshes[r]||meshes[r].subMeshCount!=originals[r].Length)throw new InvalidOperationException("31 submesh graph changed");
  var mesh=meshes[renderer];var vertices=mesh.vertices;var normals=mesh.normals;var transform=matrices[renderer];var normalMatrix=transform.inverse.transpose;
  if(normals.Length!=vertices.Length)throw new InvalidOperationException("31 native normals missing");float x0=float.PositiveInfinity,y0=x0,x1=float.NegativeInfinity,y1=x1;
  foreach(int ix in mesh.GetIndices(submesh).Concat(mesh.GetIndices(pigmentSubmesh)).Distinct()){
   if(ix<0||ix>=vertices.Length)throw new InvalidOperationException("31 source index bounds");var p=transform.MultiplyPoint3x4(vertices[ix]);var n=normalMatrix.MultiplyVector(normals[ix]).normalized;
   foreach(var w in new[]{p,p+n*width}){var q=f.Project(w);if(!float.IsFinite(q.x)||!float.IsFinite(q.y))throw new InvalidOperationException("31 projection invalid");x0=Math.Min(x0,q.x);y0=Math.Min(y0,q.y);x1=Math.Max(x1,q.x);y1=Math.Max(y1,q.y);}}
  int left=Math.Max(0,(int)Math.Floor(x0)-1),top=Math.Max(0,(int)Math.Floor(y0)-1),right=Math.Min(480,(int)Math.Ceiling(x1)+1),bottom=Math.Min(272,(int)Math.Ceiling(y1)+1);
  ROI=new RectInt(left,top,right-left,bottom-top);if(ROI.width<=0||ROI.height<=0||(long)ROI.width*ROI.height>4096)throw new InvalidOperationException("31 logical ROI budget");
  int qx=Math.Max(0,left-1),qy=Math.Max(0,top-1),qr=Math.Min(480,right+1),qb=Math.Min(272,bottom+1);QROI=new RectInt(qx,qy,qr-qx,qb-qy);
  for(int i=0;i<Fields.Length;i++)Fields[i]=Target(ROI.width*8,ROI.height*8);depth=Target(ROI.width*8,ROI.height*8,true);Classification=Target(ROI.width,ROI.height,uav:true);
  for(int i=0;i<QFields.Length;i++)QFields[i]=Target(QROI.width,QROI.height);qDepth=Target(QROI.width,QROI.height,true);
  view=camera.worldToCameraMatrix;vp=GL.GetGPUProjectionMatrix(Projection31.Crop(ROI,f.effectiveProjection),true)*view;qvp=GL.GetGPUProjectionMatrix(Projection31.Crop(QROI,f.effectiveProjection),true)*view;
  frame=Time.frameCount;FrameKey=packet+"/"+viewKey+"/frame"+frame+"/generation"+generation;
  float[] M(Matrix4x4 m)=>Enumerable.Range(0,16).Select(i=>m[i]).ToArray();
  GridBinding30 Descriptor(RTHandle t)=>new GridBinding30(FrameKey,viewKey,model,GridSpace30.PhysicalHead,frame,generation,ROI.x,ROI.y,ROI.width,ROI.height,8,t.rt.width,t.rt.height,M(vp));
  GridBinding30.RequirePair(Descriptor(Fields[0]),Descriptor(Fields[0]),Descriptor(Fields[2]));
  QMetaLattice31.Require(new[]{ROI.x,ROI.y,ROI.width,ROI.height},new[]{QROI.x,QROI.y,QROI.width,QROI.height},QFields[3].rt.width,QFields[3].rt.height,QFields[4].rt.width,QFields[4].rt.height);
 }
 public override void RecordRenderGraph(RenderGraph graph,ContextContainer context){
  if(stopped||Disposed||recorded)return;
  try{
   if(context.Get<UniversalCameraData>().camera!=camera)return;Prepare();submission=new Submission31(FrameKey,generation);recorded=true;
   // Conservatively retain resources even if graph recording aborts before execution.
   submission.BeforeCommands();
   foreach(int stage in new[]{1,2,4}){using var b=graph.AddUnsafePass<Data>("31 source producer "+stage,out var d);d.owner=this;d.stage=stage;
    if(stage==4){foreach(var t in QFields)b.UseTexture(graph.ImportTexture(t),AccessFlags.Write);b.UseTexture(graph.ImportTexture(qDepth),AccessFlags.Write);b.UseAllGlobalTextures(true);var res=context.Get<UniversalResourceData>();if(res.mainShadowsTexture.IsValid())b.UseTexture(res.mainShadowsTexture);if(res.additionalShadowsTexture.IsValid())b.UseTexture(res.additionalShadowsTexture);}
    else{int start=stage==1?0:4;for(int i=start;i<start+4;i++)b.UseTexture(graph.ImportTexture(Fields[i]),AccessFlags.Write);b.UseTexture(graph.ImportTexture(depth),AccessFlags.Write);}
    b.AllowPassCulling(false);b.SetRenderFunc(static(Data p,UnsafeGraphContext c)=>p.owner.Produce(c,p.stage));
   }
   using(var b=graph.AddUnsafePass<Data>("31 classify source evidence",out var d)){d.owner=this;foreach(var t in Fields.Concat(QFields))b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);b.UseTexture(graph.ImportTexture(Classification),AccessFlags.Write);b.AllowPassCulling(false);b.SetRenderFunc(static(Data p,UnsafeGraphContext c)=>p.owner.Classify(c));}
   using(var b=graph.AddUnsafePass<Data>("31 end barrier includes hair ON/OFF and Q/meta",out var d)){d.owner=this;foreach(var t in Fields.Concat(QFields).Concat(new[]{Classification,depth,qDepth}))b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);b.AllowPassCulling(false);b.SetRenderFunc(static(Data p,UnsafeGraphContext c)=>p.owner.EndBarrier(c));}
  }catch(Exception e){stopped=true;Fail(e);}
 }
 void Produce(UnsafeGraphContext context,int stage){
  if(stopped||Failure!=null){submission.Fail();return;}try{if(Time.frameCount!=frame)throw new InvalidOperationException("31 stale graph frame");if(stage==4)DrawQ(context);else DrawSource(context,stage==1);submission.StageRecorded(stage);}catch(Exception e){Fail(e);}
 }
 MaterialPropertyBlock SourceProperties(){var p=new MaterialPropertyBlock();p.SetMatrix("_ProbeGPUVP29",vp);p.SetMatrix("_ProbeView29",view);return p;}
 void DrawSource(UnsafeGraphContext context,bool hair){var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);int start=hair?0:4;var props=SourceProperties();
  cmd.SetRenderTarget(new[]{new RenderTargetIdentifier(Fields[start].rt),new RenderTargetIdentifier(Fields[start+1].rt)},depth.rt);cmd.SetViewport(new Rect(0,0,ROI.width*8,ROI.height*8));cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1,0);
  for(int r=0;r<meshes.Length;r++){if(!hair&&r==2)continue;for(int sm=0;sm<depthMats[r].Length;sm++)cmd.DrawMesh(meshes[r],matrices[r],depthMats[r][sm],sm,0,props);}
  cmd.SetRenderTarget(new[]{new RenderTargetIdentifier(Fields[start+2].rt),new RenderTargetIdentifier(Fields[start+3].rt)},depth.rt);cmd.ClearRenderTarget(RTClearFlags.Color,Color.clear,1,0);cmd.DrawMesh(meshes[renderer],matrices[renderer],pigment,pigmentSubmesh,2,props);
  cmd.SetRenderTarget(new[]{new RenderTargetIdentifier(Fields[start].rt),new RenderTargetIdentifier(Fields[start+1].rt)},depth.rt);cmd.DrawMesh(meshes[renderer],matrices[renderer],ink,submesh,1,props);
 }
 void DrawQ(UnsafeGraphContext context){var f=eye.full;var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);var p=new MaterialPropertyBlock();
  var origin=QMetaLattice31.RasterOrigin(new[]{QROI.x,QROI.y,QROI.width,QROI.height},SystemInfo.graphicsUVStartsAtTop);QFullRasterOrigin=new Vector2(origin[0],origin[1]);p.SetVector("_QMetaRasterOrigin31",new Vector4(origin[0],origin[1],0,0));
  p.SetMatrix("_QMetaVP31",qvp);p.SetVector("_SurfaceInvRaster335",new Vector4(1f/480,1f/272,0,0));p.SetFloat("_SurfaceLayers335",f.layeredSurface&&f.styleEnabled?1:0);p.SetFloat("_ShadeLayer335",f.shadeLayer?1:0);p.SetFloat("_SurfaceOwnShade335",f.motion.animation.shadeProfile.x);p.SetFloat("_FaceShadeSteps335",f.faceShadeSteps);p.SetFloat("_SurfaceShadeSteps335",f.surfaceShadeSteps);p.SetInt("_SurfaceLayerView335",f.surfaceLayerView);p.SetFloat("_FaceShadeTint335",f.faceShadeTint?1:0);p.SetVector("_FaceShadeChromaticity335",f.faceShadeChromaticity);p.SetFloat("_SurfaceMaskReady335",0);
  p.SetFloat("_Auto245Stage",2);p.SetFloat("_Auto245Local",0);p.SetFloat("_Auto245MembershipEnabled",1);p.SetFloat("_Auto249VisibilityOne",0);p.SetFloat("_Auto249Probe",0);p.SetFloat("_Style297Enabled",1);p.SetFloat("_Style297SkinMode",1);p.SetFloat("_Style297OwnShade",.72f);p.SetVector("_Auto245StockLit",f.stockLit);p.SetVector("_Auto245StockShade",f.stockShade);p.SetVector("_Auto245CreamShade",f.creamShade);p.SetVector("_Auto245SkinShade",f.skinShade);
  cmd.SetRenderTarget(QFields.Select(t=>new RenderTargetIdentifier(t.rt)).ToArray(),qDepth.rt);cmd.SetViewport(new Rect(0,0,QROI.width,QROI.height));cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1,0);int k=0;
  for(int r=0;r<meshes.Length;r++)for(int sm=0;sm<depthMats[r].Length;sm++)cmd.DrawMesh(meshes[r],matrices[r],qMats[k++],sm,0,p);
 }
 void Classify(UnsafeGraphContext context){if(stopped||Failure!=null){submission.Fail();return;}try{var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);
  cmd.SetComputeTextureParam(classify,kernel,"_Outline29",Fields[0].rt);cmd.SetComputeTextureParam(classify,kernel,"_Pigment29",Fields[2].rt);cmd.SetComputeTextureParam(classify,kernel,"_Q31",QFields[3].rt);cmd.SetComputeTextureParam(classify,kernel,"_QMeta31",QFields[4].rt);cmd.SetComputeTextureParam(classify,kernel,"_Class29",Classification.rt);
  cmd.SetComputeIntParams(classify,"_Rect29",ROI.x,ROI.y,ROI.width,ROI.height);cmd.SetComputeIntParams(classify,"_QRect31",QROI.x,QROI.y,QROI.width,QROI.height);cmd.DispatchCompute(classify,kernel,(ROI.width+7)/8,(ROI.height+7)/8,1);submission.StageRecorded(8);
 }catch(Exception e){Fail(e);}}
 void EndBarrier(UnsafeGraphContext context){
  // Deliberately runs even when a producer failed or exit has been requested.
  try{var ticket=submission;string key=FrameKey;int gen=generation;ticket.BeforeBarrier();var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);
   cmd.RequestAsyncReadback(Classification.rt,0,0,1,0,1,0,1,r=>{try{bool done=r.done,error=r.hasError;if(done&&!error&&r.layerDataSize!=16)error=true;ticket.AcceptCallback(key,gen,done,error);if(!done||error)Fail(new InvalidOperationException("31 end readback incomplete/error or unexpected byte count; resources retained"));}catch(Exception e){Fail(e);}});
  }catch(Exception e){Fail(e);}
 }
 public void StopRecording(){stopped=true;submission?.Stop();}
 public void ReportFailure(Exception error){stopped=true;Fail(error);}
 public void RequireCompleted(){if(Failure!=null)throw new InvalidOperationException("31 source producer failed",Failure);if(!CanUsePixels)throw new InvalidOperationException("31 pending/invalid GPU completion; no output marker");}
 public bool TryReleaseOwned(){
  StopRecording();if(Disposed)return true;if(!CanRelease||releaseAttempted)return false;releaseAttempted=true;
  try{foreach(var t in owned)t?.Release();owned.Clear();if(depthMats!=null)foreach(var row in depthMats)if(row!=null)foreach(var m in row)if(m)UnityEngine.Object.DestroyImmediate(m);if(qMats!=null)foreach(var m in qMats)if(m)UnityEngine.Object.DestroyImmediate(m);if(ink)UnityEngine.Object.DestroyImmediate(ink);if(pigment)UnityEngine.Object.DestroyImmediate(pigment);if(classify)UnityEngine.Object.DestroyImmediate(classify);Disposed=true;return true;}catch(Exception e){Fail(e);return false;}
 }
 public void Dispose(){TryReleaseOwned();} // Pending means retained, never forced.
}
}
