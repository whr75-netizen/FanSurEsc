using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;
using UnityEngine.SceneManagement;

internal class CommandScript : IRunCommand
{
 const string Root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66";
 static string Hash(string p){using(var h=SHA256.Create())using(var f=File.OpenRead(p))return BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant();}
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isPlaying||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required");
  if(File.Exists(Path.Combine(Root,"SAVE_STARTED66.json")))throw new InvalidOperationException("Save request already started; inspect outcome");
  var backup=(Obj58)Json58.Parse(File.ReadAllText(Path.Combine(Root,"BACKUP66.json")));
  var check=(Obj58)Json58.Parse(File.ReadAllText(Path.Combine(Root,"BACKUP_CHECK66.json")));
  if(!(bool)check["verified"])throw new InvalidOperationException("Backup not externally verified");
  var expected=(Arr58)backup["native"];
  var objects=Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o))
   .Where(o=>{string p=AssetDatabase.GetAssetPath(o);return p.StartsWith("Assets/")||p.StartsWith("ProjectSettings/");}).ToArray();
  if(objects.Length!=expected.Count)throw new InvalidOperationException("Dirty set changed");
  foreach(Obj58 e in expected)if(!objects.Any(o=>AssetDatabase.GetAssetPath(o)==(string)e["path"]&&o.GetEntityId().ToString()==(string)e["entityId"]))throw new InvalidOperationException("Dirty identity changed");
  File.WriteAllText(Path.Combine(Root,"SAVE_STARTED66.json"),new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["targets"]=expected,["individualSaveAssetIfDirty"]=true,["SaveAssets"]=false}.ToString());
  var rows=new Arr58();
  foreach(var o in objects)
  {
   string path=AssetDatabase.GetAssetPath(o);
   var row=new Obj58{["path"]=path,["type"]=o.GetType().FullName,["beforeSHA256"]=Hash(path),["dirtyBefore"]=EditorUtility.IsDirty(o)};
   try{AssetDatabase.SaveAssetIfDirty(o);row["apiReturned"]=true;}
   catch(Exception e){row["error"]=e.GetType().Name+": "+e.Message;}
   row["dirtyAfter"]=EditorUtility.IsDirty(o);row["afterSHA256"]=Hash(path);
   if(!(o is Shader))
   {
    string native=EditorJsonUtility.ToJson(o);string prior=File.ReadAllText(Path.Combine(Root,"backup","serialized",path+".json"));
    row["serializedContentSame"]=Json58.DeepEquals(Json58.Parse(prior),Json58.Parse(native));
   }
   rows.Add(row);
   File.WriteAllText(Path.Combine(Root,"SAVE_PROGRESS66.json"),rows.ToString());
  }
  var remaining=new Arr58(Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o)).Select(o=>new Obj58{["path"]=AssetDatabase.GetAssetPath(o),["type"]=o.GetType().FullName,["entityId"]=o.GetEntityId().ToString()}));
  var scenes=new Arr58();for(int i=0;i<SceneManager.sceneCount;i++){var s=SceneManager.GetSceneAt(i);scenes.Add(new Obj58{["path"]=s.path,["dirty"]=s.isDirty});}
  File.WriteAllText(Path.Combine(Root,"SAVE66.json"),new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["targets"]=rows,["remainingDirty"]=remaining,["scenes"]=scenes,["SaveAssets"]=false,["sceneSave"]=false,["ClearDirty"]=false}.ToString());
  result.Log("66 individual SaveAssetIfDirty targets="+rows.Count+" remaining dirty="+remaining.Count+" no scene save");
 }
}
