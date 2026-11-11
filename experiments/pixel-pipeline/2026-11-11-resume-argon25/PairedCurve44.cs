using System;using UnityEngine;using UnityEditor;using UnityEngine.Rendering;using UnityEngine.Rendering.RenderGraphModule;
namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {
public sealed partial class SourceOutline40 {
 Material legacyPoint44;
 void InitLegacy44(){var shader=AssetDatabase.LoadAssetAtPath<Shader>("Assets/EUnityValidation01/SourceBoundary40Authored/GeoContour40Authored.shader");if(!shader||!shader.isSupported)throw new InvalidOperationException("44 legacy comparison shader missing");legacyPoint44=new Material(shader){hideFlags=HideFlags.DontSave};}
 void ReleaseLegacy44(){if(legacyPoint44)UnityEngine.Object.DestroyImmediate(legacyPoint44);}
 void DrawLegacy44(UnsafeGraphContext context){
  var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);var p=new MaterialPropertyBlock();p.SetMatrix("_ProbeGPUVP29",qvp);p.SetMatrix("_ProbeView29",view);cmd.SetRenderTarget(new[]{new RenderTargetIdentifier(Fields[15].rt),new RenderTargetIdentifier(Fields[16].rt)},styleDepth39.rt);cmd.SetViewport(new Rect(0,0,QROI.width,QROI.height));cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1,0);for(int r=0;r<meshes.Length;r++)for(int sm=0;sm<depthMats[r].Length;sm++)cmd.DrawMesh(meshes[r],matrices[r],depthMats[r][sm],sm,0,p);
  p.SetMatrix("_ContourVP40",qvp);p.SetMatrix("_ContourView40",view);p.SetVector("_ContourRGB40",sourceInk);p.SetTexture("_WidthMap40",sourceWidth40);p.SetFloat("_WidthMapEnabled40",widthMap40?1:0);cmd.DrawMesh(contourMesh40,Matrix4x4.identity,legacyPoint44,0,0,p);
 }
}
}
