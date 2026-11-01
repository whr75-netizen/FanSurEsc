using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
internal class CommandScript:IRunCommand{public void Execute(ExecutionResult result){
 if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("101 stable Edit required");
 const string path="Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/LayerZero101.shader";
 AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport);
 var s=AssetDatabase.LoadAssetAtPath<Shader>(path);if(!s)throw new InvalidOperationException("101 shader missing");
 var messages=ShaderUtil.GetShaderMessages(s);var rows=new Arr58(messages.Select(m=>new Obj58{["message"]=m.message,["severity"]=m.severity.ToString(),["line"]=m.line}));
 CreateOnly73.Text(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\layer-zero101\capture\IMPORT101.json",new Obj58{["messages"]=rows,["supported"]=s.isSupported,["noCSharpImport"]=true,["playing"]=EditorApplication.isPlaying,["domain"]=AppDomain.CurrentDomain.Id}.ToString());
 if(messages.Any(m=>m.severity.ToString()=="Error"))throw new InvalidOperationException("101 isolated shader compile error; no Play");result.Log("101 shader-only import; no C# reload or Play");
}}
