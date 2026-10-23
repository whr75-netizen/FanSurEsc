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
    Vector2[] Fit(Vector2[] ring)
    {
        int n=ring.Length,split=0;float far=0;for(int i=1;i<n;i++){float d=(ring[i]-ring[0]).sqrMagnitude;if(d>far){far=d;split=i;}}
        var keep=new bool[n+1];keep[0]=keep[split]=keep[n]=true;
        void Run(int a,int b)
        {
            if(b<=a+1)return;var p=ring[a%n];var dd=ring[b%n]-p;double length=Math.Sqrt(dd.sqrMagnitude),area=0,previousS=0,previousH=0,maxH=-1;int at=-1;bool ordered=length>0;
            for(int k=a+1;k<=b;k++)
            {
                var v=ring[k%n]-p;double s=length>0?((double)v.x*dd.x+(double)v.y*dd.y)/length:0,h=length>0?((double)dd.x*v.y-(double)dd.y*v.x)/length:0;
                if(s<previousS)ordered=false;
                double u=Math.Abs(previousH),w=Math.Abs(h),ds=s-previousS;
                area+=ds*(previousH*h<0?(u*u+w*w)/(2*(u+w)):(u+w)*.5);
                if(k<b&&Math.Abs(h)>maxH){maxH=Math.Abs(h);at=k;}
                previousS=s;previousH=h;
            }
            if(ordered&&area<=1.0)return;
            if(at<=a||at>=b)at=(a+b)/2;keep[at]=true;Run(a,at);Run(at,b);
        }
        Run(0,split);Run(split,n);return Enumerable.Range(0,n).Where(i=>keep[i]).Select(i=>ring[i]).ToArray();
    }
    void Write(string name,List<Vector2[]> source)
    {
        var rings=source.Select(Fit).Where(r=>r.Length>=3).ToList();if(rings.Count==0)throw new Exception("No region "+name);
        int x0=Mathf.FloorToInt(rings.Min(r=>r.Min(p=>p.x)))-2,y0=Mathf.FloorToInt(rings.Min(r=>r.Min(p=>p.y)))-2,x1=Mathf.CeilToInt(rings.Max(r=>r.Max(p=>p.x)))+2,y1=Mathf.CeilToInt(rings.Max(r=>r.Max(p=>p.y)))+2;
        int w=x1-x0,h=y1-y0;var graph=rings.Select(r=>r.Select(p=>new CurveArea511.P(p.x,p.y)).ToArray()).ToList();var areas=CurveArea511.Compute(graph,x0,y0,w,h);var mask=HeadRegion502.SelectRegions(areas,w,h);
        using(var b=new BinaryWriter(File.Create(Root+"/"+name+".bin"))){b.Write(rings.Count);foreach(var r in rings){b.Write(r.Length);foreach(var p in r){b.Write(p.x);b.Write(p.y);}}b.Write(x0);b.Write(y0);b.Write(w);b.Write(h);foreach(float a in areas)b.Write(a);foreach(bool m in mask)b.Write(m);}
    }
    public void Execute(ExecutionResult result)
    {
        if(Application.dataPath!="C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets"||EditorApplication.isPlaying||ClothRegion524.Enabled||ClothRegion524.UseOpacityCurves527)throw new Exception("Edit/OFF required in intended project");
        foreach(int frame in new[]{42,43,44,45})Write("actual"+frame+"_area",Read("C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Cloth527/FullLoopB/"+frame.ToString("D3")+"_ALT_GEOMETRY.bin"));
        var p=new[]{new Vector2(0,0),new Vector2(4,0),new Vector2(4,11),new Vector2(0,11),new Vector2(0,10),new Vector2(-.75f,10),new Vector2(-.75f,7),new Vector2(0,7),new Vector2(0,4),new Vector2(-.75f,4),new Vector2(-.75f,1),new Vector2(0,1)};
        for(int rot=0;rot<4;rot++)for(int sub=0;sub<2;sub++){
            Vector2 Turn(Vector2 v){for(int k=0;k<rot;k++)v=new Vector2(-v.y,v.x);return v;}
            var rs=new List<Vector2>();for(int i=0;i<p.Length;i++){rs.Add(Turn(p[i]));if(sub!=0)rs.Add(Turn((p[i]+p[(i+1)%p.Length])*.5f));}
            Write("thin"+rot+"_"+sub+"_area",new List<Vector2[]>{rs.ToArray()});
        }
        result.Log("532 ordered symmetric-area chord replacement; budget1 logicalcell area; original baseline reused, area and cut unchanged; 12 cases written; Edit="+!EditorApplication.isPlaying+" cloth="+ClothRegion524.Enabled+" curves="+ClothRegion524.UseOpacityCurves527);
    }
}
