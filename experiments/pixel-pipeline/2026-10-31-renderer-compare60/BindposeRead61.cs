using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
internal class CommandScript:IRunCommand {
 public void Execute(ExecutionResult result){
  if(EditorApplication.isPlaying||EditorApplication.isPlayingOrWillChangePlaymode)throw new InvalidOperationException("Edit only");
  var mesh=AssetDatabase.LoadAssetAtPath<UnityEngine.Mesh>("Assets/EUnityValidation01/EyeContoursLayers202/Meshes/FaceSourceOwner202.asset");
  var poses=mesh.bindposes;
  var report=new Obj58{["entityId"]=mesh.GetEntityId().ToString(),["bindposeCount"]=poses.Length,["bindposesRowMajor"]=new Arr58(poses.Select(m=>new Arr58(Enumerable.Range(0,16).Select(i=>m[i/4,i%4])))),["settersExecuted"]=0};
  File.WriteAllText(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\renderer-compare60\BINDPOSE_READ61.json",report.ToString());result.Log("61 sparse bindpose read; count="+poses.Length+" no setters/render");
 }
}
