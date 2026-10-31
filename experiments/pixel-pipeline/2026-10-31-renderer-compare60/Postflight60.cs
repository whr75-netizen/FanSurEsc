using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
internal class CommandScript:IRunCommand {
 public void Execute(ExecutionResult result){
  const string root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\renderer-compare60";
  var state=State58.Read();State58.RequireEdit(state);
  var mesh=AssetDatabase.LoadAssetAtPath<UnityEngine.Mesh>("Assets/EUnityValidation01/EyeContoursLayers202/Meshes/FaceSourceOwner202.asset");
  if(mesh)File.WriteAllText(Path.Combine(root,"FACE_NATIVE_AFTER60.json"),EditorJsonUtility.ToJson(mesh));
  var r=new Obj58{["state"]=state,["memory"]=State58.Memory(),["liveNativeCount"]=UnityEngine.Object.FindObjectsByType<NativePlayer395>(FindObjectsInactive.Include,FindObjectsSortMode.None).Length,
   ["optionsEnabled"]=EditorSettings.enterPlayModeOptionsEnabled,["options"]=(int)EditorSettings.enterPlayModeOptions,["timeScale"]=Time.timeScale,["captureDeltaTime"]=Time.captureDeltaTime,
   ["graphicsPipelinePath"]=AssetDatabase.GetAssetPath(GraphicsSettings.defaultRenderPipeline),["qualityPipelinePath"]=AssetDatabase.GetAssetPath(QualitySettings.renderPipeline),
   ["faceVertexCount"]=mesh?mesh.vertexCount:0,["faceSubMeshCount"]=mesh?mesh.subMeshCount:0};
  File.WriteAllText(Path.Combine(root,"POSTFLIGHT60.json"),r.ToString());
  result.Log("60 postflight Edit; native="+r["liveNativeCount"]+" dirty="+state["dirty"].Count+" options="+r["options"]+" enabled="+r["optionsEnabled"]);
 }
}
