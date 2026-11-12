using System;
using System.Collections.Generic;
using System.Linq;
using System.Diagnostics;
using UnityEngine;
using BigInteger = System.Numerics.BigInteger;

// Vector union of projected triangles, followed by a closed polygonal fit.
// Ports compile_curve511.vector_union; coordinates are geometric, never a raster mask.
public static class ClosedRegion524
{
    const double ArithmeticGrid = 1e8;
    // Keep the existing input grid. Intersections and predicates stay exact until
    // the closed ring is converted to the existing Vector2 design input.
    internal readonly struct Rational : IComparable<Rational>, IEquatable<Rational>
    {
        readonly BigInteger numerator,denominator;
        BigInteger Denominator=>denominator.IsZero?BigInteger.One:denominator;
        public Rational(BigInteger n,BigInteger d){if(d.IsZero)throw new DivideByZeroException();if(d.Sign<0){n=-n;d=-d;}if(d.IsOne){numerator=n;denominator=d;return;}var g=BigInteger.GreatestCommonDivisor(BigInteger.Abs(n),d);numerator=n/g;denominator=d/g;}
        Rational(BigInteger n,BigInteger d,bool canonical){numerator=n;denominator=d;}
        public static implicit operator Rational(long n)=>new Rational(n,BigInteger.One,true);
        internal BigInteger Numerator=>numerator;
        internal BigInteger Divisor=>Denominator;
        public double Value=>(double)numerator/(double)Denominator;
        public int CompareTo(Rational b)=>(numerator*b.Denominator).CompareTo(b.numerator*Denominator);
        public bool Equals(Rational b)=>numerator==b.numerator&&Denominator==b.Denominator;
        public override bool Equals(object b)=>b is Rational r&&Equals(r);
        public override int GetHashCode()=>unchecked(numerator.GetHashCode()*397^Denominator.GetHashCode());
        public static Rational operator +(Rational a,Rational b)=>a.Denominator.IsOne?new Rational(a.numerator*b.Denominator+b.numerator,b.Denominator,true):b.Denominator.IsOne?new Rational(a.numerator+b.numerator*a.Denominator,a.Denominator,true):new Rational(a.numerator*b.Denominator+b.numerator*a.Denominator,a.Denominator*b.Denominator);
        public static Rational operator -(Rational a,Rational b)=>a.Denominator.IsOne?new Rational(a.numerator*b.Denominator-b.numerator,b.Denominator,true):b.Denominator.IsOne?new Rational(a.numerator-b.numerator*a.Denominator,a.Denominator,true):new Rational(a.numerator*b.Denominator-b.numerator*a.Denominator,a.Denominator*b.Denominator);
        public static Rational operator -(Rational a)=>new Rational(-a.numerator,a.Denominator,true);
        public static Rational operator *(Rational a,Rational b)=>new Rational(a.numerator*b.numerator,a.Denominator*b.Denominator);
        public static Rational operator /(Rational a,Rational b)=>new Rational(a.numerator*b.Denominator,a.Denominator*b.numerator);
        public static bool operator <(Rational a,Rational b)=>a.CompareTo(b)<0;
        public static bool operator >(Rational a,Rational b)=>a.CompareTo(b)>0;
        public static bool operator <=(Rational a,Rational b)=>a.CompareTo(b)<=0;
        public static bool operator >=(Rational a,Rational b)=>a.CompareTo(b)>=0;
        public static bool operator ==(Rational a,Rational b)=>a.Equals(b);
        public static bool operator !=(Rational a,Rational b)=>!a.Equals(b);
        public static Rational Abs(Rational a)=>a.numerator.Sign<0?-a:a;
    }
    public readonly struct P : IEquatable<P>, IComparable<P>
    {
        internal readonly Rational x,y;
        public P(double x,double y){this.x=(long)Math.Round(x*ArithmeticGrid);this.y=(long)Math.Round(y*ArithmeticGrid);}
        internal P(Rational x,Rational y){this.x=x;this.y=y;}
        public double X=>x.Value/ArithmeticGrid;public double Y=>y.Value/ArithmeticGrid;
        public bool Equals(P p)=>x==p.x&&y==p.y;public override bool Equals(object p)=>p is P q&&Equals(q);
        public override int GetHashCode()=>unchecked(x.GetHashCode()*397^y.GetHashCode());
        public int CompareTo(P p){int c=x.CompareTo(p.x);return c!=0?c:y.CompareTo(p.y);}
        public Vector2 Vector=>new Vector2((float)X,(float)Y);
    }
    public sealed class Anchor579 {public int sm,primitive,a,b,c;public double u,v,w;}
    public sealed class Node579 {public Vector2 point;public List<Anchor579> anchors;}
    sealed class Origin579 {public P start,end;public int sm,primitive,a,b,c,from,to;}
    sealed class Edge{public P a,b;public int weight;public readonly List<Rational> split=new List<Rational>{0,1};public List<Origin579> origins579;
        // BuildCounts edges still have the original integer-grid endpoints.
        public long ax,ay,bx,by;public BigInteger dx,dy,lineC;
        public void Prepare526(){ax=(long)a.x.Numerator;ay=(long)a.y.Numerator;bx=(long)b.x.Numerator;by=(long)b.y.Numerator;dx=(BigInteger)bx-ax;dy=(BigInteger)by-ay;lineC=dy*ax-dx*ay;}
    }
    static (P,P) OriginKey579(P a,P b)=>a.CompareTo(b)<0?(a,b):(b,a);
    static void Register579(Dictionary<P,List<Anchor579>> output,P p,Edge edge,Rational t)
    {
        if(output==null)return;if(!output.TryGetValue(p,out var list))output.Add(p,list=new List<Anchor579>());
        foreach(var source in edge.origins579){double along=(source.start.Equals(edge.a)?t:1-t).Value;var weights=new double[3];weights[source.from]=1-along;weights[source.to]=along;list.Add(new Anchor579{sm=source.sm,primitive=source.primitive,a=source.a,b=source.b,c=source.c,u=weights[0],v=weights[1],w=weights[2]});}
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
    static Rational Cross(Rational x,Rational y,Rational u,Rational v)=>x*v-y*u;
    static P At(Edge e,Rational t)=>new P(e.a.x+t*(e.b.x-e.a.x),e.a.y+t*(e.b.y-e.a.y));
    static void Intersect(Edge a,Edge b)
    {
        // Both original edges are integer-grid segments. Reduce only accepted split ratios.
        var rx=a.dx;var ry=a.dy;var sx=b.dx;var sy=b.dy;var qx=(BigInteger)b.ax-a.ax;var qy=(BigInteger)b.ay-a.ay;
        var den=rx*sy-ry*sx;
        if(!den.IsZero){var t=qx*sy-qy*sx;var u=qx*ry-qy*rx;if(den.Sign<0){den=-den;t=-t;u=-u;}if(t.Sign>=0&&t<=den&&u.Sign>=0&&u<=den){a.split.Add(new Rational(t,den));b.split.Add(new Rational(u,den));}return;}
        if(!(qx*ry-qy*rx).IsZero)return;
        bool ax=BigInteger.Abs(rx)>=BigInteger.Abs(ry),bx=BigInteger.Abs(sx)>=BigInteger.Abs(sy);var ad=ax?rx:ry;var bd=bx?sx:sy;if(ad.IsZero||bd.IsZero)return;
        foreach(var p in new[]{a.a,a.b,b.a,b.b}){var t=(ax?p.x.Numerator:p.y.Numerator)-(ax?a.ax:a.ay);var u=(bx?p.x.Numerator:p.y.Numerator)-(bx?b.ax:b.ay);var da=ad;var db=bd;if(da.Sign<0){da=-da;t=-t;}if(db.Sign<0){db=-db;u=-u;}if(t.Sign>=0&&t<=da&&u.Sign>=0&&u<=db){a.split.Add(new Rational(t,da));b.split.Add(new Rational(u,db));}}
    }
    // Exact candidate indices only. They never select or move a design pixel.
    // Default is inside the enclosing default-OFF clothing experiment.
    public static bool UseSpatialIndex526=true;
    public static bool PairIndexUsed526;
    public static long PairCandidates526,WindingCandidates526;
    public static double PairMs526,WindingMs526;
    readonly struct Query526
    {
        public readonly BigInteger x,y,w;public readonly long floorX,floorY,ceilY;
        public Query526(Rational px,Rational py){var dx=px.Divisor;var dy=py.Divisor;w=dx/BigInteger.GreatestCommonDivisor(dx,dy)*dy;x=px.Numerator*(w/dx);y=py.Numerator*(w/dy);var qx=BigInteger.DivRem(x,w,out var rx);var qy=BigInteger.DivRem(y,w,out var ry);if(rx.Sign<0)qx--;if(ry.Sign<0)qy--;floorX=(long)qx;floorY=(long)qy;ceilY=(long)(qy+(ry.IsZero?0:1));}
    }
    sealed class Fragment526
    {
        public P a,b;public int weight,winding;public bool rotated;public Rational Coordinate;public Query526 query;
        public Fragment526(P a,P b,int weight){this.a=a;this.b=b;this.weight=weight;rotated=Rational.Abs(b.x-a.x)>Rational.Abs(b.y-a.y);var px=(a.x+b.x)/2;var py=(a.y+b.y)/2;Coordinate=rotated?px:py;query=new Query526(px,py);}
    }
    static double Elapsed526(long start)=>1000.0*(Stopwatch.GetTimestamp()-start)/Stopwatch.Frequency;
    // The sweep already proves the half-open vertical interval is active.
    // Homogeneous orientation is the same exact determinant, with no per-edge fractions.
    static int Contribution526(Query526 q,Edge e,bool rotated)
    {
        int direction=(rotated?e.dx:e.dy).Sign;
        // Exact integer interval cases, not a rounded orientation or epsilon.
        // The active edge crosses the ray's half-open vertical interval.
        if(!rotated){if(q.floorX<Math.Min(e.ax,e.bx))return direction*e.weight;if(q.floorX>=Math.Max(e.ax,e.bx))return 0;}
        else{if(q.ceilY>Math.Max(e.ay,e.by))return direction*e.weight;if(q.ceilY<=Math.Min(e.ay,e.by))return 0;}
        int orient=(e.dx*q.y-e.dy*q.x+e.lineC*q.w).Sign;
        if(direction>0&&orient>0)return e.weight;
        if(direction<0&&orient<0)return -e.weight;return 0;
    }
    static int Winding(Query526 q,List<Edge> edges,bool rotated)
    {
        int value=0;var coordinate=rotated?q.x:q.y;
        foreach(var e in edges){long a=rotated?e.ax:e.ay,b=rotated?e.bx:e.by;var lo=(BigInteger)Math.Min(a,b)*q.w;var hi=(BigInteger)Math.Max(a,b)*q.w;if(lo<=coordinate&&coordinate<hi)value+=Contribution526(q,e,rotated);}
        WindingCandidates526+=edges.Count;return value;
    }
    static bool Overlap526(Edge a,Edge b)=>!(Math.Max(Math.Min(a.ax,a.bx),Math.Min(b.ax,b.bx))>Math.Min(Math.Max(a.ax,a.bx),Math.Max(b.ax,b.bx))||Math.Max(Math.Min(a.ay,a.by),Math.Min(b.ay,b.by))>Math.Min(Math.Max(a.ay,a.by),Math.Max(b.ay,b.by)));
    static void Pairs526(List<Edge> edges)
    {
        var grid=new Dictionary<(int,int),List<int>>();var boxes=new (int x,int y,int right,int bottom)[edges.Count];long entries=0;
        for(int i=0;i<edges.Count;i++)
        {
            var e=edges[i];double ax=e.a.X,ay=e.a.Y,bx=e.b.X,by=e.b.Y;var box=((int)Math.Floor(Math.Min(ax,bx)),(int)Math.Floor(Math.Min(ay,by)),(int)Math.Floor(Math.Max(ax,bx)),(int)Math.Floor(Math.Max(ay,by)));boxes[i]=box;
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
        var lo=new long[edges.Count];var hi=new long[edges.Count];
        for(int i=0;i<edges.Count;i++){var e=edges[i];long a=rotated?e.ax:e.ay,b=rotated?e.bx:e.by;lo[i]=Math.Min(a,b);hi[i]=Math.Max(a,b);}
        var begin=Enumerable.Range(0,edges.Count).OrderBy(i=>lo[i]).ThenBy(i=>i).ToArray();var end=Enumerable.Range(0,edges.Count).OrderBy(i=>hi[i]).ThenBy(i=>i).ToArray();var active=new SortedSet<int>();int first=0,last=0;
        foreach(var q in queries.Where(q=>q.rotated==rotated).OrderBy(q=>q.Coordinate))
        {
            long coordinate=rotated?q.query.floorX:q.query.floorY;while(first<begin.Length&&coordinate>=lo[begin[first]]){int i=begin[first++];if(lo[i]<hi[i])active.Add(i);}while(last<end.Length&&coordinate>=hi[end[last]])active.Remove(end[last++]);
            int value=0;foreach(int i in active)value+=Contribution526(q.query,edges[i],rotated);q.winding=value;WindingCandidates526+=active.Count;
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
        // Cancel original input edges on the original integer grid before creating fractions.
        var grid=new Dictionary<((long x,long y),(long x,long y)),int>();
        foreach(var line in segments){var a=((long)Math.Round(line.Item1.x*ArithmeticGrid),(long)Math.Round(line.Item1.y*ArithmeticGrid));var b=((long)Math.Round(line.Item2.x*ArithmeticGrid),(long)Math.Round(line.Item2.y*ArithmeticGrid));if(a==b)continue;bool forward=a.Item1<b.Item1||(a.Item1==b.Item1&&a.Item2<b.Item2);var key=forward?(a,b):(b,a);grid.TryGetValue(key,out int count);grid[key]=count+(forward?1:-1);}
        var counts=new Dictionary<(P,P),int>();foreach(var row in grid)if(row.Value!=0){var a=row.Key.Item1;var b=row.Key.Item2;counts.Add((new P((Rational)a.x,(Rational)a.y),new P((Rational)b.x,(Rational)b.y)),row.Value);}
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
        var edges=new List<Edge>();foreach(var row in counts)if(row.Value!=0)edges.Add(row.Value>0?new Edge{a=row.Key.Item1,b=row.Key.Item2,weight=row.Value}:new Edge{a=row.Key.Item2,b=row.Key.Item1,weight=-row.Value});WeightedEdges=edges.Count;foreach(var edge in edges)edge.Prepare526();
        if(origins579!=null)foreach(var edge in edges)edge.origins579=origins579[OriginKey579(edge.a,edge.b)];
        var nodes579=origins579==null?null:new Dictionary<P,List<Anchor579>>();
        PairCandidates526=WindingCandidates526=0;PairIndexUsed526=false;long pairStart=Stopwatch.GetTimestamp();
        if(UseSpatialIndex526)Pairs526(edges);else{PairCandidates526=(long)edges.Count*(edges.Count-1)/2;for(int i=0;i<edges.Count;i++)for(int j=i+1;j<edges.Count;j++)if(Overlap526(edges[i],edges[j]))Intersect(edges[i],edges[j]);}
        PairMs526=Elapsed526(pairStart);
        counts.Clear();foreach(var e in edges){e.split.Sort();Rational t=0;var a=e.a;for(int i=1;i<e.split.Count;i++)if(e.split[i]>t){var next=e.split[i];var b=At(e,next);Count(counts,a,b,e.weight);Register579(nodes579,a,e,t);Register579(nodes579,b,e,next);a=b;t=next;}}Fragments=counts.Count;
        long windingStart=Stopwatch.GetTimestamp();var queries=new List<Fragment526>();
        foreach(var row in counts){if(row.Value==0)continue;P a=row.Value>0?row.Key.Item1:row.Key.Item2,b=row.Value>0?row.Key.Item2:row.Key.Item1;queries.Add(new Fragment526(a,b,Math.Abs(row.Value)));}
        if(UseSpatialIndex526){Sweep526(edges,queries,false);Sweep526(edges,queries,true);}else foreach(var q in queries)q.winding=Winding(q.query,edges,q.rotated);
        WindingMs526=Elapsed526(windingStart);var outgoing=new Dictionary<P,HashSet<P>>();BoundaryEdges=0;
        foreach(var q in queries){P a=q.a,b=q.b;int w=q.weight;int sign=(q.rotated?b.x.CompareTo(a.x):b.y.CompareTo(a.y))>0?1:-1;int right=q.winding,minus=right+sign*w,left=sign>0?minus:right;right=sign>0?right:minus;
            if(left<0||right<0)throw new InvalidOperationException("524 negative union winding");if((left>0)==(right>0))continue;if(left<=0)(a,b)=(b,a);if(!outgoing.TryGetValue(a,out var targets)){targets=new HashSet<P>();outgoing.Add(a,targets);}if(targets.Add(b))BoundaryEdges++;}
        var loops=new List<Vector2[]>();int remaining=BoundaryEdges;
        while(outgoing.Count>0){P start=outgoing.Keys.Min(),at=start,prior=default;bool first=true;var ring=new List<Vector2>();var originRing579=anchored579==null?null:new List<Node579>();
            do{if(!outgoing.TryGetValue(at,out var targets)||targets.Count==0)throw new InvalidOperationException("524 open vector boundary");ring.Add(at.Vector);if(originRing579!=null)originRing579.Add(new Node579{point=at.Vector,anchors=nodes579[at]});P next;
                if(first)next=targets.Min();else{var dx=at.x-prior.x;var dy=at.y-prior.y;next=targets.OrderByDescending(q=>Math.Atan2(Cross(dx,dy,q.x-at.x,q.y-at.y).Value,(dx*(q.x-at.x)+dy*(q.y-at.y)).Value)).ThenBy(q=>q).First();}
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

