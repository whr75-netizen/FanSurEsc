// Metadata-compiled only. No call is made by this turn's CPU tests.
using System;using UnityEngine;using UnityEngine.Experimental.Rendering;
namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {
public static class ReadbackPreflight32 {
 public static void RequireCapabilities(){
  var f=GraphicsFormat.R32G32B32A32_SFloat;
  if(!SystemInfo.supportsAsyncGPUReadback||SystemInfo.supportedRenderTargetCount<5||
   !SystemInfo.IsFormatSupported(f,GraphicsFormatUsage.Render)||!SystemInfo.IsFormatSupported(f,GraphicsFormatUsage.LoadStore)||!SystemInfo.IsFormatSupported(f,GraphicsFormatUsage.ReadPixels))
   throw new NotSupportedException("32 five float MRTs/render/UAV/readback capabilities required; no fallback");
 }
 public static int RequireColourSource(RenderTexture target,int x,int y,int width,int height){
  if(!target||target.dimension!=UnityEngine.Rendering.TextureDimension.Tex2D||target.antiAliasing!=1||target.volumeDepth!=1||target.graphicsFormat!=GraphicsFormat.R32G32B32A32_SFloat||target.sRGB||target.useDynamicScale)
   throw new InvalidOperationException("32 exact non-MSAA, non-scaled, linear RGBAFloat colour target required");
  return ConsumerReads32.ColourBytes(x,y,width,height,target.width,target.height);
 }
}
}
