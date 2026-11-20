using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.Rendering.RenderGraphModule;

// Original world passes remain unchanged. This feature reads their native result.
public sealed class NativeWorldFeature395:ScriptableRendererFeature
{
 Capture capture;Present present;
 public override void Create(){capture=new Capture{renderPassEvent=(RenderPassEvent)901};present=new Present{renderPassEvent=(RenderPassEvent)601};}
 public override void AddRenderPasses(ScriptableRenderer renderer,ref RenderingData data){if(PixelRenderPipelineControl399.BypassPresentation)return;var v=NativePlayer395.Active;if(!v||!v.compute||(!v.gameCamera&&!v.baselineCamera))return;if(data.cameraData.camera==v.gameCamera||data.cameraData.camera==v.baselineCamera){capture.ConfigureInput(ScriptableRenderPassInput.Depth);renderer.EnqueuePass(capture);}else if(v.ready&&data.cameraData.camera==v.localCamera)renderer.EnqueuePass(present);}
 sealed class Data{public NativePlayer395 view;public TextureHandle colour,depth;public Camera camera;}
 sealed class Capture:ScriptableRenderPass{
  public override void RecordRenderGraph(RenderGraph graph,ContextContainer frame){
   var v=NativePlayer395.Active;v.EnsureWorld();var resources=frame.Get<UniversalResourceData>();var camera=frame.Get<UniversalCameraData>();
   var desc=graph.GetTextureDesc(resources.activeColorTexture);if(desc.width!=960||desc.height!=544)return;
   using var builder=graph.AddUnsafePass<Data>("395 retain original native960 world and depth",out var data);
   data.view=v;data.colour=resources.activeColorTexture;data.depth=resources.cameraDepthTexture.IsValid()?resources.cameraDepthTexture:resources.activeDepthTexture;data.camera=camera.camera;
   builder.UseTexture(data.colour);builder.UseTexture(data.depth);builder.UseTexture(graph.ImportTexture(v.world),AccessFlags.Write);builder.UseTexture(graph.ImportTexture(v.worldDepth),AccessFlags.Write);builder.AllowPassCulling(false);
   builder.SetRenderFunc(static(Data d,UnsafeGraphContext context)=>{var v=d.view;var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);var cs=v.compute;int kernel=cs.FindKernel("CaptureWorld");RTHandle source=d.colour,depth=d.depth;cmd.SetComputeTextureParam(cs,kernel,"_MainSource395",source.rt);cmd.SetComputeTextureParam(cs,kernel,"_MainDepth395",depth.rt);cmd.SetComputeTextureParam(cs,kernel,"_WorldRW395",v.world.rt);cmd.SetComputeTextureParam(cs,kernel,"_WorldDepthRW395",v.worldDepth.rt);cmd.DispatchCompute(cs,kernel,120,68,1);v.worldView=d.camera.worldToCameraMatrix;v.worldProjection=d.camera.projectionMatrix;v.worldSerial++;});
  }
 }
 sealed class Present:ScriptableRenderPass{
  public override void RecordRenderGraph(RenderGraph graph,ContextContainer frame){
   var v=NativePlayer395.Active;var full=v.host.main;var motion=full.motion;var resources=frame.Get<UniversalResourceData>();
   using(var builder=graph.AddUnsafePass<Data>("395 existing E cells at original world native samples",out var data)){
    data.view=v;
    foreach(var texture in new[]{v.world,v.worldDepth,full.colour,full.resolvedMeta,full.resolvedUV,full.domain,full.audit,motion.historyColour,motion.historyMeta,motion.historyUV})builder.UseTexture(graph.ImportTexture(texture));
    foreach(var texture in new[]{v.output,v.owner,v.cellID,v.depthAudit})builder.UseTexture(graph.ImportTexture(texture),AccessFlags.Write);
    builder.AllowPassCulling(false);builder.AllowGlobalStateModification(true);
    builder.SetRenderFunc(static(Data d,UnsafeGraphContext context)=>{var v=d.view;var full=v.host.main;var m=full.motion;var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);var cs=v.compute;int kernel=cs.FindKernel("Present");
     void T(string name,RTHandle texture)=>cmd.SetComputeTextureParam(cs,kernel,name,texture.rt);
     T("_World395",v.world);T("_WorldDepth395",v.worldDepth);T("_Local395",full.colour);T("_Meta395",full.resolvedMeta);T("_UV395",full.resolvedUV);T("_Domain395",full.domain);T("_Line395",full.audit);T("_History395",m.historyColour);T("_HistoryMeta395",m.historyMeta);T("_HistoryUV395",m.historyUV);T("_Output395",v.output);T("_Owner395",v.owner);T("_CellID395",v.cellID);T("_DepthAudit395",v.depthAudit);
     v.deliveredDelta=v.manualDelta?v.delta:m.composeDelta;
     cmd.SetComputeVectorParam(cs,"_Delta395",new Vector4(v.deliveredDelta.x,v.deliveredDelta.y,0,0));cmd.SetComputeIntParams(cs,"_Origin395",v.origin.x,v.origin.y);cmd.SetComputeIntParam(cs,"_CellScale395",v.nativePixelsPerCell);cmd.SetComputeIntParam(cs,"_WorldCellScale395",PixelRenderPipelineControl399.WorldCellScale);cmd.SetComputeIntParam(cs,"_WorldQuantizeSteps395",PixelRenderPipelineControl399.WorldQuantizeSteps);cmd.SetComputeIntParam(cs,"_Show395",(v.showCharacter&&PixelRenderPipelineControl399.EnableCharacterPass)?1:0);cmd.SetComputeIntParam(cs,"_Capture395",full.capturePending&&full.contourReady?1:0);cmd.SetComputeIntParam(cs,"_EnableHistory395",PixelRenderPipelineControl399.EnableTemporalHistory?1:0);
     cmd.SetComputeVectorParam(cs,"_NearFar395",new Vector4(v.gameCamera.nearClipPlane,v.gameCamera.farClipPlane,SystemInfo.usesReversedZBuffer?1:0,0));cmd.SetComputeVectorArrayParam(cs,"_Texel395",m.texelSizes);cmd.SetComputeFloatParam(cs,"_UVTolerance395",m.uvToleranceTexels);cmd.DispatchCompute(cs,kernel,120,68,1);v.presentSerial++;
    });
   }
   resources.cameraColor=graph.ImportTexture(v.output);
  }
 }
}
