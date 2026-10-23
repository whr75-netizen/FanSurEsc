using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using FantasySurvival.WorldLighting;

// Existing actual-Walk capture lifecycle; three matched renders per observed pose.
public static class CaptureCommon540
{
 static string root;static int first,last,count;static bool queued,includeBody;static double deadline;
 static Gameplay397 g;static HeadLocal367 h;static Full319View335 f;static Animator a;static PlayerMovement move;static SkyLightingCycleController sky;static Action prior;
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
 static Stage Render(string prefix,string mode,int bits)
 {
  ClothRegion524.Enabled=bits!=0;ClothRegion524.PartBits540=bits==0?8:bits;ClosedRegion524.UseSpatialIndex526=true;ClothRegion524.UseOpacityCurves527=bits!=0;ClothRegion524.UseAreaCurves532=false;ClothRegion524.UseWholeRegions539=bits!=0;
  double start=EditorApplication.timeSinceStartup;h.RenderFrame();var record=new Stage{mode=mode,bits=bits,renderMs=(EditorApplication.timeSinceStartup-start)*1000};
  if(bits!=0&&!ClothRegion524.Ready(f))throw new Exception(ClothRegion524.Status);
  var colour=Read(f.colour.rt);var meta=Read(f.resolvedMeta.rt);var uv=Read(f.resolvedUV.rt);int x0=480,y0=272,x1=0,y1=0;
  for(int y=0;y<272;y++)for(int x=0;x<480;x++)if(colour[(271-y)*480+x].a>.5f){x0=Math.Min(x0,x);y0=Math.Min(y0,y);x1=Math.Max(x1,x+1);y1=Math.Max(y1,y+1);}
  if(x1<=x0)throw new Exception("Actor absent");var b=new RectInt(Math.Max(0,x0-3),Math.Max(0,y0-3),Math.Min(480,x1+3)-Math.Max(0,x0-3),Math.Min(272,y1+3)-Math.Max(0,y0-3));
  Crop(root+prefix+"_FINAL.bin",colour,b);Crop(root+prefix+"_META.bin",meta,b);Crop(root+prefix+"_UV.bin",uv,b);Crop(root+prefix+"_PREPARED.bin",Read(f.prepared.rt),b);Crop(root+prefix+"_POSTLINE.bin",Read(f.postLine.rt),b);
  var world=Read(g.player.output.rt);var png=new Texture2D(960,544,TextureFormat.RGBA32,false);try{png.SetPixels(world.Select(c=>new Color(Mathf.LinearToGammaSpace(c.r),Mathf.LinearToGammaSpace(c.g),Mathf.LinearToGammaSpace(c.b),1)).ToArray());png.Apply();File.WriteAllBytes(root+prefix+".png",png.EncodeToPNG());}finally{UnityEngine.Object.Destroy(png);}
  if(bits!=0)
  {
   record.geometryMs=ClothRegion524.GeometryMs;record.areaMs=ClothRegion524.AreaMs;record.selectionMs=ClothRegion524.SelectionMs;record.uploadMs=ClothRegion524.UploadMs;record.packetMs=ClothSurface525.BuildMs;record.requested=ClothSurface525.Requested;record.packets=ClothSurface525.Packets.Count;record.unsupported=ClothSurface525.Unsupported;
   var audit=Read(ClothRegion524.Audit.rt);for(int i=0;i<audit.Length;i++){if(audit[i].a>.5)record.missing++;if(audit[i].b>.5)record.gate++;if(colour[i].a>.5&&meta[i].r<=0)record.invalidOwner++;}
   foreach(var part in ClothRegion524.Parts540)
   {
    if(!ClothRegion524.Active540(part.submesh))continue;var pr=new PartAudit{part=part.submesh,sourcePoints=part.source.Sum(r=>r.Length),controlPoints=part.curves.Sum(r=>r.Length),selected=part.selected.Count(v=>v),preprocessMs=part.opacity.PreprocessMs};
    for(int y=0;y<272;y++)for(int x=0;x<480;x++){int i=(271-y)*480+x;if(colour[i].a>.5&&Mathf.RoundToInt(meta[i].g)==8+part.submesh&&!ClothRegion524.Selected540(part.submesh,x,y))pr.outside++;}record.parts.Add(pr);
    using(var w=new BinaryWriter(File.Create(root+prefix+"_PART"+part.submesh+".bin"))){var r=part.bounds;w.Write(r.x);w.Write(r.y);w.Write(r.width);w.Write(r.height);foreach(float v in part.areas)w.Write(v);foreach(bool v in part.selected)w.Write(v);foreach(var rings in new[]{part.source,part.curves}){w.Write(rings.Length);foreach(var ring in rings){w.Write(ring.Length);foreach(var p in ring){w.Write(p.x);w.Write(p.y);}}}}
   }
   File.WriteAllText(root+prefix+"_packets.json",JsonUtility.ToJson(new PacketList{values=ClothSurface525.Packets.ToArray()},true));
  }
  File.WriteAllText(root+prefix+"_FACE.txt",FaceState524.Snapshot(h));File.WriteAllText(root+prefix+"_stage.json",JsonUtility.ToJson(record,true));
  if(bits!=0&&(record.unsupported+record.gate+record.invalidOwner+record.parts.Sum(p=>p.outside)>0))throw new Exception("540 contract failure "+prefix+": "+JsonUtility.ToJson(record));
  return record;
 }
 [Serializable]class PacketList{public ClothSurface525.Packet[]values;}
 static void Capture()
 {
  try
  {
   int frame=first+count;string prefix=frame.ToString("D3");var info=a.GetCurrentAnimatorStateInfo(0);var p=new Pose{frame=frame,phase=Mathf.Repeat(info.normalizedTime,1),skyHour=sky.CurrentHour,clip=a.GetCurrentAnimatorClipInfo(0)[0].clip.name};
   if(p.clip!="Rig|Walk_Loop")throw new Exception("Not actual Walk: "+p.clip);
   p.stages.Add(Render(prefix+"_OFF","product OFF",0));p.stages.Add(Render(prefix+"_CLOTH","outerwear-bottom-shoes",14));if(includeBody)p.stages.Add(Render(prefix+"_BODY","Body0 plus clothes; hands included",15));
   ClothRegion524.Enabled=false;ClothRegion524.UseWholeRegions539=false;h.RenderFrame();File.WriteAllText(root+prefix+"_pose.json",JsonUtility.ToJson(p,true));count++;
   File.WriteAllText(root+"progress.json","{\"capturedPoses\":"+count+",\"targetPoses\":"+(last-first+1)+",\"lastFrame\":"+frame+"}");
   if(count==last-first+1){End("CAPTURED");return;}queued=false;f.validateRender=OnFinal;EditorApplication.isPaused=false;
  }
  catch(Exception e){End("FAILED",e.ToString());}
 }
 static void OnFinal(){prior?.Invoke();if(!f.contourReady||queued)return;queued=true;f.validateRender=prior;EditorApplication.isPaused=true;EditorApplication.delayCall+=Capture;}
 static void Tick(){if(!EditorApplication.isPlaying||EditorApplication.timeSinceStartup>deadline){End("FAILED","Play ended or capture deadline");return;}EditorApplication.QueuePlayerLoopUpdate();}
 static void End(string status,string error="")
 {
  ClothRegion524.Enabled=false;ClothRegion524.UseOpacityCurves527=oldOpacity;ClothRegion524.UseAreaCurves532=oldArea;ClothRegion524.UseWholeRegions539=oldWhole;ClothRegion524.PartBits540=oldBits;ClosedRegion524.UseSpatialIndex526=oldIndex;Shader.SetGlobalInt("_Cloth524Enabled",0);
  if(f)f.validateRender=prior;if(sky)sky.SetAutomaticAdvance(oldAuto);if(a){a.transform.rotation=oldRotation;a.SetFloat("LocomotionSpeed",oldLoc);a.speed=oldSpeed;a.Play(oldState,0,oldTime);a.Update(0);a.enabled=oldAnim;}if(move)move.enabled=oldMove;Time.captureDeltaTime=oldCapture;Application.runInBackground=oldBg;EditorApplication.update-=Tick;EditorApplication.delayCall-=Capture;EditorApplication.isPaused=oldPaused;
  if(h)File.WriteAllText(root+"face_after.txt",FaceState524.Snapshot(h));
  File.WriteAllText(root+"status.json","{\"status\":\""+status+"\",\"error\":\""+error.Replace("\\","/").Replace("\"","'").Replace("\r"," ").Replace("\n"," ")+"\",\"poses\":"+count+",\"inputRestored\":"+(move&&move.enabled==oldMove?"true":"false")+",\"animatorRestored\":"+(a&&a.enabled==oldAnim&&a.speed==oldSpeed?"true":"false")+",\"clockRestored\":"+(sky&&sky.IsAdvancingAutomatically==oldAuto?"true":"false")+"}");if(EditorApplication.isPlaying)EditorApplication.isPlaying=false;
 }
 public static void Start(int from,int to,string output,string startup,bool testBody=true)
 {
  if(!EditorApplication.isPlaying||EditorApplication.isPaused||ClothRegion524.Enabled)throw new Exception("Ready Play / product OFF required");g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();if(!g||!g.connected)throw new Exception("Runtime not ready");h=g.player.host;f=h.main;a=f.motion.animation.target;move=g.player.player.GetComponent<PlayerMovement>();sky=UnityEngine.Object.FindFirstObjectByType<SkyLightingCycleController>();
  if(HeadRegion502.Enabled||h.post.candidateEnabled)throw new Exception("Other trial enabled");prior=f.validateRender;if(prior!=null&&prior.GetInvocationList().Any(x=>!(x.Target is PostView366)))throw new Exception("Other capture hook active");if(Directory.Exists(output))throw new Exception("Output exists; no duplicate capture");
  root=output;first=from;last=to;includeBody=testBody;Directory.CreateDirectory(root);oldMove=move.enabled;oldAnim=a.enabled;oldAuto=sky.IsAdvancingAutomatically;oldBg=Application.runInBackground;if(File.Exists(startup))oldBg=JsonUtility.FromJson<Startup>(File.ReadAllText(startup)).oldBackground;oldPaused=EditorApplication.isPaused;oldIndex=ClosedRegion524.UseSpatialIndex526;oldOpacity=ClothRegion524.UseOpacityCurves527;oldArea=ClothRegion524.UseAreaCurves532;oldWhole=ClothRegion524.UseWholeRegions539;oldBits=ClothRegion524.PartBits540;oldLoc=a.GetFloat("LocomotionSpeed");oldSpeed=a.speed;oldCapture=Time.captureDeltaTime;oldRotation=a.transform.rotation;var state=a.GetCurrentAnimatorStateInfo(0);oldState=state.fullPathHash;oldTime=state.normalizedTime;
  File.WriteAllText(root+"face_before.txt",FaceState524.Snapshot(h));sky.SetAutomaticAdvance(false);move.enabled=false;a.enabled=true;a.speed=1;a.SetFloat("LocomotionSpeed",1);a.transform.rotation=Quaternion.Euler(0,80,0);a.Play(oldState,0,1f+(from-1)/80f+.00000248f);a.Update(0);Time.captureDeltaTime=1f/60;Application.runInBackground=true;count=0;queued=false;deadline=EditorApplication.timeSinceStartup+900;f.validateRender=OnFinal;EditorApplication.update+=Tick;
  File.WriteAllText(root+"status.json","{\"status\":\"STARTED\",\"first\":"+first+",\"last\":"+last+"}");
 }
}
