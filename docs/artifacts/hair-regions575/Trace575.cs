using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
public static class Trace575
{
 const string Input="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairRegions574/Full574/";
 const string Output="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairRegions575/Trace575/";
 static string R(double d)=>d.ToString("R",System.Globalization.CultureInfo.InvariantCulture);
 static List<int[]> Groups(List<CurveArea511.P[]> graph,int x,int y,int w,int h,out List<NegativeRegion563.Feature> first,out List<NegativeRegion563.Feature> second)
 {
  var a=new NegativeRegion563(x,y,w,h,false,true);CurveArea511.Compute(graph,x,y,w,h,a);first=a.Branches566();
  var swapped=new List<CurveArea511.P[]>();foreach(var ring in graph){var q=new CurveArea511.P[ring.Length];for(int i=0;i<q.Length;i++){var v=ring[ring.Length-1-i];q[i]=new CurveArea511.P(v.y,v.x);}swapped.Add(q);}
  var b=new NegativeRegion563(y,x,h,w,true,true);CurveArea511.Compute(swapped,y,x,h,w,b);second=b.Branches566();return NegativeRegion563.Groups(first,second,w,h);
 }
 static string Cells(int[] group,int x,int y,int w)=>string.Join(";",group.Select(i=>(x+i%w)+","+(y+i/w)));
 public static void Run()
 {
  if(EditorApplication.isPlaying||EditorApplication.isCompiling||Directory.Exists(Output))throw new Exception("Edit and new trace output required");Directory.CreateDirectory(Output);int cross=CurveArea511.LastCrossings,events=CurveArea511.LastEvents;
  try{using(var t=new StreamWriter(Output+"SELECTION575.tsv"))using(var g=new StreamWriter(Output+"GROUPS575.tsv"))
  {
   t.WriteLine("frame\toldGroups\trootGroups\toldRootDiff\tnewRootDiff\tfront232_45\trear208_52\tneck220_58\tneck221_58");g.WriteLine("frame\tdomain\tbranch\tstart\tend\townedCells\tgroupedCells");
   foreach(int frame in new[]{8,9,10,16,21,22,23,24,41,42,43,44,45,46,47,48,51,62,71,72,73,77})
   {
    string prefix=Input+frame.ToString("D3")+"_OFF";int x,y,w,h;float[] areas;using(var r=new BinaryReader(File.OpenRead(prefix+"_AREAS.bin"))){x=r.ReadInt32();y=r.ReadInt32();w=r.ReadInt32();h=r.ReadInt32();areas=new float[w*h];for(int i=0;i<areas.Length;i++)areas[i]=r.ReadSingle();}
    var graph=new List<CurveArea511.P[]>();using(var r=new BinaryReader(File.OpenRead(prefix+"_SOURCE_CURVES.bin"))){for(int i=r.ReadInt32();i>0;i--){var ring=new CurveArea511.P[r.ReadInt32()];for(int j=0;j<ring.Length;j++)ring[j]=new CurveArea511.P(r.ReadSingle(),r.ReadSingle());graph.Add(ring);}}
    var oldGroups=Groups(graph,x,y,w,h,out var first,out var second);var oldMask=HeadRegion502.SelectRegions543(areas,w,h,oldGroups);var root=HairRegions574.Build(graph,x,y,w,h);var groups=Groups(root.envelopeCurves,x,y,w,h,out var extFirst,out var extSecond);var next=HeadRegion502.SelectRegions543(root.areas,w,h,groups);
    string At(int xx,int yy)=>next[(yy-y)*w+xx-x].ToString();int Diff(bool[] a,bool[] b){int n=0;for(int i=0;i<a.Length;i++)if(a[i]!=b[i])n++;return n;}
    t.WriteLine(frame+"\t"+oldGroups.Count+"\t"+groups.Count+"\t"+Diff(oldMask,next)+"\t"+Diff(root.selected,next)+"\t"+At(232,45)+"\t"+At(208,52)+"\t"+At(220,58)+"\t"+At(221,58));
    void Branches(string domain,List<NegativeRegion563.Feature> fs){foreach(var f in fs){var owned=f.OwnedCells();if(owned.Any(i=>new[]{(52-y)*w+208-x,(58-y)*w+220-x,(58-y)*w+221-x,(45-y)*w+232-x}.Contains(i)))g.WriteLine(frame+"\t"+domain+"\t"+f.boundaryId+"\t"+f.start566.kind+"\t"+f.end566.kind+"\t"+Cells(owned,x,y,w)+"\t"+string.Join("|",NegativeRegion563.Groups(new List<NegativeRegion563.Feature>{f},new List<NegativeRegion563.Feature>(),w,h).Select(z=>Cells(z,x,y,w))));}}
    Branches("source",first);Branches("source",second);Branches("exterior",extFirst);Branches("exterior",extSecond);
   }
  }}finally{CurveArea511.LastCrossings=cross;CurveArea511.LastEvents=events;}
 }
}
internal class CommandScript:IRunCommand{public void Execute(ExecutionResult result){Trace575.Run();result.Log("575 saved actual input root/source group comparison complete; no Play or product writes");}}
