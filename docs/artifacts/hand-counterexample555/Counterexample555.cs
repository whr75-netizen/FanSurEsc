using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

// Offline cause isolation only: actual public area/cut code, unchanged costs.
// A forced component is made A1 only inside the diagnostic solve. Under the
// existing .14 cost its A1 label is certified; original energy is evaluated
// afterwards. Every changed unary is constant in that constrained domain.
internal class CommandScript:IRunCommand
{
 static string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/OwnerLines553/";
 static List<Vector2[]> Read(BinaryReader r){var rings=new List<Vector2[]>();int n=r.ReadInt32();for(int j=0;j<n;j++){var p=new Vector2[r.ReadInt32()];for(int i=0;i<p.Length;i++)p[i]=new Vector2(r.ReadSingle(),r.ReadSingle());rings.Add(p);}return rings;}
 static double[] Energy(float[] a,bool[] m,int w,int h,List<int[]> groups)
 {
  double unary=0,boundary=0,constraint=0;void Pair(int i,int j,float v){if(m[i]!=m[j])boundary+=v;}
  for(int y=0;y<h;y++)for(int x=0;x<w;x++){int i=y*w+x;unary+=m[i]?(double)(1f-a[i]):a[i];if(x+1<w)Pair(i,i+1,HeadRegion502.BoundaryCost*.58578644f);if(y+1<h)Pair(i,i+w,HeadRegion502.BoundaryCost*.58578644f);if(x+1<w&&y+1<h)Pair(i,i+w+1,HeadRegion502.BoundaryCost*.29289322f);if(x>0&&y+1<h)Pair(i,i+w-1,HeadRegion502.BoundaryCost*.29289322f);}
  if(groups!=null)foreach(var g in groups)for(int j=1;j<g.Length;j++)if(m[g[0]]!=m[g[j]])constraint+=100000;
  return new[]{unary,boundary,constraint,unary+boundary+constraint};
 }
 static bool[] Forced(float[] a,int w,int h,List<int[]> groups,int target,out int component)
 {
  var included=new bool[a.Length];included[target]=true;bool changed=true;while(changed){changed=false;if(groups!=null)foreach(var g in groups)if(g.Any(i=>included[i]))foreach(int i in g)if(!included[i]){included[i]=true;changed=true;}}
  var copy=(float[])a.Clone();component=0;for(int i=0;i<a.Length;i++)if(included[i]){copy[i]=1;component++;}
  var m=HeadRegion502.SelectRegionsCompact544(copy,w,h,groups);for(int i=0;i<a.Length;i++)if(included[i]&&!m[i])throw new Exception("555 forced component certification failed");return m;
 }
 static string Number(double v)=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture);
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isPlaying||ClothRegion524.Enabled||HeadRegion502.Enabled)throw new Exception("Restored Edit/OFF required");
  string output=Root+"Minimal555/";if(Directory.Exists(output))throw new Exception("Existing555 output; do not duplicate");Directory.CreateDirectory(output);
  using(var log=new StreamWriter(output+"COMPARISON555.csv"))
  {
   log.WriteLine("frame,variant,groups,targetGroups,targetArea,targetSelected,unary,boundary,groupCost,total,forcedComponent,forcedUnary,forcedBoundary,forcedGroupCost,forcedTotal,forcedDelta,forcedChanged");
   foreach(int frame in new[]{33,49})
   {
    var source=new List<Vector2[]>();var fit=new List<Vector2[]>();using(var r=new BinaryReader(File.OpenRead(Root+(frame==33?"Actual553/033_ON_CURVES.bin":"Cases553/049_ON_CURVES.bin")))){source=Read(r);fit=Read(r);}
    var rebuilt=source.Select(ClosedRegionDesign539.Fit).ToList();if(fit.Count!=rebuilt.Count||fit.Where((r,i)=>!r.SequenceEqual(rebuilt[i])).Any())throw new Exception("555 source->Fit reproduction differs");
    int x0=Mathf.FloorToInt(source.Concat(fit).Min(r=>r.Min(p=>p.x)))-2,y0=Mathf.FloorToInt(source.Concat(fit).Min(r=>r.Min(p=>p.y)))-2,x1=Mathf.CeilToInt(source.Concat(fit).Max(r=>r.Max(p=>p.x)))+2,y1=Mathf.CeilToInt(source.Concat(fit).Max(r=>r.Max(p=>p.y)))+2;var bounds=new RectInt(x0,y0,x1-x0,y1-y0);int w=bounds.width,h=bounds.height,tx=frame==33?229:232,ty=frame==33?90:88,target=(ty-y0)*w+tx-x0;
    float[] Areas(List<Vector2[]> curves)=>CurveArea511.Compute(curves.Select(r=>r.Select(p=>new CurveArea511.P(p.x,p.y)).ToArray()).ToList(),x0,y0,w,h);
    var raw=Areas(source);var fitted=Areas(fit);var groups=BoundarySpan543.Groups(source,fitted,bounds);var rawGroups=BoundarySpan543.Groups(source,raw,bounds);
    foreach(string variant in new[]{"FIT_GROUPS","FIT_NO_GROUPS","SOURCE_FIXED_GROUPS","SOURCE_NO_GROUPS","SOURCE_REBUILT_GROUPS"})
    {
     var area=variant.StartsWith("FIT")?fitted:raw;var selectedGroups=variant.EndsWith("NO_GROUPS")?null:variant=="SOURCE_REBUILT_GROUPS"?rawGroups:groups;var mask=HeadRegion502.SelectRegionsCompact544(area,w,h,selectedGroups);var forced=Forced(area,w,h,selectedGroups,target,out int component);var e=Energy(area,mask,w,h,selectedGroups);var f=Energy(area,forced,w,h,selectedGroups);int changed=mask.Where((v,i)=>v!=forced[i]).Count();int membership=selectedGroups==null?0:selectedGroups.Count(g=>g.Contains(target));
     if(e[2]!=0||f[2]!=0)throw new Exception("555 group equality violated");
     log.WriteLine(frame+","+variant+","+(selectedGroups?.Count??0)+","+membership+","+Number(area[target])+","+mask[target]+","+string.Join(",",e.Select(Number))+","+component+","+string.Join(",",f.Select(Number))+","+Number(f[3]-e[3])+","+changed);
     var lines=new List<string>{"x,y,sourceArea,fitArea,selected,forced,groupIds"};for(int y=ty-3;y<=ty+3;y++)for(int x=tx-3;x<=tx+3;x++){int i=(y-y0)*w+x-x0;string ids=selectedGroups==null?"":string.Join(";",Enumerable.Range(0,selectedGroups.Count).Where(g=>selectedGroups[g].Contains(i)));lines.Add(x+","+y+","+Number(raw[i])+","+Number(fitted[i])+","+mask[i]+","+forced[i]+","+ids);}File.WriteAllLines(output+frame+"_"+variant+"_ROI.csv",lines);
     File.WriteAllLines(output+frame+"_"+variant+"_FORCED_DIFF.txt",Enumerable.Range(0,mask.Length).Where(i=>mask[i]!=forced[i]).Select(i=>(i%w+x0)+","+(i/w+y0)+":"+mask[i]+"->"+forced[i]));
    }
    using(var b=new BinaryWriter(File.Create(output+frame+"_SOURCE_FIT_AREAS.bin"))){b.Write(x0);b.Write(y0);b.Write(w);b.Write(h);foreach(float v in raw)b.Write(v);foreach(float v in fitted)b.Write(v);}
   }
  }
  result.Log("555 same-input two-tip isolation complete: Fit/noFit x fixed/noGroups; forced-label optimum assessed under unchanged original energy; no product changes or Unity render");
 }
}
