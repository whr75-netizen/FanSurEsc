using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
internal class CommandScript:IRunCommand {
 public void Execute(ExecutionResult result){
  var state=State58.Read();State58.RequireEdit(state);
  var report=new Obj58{["state"]=state,["memory"]=State58.Memory(),["nativeCount"]=UnityEngine.Object.FindObjectsByType<NativePlayer395>(FindObjectsInactive.Include,FindObjectsSortMode.None).Length,
   ["optionsEnabled"]=EditorSettings.enterPlayModeOptionsEnabled,["options"]=(int)EditorSettings.enterPlayModeOptions,["timeScale"]=Time.timeScale,["captureDeltaTime"]=Time.captureDeltaTime,
   ["graphicsPipelinePath"]=AssetDatabase.GetAssetPath(GraphicsSettings.defaultRenderPipeline),["qualityPipelinePath"]=AssetDatabase.GetAssetPath(QualitySettings.renderPipeline),["playStartScene"]=AssetDatabase.GetAssetPath(UnityEditor.SceneManagement.EditorSceneManager.playModeStartScene),["colourSpace"]=QualitySettings.activeColorSpace.ToString()};
  File.WriteAllText(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\renderer-compare60\PREFLIGHT60.json",report.ToString());
  result.Log("60 preflight Edit="+!(bool)state["playing"]+" dirty="+state["dirty"].Count+" native="+report["nativeCount"]+" options="+report["options"]);
 }
}
