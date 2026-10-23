using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Globalization;
using UnityEngine;
using UnityEditor;
public static class Gate544
{
 const string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Span543/";
 static string[] files;static int at;static double deadline;static readonly CultureInfo ci=CultureInfo.InvariantCulture;
 public sealed class Input{public int x,y,w,h;public float[] a;public bool[] expected;public List<Vector2[]> curves;public List<int[]> groups;}
 static List<Vector2[]> Rings(BinaryReader b){var rs=new List<Vector2[]>();int n=b.ReadInt32();for(int k=0;k<n;k++){var r=new Vector2[b.ReadInt32()];for(int j=0;j<r.Length;j++)r[j]=new Vector2(b.ReadSingle(),b.ReadSingle());rs.Add(r);}return rs;}
 public static Input Read(string file)
 {
  var p=new Input();using(var b=new BinaryReader(File.OpenRead(file))){p.x=b.ReadInt32();p.y=b.ReadInt32();p.w=b.ReadInt32();p.h=b.ReadInt32();p.a=new float[p.w*p.h];for(int i=0;i<p.a.Length;i++)p.a[i]=b.ReadSingle();p.expected=new bool[p.a.Length];for(int i=0;i<p.a.Length;i++)p.expected[i]=b.ReadBoolean();Rings(b);p.curves=Rings(b);}p.groups=BoundarySpan543.Groups(p.curves,p.a,new RectInt(p.x,p.y,p.w,p.h));return p;
 }
 static string Measure(Input p,bool compact,out bool[] mask)
 {
  long before=GC.GetAllocatedBytesForCurrentThread();double start=EditorApplication.timeSinceStartup;mask=compact?CompactCut544.Select(p.a,p.w,p.h,p.groups):HeadRegion502.SelectRegions543(p.a,p.w,p.h,p.groups);double end=EditorApplication.timeSinceStartup;long bytes=GC.GetAllocatedBytesForCurrentThread()-before;return ((end-start)*1000.0).ToString("R",ci)+","+bytes;
 }
 static void Finish(string status,string error="")
 {
  EditorApplication.update-=Tick;File.WriteAllText(Root+"CompactGate544/status.json","{\"status\":\""+status+"\",\"cases\":"+at+",\"error\":\""+error.Replace("\\","/").Replace("\"","'").Replace("\n"," ").Replace("\r"," ")+"\"}");
 }
 static void Tick()
 {
  try
  {
   if(EditorApplication.isPlaying||ClothRegion524.Enabled||EditorApplication.timeSinceStartup>deadline)throw new Exception("Diagnostic Edit guard/deadline");
   if(at<files.Length)
   {
    var p=Read(files[at]);bool[] a,b;string ma,mb;if(at%2==0){ma=Measure(p,false,out a);mb=Measure(p,true,out b);}else{mb=Measure(p,true,out b);ma=Measure(p,false,out a);}
    if(!a.SequenceEqual(p.expected)||!a.SequenceEqual(b))throw new Exception("Mask equality failed "+Path.GetFileName(files[at]));
    File.AppendAllText(Root+"CompactGate544/masks.csv",Path.GetFileName(files[at])+","+p.a.Length+","+ma+","+mb+",true\n");at++;File.WriteAllText(Root+"CompactGate544/progress.json","{\"cases\":"+at+",\"target\":"+files.Length+"}");return;
   }
   foreach(var file in Directory.GetFiles(Root+"Inputs","thin*.bin"))
   using(var b=new BinaryReader(File.OpenRead(file)))
   {
    int x=b.ReadInt32(),y=b.ReadInt32(),w=b.ReadInt32(),h=b.ReadInt32();var a=new float[w*h];for(int i=0;i<a.Length;i++)a[i]=b.ReadSingle();int n=b.ReadInt32();var gs=new List<int[]>();for(int i=0;i<n;i++){var g=new int[b.ReadInt32()];for(int j=0;j<g.Length;j++)g[j]=b.ReadInt32();gs.Add(g);}var old=File.ReadAllBytes(Root+"Results/"+Path.GetFileName(file));var actual=CompactCut544.Select(a,w,h,gs);if(actual.Where((v,i)=>v!=(old[i]!=0)).Any())throw new Exception("Thin-end equality "+file);
   }
   var sample=Read(Root+"FullLoop543/065_SPAN_PART3.bin");for(int k=0;k<5;k++){HeadRegion502.SelectRegions543(sample.a,sample.w,sample.h,sample.groups);CompactCut544.Select(sample.a,sample.w,sample.h,sample.groups);}
   File.WriteAllText(Root+"CompactGate544/paired.csv","iteration,referenceMs,referenceBytes,compactMs,compactBytes\n");
   for(int k=0;k<21;k++){bool[] a,b;string ma,mb;if(k%2==0){ma=Measure(sample,false,out a);mb=Measure(sample,true,out b);}else{mb=Measure(sample,true,out b);ma=Measure(sample,false,out a);}if(!a.SequenceEqual(b))throw new Exception("Paired mask equality");File.AppendAllText(Root+"CompactGate544/paired.csv",k+","+ma+","+mb+"\n");}
   Finish("PASS");
  }catch(Exception e){Finish("FAILED",e.ToString());}
 }
 public static void Start()
 {
  if(EditorApplication.isPlaying||ClothRegion524.Enabled||Directory.Exists(Root+"CompactGate544"))throw new Exception("Edit/OFF and new output required");Directory.CreateDirectory(Root+"CompactGate544");
  long before=GC.GetAllocatedBytesForCurrentThread();var probe=new byte[1048576];GC.KeepAlive(probe);long delta=GC.GetAllocatedBytesForCurrentThread()-before;File.WriteAllText(Root+"CompactGate544/ALLOCATION_PROBE.json","{\"requestedBytes\":1048576,\"observedBytes\":"+delta+"}");
  File.WriteAllText(Root+"CompactGate544/masks.csv","case,cells,referenceMs,referenceBytes,compactMs,compactBytes,exact\n");files=Directory.GetFiles(Root+"FullLoop543","*_SPAN_PART*.bin").OrderBy(v=>v).ToArray();if(files.Length!=243)throw new Exception("Expected243 stored actual cases");at=0;deadline=EditorApplication.timeSinceStartup+180;EditorApplication.update+=Tick;File.WriteAllText(Root+"CompactGate544/status.json","{\"status\":\"STARTED\"}");
 }
}
