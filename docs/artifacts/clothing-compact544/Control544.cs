using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using FantasySurvival.WorldLighting;

// Existing actual-Walk capture lifecycle; three matched renders per observed pose.
public static class Control544
{
 static string root;static int first,last,count;static bool queued,includeBody;static double deadline;
 static Gameplay397 g;static HeadLocal367 h;static Full319View335 f;static Animator a;static PlayerMovement move;static SkyLightingCycleController sky;static Action prior;
 static bool oldShape,oldCompact;
 static bool oldMove,oldAnim,oldAuto,oldBg,oldPaused,oldIndex,oldOpacity,oldArea,oldWhole;static int oldBits,oldState;static float oldLoc,oldSpeed,oldCapture,oldTime;static Quaternion oldRotation;
 [Serializable]class Startup{public bool oldBackground;}
 [Serializable]class PartAudit{public int part,sourcePoints,controlPoints,selected,outside,returns;public double preprocessMs;}
 [Serializable]class Stage{public string mode;public int bits,requested,packets,unsupported;public double renderMs,geometryMs,areaMs,selectionMs,uploadMs,packetMs;public int missing,gate,invalidOwner;public List<PartAudit>parts=new();}
 [Serializable]class Pose{public int frame;public float phase,skyHour;public string clip;public List<Stage>stages=new();}
 static Color[] Read(RenderTexture rt)
 {
  var previous=RenderTexture.active;Texture2D t=null;try{RenderTexture.active=rt;t=new Texture2D(rt.width,rt.height,TextureFormat.RGBAFloat,false,true);t.ReadPixels(new Rect(0,0,rt.width,rt.height),0,0,false);t.Apply(false,false);return t.GetPixels();}finally{RenderTexture.active=previous;if(t)UnityEngine.Object.Destroy(t);}
 }
 static void Crop(string path,Color[] values,RectInt b)
 {using(var w=new BinaryWriter(File.Create(path))){w.Write(b.width);w.Write(b.height);w.Write(b.x);w.Write(b.y);for(int y=b.y;y<b.yMax;y++)for(int x=b.x;x<b.xMax;x++){var c=values[(271-y)*480+x];w.Write(c.r);w.Write(c.g);w.Write(c.b);w.Write(c.a);}}}
 sealed class Snapshot{public Color[] colour,meta,uv,world;public bool[][] masks;public Stage stage;}
 static Snapshot Render(int frame,string mode,bool compact)
 {
  ClothRegion524.Enabled=true;ClothRegion524.PartBits540=14;ClosedRegion524.UseSpatialIndex526=true;ClothRegion524.UseOpacityCurves527=true;ClothRegion524.UseAreaCurves532=false;ClothRegion524.UseWholeRegions539=true;ClothRegion524.UseSpans543=true;ClothRegion524.UseCompact544=compact;
  double start=EditorApplication.timeSinceStartup;h.RenderFrame();double elapsed=(EditorApplication.timeSinceStartup-start)*1000;
  if(!ClothRegion524.Ready(f))throw new Exception(ClothRegion524.Status);
  var stage=new Stage{mode=mode,bits=14,renderMs=elapsed,geometryMs=ClothRegion524.GeometryMs,areaMs=ClothRegion524.AreaMs,selectionMs=ClothRegion524.SelectionMs,uploadMs=ClothRegion524.UploadMs,packetMs=ClothSurface525.BuildMs};
  File.WriteAllText(root+frame.ToString("D3")+"_"+mode+"_stage.json",JsonUtility.ToJson(stage,true));
  var snap=new Snapshot{stage=stage,colour=Read(f.colour.rt),meta=Read(f.resolvedMeta.rt),uv=Read(f.resolvedUV.rt),world=Read(g.player.output.rt),masks=ClothRegion524.Parts540.Select(p=>p.selected==null?null:(bool[])p.selected.Clone()).ToArray()};
  if(frame==2){var png=new Texture2D(960,544,TextureFormat.RGBA32,false);try{png.SetPixels(snap.world.Select(c=>new Color(Mathf.LinearToGammaSpace(c.r),Mathf.LinearToGammaSpace(c.g),Mathf.LinearToGammaSpace(c.b),1)).ToArray());png.Apply();File.WriteAllBytes(root+"065_"+mode+".png",png.EncodeToPNG());}finally{UnityEngine.Object.Destroy(png);}}
  return snap;
 }
 static int Different(Color[] a,Color[] b){int n=0;for(int i=0;i<a.Length;i++)if(a[i].r!=b[i].r||a[i].g!=b[i].g||a[i].b!=b[i].b||a[i].a!=b[i].a)n++;return n;}
 static void Dump(int frame,string mode,Snapshot s)
 {
  foreach(var pair in new[]{new{key="COLOUR",values=s.colour,w=480,h=272},new{key="META",values=s.meta,w=480,h=272},new{key="UV",values=s.uv,w=480,h=272},new{key="WORLD",values=s.world,w=960,h=544}})
   using(var b=new BinaryWriter(File.Create(root+mode+"_"+pair.key+".bin"))){b.Write(pair.w);b.Write(pair.h);foreach(var c in pair.values){b.Write(c.r);b.Write(c.g);b.Write(c.b);b.Write(c.a);}}
  using(var b=new BinaryWriter(File.Create(root+mode+"_INPUT.bin")))
  {var outputs=f.motion.surface.outputs;b.Write(outputs.Length);foreach(var mf in outputs){var mesh=mf.sharedMesh;var verts=mesh.vertices;var normals=mesh.normals;var uv=mesh.uv;b.Write(verts.Length);for(int i=0;i<verts.Length;i++){var p=mf.transform.TransformPoint(verts[i]);b.Write(p.x);b.Write(p.y);b.Write(p.z);b.Write(normals[i].x);b.Write(normals[i].y);b.Write(normals[i].z);b.Write(uv[i].x);b.Write(uv[i].y);}}var cam=f.motion.camera;for(int i=0;i<16;i++){b.Write(cam.worldToCameraMatrix[i]);b.Write(cam.projectionMatrix[i]);}}
  var time=Shader.GetGlobalVector("_Time");File.WriteAllText(root+mode+"_time.txt","frame="+Time.frameCount+" time="+Time.time+" unscaled="+Time.unscaledTime+" shaderTime="+time+" sky="+sky.CurrentHour);
 }
 static void Capture()
 {
  try
  {
   int frame=first+count;var state=a.GetCurrentAnimatorStateInfo(0);if(a.GetCurrentAnimatorClipInfo(0)[0].clip.name!="Rig|Walk_Loop")throw new Exception("Wrong clip");
   if(count==0)for(int k=0;k<3;k++){ClothRegion524.Enabled=true;ClothRegion524.PartBits540=14;ClothRegion524.UseOpacityCurves527=ClothRegion524.UseWholeRegions539=ClothRegion524.UseSpans543=true;ClothRegion524.UseAreaCurves532=false;ClothRegion524.UseCompact544=false;h.RenderFrame();ClothRegion524.UseCompact544=true;h.RenderFrame();}
   if(frame<2){Render(frame,"PREFIX_REF",false);Render(frame,"PREFIX_OPT",true);}
   else
   {
    var aa=Render(frame,"REF_A",false);Dump(frame,"REF_A",aa);var bb=Render(frame,"REF_B",false);Dump(frame,"REF_B",bb);var cc=Render(frame,"OPT",true);Dump(frame,"OPT",cc);var dd=Render(frame,"REF_C",false);Dump(frame,"REF_C",dd);
    var snapshots=new[]{aa,bb,cc,dd};var labels=new[]{"REF_A","REF_B","OPT","REF_C"};for(int i=1;i<4;i++)File.AppendAllText(root+"control.csv",labels[0]+","+labels[i]+","+Different(aa.colour,snapshots[i].colour)+","+Different(aa.meta,snapshots[i].meta)+","+Different(aa.uv,snapshots[i].uv)+","+Different(aa.world,snapshots[i].world)+"\n");
   }
   ClothRegion524.Enabled=ClothRegion524.UseSpans543=ClothRegion524.UseCompact544=false;h.RenderFrame();count++;if(count==last-first+1){End("CAPTURED");return;}queued=false;f.validateRender=OnFinal;EditorApplication.isPaused=false;
  }catch(Exception e){End("FAILED",e.ToString());}
 }
 static void OnFinal(){prior?.Invoke();if(!f.contourReady||queued)return;queued=true;f.validateRender=prior;EditorApplication.isPaused=true;EditorApplication.delayCall+=Capture;}
 static void Tick(){if(!EditorApplication.isPlaying||EditorApplication.timeSinceStartup>deadline){End("FAILED","Play ended or capture deadline");return;}EditorApplication.QueuePlayerLoopUpdate();}
 static void End(string status,string error="")
 {
  ClothRegion524.Enabled=false;ClothRegion524.UseSpans543=oldShape;ClothRegion524.UseCompact544=oldCompact;ClothRegion524.UseOpacityCurves527=oldOpacity;ClothRegion524.UseAreaCurves532=oldArea;ClothRegion524.UseWholeRegions539=oldWhole;ClothRegion524.PartBits540=oldBits;ClosedRegion524.UseSpatialIndex526=oldIndex;Shader.SetGlobalInt("_Cloth524Enabled",0);
  if(f)f.validateRender=prior;if(sky)sky.SetAutomaticAdvance(oldAuto);if(a){a.transform.rotation=oldRotation;a.SetFloat("LocomotionSpeed",oldLoc);a.speed=oldSpeed;a.Play(oldState,0,oldTime);a.Update(0);a.enabled=oldAnim;}if(move)move.enabled=oldMove;Time.captureDeltaTime=oldCapture;Application.runInBackground=oldBg;EditorApplication.update-=Tick;EditorApplication.delayCall-=Capture;EditorApplication.isPaused=oldPaused;
  if(h)File.WriteAllText(root+"face_after.txt",FaceState524.Snapshot(h));
  File.WriteAllText(root+"status.json","{\"status\":\""+status+"\",\"error\":\""+error.Replace("\\","/").Replace("\"","'").Replace("\r"," ").Replace("\n"," ")+"\",\"poses\":"+count+",\"inputRestored\":"+(move&&move.enabled==oldMove?"true":"false")+",\"animatorRestored\":"+(a&&a.enabled==oldAnim&&a.speed==oldSpeed?"true":"false")+",\"clockRestored\":"+(sky&&sky.IsAdvancingAutomatically==oldAuto?"true":"false")+"}");if(EditorApplication.isPlaying)EditorApplication.isPlaying=false;
 }
 public static void Start(int from,int to,string output,string startup,bool testBody=true)
 {
  if(!EditorApplication.isPlaying||EditorApplication.isPaused||ClothRegion524.Enabled)throw new Exception("Ready Play / product OFF required");g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();if(!g||!g.connected)throw new Exception("Runtime not ready");h=g.player.host;f=h.main;a=f.motion.animation.target;move=g.player.player.GetComponent<PlayerMovement>();sky=UnityEngine.Object.FindFirstObjectByType<SkyLightingCycleController>();
  if(HeadRegion502.Enabled||h.post.candidateEnabled)throw new Exception("Other trial enabled");prior=f.validateRender;if(prior!=null&&prior.GetInvocationList().Any(x=>!(x.Target is PostView366)))throw new Exception("Other capture hook active");if(Directory.Exists(output))throw new Exception("Output exists; no duplicate capture");
  root=output;first=from;last=to;includeBody=testBody;Directory.CreateDirectory(root);oldShape=ClothRegion524.UseSpans543;oldCompact=ClothRegion524.UseCompact544;oldMove=move.enabled;oldAnim=a.enabled;oldAuto=sky.IsAdvancingAutomatically;oldBg=Application.runInBackground;if(File.Exists(startup))oldBg=JsonUtility.FromJson<Startup>(File.ReadAllText(startup)).oldBackground;oldPaused=EditorApplication.isPaused;oldIndex=ClosedRegion524.UseSpatialIndex526;oldOpacity=ClothRegion524.UseOpacityCurves527;oldArea=ClothRegion524.UseAreaCurves532;oldWhole=ClothRegion524.UseWholeRegions539;oldBits=ClothRegion524.PartBits540;oldLoc=a.GetFloat("LocomotionSpeed");oldSpeed=a.speed;oldCapture=Time.captureDeltaTime;oldRotation=a.transform.rotation;var state=a.GetCurrentAnimatorStateInfo(0);oldState=state.fullPathHash;oldTime=state.normalizedTime;
  File.WriteAllText(root+"control.csv","a,b,rgba,meta,uv,world\n");File.WriteAllText(root+"face_before.txt",FaceState524.Snapshot(h));sky.SetAutomaticAdvance(false);move.enabled=false;a.enabled=true;a.speed=1;a.SetFloat("LocomotionSpeed",1);a.transform.rotation=Quaternion.Euler(0,80,0);a.Play(oldState,0,1f+(from-1)/80f+.00000248f);a.Update(0);Time.captureDeltaTime=1f/60;Application.runInBackground=true;count=0;queued=false;deadline=EditorApplication.timeSinceStartup+900;f.validateRender=OnFinal;EditorApplication.update+=Tick;
  File.WriteAllText(root+"status.json","{\"status\":\"STARTED\",\"first\":"+first+",\"last\":"+last+"}");
 }
}
