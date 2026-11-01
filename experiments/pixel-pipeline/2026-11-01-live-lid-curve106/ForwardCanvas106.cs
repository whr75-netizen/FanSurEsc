using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.Rendering.RenderGraphModule;

// Isolated live106 and baseline102 share evaluated geometry, lighting and all
// native input passes. Only106's curve augmentation differs. No GPU readback.
public sealed class ForwardCanvas106:IDisposable{
 readonly EyeFeature348 eye;readonly LayerZero101 canvas;readonly NativeRetarget96 native;
 public readonly LiveSurface96 Source;public readonly SourceCurves106 Curves;
 public RTHandle[] Fields{get;private set;}public RTHandle[] BaselineFields{get;private set;}
 public GraphicsBuffer[] Results{get;private set;}public bool Disposed{get;private set;}public int RenderedFrame{get;private set;}=-1;
 public Obj58 Info=>new Obj58{["nativeRegistration"]=native.Info,["scope"]=Source.Scope,["ownedBytes"]=Source.Engine.OwnedBytes+Curves.OwnedBytes+(Results==null?0:Results.Sum(b=>(long)b.count*b.stride)),["frames"]=Source.Engine.Frames,["canonicalSize"]=new Arr58(Source.Engine.Width,Source.Engine.Height),["curves106"]=Curves.Info,["selectionOccluders"]="native face-skin only; external hair after eye composition",["priorColourInputs"]=0,["runtimeGPUReadbacks"]=0,["baseline102SameInputs"]=true,["irisWhiteProtection"]=true,["poseOrCloseGate"]=false};
 sealed class Data{public ForwardCanvas106 o;public Matrix4x4 view,projection;}
 public ForwardCanvas106(EyeFeature348 e,LayerZero101 layer,string regPath,string diag){eye=e;canvas=layer;if(canvas.AfterCanvas!=null)throw new InvalidOperationException("106 canvas callback already owned");var reg=Json58.Parse(File.ReadAllText(regPath));var ids=reg["eyes"].Select(x=>(int)x["eye"]).OrderBy(x=>x).ToArray();var px=new Vector4[2];var py=new Vector4[2];for(int i=0;i<2;i++){var row=reg["eyes"].Single(x=>(int)x["eye"]==ids[i]);for(int c=0;c<4;c++){px[i][c]=(float)(double)row["nativeToAuthoredProjection"][c][0];py[i][c]=(float)(double)row["nativeToAuthoredProjection"][c][1];}}
  try{native=new NativeRetarget96(e,regPath,diag);Source=new LiveSurface96(e,AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye106.compute"),ids,px,py);Curves=new SourceCurves106(e,reg);canvas.AfterCanvas=Record;}catch{Curves?.Dispose();Source?.Dispose();native?.Dispose();throw;}
 }
 void Targets(){int w=eye.roi.width,h=eye.roi.height;if(Fields==null||Fields[0].rt.width!=w||Fields[0].rt.height!=h){ReleaseTargets();Fields=new RTHandle[4];BaselineFields=new RTHandle[4];try{for(int i=0;i<4;i++){Fields[i]=RTHandles.Alloc(w,h,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point,name:"106 live source curve");BaselineFields[i]=RTHandles.Alloc(w,h,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point,name:"106 same-input baseline102");}}catch{ReleaseTargets();throw;}}
  int n=Source.Engine.Colour.count;if(Results==null||Results[0].count!=n){ReleaseBuffers();Results=new GraphicsBuffer[4];try{for(int i=0;i<4;i++)Results[i]=new GraphicsBuffer(GraphicsBuffer.Target.Structured,n,16);}catch{ReleaseBuffers();throw;}}
 }
 void Record(RenderGraph graph,UniversalResourceData resources){if(Disposed)throw new ObjectDisposedException(nameof(ForwardCanvas106));native.RecordGraph(graph,resources);Source.Update();var engine=Source.Engine;engine.Resize(native.currentWidth,native.currentHeight,Source.Scope);Curves.Update(native.Anchor96,native.Bounds96);Targets();using var b=graph.AddUnsafePass<Data>("106 same-input joint eye with live source curve and external hair",out var d);d.o=this;d.view=eye.full.motion.camera.worldToCameraMatrix;d.projection=eye.full.motion.camera.projectionMatrix;
  foreach(var buffer in engine.Buffers)b.UseBuffer(graph.ImportBuffer(buffer),AccessFlags.ReadWrite);b.UseBuffer(graph.ImportBuffer(Curves.Buffer),AccessFlags.ReadWrite);foreach(var buffer in Results)b.UseBuffer(graph.ImportBuffer(buffer),AccessFlags.ReadWrite);
  foreach(var a in native.Handles96)foreach(var t in a)b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);foreach(var t in canvas.Fields)b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);foreach(var t in new[]{eye.samples[4].rgba,eye.samples[4].meta})b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);foreach(var t in Fields.Concat(BaselineFields))b.UseTexture(graph.ImportTexture(t),AccessFlags.Write);b.AllowPassCulling(false);b.AllowGlobalStateModification(true);b.SetRenderFunc(static(Data data,UnsafeGraphContext context)=>data.o.Draw(data,context));
 }
 void Compose(CommandBuffer cmd,GraphicsBuffer colour,GraphicsBuffer identity,GraphicsBuffer decision,RTHandle[] target){var e=Source.Engine;var cs=e.Shader;int k=cs.FindKernel("ComposeForward102");
  cmd.SetComputeIntParams(cs,"_ForwardROI102",eye.roi.x,272-eye.roi.y-eye.roi.height,eye.roi.width,eye.roi.height);cmd.SetComputeVectorParam(cs,"_ForwardAnchor102",new Vector4(native.Anchor96.x+native.Bounds96.x,native.Anchor96.y+native.Bounds96.y,0,0));
  cmd.SetComputeTextureParam(cs,k,"_CanvasRGBA102",canvas.Fields[0].rt);cmd.SetComputeTextureParam(cs,k,"_CanvasMeta102",canvas.Fields[1].rt);cmd.SetComputeTextureParam(cs,k,"_HairRGBA102",eye.samples[4].rgba.rt);cmd.SetComputeTextureParam(cs,k,"_HairMeta102",eye.samples[4].meta.rt);cmd.SetComputeBufferParam(cs,k,"_ReadColour96",colour);cmd.SetComputeBufferParam(cs,k,"_ReadIdentity96",identity);cmd.SetComputeBufferParam(cs,k,"_ReadDecision96",decision);for(int i=0;i<4;i++)cmd.SetComputeTextureParam(cs,k,new[]{"_EyeRGBA102","_EyeOwner102","_FinalRGBA102","_FinalOwner102"}[i],target[i].rt);cmd.DispatchCompute(cs,k,(eye.roi.width+7)/8,(eye.roi.height+7)/8,1);
 }
 void Draw(Data data,UnsafeGraphContext context){var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);var e=Source.Engine;for(int p=0;p<4;p++)e.Pack(cmd,p,native.layers[p],true);e.Dispatch(cmd,data.view,data.projection,false,0);Compose(cmd,e.Colour,e.Identity,e.Decisions,BaselineFields);
  Curves.Upload(cmd);var cs=e.Shader;int k=cs.FindKernel("ApplyCurve106");cmd.BeginSample("106 live source curve support");cmd.SetComputeIntParam(cs,"_CurveCount106",Curves.Count);cmd.SetComputeIntParams(cs,"_CurveEyeIds106",Curves.EyeId(0),Curves.EyeId(1));
  cmd.SetComputeBufferParam(cs,k,"_Curves106",Curves.Buffer);cmd.SetComputeBufferParam(cs,k,"_Layers96",e.Layers);cmd.SetComputeBufferParam(cs,k,"_Visibility96",e.Visibility);cmd.SetComputeBufferParam(cs,k,"_BaselineColour106",e.Colour);cmd.SetComputeBufferParam(cs,k,"_BaselineIdentity106",e.Identity);cmd.SetComputeBufferParam(cs,k,"_BaselineDecision106",e.Decisions);
  for(int i=0;i<4;i++)cmd.SetComputeBufferParam(cs,k,new[]{"_CurveColour106","_CurveIdentity106","_CurveDecision106","_CurveAudit106"}[i],Results[i]);cmd.DispatchCompute(cs,k,(e.Width/4+7)/8,(e.Height/4+7)/8,1);cmd.EndSample("106 live source curve support");Compose(cmd,Results[0],Results[1],Results[2],Fields);RenderedFrame=Time.frameCount;
 }
 public void AssertRendered(){canvas.AssertRendered();native.AssertRendered();if(RenderedFrame!=Time.frameCount||Curves.UpdatedFrame!=Time.frameCount)throw new InvalidOperationException("106 same-frame source/curve pass missing");}
 void ReleaseTargets(){if(Fields!=null)foreach(var f in Fields)f?.Release();if(BaselineFields!=null)foreach(var f in BaselineFields)f?.Release();Fields=null;BaselineFields=null;}
 void ReleaseBuffers(){if(Results!=null)foreach(var b in Results)b?.Dispose();Results=null;}
 public void Dispose(){if(Disposed)return;Disposed=true;if(canvas.AfterCanvas==Record)canvas.AfterCanvas=null;Curves?.Dispose();Source?.Dispose();native?.Dispose();ReleaseBuffers();ReleaseTargets();}
}
