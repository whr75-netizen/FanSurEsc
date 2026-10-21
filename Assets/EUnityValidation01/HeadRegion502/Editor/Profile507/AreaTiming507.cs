#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Diagnostics;
using P=HeadArea505.P;
using Plane=HeadArea505.Plane;
using Material=HeadArea505.Material;
using T=HeadArea505.T;
using Input=HeadArea505.Input;
using Result=HeadArea505.Result;

// Editor-only observer. No automatic startup, renderer call, game-state mutation,
// optimization, alternate area rule or production-path connection.
public static class AreaTiming507
{
    public enum Stage { Binning,CellClip,Occlusion,OverlapClip,AlphaBounds,Subtract,Union,EdgeBuild,PairIntersections,EventSort,Integration,SpanBuild,SpanSort,SpanMerge,Count }
    public static readonly long[] Ticks=new long[(int)Stage.Count],Calls=new long[(int)Stage.Count];
    static long Begin()=>Stopwatch.GetTimestamp();
    static void End(Stage stage,long start){int i=(int)stage;Ticks[i]+=Stopwatch.GetTimestamp()-start;Calls[i]++;}
    public static void Reset(){Array.Clear(Ticks,0,Ticks.Length);Array.Clear(Calls,0,Calls.Length);}
    static double Cross(P a,P b){return a.x*b.y-a.y*b.x;}
    static P Sub(P a,P b){return new P(a.x-b.x,a.y-b.y);}
    public static double Area(List<P> p){double sum=0;for(int i=0;i<p.Count;i++)sum+=Cross(p[i],p[(i+1)%p.Count]);return Math.Abs(sum)*.5;}
    static Plane Fit(P[] p,double[] v){var a=Sub(p[1],p[0]);var b=Sub(p[2],p[0]);double d=Cross(a,b),u=v[1]-v[0],w=v[2]-v[0];double x=(u*b.y-w*a.y)/d,y=(a.x*w-b.x*u)/d;return new Plane{x=x,y=y,c=v[0]-x*p[0].x-y*p[0].y};}
    static bool Same(P a,P b)=>a.x==b.x&&a.y==b.y;
    static void Append(List<P> p,P q){if(p.Count==0||!Same(p[p.Count-1],q))p.Add(q);}
    public static List<P> Clip(List<P> p,Plane plane,bool positive=true){var output=new List<P>();if(p.Count==0)return output;var a=p[p.Count-1];double da=plane.At(a)*(positive?1:-1);foreach(var b in p){double db=plane.At(b)*(positive?1:-1);if((da>=0)!=(db>=0)){double t=da/(da-db);Append(output,new P(a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t));}if(db>=0)Append(output,b);a=b;da=db;}if(output.Count>1&&Same(output[0],output[output.Count-1]))output.RemoveAt(output.Count-1);return output;}
    static List<P> Cell(T t,int x,int y){var p=t.p.ToList();p=Clip(p,new Plane{x=1,c=-x});p=Clip(p,new Plane{x=-1,c=x+1});p=Clip(p,new Plane{y=1,c=-y});return Clip(p,new Plane{y=-1,c=y+1});}
    static Plane Edge(P a,P b,double sign){var d=Sub(b,a);return new Plane{x=-d.y*sign,y=d.x*sign,c=(d.y*a.x-d.x*a.y)*sign};}
    static List<P> Overlap(List<P> p,T t){double sign=Math.Sign(Cross(Sub(t.p[1],t.p[0]),Sub(t.p[2],t.p[0])));for(int i=0;i<3;i++)p=Clip(p,Edge(t.p[i],t.p[(i+1)%3],sign));return p;}
    static List<List<P>> Subtract(List<P> p,List<P> remove){var result=new List<List<P>>();if(remove.Count<3||Area(remove)<1e-13){result.Add(p);return result;}double signed=0;for(int i=0;i<remove.Count;i++)signed+=Cross(remove[i],remove[(i+1)%remove.Count]);double sign=Math.Sign(signed);var inside=p;for(int i=0;i<remove.Count&&inside.Count>0;i++){if(Same(remove[i],remove[(i+1)%remove.Count]))continue;var edge=Edge(remove[i],remove[(i+1)%remove.Count],sign);var outside=Clip(inside,edge,false);if(Area(outside)>1e-13)result.Add(outside);inside=Clip(inside,edge);}return result;}
    static int Mod(int x,int m){int n=x%m;return n<0?n+m:n;}
    // Runtime readback proves all current source textures have mipCount=1,
    // identity UV transform, zero UV animation, repeat wrap, bilinear filtering.
    // Min/max of every contributing texel bounds alpha over this entire polygon.
    // Mixed coverage remains a lower/upper interval, never guessed opaque.
    static int Coverage(Material m,T t,List<P> p){double threshold=m.mode==1?m.cutoff:6.103515625e-5;if(m.min>=threshold)return 1;if(m.max<threshold)return 0;double u0=double.PositiveInfinity,v0=u0,u1=double.NegativeInfinity,v1=u1;foreach(var q in p){double u=t.u.At(q)*m.width-.5,v=t.v.At(q)*m.height-.5;u0=Math.Min(u0,u);u1=Math.Max(u1,u);v0=Math.Min(v0,v);v1=Math.Max(v1,v);}int xa=(int)Math.Floor(u0),xb=(int)Math.Ceiling(u1),ya=(int)Math.Floor(v0),yb=(int)Math.Ceiling(v1);int lo=255,hi=0;for(int y=ya;y<=yb;y++)for(int x=xa;x<=xb;x++){int n=m.alpha[Mod(y,m.height)*m.width+Mod(x,m.width)];lo=Math.Min(lo,n);hi=Math.Max(hi,n);}if(lo/255.0>=threshold)return 1;if(hi/255.0<threshold)return 0;return -1;}
    static List<List<P>> Remove(List<List<P>> source,List<P> remove){var output=new List<List<P>>();foreach(var p in source)output.AddRange(Subtract(p,remove));return output;}
    static double Length(List<List<P>> polygons,double y){long spanBuild=Begin();var spans=new List<P>();foreach(var p in polygons){double lo=double.PositiveInfinity,hi=double.NegativeInfinity;for(int i=0;i<p.Count;i++){var a=p[i];var b=p[(i+1)%p.Count];if((a.y<=y&&y<b.y)||(b.y<=y&&y<a.y)){double x=a.x+(y-a.y)*(b.x-a.x)/(b.y-a.y);lo=Math.Min(lo,x);hi=Math.Max(hi,x);}}if(lo<hi)spans.Add(new P(lo,hi));}End(Stage.SpanBuild,spanBuild);long spanSort=Begin();spans.Sort((a,b)=>a.x.CompareTo(b.x));End(Stage.SpanSort,spanSort);long spanMerge=Begin();double end=double.NegativeInfinity,length=0;foreach(var span in spans){length+=Math.Max(0,span.y-Math.Max(span.x,end));end=Math.Max(end,span.y);}End(Stage.SpanMerge,spanMerge);return length;}
    public static double Union(List<List<P>> polygons){if(polygons.Count==0)return 0;long union=Begin();long edgesBuild=Begin();var levels=new List<double>();var edges=new List<P[]>();foreach(var p in polygons)for(int i=0;i<p.Count;i++){var a=p[i];var b=p[(i+1)%p.Count];levels.Add(a.y);if(Math.Abs(a.y-b.y)>1e-12)edges.Add(new[]{a,b});}End(Stage.EdgeBuild,edgesBuild);long pairs=Begin();for(int i=0;i<edges.Count;i++){var a=edges[i][0];var b=edges[i][1];double k=(b.x-a.x)/(b.y-a.y),c=a.x-k*a.y;for(int j=i+1;j<edges.Count;j++){var aa=edges[j][0];var bb=edges[j][1];double kk=(bb.x-aa.x)/(bb.y-aa.y),cc=aa.x-kk*aa.y;if(Math.Abs(k-kk)<1e-12)continue;double y=(cc-c)/(k-kk);if(y>Math.Max(Math.Min(a.y,b.y),Math.Min(aa.y,bb.y))+1e-11&&y<Math.Min(Math.Max(a.y,b.y),Math.Max(aa.y,bb.y))-1e-11)levels.Add(y);}}End(Stage.PairIntersections,pairs);long sort=Begin();levels.Sort();End(Stage.EventSort,sort);long integration=Begin();double total=0;for(int i=0;i+1<levels.Count;i++){double dy=levels[i+1]-levels[i];if(dy>1e-12)total+=dy*Length(polygons,(levels[i]+levels[i+1])*.5);}End(Stage.Integration,integration);End(Stage.Union,union);return Math.Max(0,Math.Min(1,total));}



