using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
internal class CommandScript:IRunCommand
{
 [Serializable]sealed class Report{public int frame,addedRings,addedPoints,maskChanges;public CapContract572.Decision[] decisions;}
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlaying||EditorApplication.isCompiling)throw new Exception("Stored math only; requires Edit/no compiling");
  const string input="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairContract570/Full570/";
  const string output="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/RegionContract572/Stored572/";
  if(Directory.Exists(output))throw new Exception("Existing output: inspect before repeat");Directory.CreateDirectory(output);
  int oldCross=CurveArea511.LastCrossings,oldEvents=CurveArea511.LastEvents;
  try{foreach(int frame in new[]{16,51,62,71,72,73,77})
  {
   string p=input+frame.ToString("D3");int x0,y0,w,h;
   using(var r=new BinaryReader(File.OpenRead(p+"_ON_AREAS.bin"))){x0=r.ReadInt32();y0=r.ReadInt32();w=r.ReadInt32();h=r.ReadInt32();}
   var graph=new List<CurveArea511.P[]>();using(var r=new BinaryReader(File.OpenRead(p+"_ON_CURVES.bin"))){int n=r.ReadInt32();for(int i=0;i<n;i++){var ring=new CurveArea511.P[r.ReadInt32()];for(int j=0;j<ring.Length;j++)ring[j]=new CurveArea511.P(r.ReadSingle(),r.ReadSingle());graph.Add(ring);}}
   var contract=CapContract572.Create(graph,x0,y0,w,h,1.0);
   var neg=new NegativeRegion563(x0,y0,w,h,false,true);var areas=CurveArea511.Compute(contract.rings,x0,y0,w,h,neg);
   var swap=new List<CurveArea511.P[]>();foreach(var ring in contract.rings){var q=new CurveArea511.P[ring.Length];for(int j=0;j<q.Length;j++){var a=ring[ring.Length-1-j];q[j]=new CurveArea511.P(a.y,a.x);}swap.Add(q);}
   var other=new NegativeRegion563(y0,x0,h,w,true,true);CurveArea511.Compute(swap,y0,x0,h,w,other);
   var selected=HeadRegion502.SelectRegions543(areas,w,h,NegativeRegion563.Groups(neg.Branches566(),other.Branches566(),w,h));
   int changed=0;using(var r=new BinaryReader(File.OpenRead(p+"_OFF_MASK.bin"))){int mw=r.ReadInt32(),mh=r.ReadInt32(),mx=r.ReadInt32(),my=r.ReadInt32();for(int y=0;y<mh;y++)for(int x=0;x<mw;x++){r.ReadSingle();bool v=r.ReadSingle()>.5f;r.ReadSingle();r.ReadSingle();int xx=x+mx-x0,yy=y+my-y0;if(xx>=0&&yy>=0&&xx<w&&yy<h&&selected[yy*w+xx]!=v)changed++;}}
   using(var b=new BinaryWriter(File.Create(output+frame.ToString("D3")+"_LAYOUT.bin"))){b.Write(572);b.Write(frame);b.Write(x0);b.Write(y0);b.Write(w);b.Write(h);foreach(var a in areas)b.Write(a);foreach(var a in selected)b.Write(a);}
   using(var b=new BinaryWriter(File.Create(output+frame.ToString("D3")+"_CURVES.bin"))){b.Write(contract.rings.Count);foreach(var ring in contract.rings){b.Write(ring.Length);foreach(var a in ring){b.Write(a.x);b.Write(a.y);}}}
   var report=new Report{frame=frame,addedRings=contract.rings.Count-graph.Count,addedPoints=contract.rings.Skip(graph.Count).Sum(a=>a.Length),maskChanges=changed,decisions=contract.decisions.ToArray()};
   File.WriteAllText(output+frame.ToString("D3")+"_CONTRACT.json",JsonUtility.ToJson(report,true));
   File.AppendAllText(output+"STATUS.tsv",frame+"\t"+report.addedRings+"\t"+report.addedPoints+"\t"+changed+"\n");result.Log("572 stored "+frame+" caps="+report.addedRings+" points="+report.addedPoints+" changed="+changed);
  }File.WriteAllText(output+"DONE.txt","Stored seven inputs only. No Play/render/product writes. Selected-port mapping remains a gate, not assumed.");}
  finally{CurveArea511.LastCrossings=oldCross;CurveArea511.LastEvents=oldEvents;}
 }
}
