using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;
public static class TraceInputs541
{
 static Color[] Read(RenderTexture rt){var old=RenderTexture.active;Texture2D t=null;try{RenderTexture.active=rt;t=new Texture2D(rt.width,rt.height,TextureFormat.RGBAFloat,false,true);t.ReadPixels(new Rect(0,0,rt.width,rt.height),0,0,false);t.Apply(false,false);return t.GetPixels();}finally{RenderTexture.active=old;if(t)UnityEngine.Object.DestroyImmediate(t);}}
 static void Crop(string path,RenderTexture rt,RectInt r)
 {
  var data=Read(rt);using(var w=new BinaryWriter(File.Create(path+".bin"))){w.Write(r.width);w.Write(r.height);w.Write(r.x);w.Write(r.y);for(int y=r.y;y<r.yMax;y++)for(int x=r.x;x<r.xMax;x++){var c=data[(rt.height-1-y)*rt.width+x];w.Write(c.r);w.Write(c.g);w.Write(c.b);w.Write(c.a);}}
 }
 static RenderTexture New(int scale){var r=new RenderTexture(480*scale,272*scale,0){graphicsFormat=UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite=true,filterMode=FilterMode.Point,hideFlags=HideFlags.DontSave};r.Create();return r;}
 static void Replay(string path,Full319View335 f,RectInt bounds)
 {
  var cs=f.prepare;int k=cs.FindKernel("Prepare");var cmd=new CommandBuffer{name="541 isolated exact Prepare replay"};var outputs=new[]{f.before,f.colour,f.owner,f.audit,f.gridSurface,f.gridPalette,f.preparedUV,f.preparedMeta};var names=new[]{"_Before","_Colour","_Owner","_Audit","_GridSurface","_GridPalette","_PreparedUV","_PreparedMeta"};var targets=Enumerable.Range(0,8).Select(i=>New(i==4||i==5?2:1)).ToArray();
  try
  {
   void T(string n,Texture t)=>cmd.SetComputeTextureParam(cs,k,n,t);
   ClothRegion524.Bind(cmd,cs,k,f);cmd.SetComputeIntParam(cs,"_ContourMode",f.contourReady?1:0);cmd.SetComputeVectorParam(cs,"_Profile",f.motion.animation.shadeProfile);
   T("_Map",f.actionMap);T("_Physical",f.native[3].rt);T("_CentreRaw",f.motion.raw[0].rt);T("_CentrePhysical",f.motion.raw[3].rt);T("_CentreOriginal",f.motion.raw[4].rt);T("_CentreMeta",f.motion.raw[5].rt);T("_CentreUV",f.motion.raw[6].rt);T("_CentreSurface",f.centreMeta[0].rt);T("_CentrePalette",f.centreFamily.rt);T("_Surface",f.meta[0].rt);T("_Palette",f.family.rt);T("_NativeInput",f.colourNative.rt);T("_RawMeta",f.native[5].rt);T("_RawUV",f.native[6].rt);
   for(int i=0;i<8;i++)T(names[i],targets[i]);cmd.DispatchCompute(cs,k,60,34,1);
   for(int i=0;i<8;i++)T(names[i],outputs[i].rt);Graphics.ExecuteCommandBuffer(cmd);
   foreach(int i in new[]{0,2,3,6,7})Crop(path+names[i],targets[i],bounds);
  }
  finally{cmd.Release();foreach(var t in targets){t.Release();UnityEngine.Object.DestroyImmediate(t);}}
 }
 public static void Capture(string prefix,HeadLocal367 h,int x,int y)
 {
  var f=h.main;var g=h.head;var main=new RectInt(x-2,y-2,5,5);var head=new RectInt(main.x-h.offset.x,main.y+h.offset.y,5,5);
  void Both(string n,RenderTexture a,RenderTexture b){Crop(prefix+"_MAIN_"+n,a,main);Crop(prefix+"_HEAD_"+n,b,head);}
  Both("CENTRE_META",f.motion.raw[5].rt,g.motion.raw[5].rt);Both("CENTRE_UV",f.motion.raw[6].rt,g.motion.raw[6].rt);Both("BARE_OWNER",f.preparedOwner.rt,g.preparedOwner.rt);Both("BARE_COLOUR",f.prepared.rt,g.prepared.rt);
  var mn=new RectInt(main.x*2,main.y*2,10,10);var hn=new RectInt(head.x*2,head.y*2,10,10);
  foreach(int i in new[]{0,3,5,6}){Crop(prefix+"_MAIN_NATIVE"+i,f.native[i].rt,mn);Crop(prefix+"_HEAD_NATIVE"+i,g.native[i].rt,hn);}Crop(prefix+"_MAIN_NATIVE_COLOUR",f.colourNative.rt,mn);Crop(prefix+"_HEAD_NATIVE_COLOUR",g.colourNative.rt,hn);
  Replay(prefix+"_MAIN_REPLAY",f,main);Replay(prefix+"_HEAD_REPLAY",g,head);
  var part=ClothRegion524.Parts540[0];int at=part.selected!=null&&part.bounds.Contains(new Vector2Int(x,y))?(y-part.bounds.y)*part.bounds.width+x-part.bounds.x:-1;
  string F(float v)=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture);
  File.WriteAllText(prefix+"_PARAMS.txt","mainXY="+x+","+y+" headXY="+(x-h.offset.x)+","+(y+h.offset.y)+" offset="+h.offset+" depthOffset="+F(h.depthOffset)+" headReady="+h.headReady+" bodyArea="+(at>=0?F(part.areas[at]):"none")+" bodySelected="+(at>=0&&part.selected[at])+" mainContour="+f.contourReady+" headContour="+g.contourReady+" mainMap="+f.actionMap.GetPixel(x,271-y).ToString("R")+" headMap="+g.actionMap.GetPixel(x-h.offset.x,271-y-h.offset.y).ToString("R")+" profile="+f.motion.animation.shadeProfile.ToString("R")+" ortho="+F(f.motion.camera.orthographicSize)+" camera="+f.motion.camera.transform.position.ToString("R")+" forward="+f.motion.camera.transform.forward.ToString("R")+" clip="+f.motion.animation.target.GetCurrentAnimatorClipInfo(0)[0].clip.name+" phase="+F(Mathf.Repeat(f.motion.animation.target.GetCurrentAnimatorStateInfo(0).normalizedTime,1)));
  if(!ClothRegion524.Active540(0))return;
  var mf=f.motion.surface.outputs[0];var mesh=mf.sharedMesh;var world=mesh.vertices.Select(mf.transform.TransformPoint).ToArray();var uv=mesh.uv;
  using(var w=new BinaryWriter(File.Create(prefix+"_BODY_GEOMETRY.bin"))){w.Write(world.Length);for(int i=0;i<world.Length;i++){var a=f.Project(world[i]);var b=g.Project(world[i]);foreach(float v in new[]{world[i].x,world[i].y,world[i].z,a.x,a.y,b.x,b.y,uv[i].x,uv[i].y})w.Write(v);}w.Write(mesh.subMeshCount);for(int sm=0;sm<mesh.subMeshCount;sm++){var ids=mesh.GetIndices(sm);w.Write(ids.Length);foreach(int v in ids)w.Write(v);var m=f.motion.materials[sm];w.Write(m.GetInt("_M_CullMode"));w.Write(m.GetInt("_AlphaMode"));w.Write(m.GetFloat("_Cutoff"));}}
 }
}
