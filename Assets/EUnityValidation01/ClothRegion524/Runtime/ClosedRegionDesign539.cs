using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

// Whole-feature area quantization in the common logical grid. This replaces
// arbitrary RDP subchords; it does not clean a raster mask or retain history.
public static class ClosedRegionDesign539
{
    struct P
    {
        public double x,y;
        public P(double x,double y){this.x=x;this.y=y;}
        public double Axis(int axis)=>axis==0?x:y;
    }
    sealed class Return
    {
        public double start,end,area;
        public P a,b;
    }
    public static int LastReturns,LastRejected;
    static double Area(IList<P> r){double s=0;for(int i=0;i<r.Count;i++){var a=r[i];var b=r[(i+1)%r.Count];s+=a.x*b.y-a.y*b.x;}return s*.5;}
    static int Mod(int n,int length)=>(n%length+length)%length;
    static P Lerp(P a,P b,double t)=>new P(a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t);
    static double Cross(P a,P b,P c)=>(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);
    public static Vector2[] Fit(Vector2[] ring)
    {
        LastReturns=LastRejected=0;int n=ring.Length;if(n<3)return ring;
        var r=ring.Select(p=>new P(p.x,p.y)).ToArray();double winding=Math.Sign(Area(r));if(winding==0)return ring;
        var candidates=new List<Return>();var seen=new List<(int,double,double,double,double)>();
        for(int axis=0;axis<2;axis++)foreach(int sign in new[]{1,-1})for(int i=0;i<n;i++)
        {
            double V(int k)=>r[Mod(k,n)].Axis(axis)*sign;
            double v=V(i),prev=V(i-1),next=V(i+1);
            if(v>prev+1e-10||v>next+1e-10||Math.Max(prev-v,next-v)<=1e-10)continue;
            var peaks=new double[2];int dindex=0;
            foreach(int step in new[]{-1,1}){int at=i;for(int count=0;count<n-1;count++){int to=Mod(at+step,n);if(V(to)<V(at)-1e-10)break;at=to;}peaks[dindex++]=V(at);}
            double level=Math.Min(peaks[0],peaks[1]);if(level-v<=1e-9)continue;
            var paths=new List<P>[2];var parameter=new double[2];bool valid=true;dindex=0;
            foreach(int step in new[]{-1,1})
            {
                var path=paths[dindex]=new List<P>{r[i]};int at=i;bool found=false;
                for(int count=0;count<n;count++)
                {
                    int to=Mod(at+step,n);
                    if(V(to)>=level-1e-10){double t=(level-V(at))/(V(to)-V(at));path.Add(Lerp(r[at],r[to],t));double a=step==1?at+t:to+1-t;parameter[dindex]=(a%n+n)%n;found=true;break;}
                    path.Add(r[to]);at=to;
                }
                valid&=found;dindex++;
            }
            if(!valid)continue;var arc=paths[0].AsEnumerable().Reverse().Concat(paths[1].Skip(1)).ToArray();
            bool up=true,down=true,anyUp=false,anyDown=false;
            for(int k=1;k<arc.Length;k++){double d=arc[k].Axis(1-axis)-arc[k-1].Axis(1-axis);up&=d>=-1e-9;down&=d<=1e-9;anyUp|=d>1e-9;anyDown|=d<-1e-9;}
            if(!(up&&anyUp||down&&anyDown))continue;
            double area=Area(arc);if(area*winding<=1e-9||Math.Abs(area)>1.0)continue;
            var a0=arc[0];var b0=arc[arc.Length-1];var key=(axis,Math.Round(a0.x,8),Math.Round(a0.y,8),Math.Round(b0.x,8),Math.Round(b0.y,8));
            if(seen.Contains(key))continue;seen.Add(key);candidates.Add(new Return{start=parameter[0],end=parameter[1],area=Math.Abs(area),a=a0,b=b0});
        }
        var intervals=new List<(double,double)>();var picked=new List<Return>();
        foreach(var c in candidates.OrderBy(c=>c.area).ThenBy(c=>c.start).ThenBy(c=>c.end))
        {
            var spans=c.start<c.end?new[]{(c.start,c.end)}:new[]{(c.start,(double)n),(0.0,c.end)};
            if(spans.Any(s=>intervals.Any(t=>Math.Min(s.Item2,t.Item2)-Math.Max(s.Item1,t.Item1)>1e-10)))continue;
            intervals.AddRange(spans);picked.Add(c);
        }
        var points=new List<(double,P)>();
        for(int i=0;i<n;i++)if(!intervals.Any(s=>s.Item1+1e-10<i&&i<s.Item2-1e-10))points.Add((i,r[i]));
        foreach(var c in picked){points.Add((c.start,c.a));points.Add((c.end,c.b));}
        var result=new List<P>();
        foreach(var p in points.OrderBy(p=>p.Item1).Select(p=>p.Item2))if(result.Count==0||Math.Max(Math.Abs(result[result.Count-1].x-p.x),Math.Abs(result[result.Count-1].y-p.y))>1e-9)result.Add(p);
        if(result.Count>1&&Math.Max(Math.Abs(result[0].x-result[result.Count-1].x),Math.Abs(result[0].y-result[result.Count-1].y))<=1e-9)result.RemoveAt(result.Count-1);
        if(result.Count<3||Area(result)*winding<=0){LastRejected=1;return ring;}
        // Preserve the existing closed-region validity contract. Invalid
        // geometric substitutions are explicit, never raster fallbacks.
        for(int i=0;i<result.Count;i++)for(int j=i+1;j<result.Count;j++)
        {
            if(j==i+1||i==0&&j==result.Count-1)continue;var a=result[i];var b=result[(i+1)%result.Count];var c=result[j];var d=result[(j+1)%result.Count];
            if(Cross(a,b,c)*Cross(a,b,d)<0&&Cross(c,d,a)*Cross(c,d,b)<0){LastRejected=1;return ring;}
        }
        LastReturns=picked.Count;return result.Select(p=>new Vector2((float)p.x,(float)p.y)).ToArray();
    }
}
