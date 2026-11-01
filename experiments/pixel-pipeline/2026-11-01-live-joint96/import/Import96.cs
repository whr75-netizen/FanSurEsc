using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
internal class CommandScript:IRunCommand{public void Execute(ExecutionResult result){
if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit only");
const string path="Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/WholeEye96.compute";
AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport);var shader=AssetDatabase.LoadAssetAtPath<ComputeShader>(path);if(!shader)throw new InvalidOperationException("Missing compute");var messages=ShaderUtil.GetComputeShaderMessages(shader);var report=new Obj58{["kernels"]=new Arr58(new[]{"CopyAlpha","PackPart","Refit","Query","Select"}.Select(k=>new Obj58{["name"]=k,["found"]=shader.HasKernel(k)})),["errors"]=new Arr58(messages.Select(m=>new Obj58{["severity"]=m.severity.ToString(),["message"]=m.message,["line"]=m.line})),["CSharpDomainReloadRequested"]=false,["playing"]=EditorApplication.isPlaying};CreateOnly73.Text(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\live-joint96\import\IMPORT96.json",report.ToString());result.Log("96 single new compute import; no C# import, settings or Play");}}
