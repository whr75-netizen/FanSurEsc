using System;
using System.IO;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;
internal class CommandScript:IRunCommand{public void Execute(ExecutionResult result){const string root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairDirections576/Runtime577/",marker=root+"START_FinalFull260.txt";if(File.Exists(marker))throw new Exception("Inspect existing request");using(var sha=SHA256.Create()){foreach(var pair in new[]{new[]{"HairRegions574.cs","42F0B74B96E93D802EB15299F263EE1D2457302216E651654840DF9A19BF613F"},new[]{"HeadRegion502.cs","B0827EC6A1ED05F369CA1E7ED2FEA48E6C30FEA84C5AD95B56D30A900F3D1CE4"}})if(BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes("C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets/EUnityValidation01/HeadRegion502/Runtime/"+pair[0]))).Replace("-","")!=pair[1])throw new Exception("Product source changed");}File.WriteAllText(marker,"SCHEDULED");EditorApplication.delayCall+=()=>{File.AppendAllText(marker,"\nENTERED");try{CanvasView577.Start(260,"C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairDirections576/Compiled260/HeadCurve511.bytes","FinalFull260",System.Linq.Enumerable.Range(0,81).ToArray());File.AppendAllText(marker,"\nSTARTED");}catch(Exception e){File.AppendAllText(marker,"\nFAILED "+e);HeadRegion502.SetCurveInput511(null);string initial=root+"StartupFinalFull260/WARMUP_INITIAL540.json";if(File.Exists(initial))Application.runInBackground=File.ReadAllText(initial).Contains("\"oldBackground\":true");if(EditorApplication.isPlaying)EditorApplication.isPlaying=false;throw;}};result.Log("FinalFull260 actual paired Walk scheduled once; original whole canvas retained");}}



