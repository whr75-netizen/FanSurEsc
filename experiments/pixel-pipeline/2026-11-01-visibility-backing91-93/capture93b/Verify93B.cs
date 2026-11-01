using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.InputSystem;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result){
  const string root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\visibility-backing91\capture93b";
  var loaded=Resources.FindObjectsOfTypeAll<PlayerSettings>();
  var rows=new Arr58();foreach(var row in Json58.Parse(File.ReadAllText(Path.Combine(root,"NATIVE_BEFORE73.json"))))rows.Add(new Obj58{["path"]=row["path"],["type"]=row["type"],["snapshot"]=row["snapshot"]});
  var r=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["playing"]=EditorApplication.isPlaying,["settingsAlive"]=InputSystem.settings?true:false,["settingsId"]=InputSystem.settings.GetEntityId().ToString(),["settingsJSON"]=JsonUtility.ToJson(InputSystem.settings),["playerBackground"]=PlayerSettings.runInBackground,["loadedPlayerSettings"]=new Arr58(loaded.Select(o=>new Obj58{["id"]=o.GetEntityId().ToString(),["path"]=AssetDatabase.GetAssetPath(o),["persistent"]=EditorUtility.IsPersistent(o)})),["nativeComparisons"]=NativeSnapshot73.Compare(root,rows)};
  CreateOnly73.Text(Path.Combine(root,"VERIFY93B.json"),r.ToString());result.Log("80 separate read-only settings/native content verification");
 }
}
