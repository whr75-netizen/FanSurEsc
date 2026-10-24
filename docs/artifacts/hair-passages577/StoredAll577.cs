using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlaying||EditorApplication.isCompiling)throw new Exception("Edit required");
  const string root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairDirections576/",output=root+"StoredAll577/";if(Directory.Exists(output))throw new Exception("Inspect existing stored replay");Directory.CreateDirectory(output);int oldC=CurveArea511.LastCrossings,oldE=CurveArea511.LastEvents;
  try{using(var t=new StreamWriter(output+"STATUS577.tsv")){
   t.WriteLine("view\tframe\tbaselineError\tselectionDiff\tactualDiff\tpositiveErased\toutsideEnvelope\tnegativeConstraints");int count=0;
   foreach(int view in new[]{80,260})foreach(int frame in(view==80?Enumerable.Range(0,81):Enumerable.Range(0,43).Concat(Enumerable.Range(70,5)))){
    string folder=view==80?"C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairRegions575/Full575/":root+(frame>=70?"Compare260/":"CanvasFull260/");string p=folder+frame.ToString("D3")+"_ON",input=view==80?p:folder+frame.ToString("D3")+"_OFF";int x,y,w,h;using(var b=new BinaryReader(File.OpenRead(input+"_AREAS.bin"))){x=b.ReadInt32();y=b.ReadInt32();w=b.ReadInt32();h=b.ReadInt32();}
    string raw=input+"_SOURCE_CURVES.bin";if(!File.Exists(raw))raw=Path.Combine(folder,File.ReadAllText(input+"_SOURCE_REF.txt").Trim());var graph=new List<CurveArea511.P[]>();using(var b=new BinaryReader(File.OpenRead(raw))){for(int n=b.ReadInt32();n>0;n--){var ring=new CurveArea511.P[b.ReadInt32()];for(int j=0;j<ring.Length;j++)ring[j]=new CurveArea511.P(b.ReadSingle(),b.ReadSingle());graph.Add(ring);}}
    HairRegions574.Layout before=null;string error="";try{before=HairRegions574.Build(graph,x,y,w,h);}catch(InvalidOperationException e){error=e.Message;}var after=HairCandidate577.Build(graph,x,y,w,h);int diff=before==null?-1:0,actual=File.Exists(p+"_MASK.bin")?0:-1,erased=0,outside=0;
    for(int i=0;i<w*h;i++){if(before!=null&&before.selected[i]!=after.selected[i])diff++;if(after.protectedPositive[i]&&!after.selected[i])erased++;if(after.selected[i]&&!after.envelope[i])outside++;}
    if(actual>=0)using(var b=new BinaryReader(File.OpenRead(p+"_MASK.bin"))){int mw=b.ReadInt32(),mh=b.ReadInt32(),mx=b.ReadInt32(),my=b.ReadInt32();for(int v=0;v<mh;v++)for(int u=0;u<mw;u++){b.ReadSingle();bool s=b.ReadSingle()>.5;b.ReadSingle();b.ReadSingle();int xx=mx+u-x,yy=my+v-y;if(xx>=0&&yy>=0&&xx<w&&yy<h&&s!=after.selected[yy*w+xx])actual++;}}
    t.WriteLine(view+"\t"+frame+"\t"+error+"\t"+diff+"\t"+actual+"\t"+erased+"\t"+outside+"\t"+HairCandidate577.passages577.Count);t.Flush();count++;
    if((before==null&&!(view==260&&frame==42))||diff>0||actual>0||erased!=0||outside!=0)throw new Exception("Stored candidate regression at "+view+"/"+frame);
   }
   File.WriteAllText(output+"DONE.txt",count+" stored inputs passed; old42 has no candidate output and is not counted as equal");result.Log(count+" stored inputs checked; yaw80 actual81 unchanged; candidate42 accepted; no new render");
  }}finally{CurveArea511.LastCrossings=oldC;CurveArea511.LastEvents=oldE;}
 }
}
