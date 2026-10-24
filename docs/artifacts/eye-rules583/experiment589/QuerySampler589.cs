using System;
using System.IO;
using UnityEngine;
using UnityEditor;
using UnityEditor.PackageManager;
internal class CommandScript:IRunCommand{
 public void Execute(ExecutionResult result){
  const string path="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/EyeInput589/SAMPLER_STATE589.txt";
  if(File.Exists(path)||EditorApplication.isPlaying)throw new Exception("Single read-only Edit query required");
  var package=PackageInfo.FindForAssetPath("Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_forward_fragment.hlsl");
  string state="anisotropicFiltering="+QualitySettings.anisotropicFiltering+"\nquality="+QualitySettings.GetQualityLevel()+"\ngraphicsAPI="+SystemInfo.graphicsDeviceType+"\npackagePath="+(package==null?"UNAVAILABLE":package.resolvedPath);
  File.WriteAllText(path,state);result.Log(state);
 }
}
