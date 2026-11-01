using System;
using System.IO;
using UnityEngine;
using UnityEditor;
internal class CommandScript : IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  var report=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["ApplicationRunInBackground"]=Application.runInBackground,["PlayerSettingsRunInBackground"]=PlayerSettings.runInBackground,["playing"]=EditorApplication.isPlaying};
  File.WriteAllText(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66\TARGET_OPTION68.json",report.ToString());
  result.Log("68 target background getters: Application="+Application.runInBackground+" PlayerSettings="+PlayerSettings.runInBackground+"; no setters");
 }
}
