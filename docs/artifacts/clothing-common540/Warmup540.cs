using UnityEngine;
using UnityEditor;
using System;
using System.IO;
public static class Warmup540
{
 static string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Common540/";
 static bool oldBackground;static double deadline;
 static void Finish(string state,string error="")
 {
  EditorApplication.update-=Tick;
  if(state!="READY")Application.runInBackground=oldBackground;
  File.WriteAllText(Root+"WARMUP_STATUS540.json","{\"status\":\""+state+"\",\"frame\":"+Time.frameCount+",\"error\":\""+error.Replace("\"","'").Replace("\n"," ").Replace("\r"," ").Replace("\\","/")+"\"}");
 }
 static void Tick()
 {
  if(!EditorApplication.isPlaying){Finish("FAILED","Play ended");return;}
  var g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();
  if(g&&g.player&&!string.IsNullOrEmpty(g.player.failure)){Finish("FAILED",g.player.failure);return;}
  if(g&&!string.IsNullOrEmpty(g.failure)){Finish("FAILED",g.failure);return;}
  if(g&&g.connected&&(!g.runInputTest||g.testFinished)){Finish("READY");return;}
  if(EditorApplication.timeSinceStartup>deadline){Finish("FAILED","60s startup deadline");return;}
  EditorApplication.QueuePlayerLoopUpdate();
 }
 public static void Start(string output=null)
 {
  if(!EditorApplication.isPlaying||EditorApplication.isPaused)throw new Exception("Ready Play required");
  if(output!=null)Root=output;Directory.CreateDirectory(Root);
  if(File.Exists(Root+"WARMUP_INITIAL540.json"))throw new Exception("Startup already requested; inspect status");
  oldBackground=Application.runInBackground;
  File.WriteAllText(Root+"WARMUP_INITIAL540.json","{\"oldBackground\":"+(oldBackground?"true":"false")+",\"initialFrame\":"+Time.frameCount+"}");
  deadline=EditorApplication.timeSinceStartup+60;Application.runInBackground=true;EditorApplication.update+=Tick;EditorApplication.QueuePlayerLoopUpdate();
  File.WriteAllText(Root+"WARMUP_STATUS540.json","{\"status\":\"STARTED\"}");
 }
}