    public static Result Compute(Input input,Material[] materials)
    {
        Reset(); var watch=Stopwatch.StartNew();int w=input.w,h=input.h;
        long binning=Begin();var bins=new List<T>[w*h];
        foreach(var t in input.triangles)
        {
            int x0=Math.Max(input.x,(int)Math.Floor(t.x0)),y0=Math.Max(input.y,(int)Math.Floor(t.y0));
            int x1=Math.Min(input.x+w-1,(int)Math.Floor(t.x1)),y1=Math.Min(input.y+h-1,(int)Math.Floor(t.y1));
            for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++)
            {int at=(y-input.y)*w+x-input.x;if(bins[at]==null)bins[at]=new List<T>();bins[at].Add(t);}
        }
        End(Stage.Binning,binning);
        var output=new Result{lower=new float[w*h],upper=new float[w*h]};
        for(int y=input.y;y<input.y+h;y++)for(int x=input.x;x<input.x+w;x++)
        {
            int at=(y-input.y)*w+x-input.x;var bin=bins[at];if(bin==null)continue;
            var lower=new List<List<P>>();var upper=new List<List<P>>();
            foreach(var t in bin)
            {
                if(t.renderer!=2)continue;
                long cell=Begin();var p=Cell(t,x,y);End(Stage.CellClip,cell);
                if(Area(p)<1e-12)continue;
                var lo=new List<List<P>>{p};var hi=new List<List<P>>{p};
                long occlusion=Begin();
                foreach(var o in bin)
                {
                    if(o.renderer==2||o.z0>=t.z1||o.x1<t.x0||o.x0>t.x1||o.y1<t.y0||o.y0>t.y1)continue;
                    if(t.z.x==o.z.x&&t.z.y==o.z.y&&t.z.c==o.z.c)continue;
                    long clip=Begin();var overlap=Overlap(p,o);
                    overlap=Clip(overlap,new Plane{x=t.z.x-o.z.x,y=t.z.y-o.z.y,c=t.z.c-o.z.c});
                    End(Stage.OverlapClip,clip);
                    if(Area(overlap)<1e-12)continue;
                    long alpha=Begin();int coverage=Coverage(materials[o.sm],o,overlap);End(Stage.AlphaBounds,alpha);
                    if(coverage==0)continue;
                    long subtract=Begin();lo=Remove(lo,overlap);
                    if(coverage>0)hi=Remove(hi,overlap);else output.ambiguousFragments++;
                    End(Stage.Subtract,subtract);
                }
                End(Stage.Occlusion,occlusion);lower.AddRange(lo);upper.AddRange(hi);
            }
            output.lower[at]=(float)Union(lower);output.upper[at]=(float)Union(upper);
        }
        watch.Stop();output.milliseconds=watch.Elapsed.TotalMilliseconds;return output;
    }
    // Timer-pair calibration has the same Begin/End/store path. Its scaled result
    // is an estimate; raw stage durations and paired empirical overhead are kept.
    public static double Calibrate(int count)
    {
        Reset();long start=Stopwatch.GetTimestamp();
        for(int i=0;i<count;i++){long t=Begin();End(Stage.Binning,t);}
        return 1000.0*(Stopwatch.GetTimestamp()-start)/Stopwatch.Frequency/count;
    }
    public static Material[] ReadMaterials(string root){using(var b=new BinaryReader(File.OpenRead(Path.Combine(root,"materials505.bin")))){int n=b.ReadInt32();var rows=new Material[n];for(int i=0;i<n;i++){var m=new Material{width=b.ReadInt32(),height=b.ReadInt32(),cull=b.ReadInt32(),mode=b.ReadInt32(),cutoff=b.ReadDouble()};m.alpha=b.ReadBytes(m.width*m.height);m.min=m.alpha.Min()/255.0;m.max=m.alpha.Max()/255.0;rows[i]=m;}return rows;}}
    public static Input Read(string path,Material[] materials){using(var b=new BinaryReader(File.OpenRead(path))){int nr=b.ReadInt32();b.ReadInt32();var input=new Input{phase=b.ReadSingle(),ox=b.ReadInt32(),oy=b.ReadInt32()};for(int j=0;j<16;j++)b.ReadSingle();var tt=new List<T>();int mat=0;double x0=480,y0=272,x1=0,y1=0;for(int r=0;r<nr;r++){int nv=b.ReadInt32(),ns=b.ReadInt32();var vertices=new double[nv][];for(int j=0;j<nv;j++){vertices[j]=new double[8];for(int k=0;k<8;k++)vertices[j][k]=b.ReadSingle();if(r==2){x0=Math.Min(x0,vertices[j][5]);x1=Math.Max(x1,vertices[j][5]);y0=Math.Min(y0,vertices[j][6]);y1=Math.Max(y1,vertices[j][6]);}}for(int sm=0;sm<ns;sm++,mat++){int count=b.ReadInt32();for(int j=0;j<count;j+=3){var a=vertices[b.ReadInt32()];var bb=vertices[b.ReadInt32()];var c=vertices[b.ReadInt32()];var vv=new[]{a,bb,c};var p=vv.Select(v=>new P(v[5],v[6])).ToArray();double cross=Cross(Sub(p[1],p[0]),Sub(p[2],p[0]));if(Math.Abs(cross)<1e-10||(materials[mat].cull==2&&cross<=0))continue;tt.Add(new T{renderer=r,sm=mat,id=j/3,p=p,z=Fit(p,vv.Select(v=>v[7]).ToArray()),u=Fit(p,vv.Select(v=>v[3]).ToArray()),v=Fit(p,vv.Select(v=>v[4]).ToArray()),x0=p.Min(v=>v.x),x1=p.Max(v=>v.x),y0=p.Min(v=>v.y),y1=p.Max(v=>v.y),z0=Math.Min(a[7],Math.Min(bb[7],c[7])),z1=Math.Max(a[7],Math.Max(bb[7],c[7]))});}}}input.x=Math.Max(0,(int)Math.Floor(x0)-2);input.y=Math.Max(0,(int)Math.Floor(y0)-2);input.w=Math.Min(480,(int)Math.Ceiling(x1)+2)-input.x;input.h=Math.Min(272,(int)Math.Ceiling(y1)+2)-input.y;input.triangles=tt.ToArray();return input;}}
}
#endif
