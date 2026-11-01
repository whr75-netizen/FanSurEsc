using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
using UnityEngine.Profiling;
internal class CommandScript : IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  const string root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66";
  if(EditorApplication.isPlayingOrWillChangePlaymode)throw new InvalidOperationException("Observer must finish normal Play exit before postflight");
  var before=(Obj58)Json58.Parse(File.ReadAllText(Path.Combine(root,"BEFORE_PLAY68.json")));var checks=new Arr58();var objects=Resources.FindObjectsOfTypeAll<UnityEngine.Object>();
  foreach(Obj58 e in (Arr58)before["native"])
  {
   if(!(bool)e["available"])continue;string path=(string)e["path"];
   var o=objects.FirstOrDefault(x=>x&&AssetDatabase.GetAssetPath(x)==path&&x.GetType().FullName==(string)e["type"]);
   if(!o){checks.Add(new Obj58{["path"]=path,["status"]="unavailable; not loaded for verification"});continue;}
   var c=SerializedContent66.Verify((string)e["snapshot"],EditorJsonUtility.ToJson(o));checks.Add(new Obj58{["path"]=path,["status"]=c.Status,["equal"]=c.Equivalent.HasValue?(Json58)c.Equivalent.Value:null,["beforeSHA"]=c.BeforeSHA256,["afterSHA"]=c.AfterSHA256,["dirty"]=EditorUtility.IsDirty(o)});
  }
  var dirty=new Arr58(objects.Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o)).Select(o=>new {o,path=AssetDatabase.GetAssetPath(o)}).Where(x=>x.path.StartsWith("Assets/")||x.path.StartsWith("ProjectSettings/")).Select(x=>new Obj58{["path"]=x.path,["type"]=x.o.GetType().FullName}));
  var scene=SceneManager.GetActiveScene();var report=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["project"]=Application.dataPath,["playing"]=EditorApplication.isPlaying,["transitioning"]=EditorApplication.isPlayingOrWillChangePlaymode,["paused"]=EditorApplication.isPaused,["compiling"]=EditorApplication.isCompiling,["updating"]=EditorApplication.isUpdating,["scene"]=scene.path,["sceneDirty"]=scene.isDirty,["roots"]=scene.rootCount,["frameCount"]=Time.frameCount,["runInBackground"]=Application.runInBackground,["timeScale"]=Time.timeScale,["captureDeltaTime"]=Time.captureDeltaTime,["optionsEnabled"]=EditorSettings.enterPlayModeOptionsEnabled,["options"]=(int)EditorSettings.enterPlayModeOptions,["graphicsPipeline"]=AssetDatabase.GetAssetPath(GraphicsSettings.defaultRenderPipeline),["qualityPipeline"]=AssetDatabase.GetAssetPath(QualitySettings.renderPipeline),["nativeInstances"]=UnityEngine.Object.FindObjectsByType<NativePlayer395>(FindObjectsInactive.Include,FindObjectsSortMode.None).Length,["nativeComparisons"]=checks,["dirty"]=dirty,["memory"]=new Obj58{["allocated"]=Profiler.GetTotalAllocatedMemoryLong(),["reserved"]=Profiler.GetTotalReservedMemoryLong(),["mono"]=Profiler.GetMonoUsedSizeLong(),["renderTextureCount"]=Resources.FindObjectsOfTypeAll<RenderTexture>().Length}};
  File.WriteAllText(Path.Combine(root,"POST_PLAY68.json"),report.ToString());result.Log("68 postflight Edit="+!EditorApplication.isPlaying+" sceneDirty="+scene.isDirty+" nativeChecks="+checks.Count+" dirty="+dirty.Count);
 }
}
