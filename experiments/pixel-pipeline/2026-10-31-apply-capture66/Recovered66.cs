using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

internal class CommandScript : IRunCommand
{
 const string Root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66";
 static Arr58 Dirty()
 {
  return new Arr58(Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o))
   .Select(o=>new Obj58{["path"]=AssetDatabase.GetAssetPath(o),["type"]=o.GetType().FullName,["entityId"]=o.GetEntityId().ToString()})
   .Where(r=>((string)r["path"]).StartsWith("Assets/")||((string)r["path"]).StartsWith("ProjectSettings/")));
 }
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isPlaying||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required");
  var before=Dirty();var backup=(Obj58)Json58.Parse(File.ReadAllText(Path.Combine(Root,"BACKUP66.json")));
  var comparisons=new Arr58();
  foreach(Obj58 entry in (Arr58)backup["native"])
  {
   if(!(bool)entry["nativeSnapshot"])continue;
   string path=(string)entry["path"];
   var obj=Resources.FindObjectsOfTypeAll<UnityEngine.Object>().FirstOrDefault(o=>o&&AssetDatabase.GetAssetPath(o)==path&&o.GetType().FullName==(string)entry["type"]);
   if(!obj&&path.StartsWith("Assets/"))obj=AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(path);
   if(!obj){comparisons.Add(new Obj58{["path"]=path,["status"]="CurrentObjectUnavailable"});continue;}
   // One native string; bounded streaming SHA. Never parse the mesh JSON tree.
   var c=SerializedContent66.Verify(Path.Combine(Root,"backup","serialized",path+".json"),EditorJsonUtility.ToJson(obj));
   comparisons.Add(new Obj58{["path"]=path,["status"]=c.Status,["equivalent"]=c.Equivalent.HasValue?(Json58)c.Equivalent.Value:null,["beforeSHA256"]=c.BeforeSHA256,["afterSHA256"]=c.AfterSHA256,["beforeBytes"]=c.BeforeBytes,["afterBytes"]=c.AfterBytes});
  }
  var scenes=new Arr58();for(int i=0;i<SceneManager.sceneCount;i++){var s=SceneManager.GetSceneAt(i);scenes.Add(new Obj58{["path"]=s.path,["dirty"]=s.isDirty,["active"]=s==SceneManager.GetActiveScene(),["roots"]=s.rootCount});}
  var report=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["project"]=Application.dataPath,["version"]=Application.unityVersion,["domain"]=AppDomain.CurrentDomain.Id,["playing"]=EditorApplication.isPlaying,["compiling"]=EditorApplication.isCompiling,["updating"]=EditorApplication.isUpdating,
   ["dirtyBefore"]=before,["dirtyAfter"]=Dirty(),["scenes"]=scenes,["nativeComparisons"]=comparisons,
   ["optionsEnabled"]=EditorSettings.enterPlayModeOptionsEnabled,["options"]=(int)EditorSettings.enterPlayModeOptions,["timeScale"]=Time.timeScale,["captureDeltaTime"]=Time.captureDeltaTime,
   ["graphicsPipelinePath"]=AssetDatabase.GetAssetPath(GraphicsSettings.defaultRenderPipeline),["qualityPipelinePath"]=AssetDatabase.GetAssetPath(QualitySettings.renderPipeline),
   ["limits"]="No save/restore/import/Play; serialized-content comparison does not reconstruct runtime native/GPU/static state or original object identity."};
  File.WriteAllText(Path.Combine(Root,"RECOVERED66.json"),report.ToString());result.Log("66 recovered Edit, compared native snapshots="+comparisons.Count+" dirty before/after="+before.Count+"/"+((Arr58)report["dirtyAfter"]).Count);
 }
}
