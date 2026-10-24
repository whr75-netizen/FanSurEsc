using System;
using System.IO;
using System.Collections.Generic;
using UnityEditor;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlaying||EditorApplication.isCompiling)throw new Exception("Stored output contract only; requires Edit/no compiling");
  const string root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/RegionContract572/Stored572/";
  const string input="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairContract570/Full570/";
  int cross=CurveArea511.LastCrossings,events=CurveArea511.LastEvents;
  try{foreach(int frame in new[]{16,51,62,71,72,73,77})
  {
   string p=root+frame.ToString("D3");if(File.Exists(p+"_RESOLVED.bin"))throw new Exception("Resolved contract exists");
   int x,y,w,h;bool[] mask;using(var r=new BinaryReader(File.OpenRead(p+"_LAYOUT.bin"))){if(r.ReadInt32()!=572||r.ReadInt32()!=frame)throw new Exception("Layout header");x=r.ReadInt32();y=r.ReadInt32();w=r.ReadInt32();h=r.ReadInt32();r.BaseStream.Position+=4*w*h;mask=new bool[w*h];for(int i=0;i<mask.Length;i++)mask[i]=r.ReadBoolean();}
   var graph=new List<CurveArea511.P[]>();using(var r=new BinaryReader(File.OpenRead(input+frame.ToString("D3")+"_ON_CURVES.bin"))){int n=r.ReadInt32();for(int i=0;i<n;i++){var q=new CurveArea511.P[r.ReadInt32()];for(int j=0;j<q.Length;j++)q[j]=new CurveArea511.P(r.ReadSingle(),r.ReadSingle());graph.Add(q);}}
   var bld=CapContract572.Create(graph,x,y,w,h,1.0);CapContract572.Finish(bld,mask,x,y,w,h);
   int tested=0,bad=0;using(var b=new BinaryWriter(File.Create(p+"_RESOLVED.bin")))
   {
    b.Write(572);b.Write(frame);b.Write(bld.decisions.Count);
    foreach(var d in bld.decisions){b.Write(d.sourceBranch);b.Write(d.validationScope);b.Write(d.selectedMode);b.Write(d.invalidComponents);b.Write(d.retainedCells.Length);foreach(int c in d.retainedCells)b.Write(c);b.Write(d.selectedPorts.Length);foreach(var port in d.selectedPorts){b.Write(port.sourceSide);b.Write(port.from);b.Write(port.to);b.Write(port.source.leftId);b.Write(port.source.rightId);}if(d.invalidComponents>=0){tested++;bad+=d.invalidComponents;}}
   }
   result.Log("572 stored C# output contract frame="+frame+" open="+tested+" invalid="+bad+"; no area/selector/render rerun");
  }}finally{CurveArea511.LastCrossings=cross;CurveArea511.LastEvents=events;}
 }
}
