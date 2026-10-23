using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
internal class CommandScript:IRunCommand
{
 const string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Span543/";
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlaying||ClothRegion524.Enabled)throw new Exception("Edit/OFF required");
  foreach(var file in Directory.GetFiles(Root+"Inputs","*.bin"))
  using(var b=new BinaryReader(File.OpenRead(file)))
  {
   string name=Path.GetFileNameWithoutExtension(file);int x=b.ReadInt32(),y=b.ReadInt32(),w=b.ReadInt32(),h=b.ReadInt32();var a=new float[w*h];for(int i=0;i<a.Length;i++)a[i]=b.ReadSingle();int n=b.ReadInt32();var expected=new List<int[]>();for(int i=0;i<n;i++){var q=new int[b.ReadInt32()];for(int j=0;j<q.Length;j++)q[j]=b.ReadInt32();expected.Add(q);}
   var rings=new List<Vector2[]>();using(var c=new BinaryReader(File.OpenRead(Root+"Curves543/"+name+".bin"))){int nr=c.ReadInt32();for(int k=0;k<nr;k++){var ring=new Vector2[c.ReadInt32()];for(int j=0;j<ring.Length;j++)ring[j]=new Vector2(c.ReadSingle(),c.ReadSingle());rings.Add(ring);}}
   var actual=BoundarySpan543.Groups(rings,a,new RectInt(x,y,w,h));
   if(actual.Count!=expected.Count||actual.Where((q,i)=>!q.SequenceEqual(expected[i])).Any())throw new Exception("Group parity failed "+name+" actual="+actual.Count+" expected="+expected.Count);
   result.Log(name+" C# source grouping exact="+actual.Count);
  }
  result.Log("All15 geometry/group formation parity passed. Product unchanged.");
 }
}
