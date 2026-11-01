using System;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.Rendering.RenderGraphModule;

// Own offscreen forward canvas. It never reads product77/295/348/98 colour.
public sealed class LayerZero101:ScriptableRenderPass,IDisposable {
 readonly EyeFeature348 eye;readonly Material skin,white,iris;readonly Material[] mats;
 RTHandle[] fields;RTHandle depth;int width,height;Exception failure;
 public RTHandle[] Fields=>fields;public int RenderedFrame{get;private set;}=-1;
 public readonly SkinSource101 Source;public bool Disposed{get;private set;}
 public Action<RenderGraph,UniversalResourceData> AfterCanvas;
 sealed class Data{public LayerZero101 owner;}
 public LayerZero101(EyeFeature348 e,string registry){eye=e;Source=new SkinSource101(e,registry);renderPassEvent=(RenderPassEvent)551;
  var shader=AssetDatabase.LoadAssetAtPath<Shader>("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/LayerZero101.shader");if(!shader||!shader.isSupported)throw new InvalidOperationException("101 shader unavailable");
  try{skin=Make(e.materials[7],shader,0);white=Make(e.materials[8],shader,1);iris=Make(e.materials[5],shader,1);mats=new[]{skin,white,iris};RenderPipelineManager.beginCameraRendering+=Enqueue;}catch{if(skin)UnityEngine.Object.DestroyImmediate(skin);if(white)UnityEngine.Object.DestroyImmediate(white);if(iris)UnityEngine.Object.DestroyImmediate(iris);throw;}
 }
 Material Make(Material original,Shader shader,int proxy){var m=new Material(original){shader=shader,hideFlags=HideFlags.DontSave,name="101 owned clean canvas"};m.shaderKeywords=original.shaderKeywords;m.SetInt("_Proxy101",proxy);m.SetInt("_Steps101",Source.Steps);m.SetVectorArray("_Palette101",Source.linearPalette);return m;}
 void Enqueue(ScriptableRenderContext c,Camera camera){if(Disposed||camera!=eye.full.motion.camera||failure!=null)return;try{var data=camera.GetComponent<UniversalAdditionalCameraData>();var renderer=data?data.scriptableRenderer:UniversalRenderPipeline.asset?UniversalRenderPipeline.asset.scriptableRenderer:null;if(renderer==null)throw new InvalidOperationException("101 no existing live/default camera renderer");renderer.EnqueuePass(this);}catch(Exception ex){failure=ex;}}
 void Targets(){int w=eye.roi.width*4,h=eye.roi.height*4;if(fields!=null&&w==width&&h==height)return;Release();width=w;height=h;fields=new RTHandle[4];try{for(int i=0;i<4;i++)fields[i]=RTHandles.Alloc(w,h,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,filterMode:FilterMode.Point,name:"101 owned canvas channel");depth=RTHandles.Alloc(w,h,depthBufferBits:DepthBits.Depth32,name:"101 owned canvas depth");}catch{Release();throw;}}
 void Bind(Material m){var f=eye.full;var camera=f.motion.camera;m.SetMatrix("_ProbeGPUVP91",GL.GetGPUProjectionMatrix(eye.cropProjection,true)*camera.worldToCameraMatrix);m.SetFloat("_RasterScale91",4);m.SetVector("_ROI348",new Vector4(eye.roi.x,272-eye.roi.y-eye.roi.height,eye.roi.width,eye.roi.height));m.SetVector("_SurfaceInvRaster335",new Vector4(1f/480,1f/272,0,0));m.SetFloat("_FaceShadeSteps335",f.faceShadeSteps);m.SetFloat("_SurfaceShadeSteps335",f.surfaceShadeSteps);m.SetInt("_SurfaceMaskReady335",0);m.SetFloat("_BindSH91",0);}
 public override void RecordRenderGraph(RenderGraph graph,ContextContainer frame){if(Disposed||frame.Get<UniversalCameraData>().camera!=eye.full.motion.camera)return;Targets();foreach(var m in mats)Bind(m);var r=frame.Get<UniversalResourceData>();using(var b=graph.AddUnsafePass<Data>("101 clean native face and skin socket proxy",out var d)){d.owner=this;foreach(var t in fields)b.UseTexture(graph.ImportTexture(t),AccessFlags.Write);b.UseTexture(graph.ImportTexture(depth),AccessFlags.Write);b.UseAllGlobalTextures(true);if(r.mainShadowsTexture.IsValid())b.UseTexture(r.mainShadowsTexture);if(r.additionalShadowsTexture.IsValid())b.UseTexture(r.additionalShadowsTexture);b.AllowPassCulling(false);b.AllowGlobalStateModification(true);b.SetRenderFunc(static(Data data,UnsafeGraphContext context)=>data.owner.Draw(context));}AfterCanvas?.Invoke(graph,r);}
 void Draw(UnsafeGraphContext context){var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);cmd.SetRenderTarget(fields.Select(t=>new RenderTargetIdentifier(t.rt)).ToArray(),depth.rt);cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1,0);cmd.SetViewport(new Rect(0,0,width,height));var matrix=eye.full.motion.surface.outputs[1].transform.localToWorldMatrix;
  cmd.DrawMesh(eye.sampleFace,matrix,skin,3,0);cmd.DrawMesh(eye.sampleFace,matrix,white,4,0);cmd.DrawMesh(eye.sampleFace,matrix,iris,1,0);RenderedFrame=Time.frameCount;
 }
 public void AssertRendered(){if(failure!=null)throw new InvalidOperationException("101 pass enqueue failed",failure);if(RenderedFrame!=Time.frameCount)throw new InvalidOperationException("101 no same-frame in-graph canvas; no manual fallback");}
 void Release(){if(fields!=null)foreach(var t in fields)t?.Release();depth?.Release();fields=null;depth=null;}
 public void Dispose(){if(Disposed)return;Disposed=true;RenderPipelineManager.beginCameraRendering-=Enqueue;AfterCanvas=null;Release();if(mats!=null)foreach(var m in mats)if(m)UnityEngine.Object.DestroyImmediate(m);}
}
