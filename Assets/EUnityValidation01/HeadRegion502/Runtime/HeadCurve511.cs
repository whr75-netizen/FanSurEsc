using System;
using System.IO;
using System.Collections.Generic;
using System.Diagnostics;
using UnityEngine;

// Alternative form input, defaultOFF. Model-prepared closed polygonal controls;
// actual current mesh deformation supplies every anchor on every frame.
public static partial class HeadRegion502
{
    public static bool UseAutomaticCurve511;
    public static bool UseNegativeRegions563; // Default-OFF source-domain output contract trial.
    public static readonly List<NegativeRegion563.Feature> NegativeRegions563=new();
    public static readonly List<int[]> NegativeGroups563=new();
    public static double NegativeMs563;
    public static string Auto511Status="disabled";
    public static int Auto511Controls,Auto511SourcePoints,Auto511SourceRings,Auto511Repairs,Auto511CurveCrossings,Auto511CurveEvents;
    public static double Auto511PreparationSeconds,Auto511InitMs,Auto511CurveMs,Auto511AreaMs,Auto511BinMs,Auto511PacketMs;
    public static float[] Auto511Areas;
    public static RectInt Auto511Bounds;
    sealed class Control511 {public int sm,primitive,a,b,c;public double u,v,w;}
    static Control511[][] controls511;
    static Mesh source511,output511,registered511;
    static int[][] indices511;
    static readonly HashSet<(int,int,int)> registeredTriangles511=new();
    static readonly List<Triangle>[] bins511=new List<Triangle>[480*272];
    static readonly List<int> usedBins511=new();
    static readonly Triangle[] noTriangles511=Array.Empty<Triangle>();
    static ulong signature511;
    static bool triangleCache511;
    static void HashInt511(int value){unchecked{for(int i=0;i<4;i++){signature511^=(byte)(value>>(i*8));signature511*=1099511628211UL;}}}
    static void HashFloat511(float value)=>HashInt511(BitConverter.SingleToInt32Bits(value));
    static ulong Fingerprint511(Mesh mesh)
    {
        signature511=14695981039346656037UL;HashInt511(mesh.vertexCount);HashInt511(mesh.subMeshCount);
        foreach(var p in mesh.vertices){HashFloat511(p.x);HashFloat511(p.y);HashFloat511(p.z);}foreach(var p in mesh.uv){HashFloat511(p.x);HashFloat511(p.y);}
        for(int s=0;s<mesh.subMeshCount;s++){var a=mesh.GetIndices(s);HashInt511(a.Length);foreach(int v in a)HashInt511(v);}
        foreach(var m in mesh.bindposes)for(int i=0;i<16;i++)HashFloat511(m[i]);return signature511;
    }
    static (int,int,int) Key511(int a,int b,int c){if(a>b)(a,b)=(b,a);if(b>c)(b,c)=(c,b);if(a>b)(a,b)=(b,a);return(a,b,c);}
    static int[][] Indices511(Full319View335 f,Mesh output)
    {
        var source=f.motion.surface.source[2].sharedMesh; // Declared Hair adapter.
        if(source511==source&&output511==output&&controls511!=null)return indices511;
        long start=Stopwatch.GetTimestamp();var asset=Resources.Load<TextAsset>("HeadCurve511");
        if(!asset)throw new InvalidOperationException("511 model curve input not compiled");
        using var r=new BinaryReader(new MemoryStream(asset.bytes));
        if(r.ReadInt32()!=511||r.ReadInt32()!=2)throw new InvalidOperationException("511 curve format differs");
        int nv=r.ReadInt32(),ns=r.ReadInt32();ulong expected=r.ReadUInt64();
        if(nv!=source.vertexCount||nv!=output.vertexCount||ns!=source.subMeshCount||ns!=output.subMeshCount||expected!=Fingerprint511(source))throw new InvalidOperationException("511 model topology/UV/bind signature requires automatic recompilation");
        if(ns>4)throw new InvalidOperationException("511 current renderer adapter supports at most four Hair semantic material roles");
        int count=r.ReadInt32();Auto511SourceRings=r.ReadInt32();Auto511SourcePoints=r.ReadInt32();Auto511Repairs=r.ReadInt32();Auto511PreparationSeconds=r.ReadDouble();
        indices511=new int[ns][];for(int s=0;s<ns;s++)indices511[s]=output.GetIndices(s);
        controls511=new Control511[count][];Auto511Controls=0;
        for(int n=0;n<count;n++)
        {
            int length=r.ReadInt32();if(length<3)throw new InvalidOperationException("511 open/empty control ring");controls511[n]=new Control511[length];
            for(int j=0;j<length;j++)
            {
                var p=new Control511{sm=r.ReadInt32(),primitive=r.ReadInt32(),a=r.ReadInt32(),b=r.ReadInt32(),c=r.ReadInt32(),u=r.ReadDouble(),v=r.ReadDouble(),w=r.ReadDouble()};
                if(p.sm<0||p.sm>=ns||p.primitive<0||p.primitive*3+2>=indices511[p.sm].Length||indices511[p.sm][p.primitive*3]!=p.a||indices511[p.sm][p.primitive*3+1]!=p.b||indices511[p.sm][p.primitive*3+2]!=p.c||Math.Abs(p.u+p.v+p.w-1)>1e-12||Math.Min(p.u,Math.Min(p.v,p.w))<0)throw new InvalidOperationException("511 source anchor invalid");
                controls511[n][j]=p;Auto511Controls++;
            }
        }
        if(r.BaseStream.Position!=r.BaseStream.Length)throw new InvalidOperationException("511 curve input trailing data");
        source511=source;output511=output;registered511=null;triangleCache511=false;triangles.Clear();Auto511Status="loaded automatic polygonal curves";
        Auto511InitMs=1000.0*(Stopwatch.GetTimestamp()-start)/Stopwatch.Frequency;return indices511;
    }
    static float[] Areas511(Full319View335 f,out RectInt bounds)
    {
        long start=Stopwatch.GetTimestamp();float x0=480,y0=272,x1=0,y1=0;
        foreach(var ring in controls511)
        {
            var p=new Vector2[ring.Length];
            for(int i=0;i<p.Length;i++)
            {
                var a=ring[i];var u=world[a.a];var v=world[a.b];var w=world[a.c];
                var position=new Vector3((float)(u.x*a.u+v.x*a.v+w.x*a.w),(float)(u.y*a.u+v.y*a.v+w.y*a.w),(float)(u.z*a.u+v.z*a.v+w.z*a.w));
                p[i]=f.Project(position);if(float.IsNaN(p[i].x)||float.IsNaN(p[i].y)||float.IsInfinity(p[i].x)||float.IsInfinity(p[i].y))throw new InvalidOperationException("511 nonfinite projected curve");
                x0=Mathf.Min(x0,p[i].x);x1=Mathf.Max(x1,p[i].x);y0=Mathf.Min(y0,p[i].y);y1=Mathf.Max(y1,p[i].y);
            }
            SourceLoops.Add(p);Curves.Add(p);
        }
        bounds=new RectInt(Mathf.Clamp(Mathf.FloorToInt(x0)-2,0,479),Mathf.Clamp(Mathf.FloorToInt(y0)-2,0,271),0,0);bounds.xMax=Mathf.Clamp(Mathf.CeilToInt(x1)+2,bounds.x+1,480);bounds.yMax=Mathf.Clamp(Mathf.CeilToInt(y1)+2,bounds.y+1,272);
        Auto511CurveMs=1000.0*(Stopwatch.GetTimestamp()-start)/Stopwatch.Frequency;start=Stopwatch.GetTimestamp();
        var graph=new List<CurveArea511.P[]>();foreach(var ring in Curves){var p=new CurveArea511.P[ring.Length];for(int i=0;i<p.Length;i++)p[i]=new CurveArea511.P(ring[i].x,ring[i].y);graph.Add(p);}
        NegativeRegions563.Clear();NegativeGroups563.Clear();NegativeMs563=0;
        var negative=UseNegativeRegions563?new NegativeRegion563(bounds.x,bounds.y,bounds.width,bounds.height):null;
        var result=CurveArea511.Compute(graph,bounds.x,bounds.y,bounds.width,bounds.height,negative);Auto511CurveCrossings=CurveArea511.LastCrossings;Auto511CurveEvents=CurveArea511.LastEvents;
        if(negative!=null)
        {
            long negativeStart=Stopwatch.GetTimestamp();var swapped=new List<CurveArea511.P[]>();foreach(var ring in graph){var p=new CurveArea511.P[ring.Length];for(int i=0;i<p.Length;i++){var a=ring[ring.Length-1-i];p[i]=new CurveArea511.P(a.y,a.x);}swapped.Add(p);}
            var other=new NegativeRegion563(bounds.y,bounds.x,bounds.height,bounds.width,true);CurveArea511.Compute(swapped,bounds.y,bounds.x,bounds.height,bounds.width,other);
            var first=negative.Features();var second=other.Features();NegativeRegions563.AddRange(first);NegativeRegions563.AddRange(second);NegativeGroups563.AddRange(NegativeRegion563.Groups(first,second,bounds.width,bounds.height));NegativeMs563=1000.0*(Stopwatch.GetTimestamp()-negativeStart)/Stopwatch.Frequency;
        }
        Auto511AreaMs=1000.0*(Stopwatch.GetTimestamp()-start)/Stopwatch.Frequency;Auto511Areas=result;Auto511Bounds=bounds;Auto511Status="ready polygonal curve graph input";return result;
    }
    static void Triangles511(int[][] indices,RectInt bounds,Full319View335 f)
    {
        long start=Stopwatch.GetTimestamp();
        if(!triangleCache511){triangles.Clear();for(int sm=0;sm<indices.Length;sm++)for(int k=0;k<indices[sm].Length;k+=3)triangles.Add(new Triangle{sm=sm,primitive=k/3,ia=indices[sm][k],ib=indices[sm][k+1],ic=indices[sm][k+2]});triangleCache511=true;}
        foreach(int at in usedBins511)bins511[at].Clear();usedBins511.Clear();
        foreach(var t in triangles)
        {
            t.a=projected[t.ia];t.b=projected[t.ib];t.c=projected[t.ic];
            t.minX=Mathf.Min(t.a.x,Mathf.Min(t.b.x,t.c.x));t.maxX=Mathf.Max(t.a.x,Mathf.Max(t.b.x,t.c.x));t.minY=Mathf.Min(t.a.y,Mathf.Min(t.b.y,t.c.y));t.maxY=Mathf.Max(t.a.y,Mathf.Max(t.b.y,t.c.y));
            if(Mathf.Abs(Cross(t.b-t.a,t.c-t.a))<1e-10f)continue;
            int x0=Mathf.Max(bounds.x,Mathf.CeilToInt(t.minX-1.1f-.5f)),x1=Mathf.Min(bounds.xMax-1,Mathf.FloorToInt(t.maxX+1.1f-.5f));
            int y0=Mathf.Max(bounds.y,Mathf.CeilToInt(t.minY-1.1f-.5f)),y1=Mathf.Min(bounds.yMax-1,Mathf.FloorToInt(t.maxY+1.1f-.5f));
            for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++){int at=y*480+x;if(bins511[at]==null)bins511[at]=new List<Triangle>();if(bins511[at].Count==0)usedBins511.Add(at);bins511[at].Add(t);}
        }
        if(registered511!=f.registeredHair)
        {
            registeredTriangles511.Clear();registered511=f.registeredHair;
            if(registered511){var ids=registered511.GetIndices(0);for(int i=0;i<ids.Length;i+=3)registeredTriangles511.Add(Key511(ids[i],ids[i+1],ids[i+2]));}
        }
        Occluders511(f,bounds);
        Auto511BinMs=1000.0*(Stopwatch.GetTimestamp()-start)/Stopwatch.Frequency;
    }
    static IEnumerable<Triangle> Candidates511(int x,int y)=>bins511[y*480+x]as IEnumerable<Triangle>??noTriangles511;
    static int Part511(Packet p,int[][] indices){var a=indices[p.submesh];int i=p.primitive*3;return registeredTriangles511.Contains(Key511(a[i],a[i+1],a[i+2]))?1:2;}
    static void Release511()
    {
        UseAutomaticCurve511=UseNegativeRegions563=false;NegativeRegions563.Clear();NegativeGroups563.Clear();controls511=null;source511=output511=registered511=null;indices511=null;triangleCache511=false;
        foreach(int at in usedBins511)bins511[at]?.Clear();usedBins511.Clear();registeredTriangles511.Clear();Auto511Areas=null;Auto511Status="disabled";ReleaseVisibility511();
    }
}
