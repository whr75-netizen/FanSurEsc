using System;
using System.IO;
using System.Collections.Generic;
using System.Globalization;
using UnityEngine;
using UnityEditor;
using UnityEditorInternal;
using Unity.Profiling;
using UnityEngine.Profiling;
public static class Cost587B {
 static string root;static Action restore;static bool active,oldProfiler,oldEditor,oldCPU,oldGPU;
 static string[] names;static double[] ms;static long[] bytes;static int[] events;static int firstFrame;
 static double deadline;static byte[] held;static Recorder gpuRaster,gpuReduce;static bool oldRaster,oldReduce;
 static ProfilerMarker[] markers;static HeadLocal367 host;static Vector3[] positions;static int step;static bool pending;
 static void Finish(string state,string error=""){
  if(!active)return;active=false;EditorApplication.update-=Tick;AssemblyReloadEvents.beforeAssemblyReload-=Cancel;
  try{
   using(var t=new StreamWriter(root+"COST587.tsv")){t.WriteLine("scope\twallMs\tmainThreadScopedBytes\tallocationEvents");for(int i=0;i<names.Length;i++)t.WriteLine(names[i]+"\t"+ms[i].ToString("R",CultureInfo.InvariantCulture)+"\t"+bytes[i]+"\t"+events[i]);}
   string F(long n)=>n.ToString(CultureInfo.InvariantCulture);
   File.WriteAllText(root+"GPU587.json","{\"rasterValid\":"+(gpuRaster!=null&&gpuRaster.isValid?"true":"false")+",\"rasterNs\":"+F(gpuRaster!=null?gpuRaster.gpuElapsedNanoseconds:0)+",\"rasterBlocks\":"+F(gpuRaster!=null?gpuRaster.gpuSampleBlockCount:0)+",\"reduceValid\":"+(gpuReduce!=null&&gpuReduce.isValid?"true":"false")+",\"reduceNs\":"+F(gpuReduce!=null?gpuReduce.gpuElapsedNanoseconds:0)+",\"reduceBlocks\":"+F(gpuReduce!=null?gpuReduce.gpuSampleBlockCount:0)+",\"scope\":\"one profiler frame batch; GPU values require valid nonzero matched sample counts, otherwise unmeasured\"}");
  } finally {
   if(gpuRaster!=null)gpuRaster.enabled=oldRaster;if(gpuReduce!=null)gpuReduce.enabled=oldReduce;
   UnityEngine.Profiling.Profiler.SetAreaEnabled(ProfilerArea.CPU,oldCPU);UnityEngine.Profiling.Profiler.SetAreaEnabled(ProfilerArea.GPU,oldGPU);UnityEngine.Profiling.Profiler.enabled=oldProfiler;ProfilerDriver.profileEditor=oldEditor;
   held=null;try{restore?.Invoke();}finally{File.WriteAllText(root+"status.json","{\"status\":\""+state+"\",\"error\":\""+error.Replace("\\","/").Replace("\"","'").Replace("\n"," ").Replace("\r"," ")+"\",\"profilerRestored\":"+(UnityEngine.Profiling.Profiler.enabled==oldProfiler&&ProfilerDriver.profileEditor==oldEditor?"true":"false")+"}");}
  }
 }
 static void Cancel(){Finish("UNMEASURED","Assembly reload");}
 static void Tick(){
  try{
   bool all=true;int last=ProfilerDriver.lastFrameIndex;
   for(int wanted=step;pending&&wanted==step;wanted++){
    if(events[wanted]>=0)continue;bool found=false;
    for(int frame=firstFrame;frame<=last&&!found;frame++)for(int thread=0;!found;thread++)using(var raw=ProfilerDriver.GetRawFrameDataView(frame,thread)){
     if(!raw.valid)break;int marker=raw.GetMarkerId(names[wanted]);if(marker==UnityEditor.Profiling.FrameDataView.invalidMarkerId)continue;int gc=raw.GetMarkerId("GC.Alloc");
     for(int i=0;i<raw.sampleCount;i++)if(raw.GetSampleMarkerId(i)==marker){long sum=0;int count=0,end=i+raw.GetSampleChildrenCountRecursive(i);for(int j=i+1;j<=end;j++)if(raw.GetSampleMarkerId(j)==gc){if(raw.GetSampleMetadataCount(j)<1)throw new Exception("GC size metadata unavailable");sum+=raw.GetSampleMetadataAsLong(j,0);count++;}bytes[wanted]=sum;events[wanted]=count;found=true;break;}
    }
    if(!found)all=false;
   }
   if(pending&&all){step++;pending=false;if(step==3&&!(bytes[0]==0&&events[0]==0&&events[1]==1&&events[2]==1&&bytes[1]>=1048576&&bytes[2]-bytes[1]==1048576)){Finish("UNMEASURED","Positive control failed");return;}if(step==names.Length){Finish("MEASURED_CPU_ALLOC");return;}}
   if(EditorApplication.timeSinceStartup>deadline){Finish("UNMEASURED","Raw scoped frame data did not arrive within60s");return;}
   if(!pending){firstFrame=Math.Max(0,ProfilerDriver.lastFrameIndex+1);double start=EditorApplication.timeSinceStartup;using(markers[step].Auto()){if(step==1)held=new byte[1048576];else if(step==2)held=new byte[2097152];else if(step>=3&&step<8)host.headEyes.area587.Prepare(host.headEyes,positions);else if(step>=8){bool on=(step-8)/2%2==0?(step-8)%2==1:(step-8)%2==0;EyeFeature348.UseLashArea587=on;host.RenderFrame();}}ms[step]=(EditorApplication.timeSinceStartup-start)*1000;EyeFeature348.UseLashArea587=false;GC.KeepAlive(held);pending=true;File.WriteAllText(root+"progress.json","{\"scopesExecuted\":"+(step+1)+",\"target\":18}");}
   EditorApplication.QueuePlayerLoopUpdate();
  }catch(Exception e){Finish("UNMEASURED",e.ToString());}
 }
 public static void Start(HeadLocal367 h,string output,Action onRestore){
  if(active||Directory.Exists(output))throw new Exception("Unique cost run required");root=output;restore=onRestore;Directory.CreateDirectory(root);
  var e=h.headEyes;
  for(int i=0;i<3;i++){EyeFeature348.UseLashArea587=false;h.RenderFrame();EyeFeature348.UseLashArea587=true;h.RenderFrame();}EyeFeature348.UseLashArea587=false;
  positions=e.full.motion.surface.outputs[1].sharedMesh.vertices;host=h;
  names=new string[18];ms=new double[18];bytes=new long[18];events=new int[18];for(int i=0;i<18;i++)events[i]=-1;
  names[0]="Codex.Area587.Empty";names[1]="Codex.Area587.OneMiB";names[2]="Codex.Area587.TwoMiB";
  for(int i=0;i<5;i++)names[3+i]="Codex.Area587.Prepare"+i;
  for(int i=0;i<10;i++){bool on=(i/2)%2==0?i%2==1:i%2==0;names[8+i]="Codex.Area587.Render"+i+(on?"_ON":"_OFF");}
  markers=new ProfilerMarker[18];for(int i=0;i<18;i++)markers[i]=new ProfilerMarker(names[i]);
  oldProfiler=UnityEngine.Profiling.Profiler.enabled;oldEditor=ProfilerDriver.profileEditor;oldCPU=UnityEngine.Profiling.Profiler.GetAreaEnabled(ProfilerArea.CPU);oldGPU=UnityEngine.Profiling.Profiler.GetAreaEnabled(ProfilerArea.GPU);active=true;
  try{
   ProfilerDriver.profileEditor=true;UnityEngine.Profiling.Profiler.enabled=true;UnityEngine.Profiling.Profiler.SetAreaEnabled(ProfilerArea.CPU,true);UnityEngine.Profiling.Profiler.SetAreaEnabled(ProfilerArea.GPU,true);
   gpuRaster=Recorder.Get("587 continuous lash area source");gpuReduce=Recorder.Get("587 lash area GPU reduction");oldRaster=gpuRaster.enabled;oldReduce=gpuReduce.enabled;gpuRaster.enabled=true;gpuReduce.enabled=true;
   firstFrame=Math.Max(0,ProfilerDriver.lastFrameIndex+1);File.WriteAllText(root+"status.json","{\"status\":\"MEASURING\"}");
   EyeFeature348.UseLashArea587=false;File.WriteAllText(root+"RESOURCE587.json","{\"ownedAreaTextureLogicalBytes\":"+e.area587.textureBytes+",\"runtimeReadback\":false,\"samples\":5,\"scope\":\"warm fixed-pose render calls exclude this diagnostic file writing/readbacks; existing render pipeline waits remain\"}");
   step=0;pending=false;deadline=EditorApplication.timeSinceStartup+60;EditorApplication.update+=Tick;AssemblyReloadEvents.beforeAssemblyReload+=Cancel;EditorApplication.QueuePlayerLoopUpdate();
  }catch(Exception ex){Finish("UNMEASURED",ex.ToString());throw;}
 }
}
