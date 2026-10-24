using System;
using System.IO;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
internal class CommandScript:IRunCommand
{
 [Serializable]class Params{public int offsetX,offsetY;}
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlaying||EditorApplication.isCompiling)throw new Exception("575 replay needs restored Edit");
  const string input="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairRegions575/Full575/",output="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairRegions575/Replay575/";
  if(Directory.Exists(output))throw new Exception("Inspect prior replay; do not duplicate");Directory.CreateDirectory(output);int cross=CurveArea511.LastCrossings,events=CurveArea511.LastEvents;
  try{using(var t=new StreamWriter(output+"STATUS.tsv"))
  {
   t.WriteLine("frame\tactualMismatch\tremovedBaseline\tremoved574\trestored574Loss\tnewOutsideBoth\tfaceSelectionDifferent574\tfilledFamilies");
   for(int frame=0;frame<=80;frame++)
   {
    string p=input+frame.ToString("D3");int x,y,w,h;using(var b=new BinaryReader(File.OpenRead(p+"_ON_AREAS.bin"))){x=b.ReadInt32();y=b.ReadInt32();w=b.ReadInt32();h=b.ReadInt32();}
    var graph=new List<CurveArea511.P[]>();using(var b=new BinaryReader(File.OpenRead(p+"_ON_SOURCE_CURVES.bin"))){for(int n=b.ReadInt32();n>0;n--){var ring=new CurveArea511.P[b.ReadInt32()];for(int j=0;j<ring.Length;j++)ring[j]=new CurveArea511.P(b.ReadSingle(),b.ReadSingle());graph.Add(ring);}}
    var old=HairRegions574Before575.Build(graph,x,y,w,h);var next=HairRegions574.Build(graph,x,y,w,h);int mismatch=0,removedBase=0,removedOld=0,restored=0,extra=0,face=0;
    for(int i=0;i<w*h;i++){if(next.protectedPositive[i]&&!next.selected[i])removedBase++;if(old.selected[i]&&!next.selected[i])removedOld++;if(next.protectedPositive[i]&&!old.selected[i]&&next.selected[i])restored++;if(next.selected[i]&&!old.selected[i]&&!next.protectedPositive[i])extra++;}
    using(var b=new BinaryReader(File.OpenRead(p+"_ON_MASK.bin"))){int mw=b.ReadInt32(),mh=b.ReadInt32(),mx=b.ReadInt32(),my=b.ReadInt32();for(int v=0;v<mh;v++)for(int u=0;u<mw;u++){b.ReadSingle();bool selected=b.ReadSingle()>.5;b.ReadSingle();b.ReadSingle();int xx=mx+u-x,yy=my+v-y;if(xx>=0&&yy>=0&&xx<w&&yy<h&&selected!=next.selected[yy*w+xx])mismatch++;}}
    var cfg=JsonUtility.FromJson<Params>(File.ReadAllText(p+"_ON_PARAMS.json"));using(var a=new BinaryReader(File.OpenRead(p+"_OFF_META.bin")))using(var b=new BinaryReader(File.OpenRead(p+"_ON_META.bin")))
    {
     int mw=a.ReadInt32(),mh=a.ReadInt32(),mx=a.ReadInt32(),my=a.ReadInt32();for(int n=0;n<4;n++)b.ReadInt32();for(int v=0;v<mh;v++)for(int u=0;u<mw;u++){a.ReadSingle();float ar=a.ReadSingle();a.ReadSingle();a.ReadSingle();b.ReadSingle();float br=b.ReadSingle();b.ReadSingle();b.ReadSingle();if((ar==4||ar==5)==(br==4||br==5))continue;int xx=mx+u-cfg.offsetX-x,yy=my+v+cfg.offsetY-y;if(xx<0||yy<0||xx>=w||yy>=h||old.selected[yy*w+xx]!=next.selected[yy*w+xx])face++;}
    }
    using(var b=new BinaryWriter(File.Create(output+frame.ToString("D3")+"_MASKS.bin"))){b.Write(x);b.Write(y);b.Write(w);b.Write(h);foreach(bool v in old.selected)b.Write(v);foreach(bool v in next.selected)b.Write(v);foreach(bool v in next.protectedPositive)b.Write(v);}
    t.WriteLine(frame+"\t"+mismatch+"\t"+removedBase+"\t"+removedOld+"\t"+restored+"\t"+extra+"\t"+face+"\t"+next.filledFamilies);
    if(mismatch!=0||removedBase!=0||removedOld!=0)throw new Exception("575 exact replay invariant failed at "+frame);
   }
  }File.WriteAllText(output+"DONE.txt","81 current actual source inputs, old574/new575 selector replay; no rendering; reference counters restored.");result.Log("575 81 current input selector replay completed; no extra rendering or ray audit");}
  finally{CurveArea511.LastCrossings=cross;CurveArea511.LastEvents=events;}
 }
}
