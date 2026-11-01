using System;
using UnityEngine.Profiling;
// Standard public marker recorder only; do not turn on profiling/player settings.
// A zero GPU block count means unavailable, never zero-cost work.
public sealed class GpuTiming98:IDisposable{
 readonly string[] names={"WholeEye96 BVH visibility and joint selection","WholeEye98 current non-eye backing","WholeEye98 exact world underlay pack","WholeEye98 final compose"};readonly Recorder[] recorders;readonly bool[] prior;
 public GpuTiming98(){recorders=new Recorder[names.Length];prior=new bool[names.Length];for(int i=0;i<names.Length;i++){recorders[i]=Recorder.Get(names[i]);prior[i]=recorders[i].enabled;recorders[i].enabled=true;}}
 public Arr58 Read(){var a=new Arr58();for(int i=0;i<names.Length;i++){var r=recorders[i];a.Add(new Obj58{["marker"]=names[i],["valid"]=r.isValid,["gpuBlocks"]=r.gpuSampleBlockCount,["gpuNanoseconds"]=r.gpuElapsedNanoseconds,["cpuBlocks"]=r.sampleBlockCount,["cpuNanoseconds"]=r.elapsedNanoseconds,["measuredGPU"]=r.gpuSampleBlockCount>0,["synchronisedToCapturedSerial"]=false});}return a;}
 public void Dispose(){for(int i=0;i<names.Length;i++)recorders[i].enabled=prior[i];}
}
