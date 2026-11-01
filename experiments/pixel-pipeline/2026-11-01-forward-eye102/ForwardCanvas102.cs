using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.Rendering.RenderGraphModule;

// Clean Layer0 -> source-local whole eye -> external hair. No previous image.
public sealed class ForwardCanvas102:IDisposable {
 readonly EyeFeature348 eye;readonly LayerZero101 canvas;readonly NativeRetarget96 native;
 public readonly LiveSurface96 Source;public RTHandle[] Fields{get;private set;}
 public bool Disposed{get;private set;}public int RenderedFrame{get;private set;}=-1;
 public Obj58 Info=>new Obj58{["nativeRegistration"]=native.Info,["scope"]=Source.Scope,["ownedBytes"]=Source.Engine.OwnedBytes,["frames"]=Source.Engine.Frames,["canonicalSize"]=new Arr58(Source.Engine.Width,Source.Engine.Height),["selectionOccluders"]="native face-skin submesh only; external hair/brow/body excluded",["externalHair"]="post-selection hard colour choice, alpha coverage >= .5 and same-sample depth",["coldTiePolicy"]=0,["priorColourInputs"]=0};
 sealed class Data{public ForwardCanvas102 o;public Matrix4x4 view,projection;}
 public ForwardCanvas102(EyeFeature348 e,LayerZero101 layer,string regPath,string diag){eye=e;canvas=layer;var reg=Json58.Parse(File.ReadAllText(regPath));var ids=reg["eyes"].Select(x=>(int)x["eye"]).OrderBy(x=>x).ToArray();var px=new Vector4[2];var py=new Vector4[2];for(int i=0;i<2;i++){var row=reg["eyes"].Single(x=>(int)x["eye"]==ids[i]);for(int c=0;c<4;c++){px[i][c]=(float)(double)row["nativeToAuthoredProjection"][c][0];py[i][c]=(float)(double)row["nativeToAuthoredProjection"][c][1];}}
  try{native=new NativeRetarget96(e,regPath,diag);Source=new LiveSurface96(e,AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye102.compute"),ids,px,py);canvas.AfterCanvas=Record;}catch{Source?.Dispose();native?.Dispose();throw;}
 }
 void Targets(){int w=eye.roi.width,h=eye.roi.height;if(Fields!=null&&Fields[0].rt.width==w&&Fields[0].rt.height==h)return;Release();Fields=new RTHandle[4];try{for(int i=0;i<4;i++)Fields[i]=RTHandles.Alloc(w,h,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point,name:"102 forward eye canvas");}catch{Release();throw;}}
 void Record(RenderGraph graph,UniversalResourceData resources){if(Disposed)throw new ObjectDisposedException(nameof(ForwardCanvas102));native.RecordGraph(graph,resources);Source.Update();var engine=Source.Engine;engine.Resize(native.currentWidth,native.currentHeight,Source.Scope);Targets();using var b=graph.AddUnsafePass<Data>("102 source-local eye independent of hair then forward hard occlusion",out var d);d.o=this;d.view=eye.full.motion.camera.worldToCameraMatrix;d.projection=eye.full.motion.camera.projectionMatrix;foreach(var buffer in engine.Buffers)b.UseBuffer(graph.ImportBuffer(buffer),AccessFlags.ReadWrite);foreach(var a in native.Handles96)foreach(var t in a)b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);foreach(var t in canvas.Fields)b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);foreach(var t in new[]{eye.samples[4].rgba,eye.samples[4].meta})b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);foreach(var t in Fields)b.UseTexture(graph.ImportTexture(t),AccessFlags.Write);b.AllowPassCulling(false);b.AllowGlobalStateModification(true);b.SetRenderFunc(static(Data data,UnsafeGraphContext context)=>data.o.Draw(data,context));}
 void Draw(Data data,UnsafeGraphContext context){var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);var e=Source.Engine;for(int p=0;p<4;p++)e.Pack(cmd,p,native.layers[p],true);e.Dispatch(cmd,data.view,data.projection,false,0);var cs=e.Shader;int k=cs.FindKernel("ComposeForward102");
  cmd.SetComputeIntParams(cs,"_ForwardROI102",eye.roi.x,272-eye.roi.y-eye.roi.height,eye.roi.width,eye.roi.height);cmd.SetComputeVectorParam(cs,"_ForwardAnchor102",new Vector4(native.Anchor96.x+native.Bounds96.x,native.Anchor96.y+native.Bounds96.y,0,0));
  cmd.SetComputeTextureParam(cs,k,"_CanvasRGBA102",canvas.Fields[0].rt);cmd.SetComputeTextureParam(cs,k,"_CanvasMeta102",canvas.Fields[1].rt);cmd.SetComputeTextureParam(cs,k,"_HairRGBA102",eye.samples[4].rgba.rt);cmd.SetComputeTextureParam(cs,k,"_HairMeta102",eye.samples[4].meta.rt);cmd.SetComputeBufferParam(cs,k,"_ReadColour96",e.Colour);cmd.SetComputeBufferParam(cs,k,"_ReadIdentity96",e.Identity);cmd.SetComputeBufferParam(cs,k,"_ReadDecision96",e.Decisions);for(int i=0;i<4;i++)cmd.SetComputeTextureParam(cs,k,new[]{"_EyeRGBA102","_EyeOwner102","_FinalRGBA102","_FinalOwner102"}[i],Fields[i].rt);cmd.DispatchCompute(cs,k,(eye.roi.width+7)/8,(eye.roi.height+7)/8,1);RenderedFrame=Time.frameCount;
 }
 public void AssertRendered(){canvas.AssertRendered();native.AssertRendered();if(RenderedFrame!=Time.frameCount)throw new InvalidOperationException("102 same-frame joint forward pass missing");}
 void Release(){if(Fields!=null)foreach(var f in Fields)f?.Release();Fields=null;}
 public void Dispose(){if(Disposed)return;Disposed=true;canvas.AfterCanvas=null;Source?.Dispose();native?.Dispose();Release();}
}
