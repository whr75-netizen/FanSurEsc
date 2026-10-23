using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using FantasySurvival.WorldLighting;

// Existing actual-Walk capture lifecycle; three matched renders per observed pose.
public static class VerifiedWalk544
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
 sealed class Snapshot{public Color[] colour,meta,uv,world;public Color32[] screen;public bool[][] masks;public Stage stage;}
 static Snapshot Render(int frame,string mode,bool compact)
 {
  ClothRegion524.Enabled=true;ClothRegion524.PartBits540=14;ClosedRegion524.UseSpatialIndex526=true;ClothRegion524.UseOpacityCurves527=true;ClothRegion524.UseAreaCurves532=false;ClothRegion524.UseWholeRegions539=true;ClothRegion524.UseSpans543=true;ClothRegion524.UseCompact544=compact;
  double start=EditorApplication.timeSinceStartup;h.RenderFrame();double elapsed=(EditorApplication.timeSinceStartup-start)*1000;
  if(!ClothRegion524.Ready(f))throw new Exception(ClothRegion524.Status);
  var stage=new Stage{mode=mode,bits=14,renderMs=elapsed,geometryMs=ClothRegion524.GeometryMs,areaMs=ClothRegion524.AreaMs,selectionMs=ClothRegion524.SelectionMs,uploadMs=ClothRegion524.UploadMs,packetMs=ClothSurface525.BuildMs};
  File.WriteAllText(root+frame.ToString("D3")+"_"+mode+"_stage.json",JsonUtility.ToJson(stage,true));
  var snap=new Snapshot{stage=stage,colour=Read(f.colour.rt),meta=Read(f.resolvedMeta.rt),uv=Read(f.resolvedUV.rt),world=Read(g.player.output.rt),masks=ClothRegion524.Parts540.Select(p=>p.selected==null?null:(bool[])p.selected.Clone()).ToArray()};
  snap.screen=Screen(snap.world);
  if(frame==65){var png=new Texture2D(960,544,TextureFormat.RGBA32,false);try{png.SetPixels(snap.world.Select(c=>new Color(Mathf.LinearToGammaSpace(c.r),Mathf.LinearToGammaSpace(c.g),Mathf.LinearToGammaSpace(c.b),1)).ToArray());png.Apply();File.WriteAllBytes(root+"065_"+mode+".png",png.EncodeToPNG());}finally{UnityEngine.Object.Destroy(png);}}
  return snap;
 }
 static int Different(Color[] a,Color[] b){int n=0;for(int i=0;i<a.Length;i++)if(a[i].r!=b[i].r||a[i].g!=b[i].g||a[i].b!=b[i].b||a[i].a!=b[i].a)n++;return n;}
 static Color32[] Screen(Color[] world){var tex=new Texture2D(960,544,TextureFormat.RGBA32,false);try{tex.SetPixels(world.Select(c=>new Color(Mathf.LinearToGammaSpace(c.r),Mathf.LinearToGammaSpace(c.g),Mathf.LinearToGammaSpace(c.b),1)).ToArray());tex.Apply();return tex.GetPixels32();}finally{UnityEngine.Object.Destroy(tex);}}
 static bool Eq(Color a,Color b)=>a.r==b.r&&a.g==b.g&&a.b==b.b&&a.a==b.a;
 static int Novel(Color[] a,Color[] b,Color[] candidate){int n=0;for(int i=0;i<a.Length;i++)if(!Eq(candidate[i],a[i])&&!Eq(candidate[i],b[i]))n++;return n;}
 static int ScreenDiff(Color32[] a,Color32[] b){int n=0;for(int i=0;i<a.Length;i++)if(a[i].r!=b[i].r||a[i].g!=b[i].g||a[i].b!=b[i].b||a[i].a!=b[i].a)n++;return n;}
 static void Capture()
 {
  try
  {
   int frame=first+count;var state=a.GetCurrentAnimatorStateInfo(0);string clip=a.GetCurrentAnimatorClipInfo(0)[0].clip.name;if(clip!="Rig|Walk_Loop")throw new Exception("Wrong clip "+clip);
   if(count==0)for(int k=0;k<3;k++){ClothRegion524.Enabled=true;ClothRegion524.PartBits540=14;ClothRegion524.UseOpacityCurves527=ClothRegion524.UseWholeRegions539=ClothRegion524.UseSpans543=true;ClothRegion524.UseAreaCurves532=false;ClothRegion524.UseCompact544=false;h.RenderFrame();ClothRegion524.UseCompact544=true;h.RenderFrame();}
   var control=Render(frame,"SELF_CONTROL",false);Snapshot reference,compact;if(count%2==0){reference=Render(frame,"REFERENCE",false);compact=Render(frame,"COMPACT",true);}else{compact=Render(frame,"COMPACT",true);reference=Render(frame,"REFERENCE",false);}
   int rgba=Different(reference.colour,compact.colour),meta=Different(reference.meta,compact.meta),uv=Different(reference.uv,compact.uv),world=Different(reference.world,compact.world),mask=0;
   for(int p=1;p<4;p++)for(int i=0;i<reference.masks[p].Length;i++)if(reference.masks[p][i]!=compact.masks[p][i])mask++;
   int screenSelf=ScreenDiff(control.screen,reference.screen),screenOpt=ScreenDiff(reference.screen,compact.screen),novelRGBA=Novel(control.colour,reference.colour,compact.colour),novelUV=Novel(control.uv,reference.uv,compact.uv),novelWorld=Novel(control.world,reference.world,compact.world);
   File.AppendAllText(root+"equivalence.csv",frame+","+rgba+","+meta+","+uv+","+world+","+mask+","+Different(control.colour,reference.colour)+","+Different(control.uv,reference.uv)+","+Different(control.world,reference.world)+","+screenSelf+","+screenOpt+","+novelRGBA+","+novelUV+","+novelWorld+"\n");
   File.WriteAllText(root+frame.ToString("D3")+"_pose.json","{\"frame\":"+frame+",\"phase\":"+Mathf.Repeat(state.normalizedTime,1).ToString("R",System.Globalization.CultureInfo.InvariantCulture)+",\"skyHour\":"+sky.CurrentHour.ToString("R",System.Globalization.CultureInfo.InvariantCulture)+"}");
   if(meta+mask+screenSelf+screenOpt+novelRGBA+novelUV+novelWorld!=0)throw new Exception("544 corrected exact observable gate failed frame "+frame);
   ClothRegion524.Enabled=ClothRegion524.UseSpans543=ClothRegion524.UseCompact544=false;h.RenderFrame();count++;File.WriteAllText(root+"progress.json","{\"poses\":"+count+",\"target\":"+(last-first+1)+"}");
   if(count==last-first+1){End("CAPTURED");return;}queued=false;f.validateRender=OnFinal;EditorApplication.isPaused=false;
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
  File.WriteAllText(root+"equivalence.csv","frame,rgba,meta,uv,world,mask,selfRGBA,selfUV,selfWorld,screenSelf,screenOpt,novelRGBA,novelUV,novelWorld\n");File.WriteAllText(root+"face_before.txt",FaceState524.Snapshot(h));sky.SetAutomaticAdvance(false);move.enabled=false;a.enabled=true;a.speed=1;a.SetFloat("LocomotionSpeed",1);a.transform.rotation=Quaternion.Euler(0,80,0);a.Play(oldState,0,1f+(from-1)/80f+.00000248f);a.Update(0);Time.captureDeltaTime=1f/60;Application.runInBackground=true;count=0;queued=false;deadline=EditorApplication.timeSinceStartup+900;f.validateRender=OnFinal;EditorApplication.update+=Tick;
  File.WriteAllText(root+"status.json","{\"status\":\"STARTED\",\"first\":"+first+",\"last\":"+last+"}");
 }
}
