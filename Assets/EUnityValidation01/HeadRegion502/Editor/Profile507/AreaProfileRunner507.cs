#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections.Generic;
using System.Diagnostics;
using UnityEditor;
using Unity.Profiling;
using Unity.Profiling.LowLevel.Unsafe;

// Explicit Editor-only stored-input measurement. No renderer or gameplay calls.
public static class AreaProfileRunner507
{
    const string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Profile507/Run01/";
    const string Inputs="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/";
    const int Repeats=5;
    sealed class Slot
    {
        public string name,unit;public ProfilerRecorder recorder;
        public long value,count;public int samples;public bool valid;
    }
    static bool active;static int step;static double deadline,calibrationMs;
    static HeadArea505.Input input;static HeadArea505.Material[] materials;
    static HeadArea505.Result expected;static StreamWriter csv;
    static bool profilerBefore;static readonly List<Slot> window=new List<Slot>();
    static readonly string[] MarkerNames={"GC.Alloc","GC.Collect","GarbageCollector.CollectIncremental"};
    static string F(double n)=>n.ToString("R",System.Globalization.CultureInfo.InvariantCulture);
    static string Escape(string s)=>s.Replace("\\","/").Replace("\"","'").Replace("\r"," ").Replace("\n"," ");
    static Slot Open(string name,int capacity)
    {
        var slot=new Slot{name=name,unit="unavailable"};var handles=new List<ProfilerRecorderHandle>();
        ProfilerRecorderHandle.GetAvailable(handles);
        foreach(var h in handles)
        {
            var d=ProfilerRecorderHandle.GetDescription(h);if(d.Name!=name)continue;
            slot.unit=d.UnitType.ToString();
            slot.recorder=ProfilerRecorder.StartNew(d.Category,name,capacity,
                ProfilerRecorderOptions.SumAllSamplesInFrame|ProfilerRecorderOptions.CollectOnlyOnCurrentThread);
            slot.valid=slot.recorder.Valid;break;
        }
        return slot;
    }
    static void Close(Slot slot)
    {
        if(!slot.valid)return;
        try
        {
            slot.recorder.Stop();slot.samples=slot.recorder.Count;
            for(int i=0;i<slot.samples;i++){var s=slot.recorder.GetSample(i);slot.value+=s.Value;slot.count+=s.Count;}
        }
        finally{slot.recorder.Dispose();}
    }
    static int Different(HeadArea505.Result r)
    {
        int count=0;for(int i=0;i<r.lower.Length;i++)
        {if(BitConverter.SingleToInt32Bits(r.lower[i])!=BitConverter.SingleToInt32Bits(expected.lower[i]))count++;
         if(BitConverter.SingleToInt32Bits(r.upper[i])!=BitConverter.SingleToInt32Bits(expected.upper[i]))count++;}
        return count;
    }
    static void Finish(string status,string error="")
    {
        active=false;EditorApplication.update-=Tick;csv?.Dispose();csv=null;
        var sb=new StringBuilder("{\"scope\":\"whole diagnostic window on current thread, includes between-call Editor GC; not attributable solely to Compute\",\"markers\":[");
        for(int i=0;i<window.Count;i++)
        {
            var slot=window[i];Close(slot);if(i>0)sb.Append(',');
            sb.Append("{\"name\":\"").Append(slot.name).Append("\",\"valid\":").Append(slot.valid?"true":"false")
                .Append(",\"unit\":\"").Append(slot.unit).Append("\",\"value\":").Append(slot.value)
                .Append(",\"eventCount\":").Append(slot.count).Append(",\"samples\":").Append(slot.samples).Append('}');
        }
        sb.Append("]}");File.WriteAllText(Root+"gc_window.json",sb.ToString());window.Clear();
        File.WriteAllText(Root+"status.json","{\"status\":\""+status+"\",\"error\":\""+Escape(error)+
            "\",\"completedMeasuredCalls\":"+Math.Max(0,step)+",\"expectedMeasuredCalls\":"+(Repeats*3)+
            ",\"timerPairCalibrationMs\":"+F(calibrationMs)+",\"profilerEnabledBefore\":"+(profilerBefore?"true":"false")+
            ",\"profilerEnabledAfter\":"+(UnityEngine.Profiling.Profiler.enabled?"true":"false")+"}");
        input=null;materials=null;expected=null;
    }
    static void Tick()
    {
        if(!active)return;
        if(!EditorApplication.isPlaying||EditorApplication.isPaused||EditorApplication.isCompiling||EditorApplication.timeSinceStartup>deadline)
        {Finish("CANCELLED","Play/pause/compilation changed or240s deadline");return;}
        try
        {
            if(step==-2)
            {
                expected=HeadArea505.Compute(input,materials);step++;File.WriteAllText(Root+"progress.txt","Warmup original complete");return;
            }
            if(step==-1)
            {
                var warm=AreaTiming507.Compute(input,materials);int diff=Different(warm);
                if(diff!=0){Finish("FAILED","Instrumented warmup area differs: "+diff);return;}
                step++;foreach(var name in MarkerNames.Skip(1))window.Add(Open(name,2048));
                File.WriteAllText(Root+"progress.txt","Warmup instrumented complete; measurement starts");return;
            }
            // One extra Editor update lets the final call's deferred frame GC be observed.
            if(step>=Repeats*3){Finish("COMPLETED");return;}
            int repeat=step/3,mode=(step%3+repeat)%3;bool instrumented=mode==2,recorded=mode!=0;
            AreaTiming507.Reset();var slots=new List<Slot>();
            if(recorded)foreach(var name in MarkerNames)slots.Add(Open(name,1));
            HeadArea505.Result result=null;long allocation=0;double elapsed=0;int[] collections=new int[3];
            try
            {
                for(int i=0;i<3;i++)collections[i]=GC.CollectionCount(i);
                long before=GC.GetAllocatedBytesForCurrentThread(),start=Stopwatch.GetTimestamp();
                result=instrumented?AreaTiming507.Compute(input,materials):HeadArea505.Compute(input,materials);
                elapsed=1000.0*(Stopwatch.GetTimestamp()-start)/Stopwatch.Frequency;
                allocation=GC.GetAllocatedBytesForCurrentThread()-before;
                for(int i=0;i<3;i++)collections[i]=GC.CollectionCount(i)-collections[i];
            }
            finally{foreach(var slot in slots)Close(slot);}
            var ticks=(long[])AreaTiming507.Ticks.Clone();var calls=(long[])AreaTiming507.Calls.Clone();
            int differences=Different(result);long timerPairs=calls.Sum();
            var row=new List<string>{repeat.ToString(),mode.ToString(),F(elapsed),F(result.milliseconds),allocation.ToString(),
                collections[0].ToString(),collections[1].ToString(),collections[2].ToString(),differences.ToString(),timerPairs.ToString(),F(timerPairs*calibrationMs)};
            foreach(var name in MarkerNames)
            {
                var slot=slots.FirstOrDefault(x=>x.name==name);
                row.Add(slot!=null&&slot.valid?"1":"0");row.Add((slot?.value??0).ToString());
                row.Add((slot?.count??0).ToString());row.Add((slot?.samples??0).ToString());
            }
            for(int i=0;i<(int)AreaTiming507.Stage.Count;i++){row.Add(F(1000.0*ticks[i]/Stopwatch.Frequency));row.Add(calls[i].ToString());}
            csv.WriteLine(string.Join(",",row));csv.Flush();step++;
            File.WriteAllText(Root+"progress.txt",step+"/"+(Repeats*3)+" measured area-only calls; last mode="+mode);
            if(differences!=0)Finish("FAILED","Instrumented output differs: "+differences);
        }
        catch(Exception ex){Finish("FAILED",ex.ToString());}
    }
    [MenuItem("Tools/EValidation/Measure stored area507")]
    public static void Start()
    {
        if(active)throw new InvalidOperationException("507 already running");
        if(Directory.Exists(Root))throw new InvalidOperationException("Preserve existing507 output");
        if(!EditorApplication.isPlaying||EditorApplication.isPaused||EditorApplication.isCompiling||HeadRegion502.Enabled||HeadRegion502.UseVisibleArea505||HairBoundary491.Enabled)
            throw new InvalidOperationException("Expected restored original Play with all experimentsOFF");
        Directory.CreateDirectory(Root);profilerBefore=UnityEngine.Profiling.Profiler.enabled;
        long load=Stopwatch.GetTimestamp();materials=AreaTiming507.ReadMaterials(Inputs+"Area505/");
        input=AreaTiming507.Read(Inputs+"Loop499/022.allmesh",materials);
        double loadMs=1000.0*(Stopwatch.GetTimestamp()-load)/Stopwatch.Frequency;
        calibrationMs=AreaTiming507.Calibrate(200000);
        File.WriteAllText(Root+"manifest.json","{\"scope\":\"Unity Editor stored505.Compute only; no renderer call, projection/build, loading or capture inside timing\",\"framework\":\""+Escape(System.Runtime.InteropServices.RuntimeInformation.FrameworkDescription)+"\",\"representative\":\"Loop499/022.allmesh\",\"phase\":"+F(input.phase)+
            ",\"repeatsPerMode\":"+Repeats+",\"modes\":[\"0 original without per-call recorder\",\"1 original with GC recorders\",\"2 instrumented copy with GC recorders\"],\"loadOutsideComputeMs\":"+F(loadMs)+
            ",\"maxGeneration\":"+GC.MaxGeneration+",\"gcWindowIsCommonToAllMeasuredModes\":true,\"noForcedGC\":true,\"noGlobalProfilerChange\":true}");
        csv=new StreamWriter(Root+"measurements.csv");
        var header=new List<string>{"repeat","mode","outerComputeMs","resultComputeMs","allocatedBytes","gen0Collections","gen1Collections","gen2Collections","areaBitDifferences","timerPairs","estimatedTimerOverheadMs"};
        foreach(var name in new[]{"GCAlloc","GCCollect","GCIncremental"})header.AddRange(new[]{name+"Valid",name+"ValueNs",name+"Events",name+"Samples"});
        foreach(var stage in Enum.GetNames(typeof(AreaTiming507.Stage)).Where(x=>x!="Count")){header.Add(stage+"Ms");header.Add(stage+"Calls");}
        csv.WriteLine(string.Join(",",header));csv.Flush();step=-2;deadline=EditorApplication.timeSinceStartup+240;active=true;EditorApplication.update+=Tick;
    }
}
#endif
