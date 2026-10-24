using System;
using System.IO;
using System.Collections.Generic;
using System.Globalization;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEditor;
public static class Counter587 {
 static string F(float v)=>v.ToString("R",CultureInfo.InvariantCulture);
 public static void Run(){
  const string root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/EyeArea587/";
  if(EditorApplication.isPlaying||File.Exists(root+"COUNTERS587.tsv"))throw new Exception("Clean Edit and unused counter output required");
  var source=AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/EyeFeature348.compute");
  var cs=UnityEngine.Object.Instantiate(source);var mat=new Material(Shader.Find("EValidation/EyeSurface348")){hideFlags=HideFlags.DontSave};
  var mesh=new UnityEngine.Mesh();var rt=new RenderTexture(512,512,32,RenderTextureFormat.ARGBFloat,RenderTextureReadWrite.Linear);var empty=new RenderTexture(512,512,0,RenderTextureFormat.ARGBFloat,RenderTextureReadWrite.Linear);var hair=new Texture2D(4,4,TextureFormat.RGBAFloat,false,true);
  ComputeBuffer partial=null,area=null;CommandBuffer cmd=null;
  string[] globals={"_AreaCentre587","_AreaAxisX587","_AreaAxisY587","_AreaUpper587"};var old=new Vector4[4];for(int i=0;i<4;i++)old[i]=Shader.GetGlobalVector(globals[i]);float oldDensity=Shader.GetGlobalFloat("_AreaDensity587");
  try {
   rt.Create();empty.Create();mat.SetTexture("_MainTex",Texture2D.whiteTexture);mat.SetColor("_Color",Color.white);mat.SetFloat("_M_CullMode",0);mat.DisableKeyword("_ALPHATEST_ON");mat.DisableKeyword("_ALPHABLEND_ON");mat.EnableKeyword("EYE_AREA_587");
   mesh.vertices=new Vector3[4];mesh.uv=new[]{Vector2.zero,Vector2.zero,Vector2.zero,Vector2.zero};mesh.normals=new[]{Vector3.forward,Vector3.forward,Vector3.forward,Vector3.forward};
   var rest=new List<Vector3>{new Vector3(-1.08f,1.5f,0),new Vector3(-1.08f,-.5f,0),new Vector3(1.08f,-.5f,0),new Vector3(1.08f,1.5f,0)};
   mesh.vertices=new Vector3[4];mesh.SetUVs(1,rest);mesh.SetUVs(7,new List<Vector2>{new Vector2(2,0),new Vector2(2,0),new Vector2(2,0),new Vector2(2,0)});mesh.triangles=new[]{0,1,2,0,2,3};
   partial=new ComputeBuffer(1024,16);area=new ComputeBuffer(2,16);int integrate=cs.FindKernel("IntegrateArea587"),finish=cs.FindKernel("FinalizeArea587");
   cmd=new CommandBuffer{name="587 analytic-plane input counterexamples"};cmd.SetRenderTarget(empty);cmd.ClearRenderTarget(false,true,Color.clear);Graphics.ExecuteCommandBuffer(cmd);cmd.Clear();
   var targets=new List<float>{.49f,.499f,.5f,.501f,.51f,.65f,.55f,.45f,.35f,.51f,0};
   for(int i=0;i<16;i++)targets.Add(.45f);
   using(var writer=new StreamWriter(root+"COUNTERS587.tsv")) {
    writer.WriteLine("case\ttargetArea\tshiftX\tshiftY\tfullyOccluded\tGPUArea\terrorEstimate\tbudget\tthresholdSeparated\tabsoluteError");
    for(int test=0;test<targets.Count;test++) {
     float target=targets[test],s=Mathf.Sqrt(target/(2.16f*.58f)),sx=test>=11?(test-11)/16f:0,sy=test>=11?((test-11)*7%16)/16f:0;bool blocked=test==9;
     var positions=new Vector3[4];for(int i=0;i<4;i++)positions[i]=new Vector3(1.5f+sx+rest[i].x*s,1.5f+sy-rest[i].y*s,-6);
     mesh.vertices=positions;mesh.RecalculateBounds();var hc=new Color[16];for(int i=0;i<16;i++)hc[i]=blocked?new Color(.5f,12,0,1):Color.clear;hair.SetPixels(hc);hair.Apply();
     cmd.Clear();cmd.SetRenderTarget(rt);cmd.ClearRenderTarget(true,true,Color.clear);cmd.SetViewport(new Rect(0,0,512,512));cmd.SetViewProjectionMatrices(Matrix4x4.identity,Matrix4x4.Ortho(0,4,0,4,.1f,10));
     cmd.SetGlobalFloat("_AreaDensity587",128);cmd.SetGlobalVector("_AreaCentre587",new Vector4(0,0,0,2));cmd.SetGlobalVector("_AreaAxisX587",new Vector4(1,0,0,1));cmd.SetGlobalVector("_AreaAxisY587",new Vector4(0,1,0,1));cmd.SetGlobalVector("_AreaUpper587",new Vector4(-.82f,.35f,0,0));cmd.DrawMesh(mesh,Matrix4x4.identity,mat);
     cmd.SetComputeVectorArrayParam(cs,"_Centres348",new[]{new Vector4(0,0,0,2),new Vector4(0,0,0,1)});cmd.SetComputeIntParam(cs,"_UseHairRegion502",1);cmd.SetComputeIntParam(cs,"_AreaDensity587",128);cmd.SetComputeIntParam(cs,"_AreaEyeIndex587",0);cmd.SetComputeIntParams(cs,"_AreaBox587",0,0,4,4);
     for(int layer=0;layer<7;layer++)cmd.SetComputeTextureParam(cs,integrate,"_A"+layer+"_587",layer==0?rt:empty);cmd.SetComputeTextureParam(cs,integrate,"_HairMETA",hair);cmd.SetComputeBufferParam(cs,integrate,"_AreaPartials587",partial);cmd.SetComputeBufferParam(cs,finish,"_AreaPartials587",partial);cmd.SetComputeBufferParam(cs,finish,"_LashArea587",area);cmd.DispatchCompute(cs,integrate,1024,1,1);cmd.DispatchCompute(cs,finish,1,1,1);Graphics.ExecuteCommandBuffer(cmd);
     var values=new Vector4[2];area.GetData(values);var a=values[0];float expected=blocked?0:target;
     writer.WriteLine(test+"\t"+F(target)+"\t"+F(sx)+"\t"+F(sy)+"\t"+blocked+"\t"+F(a.x)+"\t"+F(a.y)+"\t"+Mathf.FloorToInt(a.x+.5f)+"\t"+(Mathf.Abs(a.x-.5f)>a.y)+"\t"+F(Mathf.Abs(a.x-expected)));writer.Flush();
    }
   }
   foreach(var m in ShaderUtil.GetComputeShaderMessages(cs))if(m.severity.ToString()=="Error")throw new Exception(m.message);
   File.WriteAllText(root+"COUNTER_COMPLETE587.json","{\"cases\":"+targets.Count+",\"geometry\":\"two-triangle plane with exact parabolic band2.16*0.58*s*s; original shader area variant and production reduction\",\"originalRenderBuffersTouched\":false,\"readback\":\"test only\"}");
  } finally {
   for(int i=0;i<4;i++)Shader.SetGlobalVector(globals[i],old[i]);Shader.SetGlobalFloat("_AreaDensity587",oldDensity);cmd?.Release();partial?.Release();area?.Release();rt.Release();empty.Release();UnityEngine.Object.DestroyImmediate(rt);UnityEngine.Object.DestroyImmediate(empty);UnityEngine.Object.DestroyImmediate(hair);UnityEngine.Object.DestroyImmediate(mesh);UnityEngine.Object.DestroyImmediate(mat);UnityEngine.Object.DestroyImmediate(cs);
  }
 }
}
