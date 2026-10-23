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
  if(EditorApplication.isPlaying||ClothRegion524.Enabled||Application.dataPath!="C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets")throw new Exception("Current Edit/OFF required");
  if(Directory.Exists(Root+"Results"))throw new Exception("Results exist; do not duplicate");Directory.CreateDirectory(Root+"Results");
  foreach(var file in Directory.GetFiles(Root+"Inputs","*.bin"))
  {
   using(var b=new BinaryReader(File.OpenRead(file)))
   {
    int x=b.ReadInt32(),y=b.ReadInt32(),w=b.ReadInt32(),h=b.ReadInt32();var areas=new float[w*h];for(int i=0;i<areas.Length;i++)areas[i]=b.ReadSingle();int n=b.ReadInt32();var groups=new List<int[]>();for(int i=0;i<n;i++){var g=new int[b.ReadInt32()];for(int j=0;j<g.Length;j++)g[j]=b.ReadInt32();groups.Add(g);}var old=new bool[w*h];for(int i=0;i<old.Length;i++)old[i]=b.ReadBoolean();
    var baseline=HeadRegion502.SelectRegions(areas,w,h);if(!baseline.SequenceEqual(old))throw new Exception("Baseline mismatch "+file);
    var candidate=GroupedCut543.Select(areas,w,h,groups);foreach(var g in groups)if(g.Any(i=>candidate[i]!=candidate[g[0]]))throw new Exception("Hard span constraint violated");
    var name=Path.GetFileNameWithoutExtension(file);File.WriteAllBytes(Root+"Results/"+name+".bin",candidate.Select(v=>(byte)(v?1:0)).ToArray());result.Log(name+" baselineExact=true groups="+groups.Count+" changed="+baseline.Where((v,i)=>v!=candidate[i]).Count());
   }
  }
  result.Log("543 bounded spatial gate complete, product sources unchanged");
 }
}
