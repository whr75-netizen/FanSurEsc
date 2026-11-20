using UnityEngine;using UnityEngine.Rendering;using UnityEngine.Rendering.Universal;using UnityEngine.Rendering.RenderGraphModule;
public sealed class JoinSource367:ScriptableRendererFeature{
 Pass pass;public override void Create(){pass=new Pass{renderPassEvent=(RenderPassEvent)550};}
 public override void AddRenderPasses(ScriptableRenderer r,ref RenderingData d){var e=HeadLocal367.Active;if(e&&e.post&&e.post.IsRuntimeActive&&e.post.targets!=null&&e.headPost&&e.headPost.targets!=null&&e.headEnabled&&e.headReady&&e.main.motion.camera==d.cameraData.camera&&!e.main.contourReady)r.EnqueuePass(pass);}
 sealed class D{public HeadLocal367 e;}
 sealed class Pass:ScriptableRenderPass{public override void RecordRenderGraph(RenderGraph g,ContextContainer f){var e=HeadLocal367.Active;e.EnsureSampleJoin();using var b=g.AddUnsafePass<D>("365 integer copy head sample layers before original364 masks",out var d);d.e=e;for(int group=4;group<6;group++)for(int c=0;c<4;c++){b.UseTexture(g.ImportTexture(e.headPost.targets[group][c]));b.UseTexture(g.ImportTexture(e.sampleJoin[group-4][c]),AccessFlags.ReadWrite);b.UseTexture(g.ImportTexture(e.post.targets[group][c]),AccessFlags.ReadWrite);}b.AllowPassCulling(false);b.SetRenderFunc(static(D d,UnsafeGraphContext c)=>d.e.JoinSamples(CommandBufferHelpers.GetNativeCommandBuffer(c.cmd)));}}
}
