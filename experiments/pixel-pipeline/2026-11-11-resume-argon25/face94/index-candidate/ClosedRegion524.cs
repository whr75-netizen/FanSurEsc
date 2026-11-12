using System;
using System.Collections.Generic;
using System.Linq;
using System.Diagnostics;
using UnityEngine;

// Vector union of projected triangles, followed by a closed polygonal fit.
// Ports compile_curve511.vector_union; coordinates are geometric, never a raster mask.
public static class ClosedRegion524
{
    const double ArithmeticGrid = 1e8;
    public readonly struct P : IEquatable<P>, IComparable<P>
    {
        public readonly long x,y;
        public P(double x,double y){this.x=(long)Math.Round(x*ArithmeticGrid);this.y=(long)Math.Round(y*ArithmeticGrid);}
        public double X=>x/ArithmeticGrid;public double Y=>y/ArithmeticGrid;
        public bool Equals(P p)=>x==p.x&&y==p.y;public override bool Equals(object p)=>p is P q&&Equals(q);
        public override int GetHashCode()=>unchecked(x.GetHashCode()*397^y.GetHashCode());
        public int CompareTo(P p){int c=x.CompareTo(p.x);return c!=0?c:y.CompareTo(p.y);}
        public Vector2 Vector=>new Vector2((float)X,(float)Y);
    }
    public sealed class Anchor579 {public int sm,primitive,a,b,c;public double u,v,w;}
    public sealed class Node579 {public Vector2 point;public List<Anchor579> anchors;}
    sealed class Origin579 {public P start,end;public int sm,primitive,a,b,c,from,to;}
    sealed class Edge{public P a,b;public int weight;public readonly List<double> split=new List<double>{0,1};public List<Origin579> origins579;}
    static (P,P) OriginKey579(P a,P b)=>a.CompareTo(b)<0?(a,b):(b,a);
    static void Register579(Dictionary<P,List<Anchor579>> output,P p,Edge edge,double t)
    {
        if(output==null)return;if(!output.TryGetValue(p,out var list))output.Add(p,list=new List<Anchor579>());
        foreach(var source in edge.origins579){double along=source.start.Equals(edge.a)?t:1-t;var weights=new double[3];weights[source.from]=1-along;weights[source.to]=along;list.Add(new Anchor579{sm=source.sm,primitive=source.primitive,a=source.a,b=source.b,c=source.c,u=weights[0],v=weights[1],w=weights[2]});}
    }
    public static List<Node579[]> BuildAnchored579(Vector2[] points,int[][] indices)
    {
        var counts=new Dictionary<(P,P),int>();var origins=new Dictionary<(P,P),List<Origin579>>();
        for(int sm=0;sm<indices.Length;sm++)for(int j=0;j<indices[sm].Length;j+=3){
            var ids=new[]{indices[sm][j],indices[sm][j+1],indices[sm][j+2]};var p=ids.Select(i=>new P(points[i].x,points[i].y)).ToArray();var role=new[]{0,1,2};double area=Cross(p[0],p[1],p[2]);if(Math.Abs(area)<1e-12)continue;if(area<0){(p[1],p[2])=(p[2],p[1]);(role[1],role[2])=(role[2],role[1]);}
            for(int e=0;e<3;e++){int next=(e+1)%3;var a=p[e];var b=p[next];Count(counts,a,b);if(a.Equals(b))continue;var key=OriginKey579(a,b);if(!origins.TryGetValue(key,out var list))origins.Add(key,list=new List<Origin579>());list.Add(new Origin579{start=a,end=b,sm=sm,primitive=j/3,a=ids[0],b=ids[1],c=ids[2],from=role[e],to=role[next]});}
        }
        var result=new List<Node579[]>();BuildCounts(counts,origins,result);return result;
    }
    static double Cross(double x,double y,double u,double v)=>x*v-y*u;
    static double Cross(P a,P b,P c)=>Cross(b.X-a.X,b.Y-a.Y,c.X-a.X,c.Y-a.Y);
    static void Count(Dictionary<(P,P),int> counts,P a,P b,int n=1){if(a.Equals(b))return;bool ordered=a.CompareTo(b)<0;var key=ordered?(a,b):(b,a);counts.TryGetValue(key,out int old);counts[key]=old+(ordered?n:-n);}
    static P At(Edge e,double t)=>new P(e.a.X+t*(e.b.X-e.a.X),e.a.Y+t*(e.b.Y-e.a.Y));
    static void AddSplit(Edge e,double t){if(t>=-1e-12&&t<=1+1e-12)e.split.Add(Math.Max(0,Math.Min(1,t)));}
    static void Intersect(Edge a,Edge b)
    {
        double rx=a.b.X-a.a.X,ry=a.b.Y-a.a.Y,sx=b.b.X-b.a.X,sy=b.b.Y-b.a.Y,qx=b.a.X-a.a.X,qy=b.a.Y-a.a.Y;
        double den=Cross(rx,ry,sx,sy);
        if(Math.Abs(den)>1e-14){double t=Cross(qx,qy,sx,sy)/den,u=Cross(qx,qy,rx,ry)/den;if(t>=0&&t<=1&&u>=0&&u<=1){AddSplit(a,t);AddSplit(b,u);}return;}
        if(Math.Abs(Cross(qx,qy,rx,ry))>1e-10)return;
        bool ax=Math.Abs(rx)>=Math.Abs(ry),bx=Math.Abs(sx)>=Math.Abs(sy);double ad=ax?rx:ry,bd=bx?sx:sy;if(ad==0||bd==0)return;
        foreach(var p in new[]{a.a,a.b,b.a,b.b}){double t=((ax?p.X:p.Y)-(ax?a.a.X:a.a.Y))/ad,u=((bx?p.X:p.Y)-(bx?b.a.X:b.a.Y))/bd;if(t>=0&&t<=1&&u>=0&&u<=1){AddSplit(a,t);AddSplit(b,u);}}
    }
    // Exact candidate indices only. They never select or move a design pixel.
    // Default is inside the enclosing default-OFF clothing experiment.
    public static bool UseSpatialIndex526=true;
    public static bool PairIndexUsed526;
    public static long PairCandidates526,WindingCandidates526;
    public static double PairMs526,WindingMs526;
    sealed class Fragment526 {public P a,b;public int weight,winding;public bool rotated;public double Coordinate=>rotated?(a.X+b.X)*.5:(a.Y+b.Y)*.5;}
    static double Elapsed526(long start)=>1000.0*(Stopwatch.GetTimestamp()-start)/Stopwatch.Frequency;
    static int Contribution526(double x,double y,Edge e,bool rotated)
    {
        double ax=rotated?-e.a.Y:e.a.X,ay=rotated?e.a.X:e.a.Y,bx=rotated?-e.b.Y:e.b.X,by=rotated?e.b.X:e.b.Y;
        if(!((ay<=y&&y<by)||(by<=y&&y<ay)))return 0;
        double orient=Cross(bx-ax,by-ay,x-ax,y-ay),tolerance=2e-8*(Math.Abs(bx-ax)+Math.Abs(by-ay));
        if(ay<=y&&y<by&&orient>tolerance)return e.weight;
        if(by<=y&&y<ay&&orient< -tolerance)return -e.weight;return 0;
    }
    static int Winding(double px,double py,List<Edge> edges,bool rotated)
    {
        double x=rotated?-py:px,y=rotated?px:py;int value=0;
        foreach(var e in edges)value+=Contribution526(x,y,e,rotated);
        WindingCandidates526+=edges.Count;return value;
    }
    static bool Overlap526(Edge a,Edge b)=>!(Math.Max(Math.Min(a.a.X,a.b.X),Math.Min(b.a.X,b.b.X))>Math.Min(Math.Max(a.a.X,a.b.X),Math.Max(b.a.X,b.b.X))||Math.Max(Math.Min(a.a.Y,a.b.Y),Math.Min(b.a.Y,b.b.Y))>Math.Min(Math.Max(a.a.Y,a.b.Y),Math.Max(b.a.Y,b.b.Y)));
    static void Pairs526(List<Edge> edges)
    {
        var grid=new Dictionary<(int,int),List<int>>();var boxes=new (int x,int y,int right,int bottom)[edges.Count];long entries=0;
        for(int i=0;i<edges.Count;i++)
        {
            var e=edges[i];var box=((int)Math.Floor(Math.Min(e.a.X,e.b.X)),(int)Math.Floor(Math.Min(e.a.Y,e.b.Y)),(int)Math.Floor(Math.Max(e.a.X,e.b.X)),(int)Math.Floor(Math.Max(e.a.Y,e.b.Y)));boxes[i]=box;
            // Memory guard falls back to the original calculation, never a mask.
            entries+=((long)box.Item3-box.Item1+1)*((long)box.Item4-box.Item2+1);if(entries>262144){grid=null;break;}
            for(int y=box.Item2;y<=box.Item4;y++)for(int x=box.Item1;x<=box.Item3;x++){if(!grid.TryGetValue((x,y),out var ids))grid.Add((x,y),ids=new List<int>());ids.Add(i);}
        }
        PairIndexUsed526=grid!=null;
        if(grid==null){for(int i=0;i<edges.Count;i++)for(int j=i+1;j<edges.Count;j++)if(Overlap526(edges[i],edges[j]))Intersect(edges[i],edges[j]);PairCandidates526=(long)edges.Count*(edges.Count-1)/2;return;}
        for(int i=0;i<edges.Count;i++)
        {
            var b=boxes[i];var possible=new HashSet<int>();for(int y=b.y;y<=b.bottom;y++)for(int x=b.x;x<=b.right;x++)foreach(int j in grid[(x,y)])if(j>i)possible.Add(j);
            var ordered=possible.ToList();ordered.Sort();PairCandidates526+=ordered.Count;
            // Same original i,j order and identical intersection arithmetic.
            foreach(int j in ordered)if(Overlap526(edges[i],edges[j]))Intersect(edges[i],edges[j]);
        }
    }
    static void Sweep526(List<Edge> edges,List<Fragment526> queries,bool rotated)
    {
        var lo=new double[edges.Count];var hi=new double[edges.Count];
        for(int i=0;i<edges.Count;i++){var e=edges[i];double a=rotated?e.a.X:e.a.Y,b=rotated?e.b.X:e.b.Y;lo[i]=Math.Min(a,b);hi[i]=Math.Max(a,b);}
        var begin=Enumerable.Range(0,edges.Count).OrderBy(i=>lo[i]).ThenBy(i=>i).ToArray();var end=Enumerable.Range(0,edges.Count).OrderBy(i=>hi[i]).ThenBy(i=>i).ToArray();var active=new SortedSet<int>();int first=0,last=0;
        foreach(var q in queries.Where(q=>q.rotated==rotated).OrderBy(q=>q.Coordinate))
        {
            double coordinate=q.Coordinate;while(first<begin.Length&&lo[begin[first]]<=coordinate){int i=begin[first++];if(lo[i]<hi[i])active.Add(i);}while(last<end.Length&&hi[end[last]]<=coordinate)active.Remove(end[last++]);
            double px=(q.a.X+q.b.X)*.5,py=(q.a.Y+q.b.Y)*.5,x=rotated?-py:px,y=rotated?px:py;int value=0;
            foreach(int i in active)value+=Contribution526(x,y,edges[i],rotated);q.winding=value;WindingCandidates526+=active.Count;
        }
    }
    public static int WeightedEdges,Fragments,BoundaryEdges;
    public static List<Vector2[]> Build(Vector2[] points,int[] indices)
    {
        var counts=new Dictionary<(P,P),int>();
        for(int j=0;j<indices.Length;j+=3){var a=new P(points[indices[j]].x,points[indices[j]].y);var b=new P(points[indices[j+1]].x,points[indices[j+1]].y);var c=new P(points[indices[j+2]].x,points[indices[j+2]].y);double area=Cross(a,b,c);if(Math.Abs(area)<1e-12)continue;if(area<0)(b,c)=(c,b);Count(counts,a,b);Count(counts,b,c);Count(counts,c,a);}
        return BuildCounts(counts);
    }
    public static List<Vector2[]> BuildSegments(IEnumerable<(Vector2,Vector2)> segments)
    {
        var counts=new Dictionary<(P,P),int>();
        foreach(var line in segments)Count(counts,new P(line.Item1.x,line.Item1.y),new P(line.Item2.x,line.Item2.y));
        return BuildCounts(counts);
    }
    // Preserve high-precision projected source coordinates until the same
    // declared1e8 arithmetic grid. Do not round through Vector2 first.
    public static List<Vector2[]> BuildSegments(IEnumerable<(P,P)> segments)
    {
        var counts=new Dictionary<(P,P),int>();
        foreach(var edge in segments)Count(counts,edge.Item1,edge.Item2);
        return BuildCounts(counts);
    }
    static List<Vector2[]> BuildCounts(Dictionary<(P,P),int> counts,Dictionary<(P,P),List<Origin579>> origins579=null,List<Node579[]> anchored579=null)
    {
        var edges=new List<Edge>();foreach(var row in counts)if(row.Value!=0)edges.Add(row.Value>0?new Edge{a=row.Key.Item1,b=row.Key.Item2,weight=row.Value}:new Edge{a=row.Key.Item2,b=row.Key.Item1,weight=-row.Value});WeightedEdges=edges.Count;
        if(origins579!=null)foreach(var edge in edges)edge.origins579=origins579[OriginKey579(edge.a,edge.b)];
        var nodes579=origins579==null?null:new Dictionary<P,List<Anchor579>>();
        PairCandidates526=WindingCandidates526=0;PairIndexUsed526=false;long pairStart=Stopwatch.GetTimestamp();
        if(UseSpatialIndex526)Pairs526(edges);else{PairCandidates526=(long)edges.Count*(edges.Count-1)/2;for(int i=0;i<edges.Count;i++)for(int j=i+1;j<edges.Count;j++)if(Overlap526(edges[i],edges[j]))Intersect(edges[i],edges[j]);}
        PairMs526=Elapsed526(pairStart);
        counts.Clear();foreach(var e in edges){e.split.Sort();for(int i=0;i+1<e.split.Count;i++)if(e.split[i+1]-e.split[i]>1e-12){var a=At(e,e.split[i]);var b=At(e,e.split[i+1]);Count(counts,a,b,e.weight);Register579(nodes579,a,e,e.split[i]);Register579(nodes579,b,e,e.split[i+1]);}}Fragments=counts.Count;
        long windingStart=Stopwatch.GetTimestamp();var queries=new List<Fragment526>();
        foreach(var row in counts){if(row.Value==0)continue;P a=row.Value>0?row.Key.Item1:row.Key.Item2,b=row.Value>0?row.Key.Item2:row.Key.Item1;queries.Add(new Fragment526{a=a,b=b,weight=Math.Abs(row.Value),rotated=Math.Abs(b.X-a.X)>Math.Abs(b.Y-a.Y)});}
        if(UseSpatialIndex526){Sweep526(edges,queries,false);Sweep526(edges,queries,true);}else foreach(var q in queries)q.winding=Winding((q.a.X+q.b.X)*.5,(q.a.Y+q.b.Y)*.5,edges,q.rotated);
        WindingMs526=Elapsed526(windingStart);var outgoing=new Dictionary<P,HashSet<P>>();BoundaryEdges=0;
        foreach(var q in queries){P a=q.a,b=q.b;int w=q.weight;double dx=b.X-a.X,dy=b.Y-a.Y;bool rotated=q.rotated;int sign=(rotated?dx:dy)>0?1:-1;int right=q.winding,minus=right+sign*w,left=sign>0?minus:right;right=sign>0?right:minus;
            if(left<0||right<0)throw new InvalidOperationException("524 negative union winding");if((left>0)==(right>0))continue;if(left<=0)(a,b)=(b,a);if(!outgoing.TryGetValue(a,out var targets)){targets=new HashSet<P>();outgoing.Add(a,targets);}if(targets.Add(b))BoundaryEdges++;}
        var loops=new List<Vector2[]>();int remaining=BoundaryEdges;
        while(outgoing.Count>0){P start=outgoing.Keys.Min(),at=start,prior=default;bool first=true;var ring=new List<Vector2>();var originRing579=anchored579==null?null:new List<Node579>();
            do{if(!outgoing.TryGetValue(at,out var targets)||targets.Count==0)throw new InvalidOperationException("524 open vector boundary");ring.Add(at.Vector);if(originRing579!=null)originRing579.Add(new Node579{point=at.Vector,anchors=nodes579[at]});P next;
                if(first)next=targets.Min();else{double dx=at.X-prior.X,dy=at.Y-prior.Y;next=targets.OrderByDescending(q=>Math.Atan2(Cross(dx,dy,q.X-at.X,q.Y-at.Y),dx*(q.X-at.X)+dy*(q.Y-at.Y))).ThenBy(q=>q).First();}
                targets.Remove(next);if(targets.Count==0)outgoing.Remove(at);if(--remaining<0)throw new InvalidOperationException("524 cyclic edge traversal");prior=at;at=next;first=false;
            }while(!at.Equals(start));if(ring.Count>=3){loops.Add(ring.ToArray());if(originRing579!=null)anchored579.Add(originRing579.ToArray());}}
        if(remaining!=0)throw new InvalidOperationException("524 unconsumed boundary");return loops;
    }
    // Alternative clothing curve source, not a mask/RGB post-filter. A chord
    // replaces its ordered arc only when its projection does not backtrack and
    // its symmetric area difference is <= one logical cell. Width and length
    // contribute together; opposite signed lobes never cancel. No history or
    // frame/part exceptions. This is a default-OFF design trial, not an art pass.
    public static Vector2[] FitArea532(Vector2[] ring)
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
    public static Vector2[] Fit(Vector2[] ring,float error)
    {
        int n=ring.Length,split=0;float far=0;for(int i=1;i<n;i++){float d=(ring[i]-ring[0]).sqrMagnitude;if(d>far){far=d;split=i;}}
        var keep=new SortedSet<int>{0,split,n};
        void Run(int a,int b){if(b<=a+1)return;var p=ring[a%n];var d=ring[b%n]-p;float den=d.sqrMagnitude,best=error*error;int at=-1;for(int j=a+1;j<b;j++){var v=ring[j%n]-p;float t=den>0?Mathf.Clamp01(Vector2.Dot(v,d)/den):0,e=(v-t*d).sqrMagnitude;if(e>best){best=e;at=j;}}if(at<0)return;keep.Add(at);Run(a,at);Run(at,b);}
        Run(0,split);Run(split,n);return keep.Where(i=>i<n).Select(i=>ring[i]).ToArray();
    }
}
