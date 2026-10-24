using System;
using System.IO;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  const string root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairDirections576/",marker=root+"LAUNCH_CANVAS_FULL576.txt";
  if(File.Exists(marker))throw new Exception("Inspect existing launch");
  using(var sha=SHA256.Create())if(BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes("C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets/EUnityValidation01/HeadRegion502/Runtime/HairRegions574.cs"))).Replace("-","")!="F4D26A5BE157C46BAE730F245F2D54E51E7AB072E9AA4042873A739A8BCC8411")throw new Exception("Approved source differs");
  if(typeof(HairRegions574.Family).GetField("referenceOpen")==null)throw new Exception("Approved source not compiled");
  File.WriteAllText(marker,"SCHEDULED");
  EditorApplication.delayCall+=()=>{
   File.AppendAllText(marker,"\nENTERED");
   try{CanvasView576.Start(260,root+"Compiled260/HeadCurve511.bytes",true);File.AppendAllText(marker,"\nSTARTED");}
   catch(Exception e){File.AppendAllText(marker,"\nFAILED "+e);HeadRegion502.SetCurveInput511(null);string initial=root+"StartupCompare576/WARMUP_INITIAL540.json";if(File.Exists(initial))Application.runInBackground=File.ReadAllText(initial).Contains("\"oldBackground\":true");if(EditorApplication.isPlaying)EditorApplication.isPlaying=false;throw;}
  };
  result.Log("One full-original-canvas yaw26081-pair loop scheduled; OFF=signed selection566, ON=shared KEEP576");
 }
}
