using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.Rendering.RenderGraphModule;

// One actual graph frame, shared intrinsic8x input, separate113/115 outputs.
// Product77 output, borrowed meshes/materials and global buffers are untouched.
public sealed class Forward115:IDisposable{
 public readonly RegionDriver115 Region;public readonly RegionDriver113 Baseline113;
 readonly EyeFeature348 eye;readonly LayerZero101 canvas;readonly NativeRetarget96 native;
 public readonly NativeDense107 DenseNative;public readonly LiveSurface107 DenseSource,Source,CarrierSource,BaselineCarrierSource;
 public readonly NativeCarrier115 CarrierNative;public readonly NativeCarrier113 BaselineCarrierNative;
 public readonly SourcePigment113 Curves;
 public RTHandle[] Fields{get;private set;}public RTHandle[] BaselineFields{get;private set;}public RTHandle[] LegacyFields{get;private set;}
 public GraphicsBuffer[] Results{get;private set;}public GraphicsBuffer[] LegacyResults{get;private set;}
 public bool Disposed{get;private set;}public int RenderedFrame{get;private set;}=-1;
 public Obj58 Info=>new Obj58{["nativeRegistration"]=native.Info,["scope"]=Source.Scope,["frames"]=Source.Engine.Frames,["canonicalSize"]=new Arr58(Source.Engine.Width,Source.Engine.Height),["curves106"]=Curves.Info,["denseSampler"]=8,["denseSize"]=new Arr58(DenseNative.currentWidth,DenseNative.currentHeight),["carrier115"]=CarrierNative.Info,["baselineCarrier113"]=BaselineCarrierNative.Info,["region113"]=Region.Info,["sourceForm111FullPareto"]=true,["sourceFormUsesOutwardIntervals"]=true,["baseline113SameInput"]=true,["runtimeGPUReadbacks"]=0,["priorColourInputs"]=0,["historyImplemented"]=false,["product77DefaultChanged"]=false};
 sealed class Data{public Forward115 o;public Matrix4x4 view,projection;}
 public Forward115(EyeFeature348 e,LayerZero101 layer,string regPath,string diag){
  eye=e;canvas=layer;if(canvas.AfterCanvas!=null)throw new InvalidOperationException("115 graph callback already owned");var reg=Json58.Parse(File.ReadAllText(regPath));var ids=reg["eyes"].Select(x=>(int)x["eye"]).OrderBy(x=>x).ToArray();var px=new Vector4[2];var py=new Vector4[2];for(int i=0;i<2;i++){var row=reg["eyes"].Single(x=>(int)x["eye"]==ids[i]);for(int c=0;c<4;c++){px[i][c]=(float)(double)row["nativeToAuthoredProjection"][c][0];py[i][c]=(float)(double)row["nativeToAuthoredProjection"][c][1];}}
  var shader=AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye115.compute");if(!shader)throw new InvalidOperationException("115 reviewed compute not imported");
  try{
   native=new NativeRetarget96(e,regPath,diag);Source=new LiveSurface107(e,shader,ids,px,py);Curves=new SourcePigment113(e,reg);
   DenseNative=new NativeDense107(e,regPath,diag+"-dense107");DenseSource=new LiveSurface107(e,shader,ids,px,py);
   BaselineCarrierNative=new NativeCarrier113(e,regPath,diag+"-baseline113");BaselineCarrierSource=new LiveSurface107(e,shader,ids,px,py);Baseline113=new RegionDriver113(e);
   CarrierNative=new NativeCarrier115(e,regPath,diag+"-carrier115",sampleScale:4);CarrierSource=new LiveSurface107(e,shader,ids,px,py);Region=new RegionDriver115(e);
   Region.QueryBindings(Source.Engine,false);Region.QueryBindings(DenseSource.Engine,false);Region.QueryBindings(CarrierSource.Engine,true);Baseline113.QueryBindings(BaselineCarrierSource.Engine,true);canvas.AfterCanvas=Record;
  }catch{Dispose();throw;}
 }
 void Targets(){int w=eye.roi.width,h=eye.roi.height;if(Fields==null||Fields[0].rt.width!=w||Fields[0].rt.height!=h){ReleaseTargets();Fields=new RTHandle[4];BaselineFields=new RTHandle[4];LegacyFields=new RTHandle[4];try{for(int i=0;i<4;i++){Fields[i]=RTHandles.Alloc(w,h,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point,name:"115 live source-form");LegacyFields[i]=RTHandles.Alloc(w,h,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point,name:"115 same-frame113 control");BaselineFields[i]=RTHandles.Alloc(w,h,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point,name:"115 same-frame102 debug");}}catch{ReleaseTargets();throw;}}
  int n=Source.Engine.Colour.count;if(Results==null||Results[0].count!=n){ReleaseBuffers();Results=new GraphicsBuffer[4];LegacyResults=new GraphicsBuffer[4];try{for(int i=0;i<4;i++){Results[i]=new GraphicsBuffer(GraphicsBuffer.Target.Structured,n,16);LegacyResults[i]=new GraphicsBuffer(GraphicsBuffer.Target.Structured,n,16);}}catch{ReleaseBuffers();throw;}}
 }
 void Record(RenderGraph graph,UniversalResourceData resources){
  if(Disposed)throw new ObjectDisposedException(nameof(Forward115));native.RecordGraph(graph,resources);DenseNative.RecordGraph(graph,resources);BaselineCarrierNative.RecordGraph(graph,resources);CarrierNative.RecordGraph(graph,resources);
  BaselineCarrierSource.Update();BaselineCarrierSource.Engine.Resize(BaselineCarrierNative.currentWidth,BaselineCarrierNative.currentHeight,BaselineCarrierSource.Scope);CarrierSource.Update();CarrierSource.Engine.Resize(CarrierNative.currentWidth,CarrierNative.currentHeight,CarrierSource.Scope);DenseSource.Update();DenseSource.Engine.Resize(DenseNative.currentWidth,DenseNative.currentHeight,DenseSource.Scope);Source.Update();Source.Engine.Resize(native.currentWidth,native.currentHeight,Source.Scope);Curves.Update(native.Anchor96,native.Bounds96);Targets();
  using var b=graph.AddUnsafePass<Data>("115 complete source-form + paired destination; same-frame113 control",out var d);d.o=this;d.view=eye.full.motion.camera.worldToCameraMatrix;d.projection=eye.full.motion.camera.projectionMatrix;
  foreach(var g in Region.Buffers.Concat(Baseline113.Buffers).Concat(Source.Engine.Buffers).Concat(DenseSource.Engine.Buffers).Concat(CarrierSource.Engine.Buffers).Concat(BaselineCarrierSource.Engine.Buffers).Concat(Results).Concat(LegacyResults))b.UseBuffer(graph.ImportBuffer(g),AccessFlags.ReadWrite);
  b.UseBuffer(graph.ImportBuffer(Curves.Buffer),AccessFlags.ReadWrite);foreach(var aa in new[]{native.Handles96,DenseNative.Handles96,CarrierNative.Handles96,BaselineCarrierNative.Handles96})foreach(var a in aa)foreach(var t in a)b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);foreach(var t in canvas.Fields)b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);foreach(var t in new[]{eye.samples[4].rgba,eye.samples[4].meta})b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);foreach(var t in Fields.Concat(BaselineFields).Concat(LegacyFields))b.UseTexture(graph.ImportTexture(t),AccessFlags.Write);b.AllowPassCulling(false);b.AllowGlobalStateModification(true);b.SetRenderFunc(static(Data data,UnsafeGraphContext c)=>data.o.Draw(data,c));
 }
 void Common(CommandBuffer cmd,int k,RTHandle[] target,GraphicsBuffer[] output){
  var cs=Source.Engine.Shader;cmd.SetComputeIntParams(cs,"_ForwardROI102",eye.roi.x,272-eye.roi.y-eye.roi.height,eye.roi.width,eye.roi.height);cmd.SetComputeVectorParam(cs,"_ForwardAnchor102",new Vector4(native.Anchor96.x+native.Bounds96.x,native.Anchor96.y+native.Bounds96.y,0,0));cmd.SetComputeTextureParam(cs,k,"_CanvasRGBA102",canvas.Fields[0].rt);cmd.SetComputeTextureParam(cs,k,"_CanvasMeta102",canvas.Fields[1].rt);cmd.SetComputeTextureParam(cs,k,"_HairRGBA102",eye.samples[4].rgba.rt);cmd.SetComputeTextureParam(cs,k,"_HairMeta102",eye.samples[4].meta.rt);cmd.SetComputeBufferParam(cs,k,"_ReadColour96",output[0]);cmd.SetComputeBufferParam(cs,k,"_ReadIdentity96",output[1]);cmd.SetComputeBufferParam(cs,k,"_ReadDecision96",output[2]);for(int i=0;i<4;i++)cmd.SetComputeTextureParam(cs,k,new[]{"_EyeRGBA102","_EyeOwner102","_FinalRGBA102","_FinalOwner102"}[i],target[i].rt);
 }
 void Draw(Data data,UnsafeGraphContext context){
  var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);var e=Source.Engine;
  for(int p=0;p<4;p++)DenseSource.Engine.Pack(cmd,p,DenseNative.layers[p],true);DenseSource.Engine.Dispatch(cmd,data.view,data.projection,false,0);
  for(int p=0;p<4;p++)BaselineCarrierSource.Engine.Pack(cmd,p,BaselineCarrierNative.layers[p],true);Baseline113.PrepareCarrier(cmd,BaselineCarrierSource.Engine,BaselineCarrierNative.Anchor96+new Vector2(BaselineCarrierNative.Bounds96.x,BaselineCarrierNative.Bounds96.y));BaselineCarrierSource.Engine.Dispatch(cmd,data.view,data.projection,true,0);
  for(int p=0;p<4;p++)CarrierSource.Engine.Pack(cmd,p,CarrierNative.layers[p],true);Region.PrepareCarrier(cmd,CarrierSource.Engine,CarrierNative.Anchor96+new Vector2(CarrierNative.Bounds96.x,CarrierNative.Bounds96.y));CarrierSource.Engine.Dispatch(cmd,data.view,data.projection,true,0);
  for(int p=0;p<4;p++)e.Pack(cmd,p,native.layers[p],true);e.Dispatch(cmd,data.view,data.projection,false,0);Curves.Upload(cmd);
  int k=e.Shader.FindKernel("ComposeForward102");Common(cmd,k,BaselineFields,new[]{e.Colour,e.Identity,e.Decisions});cmd.DispatchCompute(e.Shader,k,(eye.roi.width+7)/8,(eye.roi.height+7)/8,1);
  Baseline113.Draw(cmd,e,DenseSource.Engine,BaselineCarrierSource.Engine,Curves,LegacyResults,BaselineCarrierNative.Anchor96+new Vector2(BaselineCarrierNative.Bounds96.x,BaselineCarrierNative.Bounds96.y));k=e.Shader.FindKernel("ComposeRegion113");Common(cmd,k,LegacyFields,LegacyResults);Baseline113.ComposeBindings(cmd,e.Shader,k,BaselineCarrierSource.Engine);cmd.DispatchCompute(e.Shader,k,(eye.roi.width+7)/8,(eye.roi.height+7)/8,1);
  Region.Draw(cmd,e,DenseSource.Engine,CarrierSource.Engine,Curves,Results,CarrierNative.Anchor96+new Vector2(CarrierNative.Bounds96.x,CarrierNative.Bounds96.y));k=e.Shader.FindKernel("ComposeRegion115");Common(cmd,k,Fields,Results);Region.ComposeBindings(cmd,e.Shader,k,CarrierSource.Engine);cmd.DispatchCompute(e.Shader,k,(eye.roi.width+7)/8,(eye.roi.height+7)/8,1);RenderedFrame=Time.frameCount;
 }
 public void AssertRendered(){canvas.AssertRendered();native.AssertRendered();DenseNative.AssertRendered();BaselineCarrierNative.AssertRendered();CarrierNative.AssertRendered();if(RenderedFrame!=Time.frameCount||Curves.UpdatedFrame!=Time.frameCount)throw new InvalidOperationException("115 same-frame source/form/baseline missing");}
 void ReleaseBuffers(){if(Results!=null)foreach(var b in Results)b?.Dispose();if(LegacyResults!=null)foreach(var b in LegacyResults)b?.Dispose();Results=null;LegacyResults=null;}
 void ReleaseTargets(){foreach(var a in new[]{Fields,BaselineFields,LegacyFields})if(a!=null)foreach(var t in a)t?.Release();Fields=null;BaselineFields=null;LegacyFields=null;}
 public void Dispose(){if(Disposed)return;Disposed=true;if(canvas.AfterCanvas==Record)canvas.AfterCanvas=null;Region?.Dispose();Baseline113?.Dispose();CarrierSource?.Dispose();CarrierNative?.Dispose();BaselineCarrierSource?.Dispose();BaselineCarrierNative?.Dispose();DenseSource?.Dispose();DenseNative?.Dispose();Curves?.Dispose();Source?.Dispose();native?.Dispose();ReleaseBuffers();ReleaseTargets();}
}
