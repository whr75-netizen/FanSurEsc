using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using FantasySurvival.WorldLighting;
public static class ProbeOutline533
{
 const string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Outline533/GPU/";
 const string Reference="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Shape532/Adjacent/";
 [Serializable]class RefPose{public float phase;public string clip;public Vector3 rotation;}
 [Serializable]class Status{public string status,error;public int renders;public bool restored,cloth,opacity,area;}
 [Serializable]class Meta{public int frame;public float requestedPhase,actualPhase,hour,lineTone,ortho;public bool usePalette;public Vector3 rotation;public string clip;}
 static bool armed,oldBg,oldPaused;static int renders;static double deadline;
 static Color[] Read(RenderTexture rt)
 {
  var previous=RenderTexture.active;Texture2D t=null;
  try{RenderTexture.active=rt;t=new Texture2D(rt.width,rt.height,TextureFormat.RGBAFloat,false,true);t.ReadPixels(new Rect(0,0,rt.width,rt.height),0,0,false);t.Apply(false,false);return t.GetPixels();}
  finally{if(t)UnityEngine.Object.DestroyImmediate(t);RenderTexture.active=previous;}
 }
 static Color Value(Color[] values,RenderTexture rt,int x,int y)
 {return x>=0&&x<rt.width&&y>=0&&y<rt.height?values[y*rt.width+x]:Color.clear;}
 static void Colour(BinaryWriter w,Color c){w.Write(c.r);w.Write(c.g);w.Write(c.b);w.Write(c.a);}
 static void Dump(Full319View335 f,int frame,string tag)
 {
  var before=Read(f.prepared.rt);var owner=Read(f.preparedOwner.rt);var line=Read(f.postLine.rt);var audit=Read(f.audit.rt);var final=Read(f.colour.rt);var meta=Read(f.preparedMeta.rt);var uv=Read(f.preparedUV.rt);
  var surface=Read(f.gridSurface.rt);var torso=Read(f.centreMeta[1].rt);var arms=Read(f.centreMeta[2].rt);var palette=Read(f.gridPalette.rt);var paletteAudit=Read(f.paletteAudit.rt);
  var targets=frame==42?new[]{new Vector2Int(209,54),new Vector2Int(210,55),new Vector2Int(210,56),new Vector2Int(210,57)}:new[]{new Vector2Int(226,65)};
  var points=new List<Vector2Int>();foreach(var p in targets)for(int y=-2;y<=2;y++)for(int x=-2;x<=2;x++){var q=p+new Vector2Int(x,y);if(!points.Contains(q))points.Add(q);}
  string prefix=Root+frame.ToString("D3")+"_"+tag;
  using(var w=new BinaryWriter(File.Create(prefix+"_SPARSE.bin")))
  {
   w.Write(533);w.Write(points.Count);
   foreach(var p in points.OrderBy(p=>p.y).ThenBy(p=>p.x))
   {
    int x=p.x,y=271-p.y;w.Write(p.x);w.Write(p.y);
    foreach(var values in new[]{before,owner,line,audit,final,meta,uv})Colour(w,values[y*480+x]);
    Colour(w,Value(surface,f.gridSurface.rt,x*2+1,y*2+1));
    Colour(w,Value(torso,f.centreMeta[1].rt,x,y));Colour(w,Value(arms,f.centreMeta[2].rt,x,y));
    Colour(w,Value(palette,f.gridPalette.rt,x*2+1,y*2+1));Colour(w,paletteAudit[y*480+x]);
   }
  }
  using(var w=new BinaryWriter(File.Create(prefix+"_COVERAGE.bin"))){for(int y=0;y<272;y++)for(int x=0;x<480;x++)w.Write((byte)(before[(271-y)*480+x].a>0?1:0));}
 }
 static void Record(string status,string error="",bool restored=false)
 {File.WriteAllText(Root+"status.json",JsonUtility.ToJson(new Status{status=status,error=error,renders=renders,restored=restored,cloth=ClothRegion524.Enabled,opacity=ClothRegion524.UseOpacityCurves527,area=ClothRegion524.UseAreaCurves532},true));}
 static void Tick()
 {
  if(!armed)return;
  if(!EditorApplication.isPlaying||EditorApplication.timeSinceStartup>deadline){Finish("FAILED","Play ended or ready deadline");return;}
  var g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();if(!g||!g.connected)return;
  EditorApplication.update-=Tick;EditorApplication.isPaused=true;EditorApplication.delayCall+=Work;
 }
 static void Work()
 {
  Gameplay397 g=null;Full319View335 f=null;Animator a=null;PlayerMovement move=null;SkyLightingCycleController sky=null;
  bool oldAnim=false,oldMove=false,oldAuto=false;float loc=0,speed=0,time=0,sourceFrame=0;int state=0;Quaternion rotation=Quaternion.identity;Vector3 avatarPosition=default,avatarScale=default;string error="";bool saved=false;
  try
  {
   g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();if(!g||!g.connected||g.runInputTest)throw new Exception("Expected actual connected runtime");
   var h=g.player.host;f=h.main;var m=f.motion;a=m.animation.target;move=g.player.player.GetComponent<PlayerMovement>();sky=UnityEngine.Object.FindFirstObjectByType<SkyLightingCycleController>();
   if(ClothRegion524.Enabled||ClothRegion524.UseOpacityCurves527||ClothRegion524.UseAreaCurves532||HeadRegion502.Enabled||h.post.candidateEnabled)throw new Exception("Preserve baseline flags");
   if(f.validateRender!=null&&f.validateRender.GetInvocationList().Any(x=>!(x.Target is PostView366)))throw new Exception("Other capture hook active");
   oldAnim=a.enabled;oldMove=move.enabled;oldAuto=sky.IsAdvancingAutomatically;loc=a.GetFloat("LocomotionSpeed");speed=a.speed;rotation=a.transform.rotation;var s=a.GetCurrentAnimatorStateInfo(0);state=s.fullPathHash;time=s.normalizedTime;sourceFrame=m.sourceFrame;avatarPosition=g.player.avatar.position;avatarScale=g.player.avatar.localScale;saved=true;
   move.enabled=false;sky.SetAutomaticAdvance(false);a.enabled=true;a.speed=0;a.SetFloat("LocomotionSpeed",1);
   foreach(int frame in new[]{42,44})
   {
    var reference=JsonUtility.FromJson<RefPose>(File.ReadAllText(Reference+frame.ToString("D3")+"_probe.json"));
    a.Play(state,0,reference.phase);a.Update(0);a.transform.rotation=Quaternion.Euler(reference.rotation);
    g.player.avatar.position=g.player.feet.position;g.player.avatar.localScale=Vector3.one*(g.player.bodyHeight/g.player.sourceHeight);m.sourceFrame=reference.phase*40;g.player.bake.Evaluate();
    foreach(string tag in new[]{"BASE","ALT"})
    {
     ClothRegion524.Enabled=true;ClothRegion524.UseOpacityCurves527=true;ClothRegion524.UseAreaCurves532=tag=="ALT";h.RenderFrame();
     if(!ClothRegion524.Ready(f))throw new Exception(ClothRegion524.Status);
     Dump(f,frame,tag);renders++;Record("PROBING");
    }
    File.WriteAllText(Root+frame.ToString("D3")+"_META.json",JsonUtility.ToJson(new Meta{frame=frame,requestedPhase=reference.phase,actualPhase=Mathf.Repeat(a.GetCurrentAnimatorStateInfo(0).normalizedTime,1),clip=a.GetCurrentAnimatorClipInfo(0)[0].clip.name,rotation=a.transform.rotation.eulerAngles,hour=sky.CurrentHour,lineTone=f.lineTone,usePalette=f.usePalette,ortho=m.camera.orthographicSize},true));
   }
  }
  catch(Exception e){error=e.ToString();}
  finally
  {
   ClothRegion524.Enabled=ClothRegion524.UseOpacityCurves527=ClothRegion524.UseAreaCurves532=false;Shader.SetGlobalInt("_Cloth524Enabled",0);
   if(saved){a.SetFloat("LocomotionSpeed",loc);a.speed=speed;a.Play(state,0,time);a.Update(0);a.transform.rotation=rotation;a.enabled=oldAnim;move.enabled=oldMove;sky.SetAutomaticAdvance(oldAuto);f.motion.sourceFrame=sourceFrame;g.player.avatar.position=avatarPosition;g.player.avatar.localScale=avatarScale;}
   Finish(error==""?"PROBED":"FAILED",error,saved);
  }
 }
 static void Finish(string status,string error="",bool restored=false)
 {
  armed=false;EditorApplication.update-=Tick;EditorApplication.delayCall-=Work;Application.runInBackground=oldBg;EditorApplication.isPaused=oldPaused;Record(status,error,restored);
  if(EditorApplication.isPlaying)EditorApplication.isPlaying=false;
 }
 public static void Start()
 {
  if(Application.dataPath!="C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets"||!EditorApplication.isPlaying||EditorApplication.isPaused)throw new Exception("Expected current Play");
  if(Directory.Exists(Root))throw new Exception("Probe output exists; no duplicate execution");
  Directory.CreateDirectory(Root);oldBg=Application.runInBackground;oldPaused=EditorApplication.isPaused;Application.runInBackground=true;renders=0;armed=true;deadline=EditorApplication.timeSinceStartup+120;EditorApplication.update+=Tick;Record("WAITING_RUNTIME");EditorApplication.QueuePlayerLoopUpdate();
 }
}
