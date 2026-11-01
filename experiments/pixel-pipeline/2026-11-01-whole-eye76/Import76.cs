using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
internal class CommandScript : IRunCommand
{
 const string Root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\whole-eye76";
 const string Asset="Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/BaselineProbe76.compute";
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required");
  string backup=Path.Combine(Root,"import-native-before");if(Directory.Exists(backup))throw new IOException("Prior import outcome must be checked");Directory.CreateDirectory(backup);
  var native=NativeSnapshot73.Backup(backup);int domain=AppDomain.CurrentDomain.Id;
  AssetDatabase.ImportAsset(Asset,ImportAssetOptions.ForceSynchronousImport);
  var cs=AssetDatabase.LoadAssetAtPath<ComputeShader>(Asset);if(!cs)throw new InvalidOperationException("Probe compute import failed");
  var kernels=new Arr58();foreach(string k in new[]{"CountFeatures19","Evaluate","UnpackA","UnpackB","Merge"})kernels.Add(cs.FindKernel(k));
  var messages=ShaderUtil.GetComputeShaderMessages(cs);
  var report=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["domainBefore"]=domain,["domainAfter"]=AppDomain.CurrentDomain.Id,["compiling"]=EditorApplication.isCompiling,["kernels"]=kernels,["messages"]=new Arr58(messages.Select(m=>new Obj58{["message"]=m.message,["severity"]=m.severity.ToString()})),["native"]=NativeSnapshot73.Compare(backup,native)};
  CreateOnly73.Text(Path.Combine(Root,"IMPORT76.json"),report.ToString());
  if(domain!=AppDomain.CurrentDomain.Id||messages.Any(m=>m.severity.ToString()=="Error"))throw new InvalidOperationException("Probe import changed domain or has shader errors");
  result.Log("76 compute-only probe imported; original shader not modified; domain preserved");
 }
}
