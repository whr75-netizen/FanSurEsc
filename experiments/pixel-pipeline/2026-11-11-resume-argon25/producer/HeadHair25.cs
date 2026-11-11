using System;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.Rendering.RenderGraphModule;

// One owner per Forward113/view. Borrow current evaluated mesh; own only clones/RTs.
// No globals, camera/scene mutation, previous-frame colours or GPU->CPU feedback.
public sealed class HeadHair25 : IDisposable {
 public const string ShaderAsset="Assets/EUnityValidation01/HeadHair25/HeadHair25.shader";
 readonly EyeFeature348 eye;readonly UnityEngine.Mesh mesh;readonly string topology;
 readonly Material[] materials=new Material[4];
 public RTHandle[] Fields{get;private set;}RTHandle depth;
 public Vector2 Origin{get;private set;}public int Width{get;private set;}public int Height{get;private set;}
 public Matrix4x4 GPUVP{get;private set;}
 public int RecordedFrame{get;private set;}=-1;public int RenderedFrame{get;private set;}=-1;
 public bool Disposed{get;private set;}public long OwnedBytes=>(long)Width*Height*(5*16+4);
 public HeadHair25(EyeFeature348 e){
  eye=e;if(!eye||!eye.full||EditorUtility.IsPersistent(eye))throw new InvalidOperationException("Live isolated eye view required");
  mesh=eye.full.motion.surface.outputs[2].sharedMesh;topology=eye.modelTopologySHA256;
  var shader=AssetDatabase.LoadAssetAtPath<Shader>(ShaderAsset);
  if(!mesh||mesh.subMeshCount!=4||!shader||!shader.isSupported)throw new InvalidOperationException("Head hair source/shader unavailable");
  try{for(int i=0;i<4;i++){
   var src=eye.materials[11+i];if(!src)throw new InvalidOperationException("Original S4 material unavailable");
   materials[i]=new Material(src){shader=shader,hideFlags=HideFlags.DontSave,name="25 owned head-grid hair "+i};materials[i].shaderKeywords=src.shaderKeywords;
  }}catch{Dispose();throw;}
 }
 void Targets(int width,int height){
  if(Fields!=null&&Width==width&&Height==height)return;
  if(width<4||height<4||(width%4)!=0||(height%4)!=0||(long)width*height>32768)throw new InvalidOperationException("25 head-grid raster budget");
  ReleaseTargets();Width=width;Height=height;
  try{Fields=new RTHandle[5];for(int i=0;i<5;i++)Fields[i]=RTHandles.Alloc(width,height,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,filterMode:FilterMode.Point,name:"25 head hair channel "+i);
   depth=RTHandles.Alloc(width,height,depthBufferBits:DepthBits.Depth32,name:"25 head hair depth");
  }catch{ReleaseTargets();throw;}
 }
 sealed class Data {public HeadHair25 owner;public Matrix4x4 model;}
 public void Record(RenderGraph graph,UniversalResourceData resources,Vector2 origin,int width,int height){
  if(Disposed||!eye||!eye.full||eye.modelTopologySHA256!=topology||eye.full.motion.surface.outputs[2].sharedMesh!=mesh)throw new InvalidOperationException("25 model/view generation changed; dispose and recreate");
  if(HeadRegion502.Ready)throw new InvalidOperationException("25 currently requires original S4 hair producer; corrected HeadRegion path is separate");
  if(RecordedFrame==Time.frameCount)throw new InvalidOperationException("25 duplicate view record in one frame");
  if(!float.IsFinite(origin.x)||!float.IsFinite(origin.y))throw new InvalidOperationException("25 finite source origin required");
  Targets(width,height);Origin=origin;var full=eye.full;var cam=full.motion.camera;
  float w=width/4f,h=height/4f;
  // Full319View335.Project has +Y DOWN. Match its existing crop convention;
  // after GPU RT flip, raw texture row0 maps to the ROI's maximum Project Y.
  var crop=Matrix4x4.identity;crop.m00=480f/w;crop.m03=(480f-2*origin.x-w)/w;crop.m11=272f/h;crop.m13=(2*origin.y+h-272f)/h;
  var vp=GL.GetGPUProjectionMatrix(crop*full.effectiveProjection,true)*cam.worldToCameraMatrix;GPUVP=vp;
  foreach(var mat in materials){
   mat.SetMatrix("_HeadHairGPUVP25",vp);mat.SetVector("_ROI348",new Vector4(origin.x,272-origin.y-h,w,h));
   mat.SetMatrix("_WorldToHead348",eye.headMatrix.inverse);mat.SetInt("_SupportKind348",4);
   mat.SetVector("_ClipShift333",Vector4.zero);mat.SetVector("_Profile333",full.motion.animation.shadeProfile);
   mat.SetVector("_SurfaceInvRaster335",new Vector4(1f/480,1f/272,0,0));mat.SetFloat("_SurfaceOwnShade335",full.motion.animation.shadeProfile.x);
   mat.SetFloat("_ShadeLayer335",full.shadeLayer?1:0);mat.SetFloat("_SurfaceShadeSteps335",full.surfaceShadeSteps);
  }
  using(var b=graph.AddRasterRenderPass<Data>("25 original S4 hair on continuous head grid",out var d)){
   d.owner=this;d.model=full.motion.surface.outputs[2].transform.localToWorldMatrix;
   for(int i=0;i<5;i++)b.SetRenderAttachment(graph.ImportTexture(Fields[i]),i,AccessFlags.Write);
   b.SetRenderAttachmentDepth(graph.ImportTexture(depth),AccessFlags.Write);b.UseAllGlobalTextures(true);
   if(resources.mainShadowsTexture.IsValid())b.UseTexture(resources.mainShadowsTexture);
   if(resources.additionalShadowsTexture.IsValid())b.UseTexture(resources.additionalShadowsTexture);
   b.AllowPassCulling(false);b.SetRenderFunc(static(Data data,RasterGraphContext context)=>data.owner.Draw(data,context));
  }
  RecordedFrame=Time.frameCount;
 }
 void Draw(Data data,RasterGraphContext context){
  if(Disposed||RecordedFrame!=Time.frameCount)throw new InvalidOperationException("25 stale head hair pass");
  context.cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1,0);
  for(int i=0;i<4;i++)context.cmd.DrawMesh(mesh,data.model,materials[i],i,0);
  RenderedFrame=Time.frameCount;
 }
 public void Bind(CommandBuffer cmd,ComputeShader shader,int kernel,Vector2 expectedOrigin){
  if(Disposed||RenderedFrame!=Time.frameCount||Origin!=expectedOrigin)throw new InvalidOperationException("25 current hair/eye footprint mismatch");
  cmd.SetComputeTextureParam(shader,kernel,"_HeadHairRGBA25",Fields[0].rt);cmd.SetComputeTextureParam(shader,kernel,"_HeadHairMeta25",Fields[1].rt);
  cmd.SetComputeIntParams(shader,"_HeadHairSize25",Width,Height);
 }
 public void AssertRendered(){if(Disposed||RenderedFrame!=Time.frameCount)throw new InvalidOperationException("25 head hair not rendered in current frame");}
 void ReleaseTargets(){if(Fields!=null)foreach(var f in Fields)f?.Release();depth?.Release();Fields=null;depth=null;Width=Height=0;}
 public void Dispose(){if(Disposed)return;Disposed=true;ReleaseTargets();foreach(var m in materials)if(m)UnityEngine.Object.DestroyImmediate(m);}
}
