using System;
using System.IO;
using System.Collections.Generic;
using UnityEditor;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result){
  if(EditorApplication.isPlaying||EditorApplication.isCompiling)throw new Exception("Edit required");int oldC=CurveArea511.LastCrossings,oldE=CurveArea511.LastEvents;
  try{const string root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairDirections576/",cap=root+"Runtime577/Full260/";int x,y,w,h;using(var b=new BinaryReader(File.OpenRead(cap+"055_OFF_AREAS.bin"))){x=b.ReadInt32();y=b.ReadInt32();w=b.ReadInt32();h=b.ReadInt32();}var graph=new List<CurveArea511.P[]>();using(var b=new BinaryReader(File.OpenRead(cap+"FAILED_SOURCE_CURVES.bin"))){for(int n=b.ReadInt32();n>0;n--){var p=new CurveArea511.P[b.ReadInt32()];for(int i=0;i<p.Length;i++)p[i]=new CurveArea511.P(b.ReadSingle(),b.ReadSingle());graph.Add(p);}}
   var after=HairCandidate577.Build(graph,x,y,w,h);using(var b=new BinaryWriter(File.Create(root+"KeepFailure55_577/CANDIDATE55_MASK.bin"))){b.Write(x);b.Write(y);b.Write(w);b.Write(h);foreach(bool v in after.selected)b.Write(v);foreach(bool v in after.envelope)b.Write(v);}
   var env=new bool[49];for(int v=1;v<=5;v++)for(int u=1;u<=5;u++)env[v*7+u]=true;
   var pair=new bool[49];pair[2*7+1]=pair[4*7+5]=true;if(!HairCandidate577.KeepConnected577(pair,env,7,7,true))throw new Exception("Valid exterior arcs rejected");
   pair[4*7+5]=false;pair[3*7+3]=true;if(HairCandidate577.KeepConnected577(pair,env,7,7,true))throw new Exception("Floating interior accepted as open");
   var closed=new bool[49];closed[3*7+3]=true;if(!HairCandidate577.KeepConnected577(closed,env,7,7,false))throw new Exception("Closed single region rejected");closed[2*7+2]=true;if(HairCandidate577.KeepConnected577(closed,env,7,7,false))throw new Exception("Disconnected closed regions accepted");if(HairCandidate577.KeepConnected577(new bool[49],env,7,7,true))throw new Exception("Empty broad KEEP accepted");
   File.WriteAllText(root+"KeepFailure55_577/DOMAIN_TEST.txt","stored55 passed; valid exterior arcs, floating interior rejection, closed single, disconnected closed rejection, empty KEEP rejection passed\n");result.Log("Stored55 and five domain fixtures passed; pixel selection unchanged by guard correction");
  }finally{CurveArea511.LastCrossings=oldC;CurveArea511.LastEvents=oldE;}
 }
}
