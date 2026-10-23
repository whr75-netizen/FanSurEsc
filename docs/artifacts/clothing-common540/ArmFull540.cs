using UnityEngine;
using UnityEditor;
using System.IO;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  var g=Object.FindFirstObjectByType<Gameplay397>();
  if(!EditorApplication.isPlaying||!g||!g.connected||ClothRegion524.Enabled||Time.captureDeltaTime!=0||Directory.Exists("C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Common540/FullLoop540"))throw new System.Exception("Uncertain/changed capture state; do not duplicate");
  EditorApplication.delayCall+=()=>CaptureCommon540.Start(0,80,"C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Common540/FullLoop540/","C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Common540/FullStartup540/WARMUP_INITIAL540.json",false);
  result.Log("Confirmed previous request made no capture; queued one guarded81-pose clothes-only run; body trial excluded");
 }
}
