using System;using System.Linq;using System.Collections.Generic;using UnityEngine;using UnityEngine.Rendering;using UnityEngine.Rendering.Universal;using UnityEngine.Rendering.RenderGraphModule;using UnityEngine.Experimental.Rendering;
// Current VRM binding adapter of E127PartFeature's independent MRT/selected DrawRenderer route.
public static class Eye202Layers{
 public static bool Enabled;public static Eye202View Current;public static readonly string[]Names={"FaceSkin","White","IrisPupil","Glint","Eyeline","LidSkinCarrier","Hair","Brow","BaseNoEyes","FullSource"};
 public sealed class Set:IDisposable{public RTHandle rgba,meta,uv,world,depth;public Set(string n){rgba=RTHandles.Alloc(960,544,colorFormat:GraphicsFormat.R8G8B8A8_SRGB,filterMode:FilterMode.Point,name:n+"RGBA");meta=RTHandles.Alloc(960,544,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,filterMode:FilterMode.Point,name:n+"Meta");uv=RTHandles.Alloc(960,544,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,filterMode:FilterMode.Point,name:n+"UVControl");world=RTHandles.Alloc(960,544,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,filterMode:FilterMode.Point,name:n+"World");depth=RTHandles.Alloc(960,544,depthBufferBits:DepthBits.Depth32,filterMode:FilterMode.Point,name:n+"Depth");}public void Dispose(){rgba?.Release();meta?.Release();uv?.Release();world?.Release();depth?.Release();}}
 public static Set[]Sets;public static void Ensure(){if(Sets==null)Sets=Names.Select(n=>new Set("Eye202_"+n)).ToArray();}
 public static bool Selected(int part,int role)=>part switch{0=>role==3,1=>role==4,2=>role==1,3=>role==2,4=>role==6,5=>role==3,6=>role>=11,7=>role==5,8=>role!=1&&role!=2&&role!=4&&role!=6,9=>true,_=>false};
 public static void Dispose(){Enabled=false;Current=null;if(Sets!=null)foreach(var x in Sets)x.Dispose();Sets=null;}
}
public sealed class Eye202PartFeature:ScriptableRendererFeature{
 PartPass pass;public override void Create(){pass=new PartPass{renderPassEvent=RenderPassEvent.AfterRenderingTransparents};}
 public override void AddRenderPasses(ScriptableRenderer r,ref RenderingData d){var v=Eye202Layers.Current;if(Eye202Layers.Enabled&&v&&d.cameraData.camera==v.game.actor.inheritedView.worldCamera)r.EnqueuePass(pass);}
 sealed class Data{public int part;public Renderer[]renderers;public Material[]materials;public int[]submeshes;}
 sealed class PartPass:ScriptableRenderPass{
  public override void RecordRenderGraph(RenderGraph graph,ContextContainer frame){Eye202Layers.Ensure();var v=Eye202Layers.Current;
   for(int p=0;p<Eye202Layers.Names.Length;p++){
    using var b=graph.AddRasterRenderPass<Data>("Eye202 independent "+Eye202Layers.Names[p],out var d);var t=Eye202Layers.Sets[p];b.SetRenderAttachment(graph.ImportTexture(t.rgba),0,AccessFlags.Write);b.SetRenderAttachment(graph.ImportTexture(t.meta),1,AccessFlags.Write);b.SetRenderAttachment(graph.ImportTexture(t.uv),2,AccessFlags.Write);b.SetRenderAttachment(graph.ImportTexture(t.world),3,AccessFlags.Write);b.SetRenderAttachmentDepth(graph.ImportTexture(t.depth),AccessFlags.Write);b.UseAllGlobalTextures(true);var res=frame.Get<UniversalResourceData>();if(res.mainShadowsTexture.IsValid())b.UseTexture(res.mainShadowsTexture,AccessFlags.Read);if(res.additionalShadowsTexture.IsValid())b.UseTexture(res.additionalShadowsTexture,AccessFlags.Read);b.AllowPassCulling(false);b.AllowGlobalStateModification(true);
    var rr=new List<Renderer>();var mm=new List<Material>();var ss=new List<int>();foreach(var r in v.game.sourceRenderers){var mats=r.sharedMaterials;for(int s=0;s<mats.Length;s++){int role=Mathf.RoundToInt(mats[s].GetFloat("_E151Role"));if(!Eye202Layers.Selected(p,role))continue;rr.Add(r);mm.Add(mats[s]);ss.Add(s);}}d.part=p;d.renderers=rr.ToArray();d.materials=mm.ToArray();d.submeshes=ss.ToArray();
    b.SetRenderFunc(static(Data d,RasterGraphContext c)=>{c.cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1,0);c.cmd.SetGlobalFloat("_E202Part",d.part);for(int i=0;i<d.renderers.Length;i++){var m=d.materials[i];int pass=m.FindPass("IndependentEye202");if(pass<0)throw new Exception("IndependentEye202 passmissing");c.cmd.DrawRenderer(d.renderers[i],m,d.submeshes[i],pass);}c.cmd.SetGlobalFloat("_E202Part",-1);});
   }
  }
 }
}
