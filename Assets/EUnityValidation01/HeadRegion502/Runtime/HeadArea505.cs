using System;
using UnityEngine;
using UnityEngine.Rendering;
using System.Linq;
using System.Collections.Generic;
using System.Diagnostics;

// Default-OFF experiment input: continuous projected visible hair / cell area.
// Geometry is clipped analytically. Occlusion-alpha uncertainty stays bounded;
// HeadRegion502 certifies that both area bounds select the same whole region.
public static class HeadArea505
{
    public struct P { public double x,y; public P(double x,double y){this.x=x;this.y=y;} }
    public struct Plane { public double x,y,c; public double At(P p){return x*p.x+y*p.y+c;} }
    public sealed class Material { public int width,height,cull,mode; public double cutoff,min,max; public byte[] alpha; }
    public sealed class T { public int renderer,sm,id;public P[] p;public Plane z,u,v;public double x0,y0,x1,y1,z0,z1; }
    public sealed class Input { public T[] triangles;public float phase;public int ox,oy,x,y,w,h; }
    public sealed class Result { public float[] lower,upper;public int ambiguousFragments;public double milliseconds; }
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
    static double Length(List<List<P>> polygons,double y){var spans=new List<P>();foreach(var p in polygons){double lo=double.PositiveInfinity,hi=double.NegativeInfinity;for(int i=0;i<p.Count;i++){var a=p[i];var b=p[(i+1)%p.Count];if((a.y<=y&&y<b.y)||(b.y<=y&&y<a.y)){double x=a.x+(y-a.y)*(b.x-a.x)/(b.y-a.y);lo=Math.Min(lo,x);hi=Math.Max(hi,x);}}if(lo<hi)spans.Add(new P(lo,hi));}spans.Sort((a,b)=>a.x.CompareTo(b.x));double end=double.NegativeInfinity,length=0;foreach(var span in spans){length+=Math.Max(0,span.y-Math.Max(span.x,end));end=Math.Max(end,span.y);}return length;}
    // Candidate508 changes only Union/Length polygon candidates. DefaultOFF.
    public static bool UseActivePolygons508;
    public static double Union(List<List<P>> polygons){if(UseActivePolygons508)return Union508(polygons);if(polygons.Count==0)return 0;var levels=new List<double>();var edges=new List<P[]>();foreach(var p in polygons)for(int i=0;i<p.Count;i++){var a=p[i];var b=p[(i+1)%p.Count];levels.Add(a.y);if(Math.Abs(a.y-b.y)>1e-12)edges.Add(new[]{a,b});}for(int i=0;i<edges.Count;i++){var a=edges[i][0];var b=edges[i][1];double k=(b.x-a.x)/(b.y-a.y),c=a.x-k*a.y;for(int j=i+1;j<edges.Count;j++){var aa=edges[j][0];var bb=edges[j][1];double kk=(bb.x-aa.x)/(bb.y-aa.y),cc=aa.x-kk*aa.y;if(Math.Abs(k-kk)<1e-12)continue;double y=(cc-c)/(k-kk);if(y>Math.Max(Math.Min(a.y,b.y),Math.Min(aa.y,bb.y))+1e-11&&y<Math.Min(Math.Max(a.y,b.y),Math.Max(aa.y,bb.y))-1e-11)levels.Add(y);}}levels.Sort();double total=0;for(int i=0;i+1<levels.Count;i++){double dy=levels[i+1]-levels[i];if(dy>1e-12)total+=dy*Length(polygons,(levels[i]+levels[i+1])*.5);}return Math.Max(0,Math.Min(1,total));}
    public static Result Compute(Input input,Material[] materials){var watch=Stopwatch.StartNew();int w=input.w,h=input.h;var bins=new List<T>[w*h];foreach(var t in input.triangles){int x0=Math.Max(input.x,(int)Math.Floor(t.x0)),y0=Math.Max(input.y,(int)Math.Floor(t.y0)),x1=Math.Min(input.x+w-1,(int)Math.Floor(t.x1)),y1=Math.Min(input.y+h-1,(int)Math.Floor(t.y1));for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++){int at=(y-input.y)*w+x-input.x;if(bins[at]==null)bins[at]=new List<T>();bins[at].Add(t);}}var output=new Result{lower=new float[w*h],upper=new float[w*h]};for(int y=input.y;y<input.y+h;y++)for(int x=input.x;x<input.x+w;x++){int at=(y-input.y)*w+x-input.x;var bin=bins[at];if(bin==null)continue;var lower=new List<List<P>>();var upper=new List<List<P>>();foreach(var t in bin){if(t.renderer!=2)continue;var p=Cell(t,x,y);if(Area(p)<1e-12)continue;var lo=new List<List<P>>{p};var hi=new List<List<P>>{p};foreach(var o in bin){if(o.renderer==2||o.z0>=t.z1||o.x1<t.x0||o.x0>t.x1||o.y1<t.y0||o.y0>t.y1)continue;if(t.z.x==o.z.x&&t.z.y==o.z.y&&t.z.c==o.z.c)continue;var overlap=Overlap(p,o);overlap=Clip(overlap,new Plane{x=t.z.x-o.z.x,y=t.z.y-o.z.y,c=t.z.c-o.z.c});if(Area(overlap)<1e-12)continue;int coverage=Coverage(materials[o.sm],o,overlap);if(coverage==0)continue;lo=Remove(lo,overlap);if(coverage>0)hi=Remove(hi,overlap);else output.ambiguousFragments++;}lower.AddRange(lo);upper.AddRange(hi);}output.lower[at]=(float)Union(lower);output.upper[at]=(float)Union(upper);}watch.Stop();output.milliseconds=watch.Elapsed.TotalMilliseconds;return output;}


    // Only candidates for Length change. The original polygon order, edge
    // formula, events, midpoint integration and span sort/merge stay unchanged.
    static double Length508(List<List<P>> polygons,List<int> active,double y)
    {
        var spans=new List<P>();
        foreach(int index in active)
        {
            var p=polygons[index];double lo=double.PositiveInfinity,hi=double.NegativeInfinity;
            for(int i=0;i<p.Count;i++)
            {
                var a=p[i];var b=p[(i+1)%p.Count];
                if((a.y<=y&&y<b.y)||(b.y<=y&&y<a.y))
                {double x=a.x+(y-a.y)*(b.x-a.x)/(b.y-a.y);lo=Math.Min(lo,x);hi=Math.Max(hi,x);}
            }
            if(lo<hi)spans.Add(new P(lo,hi));
        }
        spans.Sort((a,b)=>a.x.CompareTo(b.x));
        double end=double.NegativeInfinity,length=0;
        foreach(var span in spans)
        {length+=Math.Max(0,span.y-Math.Max(span.x,end));end=Math.Max(end,span.y);}
        return length;
    }
    static double Union508(List<List<P>> polygons)
    {
        if(polygons.Count==0)return 0;
        var levels=new List<double>();var edges=new List<P[]>();
        int count=polygons.Count;
        var minY=new double[count];var maxY=new double[count];
        var starts=new int[count];var ends=new int[count];
        for(int index=0;index<count;index++)
        {
            var p=polygons[index];double lo=double.PositiveInfinity,hi=double.NegativeInfinity;
            for(int i=0;i<p.Count;i++)
            {
                var a=p[i];var b=p[(i+1)%p.Count];levels.Add(a.y);
                if(Math.Abs(a.y-b.y)>1e-12)edges.Add(new[]{a,b});
                lo=Math.Min(lo,a.y);hi=Math.Max(hi,a.y);
            }
            minY[index]=lo;maxY[index]=hi;starts[index]=ends[index]=index;
        }
        // Keep every original pair operation and every original event.
        for(int i=0;i<edges.Count;i++)
        {
            var a=edges[i][0];var b=edges[i][1];double k=(b.x-a.x)/(b.y-a.y),c=a.x-k*a.y;
            for(int j=i+1;j<edges.Count;j++)
            {
                var aa=edges[j][0];var bb=edges[j][1];double kk=(bb.x-aa.x)/(bb.y-aa.y),cc=aa.x-kk*aa.y;
                if(Math.Abs(k-kk)<1e-12)continue;
                double y=(cc-c)/(k-kk);
                if(y>Math.Max(Math.Min(a.y,b.y),Math.Min(aa.y,bb.y))+1e-11&&y<Math.Min(Math.Max(a.y,b.y),Math.Max(aa.y,bb.y))-1e-11)levels.Add(y);
            }
        }
        levels.Sort();
        Array.Sort(starts,(i,j)=>{int c=minY[i].CompareTo(minY[j]);return c!=0?c:i.CompareTo(j);});
        Array.Sort(ends,(i,j)=>{int c=maxY[i].CompareTo(maxY[j]);return c!=0?c:i.CompareTo(j);});
        var active=new List<int>(count);int startAt=0,endAt=0;double total=0;
        for(int i=0;i+1<levels.Count;i++)
        {
            double dy=levels[i+1]-levels[i];if(!(dy>1e-12))continue;
            double y=(levels[i]+levels[i+1])*.5;
            while(endAt<count&&maxY[ends[endAt]]<=y)
            {int at=active.BinarySearch(ends[endAt++]);if(at>=0)active.RemoveAt(at);}
            while(startAt<count&&minY[starts[startAt]]<=y)
            {
                int index=starts[startAt++];
                if(y<maxY[index]){int at=active.BinarySearch(index);active.Insert(~at,index);}
            }
            total+=dy*Length508(polygons,active,y);
        }
        return Math.Max(0,Math.Min(1,total));
    }

    static readonly Dictionary<Texture2D, byte[]> AlphaCache = new();
    static readonly Dictionary<Texture2D, uint> AlphaVersions = new();
    public static Result Last;
    static byte[] Alpha(Texture2D texture)
    {
        if (AlphaCache.TryGetValue(texture, out var cached) && AlphaVersions[texture] == texture.updateCount) return cached;
        var temp = RenderTexture.GetTemporary(texture.width, texture.height, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Linear);
        var before = RenderTexture.active;
        var readable = new Texture2D(texture.width, texture.height, TextureFormat.RGBA32, false, true);
        Color32[] pixels;
        try
        {
            Graphics.Blit(texture, temp); RenderTexture.active = temp;
            readable.ReadPixels(new Rect(0, 0, texture.width, texture.height), 0, 0, false);
            readable.Apply(false, false); pixels = readable.GetPixels32();
        }
        finally
        {
            RenderTexture.active = before; RenderTexture.ReleaseTemporary(temp);
            UnityEngine.Object.Destroy(readable);
        }
        var bytes = new byte[pixels.Length];
        for (int i = 0; i < bytes.Length; i++) bytes[i] = pixels[i].a;
        if (bytes.Length != texture.width * texture.height) throw new InvalidOperationException("505 alpha dimensions differ");
        AlphaCache[texture] = bytes; AlphaVersions[texture] = texture.updateCount; return bytes;
    }
    public static void Warm(Full319View335 f)
    {
        foreach (var m in f.motion.materials)
        {
            var t = m.mainTexture as Texture2D;
            if (!t) throw new InvalidOperationException("505 expected original Texture2D");
            Alpha(t);
        }
    }
    public static Result Build(Full319View335 f, RectInt bounds)
    {
        if (!f.motion.camera.orthographic || f.effectiveProjection[3, 3] != 1)
            throw new InvalidOperationException("505 area input currently requires orthographic projection");
        var all = new List<T>(); var materials = new List<Material>(); int materialIndex = 0;
        for (int renderer = 0; renderer < 3; renderer++)
        {
            var mf = f.motion.surface.outputs[renderer]; var mesh = mf.sharedMesh;
            var world = mesh.vertices.Select(mf.transform.TransformPoint).ToArray();
            var projected = world.Select(f.Project).ToArray(); var uv = mesh.uv;
            var depths = world.Select(p => -(double)f.motion.camera.worldToCameraMatrix.MultiplyPoint3x4(p).z).ToArray();
            for (int sm = 0; sm < mesh.subMeshCount; sm++, materialIndex++)
            {
                var m = f.motion.materials[materialIndex]; var texture = m.mainTexture as Texture2D;
                if (!texture || texture.mipmapCount != 1 || texture.filterMode != FilterMode.Bilinear ||
                    texture.wrapMode != TextureWrapMode.Repeat || m.GetVector("_MainTex_ST") != new Vector4(1, 1, 0, 0) ||
                    m.GetFloat("_UvAnimScrollXSpeed") != 0 || m.GetFloat("_UvAnimScrollYSpeed") != 0 ||
                    m.GetFloat("_UvAnimRotationSpeed") != 0 || m.color.a != 1)
                    throw new InvalidOperationException("505 unverified material alpha sampling: " + m.name);
                var a = Alpha(texture);
                var material = new Material { width = texture.width, height = texture.height,
                    cull = (int)m.GetFloat("_M_CullMode"), mode = (int)m.GetFloat("_AlphaMode"),
                    cutoff = m.GetFloat("_Cutoff"), min = a.Min() / 255.0, max = a.Max() / 255.0, alpha = a };
                if ((material.cull != 0 && material.cull != 2) || (material.mode != 1 && material.mode != 2))
                    throw new InvalidOperationException("505 unverified source render mode: " + m.name);
                if ((material.mode == 1 && (material.cutoff != .5 || !m.IsKeywordEnabled("_ALPHATEST_ON"))) ||
                    (material.mode == 2 && !m.IsKeywordEnabled("_ALPHABLEND_ON")))
                    throw new InvalidOperationException("505 unverified source alpha threshold: " + m.name);
                if (renderer == 2 && (material.min < material.cutoff || material.cull != 0))
                    throw new InvalidOperationException("505 hair source is no longer opaque/double-sided");
                materials.Add(material); var ix = mesh.GetIndices(sm);
                for (int j = 0; j < ix.Length; j += 3)
                {
                    var ids = new[] { ix[j], ix[j + 1], ix[j + 2] };
                    var p = ids.Select(i => new P(projected[i].x, projected[i].y)).ToArray();
                    double cross = Cross(Sub(p[1], p[0]), Sub(p[2], p[0]));
                    if (Math.Abs(cross) < 1e-10 || (material.cull == 2 && cross <= 0)) continue;
                    var z = ids.Select(i => depths[i]).ToArray();
                    all.Add(new T { renderer = renderer, sm = materialIndex, id = j / 3, p = p,
                        z = Fit(p, z), u = Fit(p, ids.Select(i => (double)uv[i].x).ToArray()),
                        v = Fit(p, ids.Select(i => (double)uv[i].y).ToArray()),
                        x0 = p.Min(q => q.x), x1 = p.Max(q => q.x), y0 = p.Min(q => q.y), y1 = p.Max(q => q.y),
                        z0 = z.Min(), z1 = z.Max() });
                }
            }
        }
        Last = Compute(new Input { triangles = all.ToArray(), x = bounds.x, y = bounds.y,
            w = bounds.width, h = bounds.height }, materials.ToArray());
        return Last;
    }
    public static void Release() { AlphaCache.Clear(); AlphaVersions.Clear(); Last = null; }
}
