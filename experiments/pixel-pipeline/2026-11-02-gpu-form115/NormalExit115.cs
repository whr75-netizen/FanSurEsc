using System;
using System.Linq;
using UnityEngine;
using UnityEditor;
// Restoration only. No direct invocation of observer methods, no reset/re-render.
internal class CommandScript:IRunCommand {
 public void Execute(ExecutionResult result) {
  var observers=(EditorApplication.update==null?new Delegate[0]:EditorApplication.update.GetInvocationList())
   .Where(d=>d.Target is IRunCommand&&d.Target.GetType().Assembly.GetType("Forward115",false)!=null&&d.Target.GetType().Assembly.GetType("RegionDriver115",false)!=null).ToArray();
  var before=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["playing"]=EditorApplication.isPlaying,["transitioning"]=EditorApplication.isPlayingOrWillChangePlaymode,["paused"]=EditorApplication.isPaused,["matchingObserverCount"]=observers.Length,["frame"]=Time.frameCount};
  CreateOnly73.Text(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\gpu-form115\EXIT_COMMAND_RECEIVED115.json",before.ToString());
  if(observers.Length!=1){result.Log("115 normal exit withheld: expected exactly one owned observer");return;}
  if(EditorApplication.isPlaying||EditorApplication.isPlayingOrWillChangePlaymode)EditorApplication.ExitPlaymode();
  CreateOnly73.Text(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\gpu-form115\EXIT_API_RETURNED115.json",new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["playing"]=EditorApplication.isPlaying,["transitioning"]=EditorApplication.isPlayingOrWillChangePlaymode,["observerRestorationVerified"]=false}.ToString());
  result.Log("115 public normal exit requested once; existing observer owns its cleanup/restoration, not yet verified");
 }
}
