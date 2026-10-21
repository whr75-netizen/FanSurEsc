#if UNITY_EDITOR
using System;
using System.IO;
using System.Diagnostics;
using UnityEditor;

// Explicit-start paired Compute measurement. No recorders or stage timers.
// Fixed stored input is diagnostic only; no runtime animation cache is added.
public static class AreaBench508
{
    const string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Area508/UnityPairs/";
    const string Inputs="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/";
    static HeadArea505.Input input;static HeadArea505.Material[] materials;
    static HeadArea505.Result expected;static StreamWriter csv;
    static bool active;static int step;static double deadline;
    static string F(double v)=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture);
    static int Differences(HeadArea505.Result result)
    {
        int different=0;for(int i=0;i<result.lower.Length;i++)
        {if(BitConverter.SingleToInt32Bits(result.lower[i])!=BitConverter.SingleToInt32Bits(expected.lower[i]))different++;if(BitConverter.SingleToInt32Bits(result.upper[i])!=BitConverter.SingleToInt32Bits(expected.upper[i]))different++;}
        if(result.ambiguousFragments!=expected.ambiguousFragments)throw new Exception("Ambiguity differs");return different;
    }
    static void Finish(string status,string error="")
    {
        EditorApplication.update-=Tick;active=false;HeadArea505.UseActivePolygons508=false;
        csv?.Dispose();csv=null;input=null;materials=null;expected=null;
        File.WriteAllText(Root+"status.json","{\"status\":\""+status+"\",\"measuredCalls\":"+Math.Max(0,step)+",\"callbackRemoved\":true,\"candidateOFF\":true,\"globalProfiler\":"+(UnityEngine.Profiling.Profiler.enabled?"true":"false")+",\"error\":\""+error.Replace("\\","/").Replace("\"","'").Replace("\n"," ").Replace("\r"," ")+"\"}");
    }
    static void Tick()
    {
        if(!active)return;
        if(!EditorApplication.isPlaying||EditorApplication.isPaused||EditorApplication.isCompiling||EditorApplication.timeSinceStartup>deadline)
        {Finish("CANCELLED","Play/pause/compilation changed or180s deadline");return;}
        try
        {
            if(step==-2){HeadArea505.UseActivePolygons508=false;expected=HeadArea505.Compute(input,materials);step++;return;}
            if(step==-1){HeadArea505.UseActivePolygons508=true;int d=Differences(HeadArea505.Compute(input,materials));HeadArea505.UseActivePolygons508=false;if(d!=0)throw new Exception("Warmup differs");step++;return;}
            if(step>=10){Finish("COMPLETED");return;}
            int pair=step/2;bool candidate=((step%2)^(pair%2))==1;
            HeadArea505.UseActivePolygons508=candidate;
            // Heap snapshots and collection counters are outside the Compute timer.
            // They are live heap observations, never total allocation estimates.
            long liveBefore=UnityEngine.Profiling.Profiler.GetMonoUsedSizeLong(),reservedBefore=UnityEngine.Profiling.Profiler.GetMonoHeapSizeLong();
            int gcBefore=GC.CollectionCount(0);long allocatedBefore=GC.GetAllocatedBytesForCurrentThread();
            long start=Stopwatch.GetTimestamp();var result=HeadArea505.Compute(input,materials);
            double elapsed=1000.0*(Stopwatch.GetTimestamp()-start)/Stopwatch.Frequency;
            long allocated=GC.GetAllocatedBytesForCurrentThread()-allocatedBefore;int gc=GC.CollectionCount(0)-gcBefore;
            long liveAfter=UnityEngine.Profiling.Profiler.GetMonoUsedSizeLong(),reservedAfter=UnityEngine.Profiling.Profiler.GetMonoHeapSizeLong();
            HeadArea505.UseActivePolygons508=false;int differences=Differences(result);
            csv.WriteLine(string.Join(",",new[]{pair.ToString(),candidate?"candidate":"reference",F(elapsed),F(result.milliseconds),differences.ToString(),gc.ToString(),allocated.ToString(),liveBefore.ToString(),liveAfter.ToString(),reservedBefore.ToString(),reservedAfter.ToString()}));csv.Flush();step++;
            File.WriteAllText(Root+"progress.txt",step+"/10 non-instrumented paired Compute calls");
            if(differences!=0)throw new Exception("Measured area differs");
        }
        catch(Exception ex){Finish("FAILED",ex.ToString());}
    }
    [MenuItem("Tools/EValidation/Compare active area508")]
    public static void Start()
    {
        if(active||Directory.Exists(Root))throw new Exception("Preserve508 run");
        if(!EditorApplication.isPlaying||EditorApplication.isPaused||EditorApplication.isCompiling||HeadArea505.UseActivePolygons508||HeadRegion502.Enabled||HeadRegion502.UseVisibleArea505||HairBoundary491.Enabled||UnityEngine.Profiling.Profiler.enabled)throw new Exception("Expected restored Play, all experiments/profilerOFF");
        Directory.CreateDirectory(Root);materials=AreaTiming507.ReadMaterials(Inputs+"Area505/");input=AreaTiming507.Read(Inputs+"Loop499/022.allmesh",materials);
        long before=GC.GetAllocatedBytesForCurrentThread();var sentinel=new byte[1048576];long sentinelAllocated=GC.GetAllocatedBytesForCurrentThread()-before;GC.KeepAlive(sentinel);
        File.WriteAllText(Root+"manifest.json","{\"framework\":\""+System.Runtime.InteropServices.RuntimeInformation.FrameworkDescription+"\",\"input\":\"Loop499/022.allmesh\",\"repeatsPerMode\":5,\"noRecorders\":true,\"noStageTimers\":true,\"noForcedGC\":true,\"sentinelAllocatedBytes\":"+sentinelAllocated+",\"allocatedBytesValid\":"+(sentinelAllocated>=1048576?"true":"false")+",\"heapSnapshotsAreNotAllocationOrPeak\":true,\"maxGeneration\":"+GC.MaxGeneration+"}");
        csv=new StreamWriter(Root+"paired.csv");csv.WriteLine("pair,mode,outerComputeMs,resultComputeMs,areaBitDifferences,gen0Collections,allocationApiDelta,monoLiveBefore,monoLiveAfter,monoReservedBefore,monoReservedAfter");csv.Flush();
        step=-2;deadline=EditorApplication.timeSinceStartup+180;active=true;EditorApplication.update+=Tick;
    }
}
#endif
