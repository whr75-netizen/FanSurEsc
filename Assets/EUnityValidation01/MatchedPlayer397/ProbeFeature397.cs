using UnityEngine;using UnityEngine.Rendering;using UnityEngine.Rendering.Universal;using UnityEngine.Rendering.RenderGraphModule;using UnityEngine.Experimental.Rendering;

// One-camera, opt-in source probe. Renderer lists retain URP per-object lighting.
public sealed class ProbeFeature397:ScriptableRendererFeature{
 public sealed class State{public Camera camera;public string tag;public RTHandle[]colour;public RTHandle depth;public bool executed;}
 public static State Active;
 ProbePass pass;
 public override void Create(){pass=new ProbePass{renderPassEvent=(RenderPassEvent)302};}
 public override void AddRenderPasses(ScriptableRenderer renderer,ref RenderingData data){if(Active!=null&&data.cameraData.camera==Active.camera)renderer.EnqueuePass(pass);}
 sealed class ProbePass:ScriptableRenderPass{
  sealed class Data{public RendererListHandle list;public State state;}
  public override void RecordRenderGraph(RenderGraph graph,ContextContainer frame){var s=Active;if(s==null)return;var camera=frame.Get<UniversalCameraData>();if(camera.camera!=s.camera)return;var rd=frame.Get<UniversalRenderingData>();var ld=frame.Get<UniversalLightData>();var drawing=RenderingUtils.CreateDrawingSettings(new ShaderTagId(s.tag),rd,camera,ld,camera.defaultOpaqueSortFlags);var order=drawing.sortingSettings;order.criteria=camera.defaultOpaqueSortFlags & ~SortingCriteria.OptimizeStateChanges;drawing.sortingSettings=order;drawing.perObjectData=rd.perObjectData;var filtering=new FilteringSettings(RenderQueueRange.all,-1,1u<<27);var list=graph.CreateRendererList(new RendererListParams(rd.cullResults,drawing,filtering));
   using var b=graph.AddRasterRenderPass<Data>("397 actual source preservation "+s.tag,out var d);d.list=list;d.state=s;b.UseRendererList(list);b.UseAllGlobalTextures(true);for(int i=0;i<s.colour.Length;i++)b.SetRenderAttachment(graph.ImportTexture(s.colour[i]),i,AccessFlags.Write);b.SetRenderAttachmentDepth(graph.ImportTexture(s.depth),AccessFlags.ReadWrite);b.AllowPassCulling(false);b.AllowGlobalStateModification(true);b.SetRenderFunc(static(Data x,RasterGraphContext ctx)=>{ctx.cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1f,0);ctx.cmd.DrawRendererList(x.list);x.state.executed=true;});
  }
 }
}
