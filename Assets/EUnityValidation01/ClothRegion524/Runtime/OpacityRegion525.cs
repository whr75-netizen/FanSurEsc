using System;
using System.Collections.Generic;
using System.Diagnostics;
using UnityEngine;

// Material-domain boundary input, not a logical-pixel opacity test.
// Source texel alpha is piecewise linear on a fixed diagonal. Its cutoff contour
// is intersected with each original UV triangle once and attached barycentrically.
public sealed class OpacityRegion525
{
    struct D
    {
        public double x,y;
        public D(double x,double y){this.x=x;this.y=y;}
        public static D operator +(D a,D b)=>new D(a.x+b.x,a.y+b.y);
        public static D operator -(D a,D b)=>new D(a.x-b.x,a.y-b.y);
        public static D operator *(D a,double t)=>new D(a.x*t,a.y*t);
    }
    struct Line { public D a,b; public Line(D a,D b){this.a=a;this.b=b;} }
    public struct Anchor {public int a,b,c;public Vector3 weights;public Vector3 Local(Vector3[] p)=>p[a]*weights.x+p[b]*weights.y+p[c]*weights.z;}
    public struct Boundary {public int primitive,a,b;public bool opacity;}
    public readonly List<Anchor> Anchors=new();
    public readonly List<Boundary> Segments=new();
    public readonly List<int>[] TriangleSegments;
    public readonly int[] Indices;
    public readonly Texture2D Texture;
    public readonly Vector4 ST;
    public readonly float Cutoff,Factor;
    public readonly int TexelContourSegments;
    public readonly double PreprocessMs;
    readonly byte[] alpha;
    readonly int width,height;
    readonly Dictionary<(int,int),List<int>> bins=new();
    readonly List<Line> contour=new();
    readonly Dictionary<(int,int,long),int> edgeAnchors=new();
    readonly Dictionary<(int,long,long),int> innerAnchors=new();
    readonly int[] canonical;
    readonly Vector2[] uv;
    const int Bin=16;
    static double Cross(D a,D b)=>a.x*b.y-a.y*b.x;
    static double Cross(D a,D b,D c)=>Cross(b-a,c-a);
    public OpacityRegion525(Mesh original,int submesh,Material material)
    {
        long start=Stopwatch.GetTimestamp();
        Texture=material.mainTexture as Texture2D;
        if(!Texture||Texture.mipmapCount!=1||Texture.filterMode!=FilterMode.Bilinear)throw new InvalidOperationException("525 needs a single-mip bilinear source-alpha contract");
        if(material.GetFloat("_UvAnimScrollXSpeed")!=0||material.GetFloat("_UvAnimScrollYSpeed")!=0||material.GetFloat("_UvAnimRotationSpeed")!=0)throw new InvalidOperationException("525 animated source UV is not yet represented");
        ST=material.GetVector("_MainTex_ST");Factor=material.color.a;
        int mode=(int)material.GetFloat("_AlphaMode");
        if(mode!=1)throw new InvalidOperationException("525 clothing adapter requires declared MASK material");
        Cutoff=material.GetFloat("_Cutoff");
        if(Factor<=0)throw new InvalidOperationException("525 zero material alpha");
        alpha=HeadArea505.SourceAlphaBytes525(Texture);width=Texture.width;height=Texture.height;
        uv=original.uv;Indices=original.GetIndices(submesh);TriangleSegments=new List<int>[Indices.Length/3];
        canonical=new int[original.vertexCount];var verts=original.vertices;var weights=original.boneWeights;
        if(weights.Length!=verts.Length)throw new InvalidOperationException("525 anchor weld needs original skin weights");
        var weld=new Dictionary<(Vector3,BoneWeight),int>();
        for(int i=0;i<verts.Length;i++){var key=(verts[i],weights[i]);if(!weld.TryGetValue(key,out int v))weld.Add(key,v=i);canonical[i]=v;}
        // The imported UV transform is part of the domain, including seam wrap.
        // A repeated domain spanning outside [0,1] needs explicit tiled contours.
        foreach(int i in Indices){var q=Tex(uv[i]);if(q.x<0||q.x>1||q.y<0||q.y>1)throw new InvalidOperationException("525 transformed clothing UV outside unit domain needs tiled contour support");}
        for(int y=-1;y<height;y++)for(int x=-1;x<width;x++)
        {
            double a=Node(x,y),b=Node(x+1,y),c=Node(x+1,y+1),d=Node(x,y+1),cut=Cutoff/Factor;
            if(Math.Min(Math.Min(a,b),Math.Min(c,d))>=cut||Math.Max(Math.Max(a,b),Math.Max(c,d))<cut)continue;
            D p=new D((x+.5)/width,(y+.5)/height),q=new D((x+1.5)/width,(y+.5)/height),r=new D((x+1.5)/width,(y+1.5)/height),s=new D((x+.5)/width,(y+1.5)/height);
            AddContour(p,q,r,a,b,c,cut);AddContour(p,r,s,a,c,d,cut);
        }
        TexelContourSegments=contour.Count;
        for(int pr=0;pr<Indices.Length/3;pr++)BuildTriangle(pr);BuildPlans527();
        PreprocessMs=1000.0*(Stopwatch.GetTimestamp()-start)/Stopwatch.Frequency;
    }
    D Tex(Vector2 v)=>new D(v.x*ST.x+ST.z,v.y*ST.y+ST.w);
    double Node(int x,int y)
    {
        if(Texture.wrapMode==TextureWrapMode.Repeat){x=(x%width+width)%width;y=(y%height+height)%height;}
        else if(Texture.wrapMode==TextureWrapMode.Clamp){x=Math.Max(0,Math.Min(width-1,x));y=Math.Max(0,Math.Min(height-1,y));}
        else throw new InvalidOperationException("525 unsupported alpha wrap mode");
        return alpha[y*width+x]/255.0;
    }
    double Field(D uv)
    {
        double x=uv.x*width-.5,y=uv.y*height-.5;int ix=(int)Math.Floor(x),iy=(int)Math.Floor(y);double u=x-ix,v=y-iy;
        double a=Node(ix,iy),c=Node(ix+1,iy+1);
        return u>=v?a*(1-u)+Node(ix+1,iy)*(u-v)+c*v:a*(1-v)+c*u+Node(ix,iy+1)*(v-u);
    }
    public bool Opaque(Vector2 sourceUV)=>Bilinear(sourceUV)*Factor>=Cutoff;
    public float Bilinear(Vector2 sourceUV)
    {
        var q=Tex(sourceUV);double x=q.x*width-.5,y=q.y*height-.5;int ix=(int)Math.Floor(x),iy=(int)Math.Floor(y);double u=x-ix,v=y-iy;
        return (float)((Node(ix,iy)*(1-u)+Node(ix+1,iy)*u)*(1-v)+(Node(ix,iy+1)*(1-u)+Node(ix+1,iy+1)*u)*v);
    }
    void AddContour(D a,D b,D c,double av,double bv,double cv,double cut)
    {
        var points=new List<D>(2);var p=new[]{a,b,c};var values=new[]{av,bv,cv};D inside=default;
        for(int i=0;i<3;i++){if(values[i]>=cut)inside=p[i];int j=(i+1)%3;if((values[i]>=cut)!=(values[j]>=cut))points.Add(p[i]+(p[j]-p[i])*((cut-values[i])/(values[j]-values[i])));}
        if(points.Count!=2)return;a=points[0];b=points[1];if(Cross(a,b,inside)<0)(a,b)=(b,a);
        int index=contour.Count;contour.Add(new Line(a,b));
        int x0=(int)Math.Floor(Math.Min(a.x,b.x)*width/Bin),x1=(int)Math.Floor(Math.Max(a.x,b.x)*width/Bin),y0=(int)Math.Floor(Math.Min(a.y,b.y)*height/Bin),y1=(int)Math.Floor(Math.Max(a.y,b.y)*height/Bin);
        for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++){if(!bins.TryGetValue((x,y),out var list))bins.Add((x,y),list=new List<int>());list.Add(index);}
    }
    D Bary(D p,D[] tri)
    {double den=Cross(tri[0],tri[1],tri[2]);return new D(Cross(p-tri[0],tri[2]-tri[0])/den,Cross(tri[1]-tri[0],p-tri[0])/den);}
    int AnchorAt(int pr,D p,D[] tri)
    {
        D b=Bary(p,tri);double[] w={1-b.x-b.y,b.x,b.y};int[] ids={Indices[pr*3],Indices[pr*3+1],Indices[pr*3+2]};
        for(int i=0;i<3;i++)if(Math.Abs(w[i]-1)<1e-8){var key=(canonical[ids[i]],canonical[ids[i]],0L);if(edgeAnchors.TryGetValue(key,out int old))return old;int at=Anchors.Count;Anchors.Add(new Anchor{a=canonical[ids[i]],weights=new Vector3(1,0,0)});edgeAnchors.Add(key,at);return at;}
        for(int i=0;i<3;i++)if(Math.Abs(w[i])<1e-8)
        {
            int j=(i+1)%3,k=(i+2)%3,a=canonical[ids[j]],c=canonical[ids[k]];double t=w[k]/(w[j]+w[k]);if(a>c){(a,c)=(c,a);t=1-t;}
            var key=(a,c,(long)Math.Round(t*1e8));if(edgeAnchors.TryGetValue(key,out int old))return old;int at=Anchors.Count;Anchors.Add(new Anchor{a=a,b=c,weights=new Vector3((float)(1-t),(float)t,0)});edgeAnchors.Add(key,at);return at;
        }
        var inner=(pr,(long)Math.Round(p.x*1e10),(long)Math.Round(p.y*1e10));if(innerAnchors.TryGetValue(inner,out int prior))return prior;int index=Anchors.Count;Anchors.Add(new Anchor{a=ids[0],b=ids[1],c=ids[2],weights=new Vector3((float)w[0],(float)w[1],(float)w[2])});innerAnchors.Add(inner,index);return index;
    }
    void Add(int pr,D a,D b,D[] tri,bool opacity=false)
    {
        if(Math.Abs(a.x-b.x)+Math.Abs(a.y-b.y)<1e-13)return;
        int index=Segments.Count;Segments.Add(new Boundary{primitive=pr,a=AnchorAt(pr,a,tri),b=AnchorAt(pr,b,tri),opacity=opacity});TriangleSegments[pr].Add(index);
    }
    void BuildTriangle(int pr)
    {
        TriangleSegments[pr]=new List<int>();var tri=new[]{Tex(uv[Indices[pr*3]]),Tex(uv[Indices[pr*3+1]]),Tex(uv[Indices[pr*3+2]])};double det=Cross(tri[0],tri[1],tri[2]);
        if(Math.Abs(det)<1e-16)throw new InvalidOperationException("525 degenerate UV triangle needs explicit constant/linear-alpha domain");
        var split=new[]{new List<double>{0,1},new List<double>{0,1},new List<double>{0,1}};
        var candidates=new HashSet<int>();double minX=Math.Min(tri[0].x,Math.Min(tri[1].x,tri[2].x)),maxX=Math.Max(tri[0].x,Math.Max(tri[1].x,tri[2].x)),minY=Math.Min(tri[0].y,Math.Min(tri[1].y,tri[2].y)),maxY=Math.Max(tri[0].y,Math.Max(tri[1].y,tri[2].y));
        for(int y=(int)Math.Floor(minY*height/Bin);y<=(int)Math.Floor(maxY*height/Bin);y++)for(int x=(int)Math.Floor(minX*width/Bin);x<=(int)Math.Floor(maxX*width/Bin);x++)if(bins.TryGetValue((x,y),out var list))foreach(int i in list)candidates.Add(i);
        foreach(int i in candidates)
        {
            var line=contour[i];double lo=0,hi=1;bool valid=true;
            for(int e=0;e<3;e++){D a=tri[e],b=tri[(e+1)%3];double da=Cross(a,b,line.a)*Math.Sign(det),db=Cross(a,b,line.b)*Math.Sign(det);if(da<0&&db<0){valid=false;break;}if((da<0)!=(db<0)){double t=da/(da-db);if(da<0)lo=Math.Max(lo,t);else hi=Math.Min(hi,t);}}
            if(!valid||hi-lo<1e-11)continue;D pa=line.a+(line.b-line.a)*lo,pb=line.a+(line.b-line.a)*hi;
            Add(pr,pa,pb,tri,true);
            foreach(D p in new[]{pa,pb})for(int e=0;e<3;e++){D a=tri[e],d=tri[(e+1)%3]-a;double den=d.x*d.x+d.y*d.y,t=((p.x-a.x)*d.x+(p.y-a.y)*d.y)/den;if(t>=-1e-9&&t<=1+1e-9&&Math.Abs(Cross(d,p-a))<1e-10*Math.Sqrt(den))split[e].Add(Math.Max(0,Math.Min(1,t)));}
        }
        for(int e=0;e<3;e++)
        {
            var list=split[e];list.Sort();D a=tri[e],d=tri[(e+1)%3]-a;
            for(int j=0;j+1<list.Count;j++){double lo=list[j],hi=list[j+1];if(hi-lo<1e-10||Field(a+d*((lo+hi)*.5))*Factor<Cutoff)continue;D p=a+d*lo,q=a+d*hi;if(det<0)(p,q)=(q,p);Add(pr,p,q,tri);}
        }
    }
    public List<(Vector2,Vector2)> Project(Vector2[] original,bool fitOpacity=false)
    {
        var p=new Vector2[Anchors.Count];for(int i=0;i<p.Length;i++){var a=Anchors[i];p[i]=original[a.a]*a.weights.x+original[a.b]*a.weights.y+original[a.c]*a.weights.z;}
        var orientation=new int[Indices.Length/3];
        for(int pr=0;pr<orientation.Length;pr++){int at=pr*3;var a=original[Indices[at]];var b=original[Indices[at+1]];var c=original[Indices[at+2]];double det=(double)(b.x-a.x)*(c.y-a.y)-(double)(b.y-a.y)*(c.x-a.x),uvDet=Cross(Tex(uv[Indices[at]]),Tex(uv[Indices[at+1]]),Tex(uv[Indices[at+2]]));orientation[pr]=Math.Abs(det)<1e-10?0:Math.Sign(det*uvDet);}
        InputSegments527=OpacitySegments527=FitOpacitySegments527=TopologyFallbacks527=0;UsedCurveFit527=false;CurveBuildMs527=0;TopologyFallbackDetails527.Clear();
        if(fitOpacity)return CurvedProjection527(p,orientation);
        var result=new List<(Vector2,Vector2)>(Segments.Count);
        foreach(var s in Segments){int sign=orientation[s.primitive];if(sign==0)continue;result.Add(sign>0?(p[s.a],p[s.b]):(p[s.b],p[s.a]));}InputSegments527=result.Count;
        return result;
    }
    sealed class Chain527
    {
        public int[] nodes;public bool[] keep;public readonly List<int> fitted=new();
        public Chain527(int[] nodes){this.nodes=nodes;keep=new bool[nodes.Length];}
    }
    sealed class Plan527
    {
        public bool valid;public Boundary[] fixedEdges;public Chain527[] chains;public int[][] loops;
        public readonly Dictionary<int,int> membership=new();public readonly List<(int,int)> candidate=new();
    }
    Plan527[] plans527;
    public int InputSegments527,OpacitySegments527,FitOpacitySegments527,TopologyFallbacks527;
    public readonly List<string> TopologyFallbackDetails527=new();
    public bool UsedCurveFit527;
    public double CurveBuildMs527;
    static bool Trace527(List<(int,int)> edges,bool closedOnly,out List<int[]> paths)
    {
        paths=new List<int[]>();var next=new Dictionary<int,int>();var previous=new Dictionary<int,int>();
        foreach(var e in edges){if(e.Item1==e.Item2)continue;if(next.ContainsKey(e.Item1)||previous.ContainsKey(e.Item2))return false;next.Add(e.Item1,e.Item2);previous.Add(e.Item2,e.Item1);}
        var starts=new List<int>();foreach(int a in next.Keys)if(!previous.ContainsKey(a))starts.Add(a);starts.Sort();if(closedOnly&&starts.Count!=0)return false;
        var remaining=new HashSet<int>(next.Keys);
        while(remaining.Count!=0)
        {
            int start;if(starts.Count!=0){start=starts[0];starts.RemoveAt(0);}else{start=int.MaxValue;foreach(int a in remaining)if(a<start)start=a;}
            var path=new List<int>{start};int at=start;
            while(next.TryGetValue(at,out int b)&&remaining.Remove(at)){path.Add(b);at=b;if(at==start)break;}
            if(path.Count<2||closedOnly&&at!=start)return false;paths.Add(path.ToArray());
        }
        return true;
    }
    void BuildPlans527()
    {
        plans527=new Plan527[TriangleSegments.Length];
        for(int pr=0;pr<plans527.Length;pr++)
        {
            var cut=new List<(int,int)>();var all=new List<(int,int)>();var fixedEdges=new List<Boundary>();
            foreach(int i in TriangleSegments[pr]){var s=Segments[i];all.Add((s.a,s.b));if(s.opacity)cut.Add((s.a,s.b));else fixedEdges.Add(s);}
            if(cut.Count==0)continue;var plan=plans527[pr]=new Plan527{fixedEdges=fixedEdges.ToArray()};
            if(!Trace527(cut,false,out var paths)||!Trace527(all,true,out var loops))continue;
            plan.chains=paths.ConvertAll(nodes=>new Chain527(nodes)).ToArray();plan.loops=loops.ToArray();
            for(int k=0;k<loops.Count;k++)foreach(int a in loops[k])plan.membership[a]=k;plan.valid=true;
        }
    }
    static List<int> FitChain527(Chain527 chain,Vector2[] p,float error)
    {
        Array.Clear(chain.keep,0,chain.keep.Length);chain.fitted.Clear();int n=chain.nodes.Length-1;chain.keep[0]=chain.keep[n]=true;
        void Run(int a,int b)
        {
            if(b<=a+1)return;var first=p[chain.nodes[a]];var d=p[chain.nodes[b]]-first;float den=d.sqrMagnitude,best=error*error;int at=-1;
            for(int j=a+1;j<b;j++){var v=p[chain.nodes[j]]-first;float t=den>0?Mathf.Clamp01(Vector2.Dot(v,d)/den):0,e=(v-t*d).sqrMagnitude;if(e>best){best=e;at=j;}}
            if(at<0)return;chain.keep[at]=true;Run(a,at);Run(at,b);
        }
        bool closed=chain.nodes[0]==chain.nodes[n];
        if(closed){int split=0;float far=0;for(int i=1;i<n;i++){float d=(p[chain.nodes[i]]-p[chain.nodes[0]]).sqrMagnitude;if(d>far){far=d;split=i;}}chain.keep[split]=true;Run(0,split);Run(split,n);}else Run(0,n);
        for(int i=0;i<=n;i++)if(chain.keep[i])chain.fitted.Add(chain.nodes[i]);
        if(closed&&chain.fitted.Count<4){chain.fitted.Clear();chain.fitted.AddRange(chain.nodes);}return chain.fitted;
    }
    static double Area527(int[] ring,Vector2[] p)
    {double a=0;for(int i=0;i+1<ring.Length;i++){var u=p[ring[i]];var v=p[ring[i+1]];a+=(double)u.x*v.y-(double)u.y*v.x;}return a*.5;}
    static bool SameTopology527(Plan527 plan,Vector2[] p,out string reason)
    {
        reason="";if(!Trace527(plan.candidate,true,out var loops)||loops.Count!=plan.loops.Length){reason="closed incidence or component count";return false;}
        var matched=new bool[plan.loops.Length];
        foreach(var loop in loops)
        {
            if(loop.Length<4||!plan.membership.TryGetValue(loop[0],out int source)||matched[source]){reason="loop incidence";return false;}
            foreach(int a in loop)if(!plan.membership.TryGetValue(a,out int group)||group!=source){reason="component merge";return false;}
            double before=Area527(plan.loops[source],p),after=Area527(loop,p);if(before*after<=0){reason="loop area sign";return false;}matched[source]=true;
        }
        var edges=plan.candidate;
        for(int i=0;i<edges.Count;i++)for(int j=i+1;j<edges.Count;j++)
        {
            var a=edges[i];var b=edges[j];if(a.Item1==b.Item1||a.Item1==b.Item2||a.Item2==b.Item1||a.Item2==b.Item2)continue;
            Vector2 av=p[a.Item1],bv=p[a.Item2],cv=p[b.Item1],dv=p[b.Item2];double rx=(double)bv.x-av.x,ry=(double)bv.y-av.y,sx=(double)dv.x-cv.x,sy=(double)dv.y-cv.y,qx=(double)cv.x-av.x,qy=(double)cv.y-av.y,den=rx*sy-ry*sx;
            if(Math.Abs(den)>1e-14){double t=(qx*sy-qy*sx)/den,u=(qx*ry-qy*rx)/den;if(t>0&&t<1&&u>0&&u<1){reason="new crossing";return false;}}
            else if(Math.Abs(qx*ry-qy*rx)<1e-12){bool x=Math.Abs(rx)>=Math.Abs(ry);double a0=x?av.x:av.y,a1=x?bv.x:bv.y,b0=x?cv.x:cv.y,b1=x?dv.x:dv.y;if(Math.Min(Math.Max(a0,a1),Math.Max(b0,b1))-Math.Max(Math.Min(a0,a1),Math.Min(b0,b1))>1e-8){reason="collinear overlap";return false;}}
        }
        return true;
    }
    List<(Vector2,Vector2)> CurvedProjection527(Vector2[] p,int[] orientation)
    {
        long start=Stopwatch.GetTimestamp();var result=new List<(Vector2,Vector2)>(Segments.Count);
        void Emit(int a,int b,int sign){if(sign>0)result.Add((p[a],p[b]));else result.Add((p[b],p[a]));}
        for(int pr=0;pr<TriangleSegments.Length;pr++)
        {
            int sign=orientation[pr];if(sign==0)continue;var plan=plans527[pr];bool fitted=false;
            if(plan!=null&&plan.valid)
            {
                plan.candidate.Clear();foreach(var s in plan.fixedEdges)plan.candidate.Add((s.a,s.b));int raw=0,after=0;
                foreach(var chain in plan.chains){var chosen=FitChain527(chain,p,HeadRegion502.CurveError*.5f);raw+=chain.nodes.Length-1;after+=chosen.Count-1;for(int i=0;i+1<chosen.Count;i++)plan.candidate.Add((chosen[i],chosen[i+1]));}
                OpacitySegments527+=raw;
                string reason="unchanged";if(after<raw&&SameTopology527(plan,p,out reason)){FitOpacitySegments527+=after;fitted=UsedCurveFit527=true;foreach(var e in plan.candidate)Emit(e.Item1,e.Item2,sign);}
                else{FitOpacitySegments527+=raw;if(after<raw){TopologyFallbacks527++;TopologyFallbackDetails527.Add(pr+":"+reason);}}
            }
            else if(plan!=null){TopologyFallbacks527++;TopologyFallbackDetails527.Add(pr+":source incidence");}
            if(!fitted)foreach(int i in TriangleSegments[pr]){var s=Segments[i];Emit(s.a,s.b,sign);}
        }
        InputSegments527=result.Count;CurveBuildMs527=1000.0*(Stopwatch.GetTimestamp()-start)/Stopwatch.Frequency;return result;
    }

}
