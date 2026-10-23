using UnityEngine;
using UnityEditor;
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
internal class CommandScript:IRunCommand
{
 const string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Contour534/Math/";
 const string Source="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Outline533/FullLoop/";
 List<Vector2[]> Read(int frame){using(var b=new BinaryReader(File.OpenRead(Source+frame.ToString("D3")+"_ALT_GEOMETRY.bin"))){var rs=new List<Vector2[]>();int n=b.ReadInt32();for(int i=0;i<n;i++){var p=new Vector2[b.ReadInt32()];for(int k=0;k<p.Length;k++)p[k]=new Vector2(b.ReadSingle(),b.ReadSingle());rs.Add(p);}return rs;}}
 void Write(string name,List<Vector2[]> curves)
 {
  int x0=Mathf.Max(0,Mathf.FloorToInt(curves.Min(r=>r.Min(p=>p.x)))-2),y0=Mathf.Max(0,Mathf.FloorToInt(curves.Min(r=>r.Min(p=>p.y)))-2),x1=Mathf.Min(480,Mathf.CeilToInt(curves.Max(r=>r.Max(p=>p.x)))+2),y1=Mathf.Min(272,Mathf.CeilToInt(curves.Max(r=>r.Max(p=>p.y)))+2);
  int w=x1-x0,h=y1-y0;var areas=CurveArea511.Compute(curves.Select(r=>r.Select(p=>new CurveArea511.P(p.x,p.y)).ToArray()).ToList(),x0,y0,w,h);var mask=HeadRegion502.SelectRegions(areas,w,h);
  using(var b=new BinaryWriter(File.Create(Root+name+".bin"))){b.Write(curves.Count);foreach(var r in curves){b.Write(r.Length);foreach(var p in r){b.Write(p.x);b.Write(p.y);}}b.Write(x0);b.Write(y0);b.Write(w);b.Write(h);foreach(float a in areas)b.Write(a);foreach(bool v in mask)b.Write(v);}
 }
 public void Execute(ExecutionResult result)
 {
  if(Application.dataPath!="C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets"||EditorApplication.isPlaying||ClothRegion524.Enabled||ClothRegion524.UseAreaCurves532)throw new Exception("Require intended project Edit/OFF");
  if(Directory.Exists(Root))throw new Exception("Math output exists; inspect before retry");Directory.CreateDirectory(Root);
  foreach(int frame in new[]{49,50,51})
  {
   var rs=Read(frame);Write(frame+"_source",rs);Write(frame+"_distance",rs.Select(r=>ClosedRegion524.Fit(r,.09375f)).Where(r=>r.Length>=3).ToList());Write(frame+"_area",rs.Select(ClosedRegion524.FitArea532).Where(r=>r.Length>=3).ToList());
  }
  foreach(int variant in new[]{0,1})
  {
   var top=variant==0?new[]{new Vector2(20,20),new Vector2(22,20.375f),new Vector2(24,20),new Vector2(24,18),new Vector2(20,18)}:new[]{new Vector2(20,20),new Vector2(21,20.25f),new Vector2(23,20.25f),new Vector2(24,20),new Vector2(24,18),new Vector2(20,18)};
   Write("equal"+variant+"_source",new List<Vector2[]>{top});Write("equal"+variant+"_distance",new List<Vector2[]>{ClosedRegion524.Fit(top,.09375f)});Write("equal"+variant+"_area",new List<Vector2[]>{ClosedRegion524.FitArea532(top)});
  }
  result.Log("534 exact existing source/distance/area/cut replay complete:3 saved poses+2 equal-area geometry controls; no render/Play/product mutation; flags OFF");
 }
}
