using System;
using System.IO;
using System.Collections.Generic;
using UnityEditor;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlaying||EditorApplication.isCompiling)throw new Exception("Edit required");
  const string root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/",output=root+"HairDirections578/REPLAY_VIEWS578.tsv";
  if(File.Exists(output))throw new Exception("Inspect existing replay");
  int oldC=CurveArea511.LastCrossings,oldE=CurveArea511.LastEvents,count=0;
  try{using(var t=new StreamWriter(new FileStream(output,FileMode.CreateNew))){
   t.WriteLine("view\tframe\tselectionDiff\tpositiveErased\toutsideEnvelope");
   foreach(int view in new[]{80,260})for(int frame=0;frame<=80;frame++){
    string folder=root+(view==80?"HairRegions575/Full575/":"HairDirections576/Runtime577/FinalFull260/"),p=folder+frame.ToString("D3")+"_ON";
    int x,y,w,h;using(var b=new BinaryReader(File.OpenRead(p+"_AREAS.bin"))){x=b.ReadInt32();y=b.ReadInt32();w=b.ReadInt32();h=b.ReadInt32();}
    string raw=p+"_SOURCE_CURVES.bin";if(!File.Exists(raw))raw=Path.Combine(folder,File.ReadAllText(p+"_SOURCE_REF.txt").Trim());
    var graph=new List<CurveArea511.P[]>();using(var b=new BinaryReader(File.OpenRead(raw))){for(int n=b.ReadInt32();n>0;n--){var ring=new CurveArea511.P[b.ReadInt32()];for(int j=0;j<ring.Length;j++)ring[j]=new CurveArea511.P(b.ReadSingle(),b.ReadSingle());graph.Add(ring);}}
    var after=HairRegions574.Build(graph,x,y,w,h);int diff=0,erased=0,outside=0;
    for(int i=0;i<w*h;i++){if(after.protectedPositive[i]&&!after.selected[i])erased++;if(after.selected[i]&&!after.envelope[i])outside++;}
    using(var b=new BinaryReader(File.OpenRead(p+"_MASK.bin"))){int mw=b.ReadInt32(),mh=b.ReadInt32(),mx=b.ReadInt32(),my=b.ReadInt32();for(int v=0;v<mh;v++)for(int u=0;u<mw;u++){b.ReadSingle();bool selected=b.ReadSingle()>.5;b.ReadSingle();b.ReadSingle();int xx=mx+u-x,yy=my+v-y;if(xx>=0&&yy>=0&&xx<w&&yy<h&&selected!=after.selected[yy*w+xx])diff++;}}
    t.WriteLine(view+"\t"+frame+"\t"+diff+"\t"+erased+"\t"+outside);t.Flush();count++;
    if(diff!=0||erased!=0||outside!=0)throw new Exception("Saved view regression "+view+"/"+frame);
   }
  }File.WriteAllText(root+"HairDirections578/REPLAY_VIEWS578_DONE.txt",count+" saved actual view inputs matched; not new rendering");result.Log(count+" saved actual yaw80/260 inputs matched current product selection");}
  finally{CurveArea511.LastCrossings=oldC;CurveArea511.LastEvents=oldE;}
 }
}
