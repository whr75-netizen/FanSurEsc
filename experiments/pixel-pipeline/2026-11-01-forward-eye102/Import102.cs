using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
internal class CommandScript:IRunCommand{public void Execute(ExecutionResult result){
 if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("102 stable Edit required");
 const string path="Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye102.compute";
 AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport);
 var s=AssetDatabase.LoadAssetAtPath<ComputeShader>(path);if(!s)throw new InvalidOperationException("102 shader missing");
 var messages=ShaderUtil.GetComputeShaderMessages(s);var rows=new Arr58(messages.Select(m=>new Obj58{["message"]=m.message,["severity"]=m.severity.ToString(),["line"]=m.line}));
 CreateOnly73.Text(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\forward-eye102\capture\IMPORT102.json",new Obj58{["messages"]=rows,["noCSharpImport"]=true,["playing"]=EditorApplication.isPlaying,["domain"]=AppDomain.CurrentDomain.Id}.ToString());
 if(messages.Any(m=>m.severity.ToString()=="Error"))throw new InvalidOperationException("102 isolated shader compile error; no Play");result.Log("102 shader-only import; no C# reload or Play");
}}
