using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;
internal class CommandScript : IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isCompiling||EditorApplication.isUpdating||EditorApplication.isPlayingOrWillChangePlaymode)throw new InvalidOperationException("Stable Edit required");
  // Compile-time direct public method reference; no reflection or invocation.
  Action<Full319View335> release=ClothRegion524.ReleaseScope551;
  var s=SceneManager.GetActiveScene();
  File.WriteAllText(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66\COMPILED65.json",new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["project"]=Application.dataPath,["version"]=Application.unityVersion,["domain"]=AppDomain.CurrentDomain.Id,["newPublicReleaseScopeAPIAvailable"]=release!=null,["compiling"]=EditorApplication.isCompiling,["updating"]=EditorApplication.isUpdating,["playing"]=EditorApplication.isPlaying,["scene"]=s.path,["sceneDirty"]=s.isDirty,["NoReflection"]=true}.ToString());
  result.Log("65 product compiled: ReleaseScope551 direct API available, Edit sceneDirty="+s.isDirty);
 }
}
