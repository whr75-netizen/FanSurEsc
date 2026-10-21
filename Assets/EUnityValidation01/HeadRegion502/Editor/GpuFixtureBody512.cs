using System;using System.IO;using System.Linq;using System.Collections.Generic;using UnityEngine;
// Independent temporary textures and a cloned shader; no scene/runtime buffers touched.
public static class GpuFixtureBody512
{
 const int W=480,H=272,Y=20;
 static readonly List<UnityEngine.Object> owned=new();
 static Texture2D Tex(int w,int h,Color[] data){var t=new Texture2D(w,h,TextureFormat.RGBAFloat,false,true){filterMode=FilterMode.Point};owned.Add(t);t.SetPixels(data);t.Apply(false,false);return t;}
 static RenderTexture RT(int w,int h){var t=new RenderTexture(w,h,0,RenderTextureFormat.ARGBFloat,RenderTextureReadWrite.Linear){enableRandomWrite=true,filterMode=FilterMode.Point};t.Create();owned.Add(t);return t;}
 static void At(Color[] a,int x,Color c){a[(H-1-Y)*W+x]=c;}
 static Color[] Read(RenderTexture rt){var before=RenderTexture.active;try{RenderTexture.active=rt;var t=new Texture2D(W,H,TextureFormat.RGBAFloat,false,true);owned.Add(t);t.ReadPixels(new Rect(0,0,W,H),0,0,false);t.Apply(false,false);return t.GetPixels();}finally{RenderTexture.active=before;}}
 public static void Run(ComputeShader original)
 {
  const string report="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/JOIN_FIXTURE512.json";
  if(File.Exists(report))throw new Exception("Preserve existing512 GPU fixture; do not duplicate capture");
  var prior=RenderTexture.active;try
  {
   var shader=UnityEngine.Object.Instantiate(original);owned.Add(shader);int k=shader.FindKernel("JoinBare");
   var colour=new Color[W*H];var owner=new Color[W*H];var meta=new Color[W*H];var reference=new Color[W*H];
   float[]depth={.5f,1.5f,0,1.5f,1.5f,.99995f};int[]kind={1,1,3,1,0,1};int[]expected={8,14,14,8,8,14};string[]names={"opaque-front","opaque-behind","no-body","face-excluded","missing-reference","unchanged-epsilon"};
   for(int i=0;i<depth.Length;i++){At(colour,20+i,new Color(1,0,0,1));At(owner,20+i,new Color(i==3?4:14,i==3?6:7,1,0));At(meta,20+i,new Color(1,i==3?4:14,0,123));At(reference,20+i,new Color(1,1,depth[i],kind[i]));}
   var zero=Tex(W,H,new Color[W*H]);shader.SetTexture(k,"_HColour",Tex(W,H,colour));shader.SetTexture(k,"_HOwner",Tex(W,H,owner));shader.SetTexture(k,"_HMeta",Tex(W,H,meta));shader.SetTexture(k,"_HUV",zero);shader.SetTexture(k,"_HPalette",Tex(W*2,H*2,new Color[W*H*4]));shader.SetTexture(k,"_BodyRay512",Tex(W,H,reference));
   var body=Tex(1,1,new[]{new Color(8,1,.5f,0)});var farBody=Tex(1,1,new[]{new Color(8,1,1.5f,0)});var blue=Tex(1,1,new[]{new Color(0,0,1,1)});var resultOwner=RT(W,H);var resultColour=RT(W,H);
   shader.SetTexture(k,"_MOwner",resultOwner);shader.SetTexture(k,"_MColour",resultColour);
   foreach(string name in new[]{"_MBefore","_MMeta","_MUV","_MDomain"})shader.SetTexture(k,name,RT(W,H));foreach(string name in new[]{"_MSurface","_MPalette"})shader.SetTexture(k,name,RT(W*2,H*2));
   shader.SetInts("_Offset365",0,0);shader.SetFloat("_DepthOffset365",0);
   int[] enabled=new int[depth.Length],farEnabled=new int[depth.Length],disabled=new int[depth.Length];int[]expectedFar={8,14,14,4,8,14};
   for(int pass=0;pass<3;pass++){Graphics.Blit(pass==1?farBody:body,resultOwner);Graphics.Blit(blue,resultColour);shader.SetInt("_BodyRay512Enabled",pass<2?1:0);shader.Dispatch(k,60,34,1);var v=Read(resultOwner);for(int i=0;i<depth.Length;i++)(pass==0?enabled:pass==1?farEnabled:disabled)[i]=Mathf.RoundToInt(v[(H-1-Y)*W+20+i].r);}
   bool ok=expected.SequenceEqual(enabled)&&expectedFar.SequenceEqual(farEnabled)&&disabled.All(x=>x==8);File.WriteAllText(report,"{\"passed\":"+(ok?"true":"false")+",\"names\":["+string.Join(",",names.Select(x=>"\""+x+"\""))+"],\"expectedEnabled\":["+string.Join(",",expected)+"],\"observedEnabled\":["+string.Join(",",enabled)+"],\"expectedFarEnabled\":["+string.Join(",",expectedFar)+"],\"observedFarEnabled\":["+string.Join(",",farEnabled)+"],\"observedDefaultOff\":["+string.Join(",",disabled)+"],\"runtimeBuffersUntouched\":true}");if(!ok)throw new Exception("512 GPU join fixture failed; inspect saved report");
  }
  finally{RenderTexture.active=prior;foreach(var o in owned){if(o is RenderTexture r)r.Release();UnityEngine.Object.DestroyImmediate(o);}owned.Clear();}
 }
}
