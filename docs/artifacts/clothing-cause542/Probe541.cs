using System;
using System.IO;
using UnityEngine;
using UnityEditor;
using FantasySurvival.WorldLighting;
public static class Probe541
{
 [Serializable]class Startup{public bool oldBackground;}
 const string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/BodyRay541/Probe/";
 public static void Work()
 {
  var g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();var h=g.player.host;var f=h.main;var a=f.motion.animation.target;var sky=UnityEngine.Object.FindFirstObjectByType<SkyLightingCycleController>();var move=g.player.player.GetComponent<PlayerMovement>();
  bool pause=EditorApplication.isPaused,anim=a.enabled,input=move.enabled,automatic=sky.IsAdvancingAutomatically,bg=Application.runInBackground,index=ClosedRegion524.UseSpatialIndex526;float speed=a.speed,loc=a.GetFloat("LocomotionSpeed"),capture=Time.captureDeltaTime;var rotation=a.transform.rotation;var state=a.GetCurrentAnimatorStateInfo(0);int bits=ClothRegion524.PartBits540;bool opacity=ClothRegion524.UseOpacityCurves527,area=ClothRegion524.UseAreaCurves532,whole=ClothRegion524.UseWholeRegions539;
  var startup="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/BodyRay541/Startup/WARMUP_INITIAL540.json";if(File.Exists(startup))bg=JsonUtility.FromJson<Startup>(File.ReadAllText(startup)).oldBackground;
  string status="FAILED",error="";
  try
  {
   if(Directory.Exists(Root))throw new Exception("Existing probe output; inspect instead of duplicate");Directory.CreateDirectory(Root);EditorApplication.isPaused=true;move.enabled=false;sky.SetAutomaticAdvance(false);a.enabled=true;a.speed=1;a.SetFloat("LocomotionSpeed",1);a.transform.rotation=Quaternion.Euler(0,80,0);ClosedRegion524.UseSpatialIndex526=true;
   foreach(int frame in new[]{35,36,41})
   {
    a.Play(state.fullPathHash,0,1f+frame/80f+.00000248f);a.Update(0);int x=frame==41?218:217;
    foreach(int mode in new[]{14,15}){ClothRegion524.Enabled=true;ClothRegion524.PartBits540=mode;ClothRegion524.UseOpacityCurves527=true;ClothRegion524.UseWholeRegions539=true;ClothRegion524.UseAreaCurves532=false;h.RenderFrame();if(!ClothRegion524.Ready(f))throw new Exception(ClothRegion524.Status);TraceInputs541.Capture(Root+frame+"_"+mode,h,x,49);}
   }
   status="CAPTURED";
  }
  catch(Exception e){error=e.ToString();}
  finally
  {
   ClothRegion524.Enabled=false;ClothRegion524.PartBits540=bits;ClothRegion524.UseOpacityCurves527=opacity;ClothRegion524.UseAreaCurves532=area;ClothRegion524.UseWholeRegions539=whole;ClosedRegion524.UseSpatialIndex526=index;Shader.SetGlobalInt("_Cloth524Enabled",0);a.transform.rotation=rotation;a.SetFloat("LocomotionSpeed",loc);a.speed=speed;a.Play(state.fullPathHash,0,state.normalizedTime);a.Update(0);a.enabled=anim;move.enabled=input;sky.SetAutomaticAdvance(automatic);Time.captureDeltaTime=capture;Application.runInBackground=bg;EditorApplication.isPaused=pause;
   File.WriteAllText("C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/BodyRay541/PROBE_STATUS541.json","{\"status\":\""+status+"\",\"error\":\""+error.Replace("\\","/").Replace("\"","'").Replace("\r"," ").Replace("\n"," ")+"\",\"inputRestored\":"+(move.enabled==input?"true":"false")+",\"animatorRestored\":"+(a.enabled==anim&&a.speed==speed?"true":"false")+"}");EditorApplication.isPlaying=false;
  }
 }
}
