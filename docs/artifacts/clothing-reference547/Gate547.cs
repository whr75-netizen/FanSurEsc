using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
internal class CommandScript:IRunCommand
{
 const string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/";
 [Serializable]class Row{public string name;public int part,x,y,w,h,groupsBefore,groupsAfter,changed;public List<int>removed=new(),added=new();public double referenceMs,candidateMs;}
 [Serializable]class Report{public string contract="Only Groups input Curves -> Source. Fitted area, solver, costs, fill, ink, occlusion unchanged. Stored input, not new rendering.";public List<Row>rows=new();}
 static List<Vector2[]> Rings(BinaryReader b){var rs=new List<Vector2[]>();int n=b.ReadInt32();for(int i=0;i<n;i++){var r=new Vector2[b.ReadInt32()];for(int j=0;j<r.Length;j++)r[j]=new Vector2(b.ReadSingle(),b.ReadSingle());rs.Add(r);}return rs;}
 static void Run(Report report,string output,string name,int part,int x,int y,int w,int h,float[] a,bool[] expected,List<Vector2[]> source,List<Vector2[]> curves)
 {
  double start=EditorApplication.timeSinceStartup;var oldg=BoundarySpan543.Groups(curves,a,new RectInt(x,y,w,h));var old=HeadRegion502.SelectRegionsCompact544(a,w,h,oldg);double before=(EditorApplication.timeSinceStartup-start)*1000;
  if(!old.SequenceEqual(expected))throw new Exception("Stored baseline drift "+name+" part"+part);
  start=EditorApplication.timeSinceStartup;var newg=BoundarySpan543.Groups(source,a,new RectInt(x,y,w,h));var next=HeadRegion502.SelectRegionsCompact544(a,w,h,newg);double after=(EditorApplication.timeSinceStartup-start)*1000;
  foreach(var g in newg)if(g.Any(i=>next[i]!=next[g[0]]))throw new Exception("Group constraint failed");
  var row=new Row{name=name,part=part,x=x,y=y,w=w,h=h,groupsBefore=oldg.Count,groupsAfter=newg.Count,referenceMs=before,candidateMs=after};
  for(int i=0;i<old.Length;i++)if(old[i]!=next[i]){row.changed++;if(next[i])row.added.Add(i);else row.removed.Add(i);}
  File.WriteAllBytes(output+name+"_PART"+part+".bin",next.Select(v=>(byte)(v?1:0)).ToArray());report.rows.Add(row);
 }
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlaying||ClothRegion524.Enabled)throw new Exception("Edit/OFF required");string output=Root+"Fix547/StoredGate/";if(Directory.Exists(output))throw new Exception("Existing output; recover, never duplicate");Directory.CreateDirectory(output);var report=new Report();
  for(int frame=0;frame<=80;frame++)for(int part=1;part<=3;part++)
  using(var b=new BinaryReader(File.OpenRead(Root+"Span543/FullLoop543/"+frame.ToString("D3")+"_SPAN_PART"+part+".bin")))
  {
   int x=b.ReadInt32(),y=b.ReadInt32(),w=b.ReadInt32(),h=b.ReadInt32();var a=new float[w*h];var expected=new bool[w*h];for(int i=0;i<a.Length;i++)a[i]=b.ReadSingle();for(int i=0;i<a.Length;i++)expected[i]=b.ReadBoolean();var source=Rings(b);var curves=Rings(b);Run(report,output,frame.ToString("D3"),part,x,y,w,h,a,expected,source,curves);
  }
  for(int r=0;r<4;r++)for(int phase=0;phase<2;phase++)
  {
   string name="thin"+r+"_"+phase;List<Vector2[]> source;using(var s=new BinaryReader(File.OpenRead(Root+"Integrate539/"+name+"_SOURCE.bin")))source=Rings(s);
   using(var b=new BinaryReader(File.OpenRead(Root+"Integrate539/MathWholeCS/"+name+".bin")))
   {
    var curves=Rings(b);int x=b.ReadInt32(),y=b.ReadInt32(),w=b.ReadInt32(),h=b.ReadInt32();var a=new float[w*h];for(int i=0;i<a.Length;i++)a[i]=b.ReadSingle();var expected=File.ReadAllBytes(Root+"Span543/Results/"+name+".bin").Select(v=>v!=0).ToArray();Run(report,output,name,3,x,y,w,h,a,expected,source,curves);
   }
  }
  File.WriteAllText(Root+"Fix547/STORED_GATE547.json",JsonUtility.ToJson(report,true));result.Log("Stored gate complete "+report.rows.Count+" inputs; changed cases="+report.rows.Count(r=>r.changed>0)+" added="+report.rows.Sum(r=>r.added.Count)+" removed="+report.rows.Sum(r=>r.removed.Count)+"; no Play/render/product mutation.");
 }
}
