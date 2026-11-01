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
 public void Execute(ExecutionResult result)
 {
  string output=Path.Combine(Root,"RESUME68.json");if(File.Exists(output))throw new InvalidOperationException("Existing preflight must be inspected");
  if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required for resume preflight");
  var objects=Resources.FindObjectsOfTypeAll<UnityEngine.Object>().Where(o=>o&&EditorUtility.IsPersistent(o)).ToArray();
  var dirty=new Arr58(objects.Where(o=>EditorUtility.IsDirty(o)).Select(o=>new {o,path=AssetDatabase.GetAssetPath(o)}).Where(x=>x.path.StartsWith("Assets/")||x.path.StartsWith("ProjectSettings/")).Select(x=>new Obj58{["path"]=x.path,["type"]=x.o.GetType().FullName,["entityId"]=x.o.GetEntityId().ToString()}));
  var native=new Arr58();string[] paths={"ProjectSettings/TimeManager.asset","ProjectSettings/EditorBuildSettings.asset","ProjectSettings/EditorSettings.asset","ProjectSettings/GraphicsSettings.asset","Assets/EUnityValidation01/EyeContoursLayers202/Meshes/FaceSourceOwner202.asset"};
  foreach(string path in paths)
  {
   var o=objects.FirstOrDefault(x=>AssetDatabase.GetAssetPath(x)==path);if(!o){native.Add(new Obj58{["path"]=path,["available"]=false});continue;}
   bool wasDirty=EditorUtility.IsDirty(o);string file=Path.Combine(Root,"resume68-before",path+".json");Directory.CreateDirectory(Path.GetDirectoryName(file));string text=EditorJsonUtility.ToJson(o);File.WriteAllText(file,text,new System.Text.UTF8Encoding(false));
   var verified=SerializedContent66.Verify(file,text);if(verified.Equivalent!=true)throw new InvalidOperationException("External snapshot verification failed: "+path);
   native.Add(new Obj58{["path"]=path,["available"]=true,["type"]=o.GetType().FullName,["snapshot"]=file,["sha256"]=verified.BeforeSHA256,["dirtyBefore"]=wasDirty,["dirtyAfter"]=EditorUtility.IsDirty(o)});
  }
  var scenes=new Arr58();for(int i=0;i<SceneManager.sceneCount;i++){var s=SceneManager.GetSceneAt(i);scenes.Add(new Obj58{["path"]=s.path,["dirty"]=s.isDirty,["roots"]=s.rootCount,["active"]=s==SceneManager.GetActiveScene()});}
  var report=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["project"]=Application.dataPath,["version"]=Application.unityVersion,["playing"]=EditorApplication.isPlaying,["paused"]=EditorApplication.isPaused,["compiling"]=EditorApplication.isCompiling,["updating"]=EditorApplication.isUpdating,["scenes"]=scenes,["dirty"]=dirty,["native"]=native,["optionsEnabled"]=EditorSettings.enterPlayModeOptionsEnabled,["options"]=(int)EditorSettings.enterPlayModeOptions,["runInBackground"]=Application.runInBackground,["timeScale"]=Time.timeScale,["captureDeltaTime"]=Time.captureDeltaTime,["graphicsPipeline"]=AssetDatabase.GetAssetPath(GraphicsSettings.defaultRenderPipeline),["qualityPipeline"]=AssetDatabase.GetAssetPath(QualitySettings.renderPipeline),["nativeInstances"]=UnityEngine.Object.FindObjectsByType<NativePlayer395>(FindObjectsInactive.Include,FindObjectsSortMode.None).Length};
  File.WriteAllText(output,report.ToString());result.Log("68 read-only preflight: Edit="+!EditorApplication.isPlaying+" dirty="+dirty.Count+" nativeSnapshots="+native.Count);
 }
}
