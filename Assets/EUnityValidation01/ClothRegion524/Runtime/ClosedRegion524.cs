using System;
using System.Collections.Generic;
using System.Linq;
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
    sealed class Edge{public P a,b;public int weight;public readonly List<double> split=new List<double>{0,1};}
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
    static int Winding(double px,double py,List<Edge> edges,bool rotated)
    {
        double x=rotated?-py:px,y=rotated?px:py;int value=0;
        foreach(var e in edges){double ax=rotated?-e.a.Y:e.a.X,ay=rotated?e.a.X:e.a.Y,bx=rotated?-e.b.Y:e.b.X,by=rotated?e.b.X:e.b.Y;
            if(!((ay<=y&&y<by)||(by<=y&&y<ay)))continue;
            double orient=Cross(bx-ax,by-ay,x-ax,y-ay),tolerance=2e-8*(Math.Abs(bx-ax)+Math.Abs(by-ay));
            if(ay<=y&&y<by&&orient>tolerance)value+=e.weight;else if(by<=y&&y<ay&&orient< -tolerance)value-=e.weight;}
        return value;
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
    static List<Vector2[]> BuildCounts(Dictionary<(P,P),int> counts)
    {
        var edges=new List<Edge>();foreach(var row in counts)if(row.Value!=0)edges.Add(row.Value>0?new Edge{a=row.Key.Item1,b=row.Key.Item2,weight=row.Value}:new Edge{a=row.Key.Item2,b=row.Key.Item1,weight=-row.Value});WeightedEdges=edges.Count;
        for(int i=0;i<edges.Count;i++)for(int j=i+1;j<edges.Count;j++){var a=edges[i];var b=edges[j];if(Math.Max(Math.Min(a.a.X,a.b.X),Math.Min(b.a.X,b.b.X))>Math.Min(Math.Max(a.a.X,a.b.X),Math.Max(b.a.X,b.b.X))||Math.Max(Math.Min(a.a.Y,a.b.Y),Math.Min(b.a.Y,b.b.Y))>Math.Min(Math.Max(a.a.Y,a.b.Y),Math.Max(b.a.Y,b.b.Y)))continue;Intersect(a,b);}
        counts.Clear();foreach(var e in edges){e.split.Sort();for(int i=0;i+1<e.split.Count;i++)if(e.split[i+1]-e.split[i]>1e-12)Count(counts,At(e,e.split[i]),At(e,e.split[i+1]),e.weight);}Fragments=counts.Count;
        var outgoing=new Dictionary<P,HashSet<P>>();BoundaryEdges=0;
        foreach(var row in counts){if(row.Value==0)continue;P a=row.Value>0?row.Key.Item1:row.Key.Item2,b=row.Value>0?row.Key.Item2:row.Key.Item1;int w=Math.Abs(row.Value);double dx=b.X-a.X,dy=b.Y-a.Y;bool rotated=Math.Abs(dx)>Math.Abs(dy);int sign=(rotated?dx:dy)>0?1:-1;int right=Winding((a.X+b.X)*.5,(a.Y+b.Y)*.5,edges,rotated),minus=right+sign*w,left=sign>0?minus:right;right=sign>0?right:minus;
            if(left<0||right<0)throw new InvalidOperationException("524 negative union winding");if((left>0)==(right>0))continue;if(left<=0)(a,b)=(b,a);if(!outgoing.TryGetValue(a,out var targets)){targets=new HashSet<P>();outgoing.Add(a,targets);}if(targets.Add(b))BoundaryEdges++;}
        var loops=new List<Vector2[]>();int remaining=BoundaryEdges;
        while(outgoing.Count>0){P start=outgoing.Keys.Min(),at=start,prior=default;bool first=true;var ring=new List<Vector2>();
            do{if(!outgoing.TryGetValue(at,out var targets)||targets.Count==0)throw new InvalidOperationException("524 open vector boundary");ring.Add(at.Vector);P next;
                if(first)next=targets.Min();else{double dx=at.X-prior.X,dy=at.Y-prior.Y;next=targets.OrderByDescending(q=>Math.Atan2(Cross(dx,dy,q.X-at.X,q.Y-at.Y),dx*(q.X-at.X)+dy*(q.Y-at.Y))).ThenBy(q=>q).First();}
                targets.Remove(next);if(targets.Count==0)outgoing.Remove(at);if(--remaining<0)throw new InvalidOperationException("524 cyclic edge traversal");prior=at;at=next;first=false;
            }while(!at.Equals(start));if(ring.Count>=3)loops.Add(ring.ToArray());}
        if(remaining!=0)throw new InvalidOperationException("524 unconsumed boundary");return loops;
    }
    public static Vector2[] Fit(Vector2[] ring,float error)
    {
        int n=ring.Length,split=0;float far=0;for(int i=1;i<n;i++){float d=(ring[i]-ring[0]).sqrMagnitude;if(d>far){far=d;split=i;}}
        var keep=new SortedSet<int>{0,split,n};
        void Run(int a,int b){if(b<=a+1)return;var p=ring[a%n];var d=ring[b%n]-p;float den=d.sqrMagnitude,best=error*error;int at=-1;for(int j=a+1;j<b;j++){var v=ring[j%n]-p;float t=den>0?Mathf.Clamp01(Vector2.Dot(v,d)/den):0,e=(v-t*d).sqrMagnitude;if(e>best){best=e;at=j;}}if(at<0)return;keep.Add(at);Run(a,at);Run(at,b);}
        Run(0,split);Run(split,n);return keep.Where(i=>i<n).Select(i=>ring[i]).ToArray();
    }
}
