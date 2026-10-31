using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;
internal class CommandScript : IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  const string root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66";
  if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required before import");
  var scenes=new Arr58();for(int i=0;i<SceneManager.sceneCount;i++){var s=SceneManager.GetSceneAt(i);if(s.isDirty)throw new InvalidOperationException("Scene changed before import");scenes.Add(new Obj58{["path"]=s.path,["dirty"]=s.isDirty});}
  var dirty=new Arr58(Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o)).Select(o=>new Obj58{["path"]=AssetDatabase.GetAssetPath(o),["type"]=o.GetType().FullName}));
  File.WriteAllText(Path.Combine(root,"IMPORT_REQUESTED66.json"),new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["dirty"]=dirty,["scenes"]=scenes,["SaveAssets"]=false,["project"]=Application.dataPath}.ToString());
  AssetDatabase.Refresh();
  File.WriteAllText(Path.Combine(root,"IMPORT_RETURNED66.json"),new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["compiling"]=EditorApplication.isCompiling,["updating"]=EditorApplication.isUpdating}.ToString());
  result.Log("65 two-file patch refresh requested; no save/Play. Compile completion must be checked separately.");
 }
}
