using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
internal class CommandScript : IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  const string root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66";
  var checks=new Arr58();var backup=(Obj58)Json58.Parse(File.ReadAllText(Path.Combine(root,"BACKUP66.json")));
  foreach(Obj58 e in (Arr58)backup["native"])
  {
   if(!(bool)e["nativeSnapshot"])continue;string path=(string)e["path"];
   var o=Resources.FindObjectsOfTypeAll<UnityEngine.Object>().FirstOrDefault(x=>x&&AssetDatabase.GetAssetPath(x)==path&&x.GetType().FullName==(string)e["type"]);
   if(!o&&path.StartsWith("Assets/"))o=AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(path);
   if(!o){checks.Add(new Obj58{["path"]=path,["status"]="unavailable"});continue;}
   var c=SerializedContent66.Verify(Path.Combine(root,"backup","serialized",path+".json"),EditorJsonUtility.ToJson(o));checks.Add(new Obj58{["path"]=path,["status"]=c.Status,["equal"]=c.Equivalent.HasValue?(Json58)c.Equivalent.Value:null,["beforeSHA"]=c.BeforeSHA256,["afterSHA"]=c.AfterSHA256});
  }
  var scene=SceneManager.GetActiveScene();var report=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["project"]=Application.dataPath,["playing"]=EditorApplication.isPlaying,["transitioning"]=EditorApplication.isPlayingOrWillChangePlaymode,["paused"]=EditorApplication.isPaused,["compiling"]=EditorApplication.isCompiling,["updating"]=EditorApplication.isUpdating,["scene"]=scene.path,["sceneDirty"]=scene.isDirty,["frameCount"]=Time.frameCount,["runInBackground"]=Application.runInBackground,["isFocused"]=Application.isFocused,["timeScale"]=Time.timeScale,["captureDeltaTime"]=Time.captureDeltaTime,["optionsEnabled"]=EditorSettings.enterPlayModeOptionsEnabled,["options"]=(int)EditorSettings.enterPlayModeOptions,["nativeInstances"]=UnityEngine.Object.FindObjectsByType<NativePlayer395>(FindObjectsInactive.Include,FindObjectsSortMode.None).Length,["nativeComparisons"]=checks};
  File.WriteAllText(Path.Combine(root,"POST_CAPTURE66.json"),report.ToString());result.Log("67 post-capture state: Edit="+!EditorApplication.isPlaying+" paused="+EditorApplication.isPaused+" runInBackground="+Application.runInBackground+" focused="+Application.isFocused+" native snapshots compared="+checks.Count);
 }
}
