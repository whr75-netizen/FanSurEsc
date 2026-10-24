using System;
using System.IO;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
internal class CommandScript:IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlaying||EditorApplication.isCompiling)throw new Exception("Stored atom diagnostic requires Edit/no compiling");
  const string input="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/RegionContract572/Stored572/";
  const string output="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/RegionContract573/Atoms573B/";
  if(Directory.Exists(output))throw new Exception("Atom export exists; inspect before repeat");Directory.CreateDirectory(output);
  foreach(int frame in new[]{16,51,62,71,72,73,77})
  {
   int x,y,w,h;float[] expected;using(var r=new BinaryReader(File.OpenRead(input+frame.ToString("D3")+"_LAYOUT.bin"))){if(r.ReadInt32()!=572||r.ReadInt32()!=frame)throw new Exception("Input header mismatch");x=r.ReadInt32();y=r.ReadInt32();w=r.ReadInt32();h=r.ReadInt32();expected=new float[w*h];for(int i=0;i<expected.Length;i++)expected[i]=r.ReadSingle();}
   var graph=new List<AreaProbe573.P[]>();using(var r=new BinaryReader(File.OpenRead(input+frame.ToString("D3")+"_CURVES.bin"))){int n=r.ReadInt32();for(int i=0;i<n;i++){var ring=new AreaProbe573.P[r.ReadInt32()];for(int j=0;j<ring.Length;j++)ring[j]=new AreaProbe573.P(r.ReadDouble(),r.ReadDouble());graph.Add(ring);}}
   var observer=new Observer573(x,w);var areas=AreaProbe573.Compute(graph,x,y,w,h,null,observer);int mismatch=0;double maxComplementError=0;var negative=new double[w*h];
   foreach(var a in observer.atoms)negative[(a.y-y)*w+a.x-x]+=(a.hi-a.lo)*(a.r0+a.r1-a.l0-a.l1)*.5;
   for(int i=0;i<areas.Length;i++){if(BitConverter.SingleToInt32Bits(areas[i])!=BitConverter.SingleToInt32Bits(expected[i]))mismatch++;maxComplementError=Math.Max(maxComplementError,Math.Abs(negative[i]+areas[i]-1));}
   if(mismatch!=0||maxComplementError>.0000002)throw new Exception("Instrumentation changed geometry: "+frame+" bits="+mismatch+" error="+maxComplementError);
   using(var b=new BinaryWriter(File.Create(output+frame.ToString("D3")+"_ATOMS.bin"))){b.Write(573);b.Write(frame);b.Write(x);b.Write(y);b.Write(w);b.Write(h);b.Write(observer.atoms.Count);foreach(var s in observer.atoms){b.Write(s.lo);b.Write(s.hi);b.Write(s.l0);b.Write(s.l1);b.Write(s.r0);b.Write(s.r1);b.Write(s.left);b.Write(s.right);b.Write(s.x);b.Write(s.y);}}
   File.AppendAllText(output+"STATUS.tsv",frame+"\t"+observer.atoms.Count+"\t"+mismatch+"\t"+maxComplementError.ToString("R",System.Globalization.CultureInfo.InvariantCulture)+"\n");result.Log("573 stored "+frame+" atoms="+observer.atoms.Count+" areaBitsExact complementMax="+maxComplementError);
  }
  File.WriteAllText(output+"DONE.txt","Stored geometry observation only; no selector, render or product writes.");
  result.Log("state compiling="+EditorApplication.isCompiling+" playing="+EditorApplication.isPlaying+" dirty="+EditorSceneManager.GetActiveScene().isDirty+" cloth="+ClothRegion524.Enabled+" body="+ClothRegion524.UseBodyScope551+" head="+HeadRegion502.Enabled+" negative="+HeadRegion502.UseNegativeRegions563+" branches="+HeadRegion502.UseNegativeBranches566+" profiler="+UnityEngine.Profiling.Profiler.enabled);
 }
}
