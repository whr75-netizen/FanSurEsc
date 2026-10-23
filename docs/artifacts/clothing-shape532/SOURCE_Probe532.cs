using UnityEngine;
using UnityEditor;
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
internal class CommandScript:IRunCommand
{
    const string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Shape532";
    List<Vector2[]> Read(string file)
    {
        using(var b=new BinaryReader(File.OpenRead(file))){int n=b.ReadInt32();var rings=new List<Vector2[]>();for(int i=0;i<n;i++){var r=new Vector2[b.ReadInt32()];for(int k=0;k<r.Length;k++)r[k]=new Vector2(b.ReadSingle(),b.ReadSingle());rings.Add(r);}return rings;}
    }
    void Write(string name,List<Vector2[]> source,float error)
    {
        var rings=source.Select(r=>ClosedRegion524.Fit(r,error)).Where(r=>r.Length>=3).ToList();
        if(rings.Count==0)throw new Exception("No valid region "+name);
        int x0=Mathf.FloorToInt(rings.Min(r=>r.Min(p=>p.x)))-2,y0=Mathf.FloorToInt(rings.Min(r=>r.Min(p=>p.y)))-2,x1=Mathf.CeilToInt(rings.Max(r=>r.Max(p=>p.x)))+2,y1=Mathf.CeilToInt(rings.Max(r=>r.Max(p=>p.y)))+2;
        int w=x1-x0,h=y1-y0;var graph=rings.Select(r=>r.Select(p=>new CurveArea511.P(p.x,p.y)).ToArray()).ToList();var areas=CurveArea511.Compute(graph,x0,y0,w,h);var mask=HeadRegion502.SelectRegions(areas,w,h);
        using(var b=new BinaryWriter(File.Create(Root+"/"+name+".bin"))){b.Write(rings.Count);foreach(var r in rings){b.Write(r.Length);foreach(var p in r){b.Write(p.x);b.Write(p.y);}}b.Write(x0);b.Write(y0);b.Write(w);b.Write(h);foreach(float a in areas)b.Write(a);foreach(bool m in mask)b.Write(m);}
    }
    public void Execute(ExecutionResult result)
    {
        if(Application.dataPath!="C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets")throw new Exception("Wrong project");
        if(EditorApplication.isPlaying||ClothRegion524.Enabled||ClothRegion524.UseOpacityCurves527)throw new Exception("Edit/OFF required");
        Directory.CreateDirectory(Root);
        foreach(int frame in new[]{42,43,44,45}){
            var rs=Read("C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Cloth527/FullLoopB/"+frame.ToString("D3")+"_ALT_GEOMETRY.bin");
            Write("actual"+frame+"_baseline",rs,.09375f);Write("actual"+frame+"_halfcell",rs,.5f);
        }
        var p=new[]{new Vector2(0,0),new Vector2(4,0),new Vector2(4,11),new Vector2(0,11),new Vector2(0,10),new Vector2(-.75f,10),new Vector2(-.75f,7),new Vector2(0,7),new Vector2(0,4),new Vector2(-.75f,4),new Vector2(-.75f,1),new Vector2(0,1)};
        for(int rot=0;rot<4;rot++)for(int sub=0;sub<2;sub++){
            Vector2 Turn(Vector2 v){for(int k=0;k<rot;k++)v=new Vector2(-v.y,v.x);return v;}
            var rs=new List<Vector2>();for(int i=0;i<p.Length;i++){rs.Add(Turn(p[i]));if(sub!=0)rs.Add(Turn((p[i]+p[(i+1)%p.Length])*.5f));}
            var rings=new List<Vector2[]>{rs.ToArray()};Write("thin"+rot+"_"+sub+"_baseline",rings,.09375f);Write("thin"+rot+"_"+sub+"_halfcell",rings,.5f);
        }
        result.Log("532 stored geometry4 + normal-thin8 math cases complete; actual production area and spatial selector reused; no Play/render/product state changes; cloth="+ClothRegion524.Enabled+" curves="+ClothRegion524.UseOpacityCurves527);
    }
}
