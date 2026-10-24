using System;
using System.IO;
using System.Collections.Generic;
using UnityEditor;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlaying||EditorApplication.isCompiling)throw new Exception("Stored metadata only; requires Edit/no compiling");
  const string input="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairContract570/Full570/";
  const string output="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/RegionContract572/Stored572/";
  int oldCross=CurveArea511.LastCrossings,oldEvents=CurveArea511.LastEvents;
  try{foreach(int frame in new[]{16,51,62,71,72,73,77})
  {
   string p=input+frame.ToString("D3"),o=output+frame.ToString("D3");if(File.Exists(o+"_DECISIONS.bin"))throw new Exception("Metadata exists; inspect rather than repeat");
   int x,y,w,h;using(var r=new BinaryReader(File.OpenRead(p+"_ON_AREAS.bin"))){x=r.ReadInt32();y=r.ReadInt32();w=r.ReadInt32();h=r.ReadInt32();}
   var graph=new List<CurveArea511.P[]>();using(var r=new BinaryReader(File.OpenRead(p+"_ON_CURVES.bin"))){int n=r.ReadInt32();for(int i=0;i<n;i++){var q=new CurveArea511.P[r.ReadInt32()];for(int j=0;j<q.Length;j++)q[j]=new CurveArea511.P(r.ReadSingle(),r.ReadSingle());graph.Add(q);}}
   var build=CapContract572.Create(graph,x,y,w,h,1.0);
   using(var r=new BinaryReader(File.OpenRead(o+"_CURVES.bin"))){if(r.ReadInt32()!=build.rings.Count)throw new Exception("Ring count mismatch");foreach(var ring in build.rings){if(r.ReadInt32()!=ring.Length)throw new Exception("Control count mismatch");foreach(var q in ring)if(r.ReadDouble()!=q.x||r.ReadDouble()!=q.y)throw new Exception("Ring value mismatch");}if(r.BaseStream.Position!=r.BaseStream.Length)throw new Exception("Trailing curves");}
   using(var b=new BinaryWriter(File.Create(o+"_DECISIONS.bin")))
   {
    b.Write(572);b.Write(frame);b.Write(build.decisions.Count);
    foreach(var d in build.decisions)
    {
     b.Write(d.sourceBranch);b.Write(d.axis);b.Write(d.mode);b.Write(d.splitRule);
     foreach(double z in new[]{d.pitch,d.sourceLo,d.sourceHi,d.fillLo,d.fillHi,d.keepLo,d.keepHi})b.Write(z);
     b.Write(d.insertedRing);foreach(var path in new[]{d.positiveLeftBoundary,d.positiveRightBoundary}){b.Write(path.Length);foreach(long id in path)b.Write(id);}
     foreach(var port in new[]{d.sourceStart,d.sourceEnd}){b.Write(port.kind);b.Write(port.level);b.Write(port.left);b.Write(port.right);b.Write(port.leftId);b.Write(port.rightId);}
    }
   }
   result.Log("572 metadata "+frame+" records="+build.decisions.Count+" existing derived curve values exact; no area/selector/render rerun");
  }}finally{CurveArea511.LastCrossings=oldCross;CurveArea511.LastEvents=oldEvents;}
 }
}
