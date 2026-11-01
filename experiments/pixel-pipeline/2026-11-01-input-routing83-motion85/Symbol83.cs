using System;
using System.IO;
using UnityEngine;
using UnityEditor;
using UnityEngine.InputSystem;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result){
  bool editorSymbol=false;
#if UNITY_EDITOR
  editorSymbol=true;
#endif
  var r=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["UNITY_EDITOR"]=editorSymbol,["settingsId"]=InputSystem.settings.GetEntityId().ToString(),["json"]=JsonUtility.ToJson(InputSystem.settings),["playing"]=EditorApplication.isPlaying};
  CreateOnly73.Text(@"ROOT83\SYMBOL83.json",r.ToString());result.Log("83 dynamic compiler UNITY_EDITOR="+editorSymbol+"; no settings changed");
 }
}
