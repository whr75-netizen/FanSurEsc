using System;
using System.IO;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlaying||EditorApplication.isCompiling)throw new Exception("Stored provenance only; requires Edit/no compiling");
  const string input="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairContract570/Full570/";
  const string output="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/RegionContract572/Stored572/";
  int oldCross=CurveArea511.LastCrossings,oldEvents=CurveArea511.LastEvents;
  try{foreach(int frame in new[]{16,51,62,71,72,73,77})
  {
   string p=input+frame.ToString("D3"),o=output+frame.ToString("D3")+"_SOURCE_AXES.bin";if(File.Exists(o))throw new Exception("Source axes already exported");
   int x,y,w,h;using(var r=new BinaryReader(File.OpenRead(p+"_ON_AREAS.bin"))){x=r.ReadInt32();y=r.ReadInt32();w=r.ReadInt32();h=r.ReadInt32();}
   var graph=new List<CurveArea511.P[]>();using(var r=new BinaryReader(File.OpenRead(p+"_ON_CURVES.bin"))){int n=r.ReadInt32();for(int i=0;i<n;i++){var q=new CurveArea511.P[r.ReadInt32()];for(int j=0;j<q.Length;j++)q[j]=new CurveArea511.P(r.ReadSingle(),r.ReadSingle());graph.Add(q);}}
   var build=CapContract572.Create(graph,x,y,w,h,1.0);
   using(var b=new BinaryWriter(File.Create(o)))
   {
    b.Write(572);b.Write(frame);b.Write(build.sourceBranches.Count);
    for(int i=0;i<build.sourceBranches.Count;i++)
    {
     var f=build.sourceBranches[i];b.Write(build.transposed[i]);b.Write(f.boundaryId);b.Write(f.geometry.Count);
     foreach(var s in f.geometry){b.Write(s.lo);b.Write(s.hi);b.Write(s.l0);b.Write(s.l1);b.Write(s.r0);b.Write(s.r1);b.Write(s.left);b.Write(s.right);}
     foreach(var e in new[]{f.start566,f.end566}){b.Write(e.kind);b.Write(e.level);b.Write(e.left);b.Write(e.right);b.Write(e.leftId);b.Write(e.rightId);b.Write(e.neighbours.Count);foreach(string id in e.neighbours)b.Write(id);}
    }
   }
   result.Log("572 original source axis branches "+frame+" count="+build.sourceBranches.Count+"; no selector or rendering");
  }}finally{CurveArea511.LastCrossings=oldCross;CurveArea511.LastEvents=oldEvents;}
  result.Log("state compiling="+EditorApplication.isCompiling+" playing="+EditorApplication.isPlaying+" dirty="+EditorSceneManager.GetActiveScene().isDirty+" cloth="+ClothRegion524.Enabled+" body="+ClothRegion524.UseBodyScope551+" head="+HeadRegion502.Enabled+" negative="+HeadRegion502.UseNegativeRegions563+" branches="+HeadRegion502.UseNegativeBranches566+" profiler="+UnityEngine.Profiling.Profiler.enabled);
 }
}
