using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

// Removes only a raster extremum unsupported by a feature-preserving source chord.
// Does not dilate coverage, blend colours, or use previous-frame visibility.
public static class SourceSilhouetteContour
{
    public const int Width = 480, Height = 272;
    const double SourceTolerance = .5, BoundaryTolerance = 1;
    struct Edge { public double lo, hi, slope, offset; }
    struct Piece { public double lo, hi, slope, offset; }
    struct Pair { public int a, b, count; }
    sealed class Topology
    {
        public UnityEngine.Mesh source;
        public int[][] indices;
        public int[][] parts;
        public List<Pair> boundaries;
    }
    public sealed class Result
    {
        public readonly List<int> removed = new List<int>();
        public int physicalFeatures, curvedFeatures, retainedByReference, incompatibleOwner;
        public double maximumSourceError, maximumBoundaryError;
    }
    static Topology topology;
    static readonly Vector2Int[] Directions = {
        Vector2Int.right, Vector2Int.left, Vector2Int.up, Vector2Int.down
    };
    static ulong Key(int a, int b)
    {
        return ((ulong)(uint)Math.Min(a,b)<<32)|(uint)Math.Max(a,b);
    }
    static Topology BuildTopology(UnityEngine.Mesh source, byte[] tags)
    {
        var result = new Topology {
            source=source, indices=new int[source.subMeshCount][],
            parts=new int[source.subMeshCount][], boundaries=new List<Pair>()
        };
        using(var reader=new BinaryReader(new MemoryStream(tags))) {
            int vertices=reader.ReadInt32(), groups=reader.ReadInt32();
            if(vertices!=source.vertexCount || groups!=source.subMeshCount)
                throw new ArgumentException("Source silhouette topology/tag mismatch");
            for(int sm=0;sm<groups;sm++) {
                int role=reader.ReadInt32(), count=reader.ReadInt32();
                var indices=source.GetIndices(sm);
                if(role!=sm+7 || count*3!=indices.Length)
                    throw new ArgumentException("Source silhouette material/index mismatch");
                for(int i=0;i<indices.Length;i++)
                    if(reader.ReadInt32()!=indices[i])
                        throw new ArgumentException("Source silhouette triangle order mismatch");
                result.indices[sm]=indices;
                result.parts[sm]=new int[count];
                for(int i=0;i<count;i++) {
                    result.parts[sm][i]=reader.ReadInt32();
                    reader.ReadInt32();reader.ReadInt32();
                }
            }
        }
        // Exact rest-position welding joins UV seams without welding nearby authored edges.
        var positions=source.vertices;
        var weld=new Dictionary<Vector3,int>();
        var canonical=new int[positions.Length];
        for(int i=0;i<positions.Length;i++) {
            if(!weld.TryGetValue(positions[i],out int id)) {
                id=weld.Count;weld.Add(positions[i],id);
            }
            canonical[i]=id;
        }
        var edges=new Dictionary<ulong,Pair>();
        foreach(var indices in result.indices)
            for(int i=0;i<indices.Length;i+=3)
                for(int k=0;k<3;k++) {
                    int a=indices[i+k],b=indices[i+(k+1)%3];
                    ulong key=Key(canonical[a],canonical[b]);
                    if(edges.TryGetValue(key,out var pair)) {pair.count++;edges[key]=pair;}
                    else edges.Add(key,new Pair{a=a,b=b,count=1});
                }
        foreach(var pair in edges.Values)
            if(pair.count==1)result.boundaries.Add(pair);
        return result;
    }
    static bool Covered(Color[] before,int x,int y)
    {
        return x>=0&&x<Width&&y>=0&&y<Height&&before[y*Width+x].a>.5f;
    }
    static bool SameOwner(Color[] owner,int x,int y,int role,int part)
    {
        var o=owner[y*Width+x];
        return Mathf.RoundToInt(o.r)==role&&Mathf.RoundToInt(o.g)==part;
    }
    static double Dot(Vector2 p,Vector2Int axis) { return p.x*axis.x+p.y*axis.y; }
    static bool NearPhysicalEdge(Vector2 p,Vector2[] projected,List<Pair> edges)
    {
        foreach(var edge in edges) {
            Vector2 a=projected[edge.a],b=projected[edge.b],ab=b-a;
            float t=Mathf.Clamp01(Vector2.Dot(p-a,ab)/Mathf.Max(ab.sqrMagnitude,1e-20f));
            if((a+t*ab-p).sqrMagnitude<=1f)return true;
        }
        return false;
    }
    static List<Piece> Envelope(Vector2[] projected,Topology mesh,int sm,int part,
                               Vector2Int outward,Vector2Int tangent,double lo,double hi)
    {
        var edges=new List<Edge>();
        var breaks=new List<double>{lo,hi};
        var indices=mesh.indices[sm];
        for(int i=0;i<indices.Length;i+=3) {
            if(mesh.parts[sm][i/3]!=part)continue;
            for(int k=0;k<3;k++) {
                Vector2 a=projected[indices[i+k]],b=projected[indices[i+(k+1)%3]];
                double ay=Dot(a,tangent),by=Dot(b,tangent);
                if(Math.Abs(by-ay)<1e-10)continue;
                double l=Math.Max(lo,Math.Min(ay,by)),h=Math.Min(hi,Math.Max(ay,by));
                if(h-l<=1e-10)continue;
                double ax=Dot(a,outward),bx=Dot(b,outward),s=(bx-ax)/(by-ay);
                edges.Add(new Edge{lo=l,hi=h,slope=s,offset=ax-s*ay});
                breaks.Add(l);breaks.Add(h);
            }
        }
        breaks.Sort();
        var stops=new List<double>();
        foreach(double point in breaks)
            if(stops.Count==0||point>stops[stops.Count-1])stops.Add(point);
        var pieces=new List<Piece>();
        for(int interval=1;interval<stops.Count;interval++) {
            double l=stops[interval-1],h=stops[interval],mid=(l+h)*.5;
            var active=edges.FindAll(e=>e.lo<mid&&e.hi>mid);
            if(active.Count==0)return null;
            active.Sort((a,b)=> {
                int order=a.slope.CompareTo(b.slope);
                return order!=0?order:a.offset.CompareTo(b.offset);
            });
            var unique=new List<Edge>();
            foreach(var edge in active) {
                if(unique.Count>0&&Math.Abs(edge.slope-unique[unique.Count-1].slope)<1e-12)
                    unique[unique.Count-1]=edge;
                else unique.Add(edge);
            }
            var hull=new List<Edge>();var starts=new List<double>();
            foreach(var edge in unique) {
                double cross=double.NegativeInfinity;
                while(hull.Count>0) {
                    var previous=hull[hull.Count-1];
                    cross=(previous.offset-edge.offset)/(edge.slope-previous.slope);
                    if(cross>starts[starts.Count-1]+1e-10)break;
                    hull.RemoveAt(hull.Count-1);starts.RemoveAt(starts.Count-1);
                }
                if(hull.Count==0)cross=double.NegativeInfinity;
                hull.Add(edge);starts.Add(cross);
            }
            for(int i=0;i<hull.Count;i++) {
                double a=Math.Max(l,starts[i]),b=Math.Min(h,i+1<starts.Count?starts[i+1]:double.PositiveInfinity);
                if(b-a>1e-10)pieces.Add(new Piece{lo=a,hi=b,slope=hull[i].slope,offset=hull[i].offset});
            }
        }
        return pieces;
    }
    static double At(List<Piece> pieces,double y)
    {
        foreach(var p in pieces)if(y>=p.lo-1e-8&&y<=p.hi+1e-8)return p.slope*y+p.offset;
        return double.NaN;
    }
    public static Result Apply(Color[] map,Color[] before,Color[] owner,UnityEngine.Mesh current,UnityEngine.Mesh source,
                               Matrix4x4 toClip,byte[] tags)
    {
        if(map.Length!=Width*Height||before.Length!=map.Length||owner.Length!=map.Length)
            throw new ArgumentException("Source silhouette grid mismatch");
        if(topology==null||topology.source!=source)topology=BuildTopology(source,tags);
        if(current.vertexCount!=source.vertexCount)
            throw new ArgumentException("Source silhouette baked vertex mismatch");
        var vertices=current.vertices;var projected=new Vector2[vertices.Length];
        for(int i=0;i<vertices.Length;i++) {
            var v=vertices[i];var p=toClip*new Vector4(v.x,v.y,v.z,1);
            if(Mathf.Abs(p.w)<1e-10f)throw new ArgumentException("Invalid silhouette projection");
            projected[i]=new Vector2((p.x/p.w*.5f+.5f)*Width,(p.y/p.w*.5f+.5f)*Height);
        }
        var result=new Result();var accepted=new HashSet<int>();
        for(int y=2;y<Height-2;y++)for(int x=2;x<Width-2;x++) {
            int index=y*Width+x;
            if(!Covered(before,x,y))continue;
            int role=Mathf.RoundToInt(owner[index].r),part=Mathf.RoundToInt(owner[index].g);
            if(role<8||role>11||part<2||part>5)continue;
            bool priorEdit=false;
            for(int dy=-2;dy<=2;dy++)for(int dx=-2;dx<=2;dx++)
                if(Mathf.Abs(map[(y+dy)*Width+x+dx].r)>.5f)priorEdit=true;
            if(priorEdit)continue;
            foreach(var normal in Directions) {
                var tangent=new Vector2Int(-normal.y,normal.x);
                int ix=x-normal.x,iy=y-normal.y;
                if(Covered(before,x+normal.x,y+normal.y)||
                   Covered(before,x+tangent.x,y+tangent.y)||
                   Covered(before,x-tangent.x,y-tangent.y))continue;
                if(!Covered(before,ix,iy)||
                   !Covered(before,ix+tangent.x,iy+tangent.y)||
                   !Covered(before,ix-tangent.x,iy-tangent.y))continue;
                if(!SameOwner(owner,ix,iy,role,part)||
                   !SameOwner(owner,ix+tangent.x,iy+tangent.y,role,part)||
                   !SameOwner(owner,ix-tangent.x,iy-tangent.y,role,part)) {
                    result.incompatibleOwner++;continue;
                }
                var centre=new Vector2(x+.5f,y+.5f);
                if(NearPhysicalEdge(centre,projected,topology.boundaries)) {
                    result.physicalFeatures++;continue;
                }
                double t=Dot(centre,tangent),n=Dot(centre,normal),lo=t-1.5,hi=t+1.5;
                var curve=Envelope(projected,topology,role-8,part,normal,tangent,lo,hi);
                if(curve==null||curve.Count==0)continue;
                double a=At(curve,lo),b=At(curve,hi),error=0;
                foreach(var piece in curve)
                    foreach(double yy in new[]{piece.lo,piece.hi}) {
                        double chord=a+(b-a)*(yy-lo)/(hi-lo);
                        error=Math.Max(error,Math.Abs(piece.slope*yy+piece.offset-chord));
                    }
                if(error>SourceTolerance) {result.curvedFeatures++;continue;}
                if((a+b)*.5>=n) {result.retainedByReference++;continue;}
                double boundaryError=Math.Abs(n-.5-At(curve,t));
                if(boundaryError>BoundaryTolerance)continue;
                if(accepted.Add(index)) {
                    result.removed.Add(index);
                    result.maximumSourceError=Math.Max(result.maximumSourceError,error);
                    result.maximumBoundaryError=Math.Max(result.maximumBoundaryError,boundaryError);
                }
                break;
            }
        }
        // Simultaneous deletions cannot become support for another deletion in this pass.
        foreach(int index in result.removed)map[index]=new Color(-1,0,0,1);
        return result;
    }
}
