using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using Prefix24;

static class CpuTests24 {
 static int passed;static readonly List<string> names=new List<string>();
 static void Check(string name,Action action){action();passed++;names.Add(name);}
 static void MustFail(Action action){try{action();}catch(InvalidOperationException){return;}catch(IOException){return;}catch(ArgumentException){return;}throw new Exception("Expected rejection");}
 static void Assert(bool okay){if(!okay)throw new Exception("CPU assertion");}
 static byte[] Native<T>(T[] data)where T:struct{var handle=GCHandle.Alloc(data,GCHandleType.Pinned);try{var bytes=new byte[data.Length*Marshal.SizeOf<T>()];Marshal.Copy(handle.AddrOfPinnedObject(),bytes,0,bytes.Length);return bytes;}finally{handle.Free();}}
 static StepGate24 Submitted(){var g=new StepGate24();g.BeforeDispatch();g.DispatchReturned();g.BeginReads();return g;}
 static void Main(){
  var json=new System.Text.Json.JsonSerializerOptions{IncludeFields=true};
  Protocol24.Encode=value=>System.Text.Json.JsonSerializer.SerializeToUtf8Bytes(value,value.GetType(),json);
  Protocol24.Decode=(bytes,type)=>System.Text.Json.JsonSerializer.Deserialize(bytes,type,json);
  Assert(!Directory.Exists(CaseLock24.RunRoot));
  var c=Protocol24.LoadCase(CaseLock24.FixtureRoot,CaseLock24.ManifestSha);
  string temp=Path.Combine(Path.GetTempPath(),"prefix24-cpu-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(temp);
  Check("ABI and typed upload roundtrips",()=>{Assert(Marshal.SizeOf<F4>()==Protocol24.ExpectedStride<F4>()&&Marshal.SizeOf<U4>()==16&&Marshal.SizeOf<Subset24>()==32&&Marshal.SizeOf<Group24>()==48);Assert(Marshal.OffsetOf<Group24>(nameof(Group24.masks)).ToInt32()==16&&Marshal.OffsetOf<Group24>(nameof(Group24.tail)).ToInt32()==32&&Marshal.OffsetOf<Subset24>(nameof(Subset24.b)).ToInt32()==16);Assert(Native(Protocol24.Fours(Protocol24.Input(c,CaseLock24.FixtureRoot,"cells"))).SequenceEqual(Protocol24.Input(c,CaseLock24.FixtureRoot,"cells")));Assert(Native(Protocol24.UInts(Protocol24.Input(c,CaseLock24.FixtureRoot,"frame"))).SequenceEqual(Protocol24.Input(c,CaseLock24.FixtureRoot,"frame")));Assert(Native(Protocol24.Groups(Protocol24.Input(c,CaseLock24.FixtureRoot,"old-best"))).SequenceEqual(Protocol24.Input(c,CaseLock24.FixtureRoot,"old-best")));});
  Check("Manifest hash is mandatory",()=>MustFail(()=>Protocol24.LoadCase(CaseLock24.FixtureRoot,new string('0',64))));
  Check("F103 header and bounds validated",()=>Protocol24.ValidateCaseData(c,CaseLock24.FixtureRoot));
  Check("CreateNew preserves existing bytes",()=>{var p=Path.Combine(temp,"once.bin");Protocol24.Create(p,new byte[]{1,2});MustFail(()=>Protocol24.Create(p,new byte[]{3}));Assert(File.ReadAllBytes(p).SequenceEqual(new byte[]{1,2}));});
  Check("Path traversal rejected",()=>{MustFail(()=>Protocol24.Child(temp,"../escape"));MustFail(()=>Protocol24.Child(temp,".."));});
  Check("Pre-dispatch failure can release without success",()=>{var g=new StepGate24();g.Fail();Assert(g.CanRelease);g.MarkFinalized();Assert(!g.CanComplete);});
  Check("Two callbacks settle before release; one dispatch only",()=>{var g=Submitted();g.BeforeRead("a");g.BeforeRead("b");g.CompleteRead("a",true,false);Assert(!g.CanRelease);g.CompleteRead("b",true,false);Assert(!g.CanRelease);g.EndReads();Assert(g.CanRelease);g.MarkFinalized();Assert(g.CanComplete&&g.DispatchCalls==1);MustFail(()=>g.BeforeDispatch());});
  Check("Unknown dispatch cannot release or replay",()=>{var g=new StepGate24();g.BeforeDispatch();g.Fail();Assert(!g.CanRelease);MustFail(()=>g.MarkFinalized());MustFail(()=>g.BeforeDispatch());});
  Check("Uncertain request remains retained after other callbacks",()=>{var g=Submitted();g.BeforeRead("a");g.ReadRequestUncertain();g.EndReads();g.CompleteRead("a",true,false);Assert(!g.CanRelease&&!g.CanComplete);});
  Check("GPU-error callback permits settled cleanup but no success",()=>{var g=Submitted();g.BeforeRead("a");g.EndReads();g.CompleteRead("a",true,true);Assert(g.CanRelease);g.MarkFinalized();Assert(!g.CanComplete);});
  Check("Incomplete callback is not valid zero data",()=>{var g=Submitted();g.BeforeRead("a");g.EndReads();g.CompleteRead("a",false,false);Assert(!g.CanRelease&&g.Pending==1);});
  Check("Duplicate callback rejected",()=>{var g=Submitted();g.BeforeRead("a");g.CompleteRead("a",true,false);MustFail(()=>g.CompleteRead("a",true,false));g.Fail();g.EndReads();Assert(g.CanRelease);g.MarkFinalized();Assert(!g.CanComplete);});
  Check("Same stage cannot be claimed twice",()=>{string root=Path.Combine(temp,"claims",c.RunId);Protocol24.ClaimStage(c,CaseLock24.ManifestSha,root,1);MustFail(()=>Protocol24.ClaimStage(c,CaseLock24.ManifestSha,root,1));});
  Check("Next stage refuses incomplete predecessor",()=>{string root=Path.Combine(temp,"claims",c.RunId);MustFail(()=>Protocol24.ClaimStage(c,CaseLock24.ManifestSha,root,2));Assert(!Directory.Exists(Protocol24.StagePath(root,2)));});
  Check("CPU-simulated completion cannot authorize GPU stage",()=>{
   string root=Path.Combine(temp,"claims",c.RunId);var outputs=c.InputFiles.Where(x=>x.Stage==1).Select(x=>new Blob24{Name=x.Name,File=x.Name+".bin",Stage=1,Bytes=x.Bytes,Sha256=x.Sha256}).ToArray();
   var r=new Receipt24{ExecutionKind="cpu-simulated",RunId=c.RunId,Stage=1,CaseSha256=CaseLock24.ManifestSha,SourceId=c.SourceId,ShaderSha256=c.ShaderSha256,DispatchCalls=1,Success=true,StateEqual=true,ResourcesReleased=true,BeforeStateSha256="same",AfterStateSha256="same",Outputs=outputs};
   Protocol24.CheckReceipt(c,CaseLock24.ManifestSha,1,r,"cpu-simulated");MustFail(()=>Protocol24.CheckReceipt(c,CaseLock24.ManifestSha,1,r,"gpu-prefix"));
   Protocol24.CreateJson(Path.Combine(Protocol24.StagePath(root,1),"COMPLETE.json"),r);MustFail(()=>Protocol24.ClaimStage(c,CaseLock24.ManifestSha,root,2));
  });
  Check("Tampered output cannot validate",()=>{var spec=c.InputFiles.Single(x=>x.Name=="groups");var bytes=Protocol24.ReadBounded(Path.Combine(CaseLock24.FixtureRoot,"fixture",spec.File),spec.Bytes);Protocol24.ValidateOutput(c,2,"groups",bytes);bytes[0]^=1;MustFail(()=>Protocol24.ValidateOutput(c,2,"groups",bytes));});
  Check("State/cleanup mismatch cannot pass receipt",()=>{var r=new Receipt24{ExecutionKind="gpu-prefix",RunId=c.RunId,Stage=1,CaseSha256=CaseLock24.ManifestSha,SourceId=c.SourceId,ShaderSha256=c.ShaderSha256,DispatchCalls=1,Success=true,StateEqual=false,ResourcesReleased=true,BeforeStateSha256="a",AfterStateSha256="b",Outputs=new Blob24[0]};MustFail(()=>Protocol24.CheckReceipt(c,CaseLock24.ManifestSha,1,r,"gpu-prefix"));});
  Assert(!Directory.Exists(CaseLock24.RunRoot));
  string[] assemblies=AppDomain.CurrentDomain.GetAssemblies().Select(a=>a.GetName().Name).ToArray();Assert(!assemblies.Any(n=>n.StartsWith("UnityEngine")||n.StartsWith("UnityEditor")||n=="Prefix24Host"));
  string[] gpu=Process.GetCurrentProcess().Modules.Cast<ProcessModule>().Select(m=>m.ModuleName.ToLowerInvariant()).Where(n=>new[]{"d3d11.dll","d3d12.dll","dxgi.dll","amdxx64.dll","amddxx64.dll","nvwgf2umx.dll"}.Contains(n)).ToArray();Assert(gpu.Length==0);
  var result=new Result{Passed=passed,Checks=names.ToArray(),TempArtifacts=temp,ProductionRunRootCreated=false,HostAssemblyExecuted=false,GPUDeviceCreated=false,GPUDriverModules=gpu,LoadedAssemblies=assemblies};
  Protocol24.CreateJson(Path.Combine(AppContext.BaseDirectory,"CPU_TEST_RESULT.json"),result);Console.WriteLine("CPU tests passed="+passed+"; production run untouched; Unity/host assembly not loaded; GPU0");
 }
 [System.Runtime.Serialization.DataContract] sealed class Result {
  [System.Runtime.Serialization.DataMember] public int Passed;
  [System.Runtime.Serialization.DataMember] public string[] Checks,GPUDriverModules,LoadedAssemblies;
  [System.Runtime.Serialization.DataMember] public string TempArtifacts;
  [System.Runtime.Serialization.DataMember] public bool ProductionRunRootCreated,HostAssemblyExecuted,GPUDeviceCreated;
 }
}
