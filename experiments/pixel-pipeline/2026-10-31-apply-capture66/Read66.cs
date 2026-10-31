using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.SceneManagement;
using UnityEngine.Rendering;
using UnityEngine.Profiling;

internal class CommandScript : IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  var dirty=new Arr58();
  foreach(var o in Resources.FindObjectsOfTypeAll<UnityEngine.Object>()
    .Where(o=>o&&EditorUtility.IsPersistent(o)&&EditorUtility.IsDirty(o))
    .OrderBy(o=>AssetDatabase.GetAssetPath(o)))
  {
   string path=AssetDatabase.GetAssetPath(o);
   if(!path.StartsWith("Assets/")&&!path.StartsWith("ProjectSettings/"))continue;
   var row=new Obj58{["path"]=path,["type"]=o.GetType().FullName,["entityId"]=o.GetEntityId().ToString(),["guid"]=AssetDatabase.AssetPathToGUID(path)};
   if(o is UnityEngine.Mesh mesh){row["vertexCount"]=mesh.vertexCount;row["subMeshCount"]=mesh.subMeshCount;row["blendShapeCount"]=mesh.blendShapeCount;row["isReadable"]=mesh.isReadable;}
   dirty.Add(row);
  }
  var scenes=new Arr58();
  for(int i=0;i<SceneManager.sceneCount;i++){var s=SceneManager.GetSceneAt(i);scenes.Add(new Obj58{["path"]=s.path,["dirty"]=s.isDirty,["loaded"]=s.isLoaded,["active"]=s==SceneManager.GetActiveScene()});}
  var report=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["project"]=Application.dataPath,["version"]=Application.unityVersion,["domain"]=AppDomain.CurrentDomain.Id,
   ["playing"]=EditorApplication.isPlaying,["paused"]=EditorApplication.isPaused,["transitioning"]=EditorApplication.isPlayingOrWillChangePlaymode,["compiling"]=EditorApplication.isCompiling,["updating"]=EditorApplication.isUpdating,
   ["dirty"]=dirty,["scenes"]=scenes,["optionsEnabled"]=EditorSettings.enterPlayModeOptionsEnabled,["options"]=(int)EditorSettings.enterPlayModeOptions,
   ["timeScale"]=Time.timeScale,["captureDeltaTime"]=Time.captureDeltaTime,["graphicsPipelinePath"]=AssetDatabase.GetAssetPath(GraphicsSettings.defaultRenderPipeline),["qualityPipelinePath"]=AssetDatabase.GetAssetPath(QualitySettings.renderPipeline),
   ["buildScenes"]=new Arr58(EditorBuildSettings.scenes.Select(s=>(s.enabled?"1":"0")+"\t"+s.path+"\t"+s.guid)),
   ["memory"]=new Obj58{["GetTotalAllocatedMemoryLong"]=Profiler.GetTotalAllocatedMemoryLong(),["GetTotalReservedMemoryLong"]=Profiler.GetTotalReservedMemoryLong(),["GetMonoUsedSizeLong"]=Profiler.GetMonoUsedSizeLong()}};
  File.WriteAllText(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66\CURRENT66.json",report.ToString());
  result.Log("66 read only: Play="+EditorApplication.isPlaying+" compiling="+EditorApplication.isCompiling+" dirty="+dirty.Count);
 }
}
