using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using Node579=ClosedRegion524.Node579;

// The existing compile_curve511.regularize policy, retaining the original node
// and its source-edge anchors through every keep/reverse/repair operation.
public static class CurveInputDesigner579
{
 public static int LastRepairs;
 sealed class Record579 {public Node579[] source;public SortedSet<int> keep;}
 struct Segment579 {public int record,a,b;public Vector2 p,q;}
 static double Cross579(double x,double y,double u,double v)=>x*v-y*u;
 static double Area579(Node579[] ring){double sum=0;for(int i=0;i<ring.Length;i++){var a=ring[i].point;var b=ring[(i+1)%ring.Length].point;sum+=(double)a.x*b.y-(double)a.y*b.x;}return sum*.5;}
 static bool Inside579(double x,double y,Node579[] ring)
 {
  int winding=0;for(int i=0;i<ring.Length;i++){var a=ring[i].point;var b=ring[(i+1)%ring.Length].point;double c=Cross579((double)b.x-a.x,(double)b.y-a.y,x-a.x,y-a.y);if(a.y<=y&&y<b.y&&c>0)winding++;else if(b.y<=y&&y<a.y&&c<0)winding--;}
  return winding!=0;
 }
 static double Distance579(Vector2 p,Vector2 a,Vector2 b)
 {
  double dx=(double)b.x-a.x,dy=(double)b.y-a.y,x=(double)p.x-a.x,y=(double)p.y-a.y,den=dx*dx+dy*dy,t=den==0?0:Math.Max(0,Math.Min(1,(x*dx+y*dy)/den));x-=t*dx;y-=t*dy;return x*x+y*y;
 }
 static SortedSet<int> Simplify579(Node579[] ring,double error)
 {
  int n=ring.Length,split=0;double far=-1;for(int i=0;i<n;i++){double dx=(double)ring[i].point.x-ring[0].point.x,dy=(double)ring[i].point.y-ring[0].point.y,d=dx*dx+dy*dy;if(d>far){far=d;split=i;}}
  var keep=new SortedSet<int>{0,split,n};
  void Run(int a,int b){if(b<=a+1)return;int index=-1;double best=-1;for(int i=a+1;i<b;i++){double d=Distance579(ring[i%n].point,ring[a%n].point,ring[b%n].point);if(d>best){best=d;index=i;}}if(best>error*error){keep.Add(index);Run(a,index);Run(index,b);}}
  Run(0,split);Run(split,n);keep.Remove(n);return keep;
 }
 static bool Proper579(Vector2 a,Vector2 b,Vector2 c,Vector2 d)
 {
  double rx=(double)b.x-a.x,ry=(double)b.y-a.y,sx=(double)d.x-c.x,sy=(double)d.y-c.y,den=Cross579(rx,ry,sx,sy);if(den==0)return false;
  double px=(double)c.x-a.x,py=(double)c.y-a.y,t=Cross579(px,py,sx,sy)/den,u=Cross579(px,py,rx,ry)/den;return t>0&&t<1&&u>0&&u<1;
 }
 public static List<Node579[]> Fit(List<Node579[]> loops)
 {
  int n=loops.Count;var signed=loops.Select(Area579).ToArray();var sizes=signed.Select(Math.Abs).ToArray();var perimeters=new double[n];var parents=new int[n];var children=new List<int>[n];
  for(int i=0;i<n;i++){children[i]=new List<int>();parents[i]=-1;var r=loops[i];for(int j=0;j<r.Length;j++){var a=r[j].point;var b=r[(j+1)%r.Length].point;double dx=(double)b.x-a.x,dy=(double)b.y-a.y;perimeters[i]+=Math.Sqrt(dx*dx+dy*dy);}double x=((double)r[0].point.x+r[1].point.x)*.5,y=((double)r[0].point.y+r[1].point.y)*.5;for(int j=0;j<n;j++)if(sizes[j]>sizes[i]&&Inside579(x,y,loops[j])&&(parents[i]<0||sizes[j]<sizes[parents[i]]))parents[i]=j;}
  for(int i=0;i<n;i++)if(parents[i]>=0)children[parents[i]].Add(i);
  var choices=new int[n,2];var costs=new double[n,2];var ready=new bool[n,2];
  double Cost(int i,int parent){if(ready[i,parent])return costs[i,parent];double zone=sizes[i]-children[i].Sum(j=>sizes[j]);int source=signed[i]>0?1:0;var values=new double[2];for(int label=0;label<2;label++)values[label]=(label==source?0:zone)+(label==parent?0:.14*perimeters[i])+children[i].Sum(j=>Cost(j,label));int chosen=values[0]<values[1]?0:values[1]<values[0]?1:source;choices[i,parent]=chosen;costs[i,parent]=values[chosen];ready[i,parent]=true;return values[chosen];}
  for(int i=0;i<n;i++)if(parents[i]<0)Cost(i,0);
  var records=new List<Record579>();
  void Choose(int i,int parent){int label=choices[i,parent];if(label!=parent){var source=(Node579[])loops[i].Clone();if((signed[i]>0)!=(label==1))Array.Reverse(source);var keep=Simplify579(source,.1875);var fitted=keep.Select(j=>source[j]).ToArray();if(fitted.Length>=3&&Area579(fitted)!=0)records.Add(new Record579{source=source,keep=keep});}foreach(int j in children[i])Choose(j,label);}
  for(int i=0;i<n;i++)if(parents[i]<0)Choose(i,0);LastRepairs=0;
  int limit=records.Sum(r=>r.source.Length);
  for(int iteration=0;iteration<=limit;iteration++){
   var segments=new List<Segment579>();for(int i=0;i<records.Count;i++){var r=records[i];var ids=r.keep.ToArray();for(int j=0;j<ids.Length;j++){int a=ids[j],b=ids[(j+1)%ids.Length];segments.Add(new Segment579{record=i,a=a,b=b,p=r.source[a].point,q=r.source[b].point});}}
   int first=-1,second=-1;for(int i=0;i<segments.Count&&first<0;i++)for(int j=i+1;j<segments.Count;j++){var a=segments[i];var b=segments[j];if(a.p.Equals(b.p)||a.p.Equals(b.q)||a.q.Equals(b.p)||a.q.Equals(b.q))continue;if(Proper579(a.p,a.q,b.p,b.q)){first=i;second=j;break;}}
   if(first<0)return records.Select(r=>r.keep.Select(j=>r.source[j]).ToArray()).ToList();
   bool changed=false;foreach(int index in new[]{first,second}){var s=segments[index];var record=records[s.record];int at=(s.a+1)%record.source.Length,chosen=-1;double best=-1;while(at!=s.b){double d=Distance579(record.source[at].point,s.p,s.q);if(d>best||d==best&&at<chosen){chosen=at;best=d;}at=(at+1)%record.source.Length;}if(chosen>=0){record.keep.Add(chosen);changed=true;}}
   if(!changed)throw new InvalidOperationException("579 original closed boundary has a proper crossing");LastRepairs++;
  }
  throw new InvalidOperationException("579 closed-region fit did not terminate");
 }
}

public static partial class HeadRegion502
{
    // Default-OFF input preparation only. No angle table or render-history filter.
    public static bool UseViewInput579;
    public static int ViewInput579Revision,ViewInput579SourceRings,ViewInput579SourcePoints,ViewInput579Controls,ViewInput579Repairs;
    public static double ViewInput579GenerationMs,ViewInput579KeyMs;
    public static string ViewInput579Status="disabled";
    static byte[] viewInput579;
    static Mesh viewSource579,viewOutput579;
    static ulong viewSignature579;
    static Quaternion viewRotation579;
    static Vector3 viewRootScale579,viewMeshScale579;
    static Matrix4x4 viewProjection579;

    static bool SameRotation579(Quaternion a,Quaternion b)=>a.Equals(b)||a.Equals(new Quaternion(-b.x,-b.y,-b.z,-b.w));
    static bool SameProjection579(Matrix4x4 a,Matrix4x4 b){for(int i=0;i<16;i++)if(a[i]!=b[i])return false;return true;}
    static byte[] CurrentViewInput579(Full319View335 f,Mesh output,Mesh source)
    {
        long start=System.Diagnostics.Stopwatch.GetTimestamp();
        if(!f.motion.camera.orthographic)throw new InvalidOperationException("579 current view input requires the existing orthographic ray contract");
        ulong signature=Fingerprint511(source);
        if(viewSource579!=source||viewSignature579!=signature){view511=null;alpha511=null;}
        Materials511(f); // Existing opaque, double-sided Hair / UV / alpha contract.
        var root=f.motion.animation.target.transform;
        var rotation=Quaternion.Inverse(f.motion.camera.transform.rotation)*root.rotation;
        var rootScale=root.lossyScale;var meshScale=f.motion.surface.outputs[2].transform.lossyScale;
        // Orthographic translation changes pixel phase, not the source chart's
        // view direction or density. Anchors still follow every actual pose.
        var projection=f.effectiveProjection;projection.SetColumn(3,new Vector4(0,0,0,1));
        bool same=viewInput579!=null&&viewSource579==source&&viewOutput579==output&&viewSignature579==signature&&SameRotation579(viewRotation579,rotation)&&viewRootScale579.Equals(rootScale)&&viewMeshScale579.Equals(meshScale)&&SameProjection579(viewProjection579,projection);
        ViewInput579KeyMs=1000.0*(System.Diagnostics.Stopwatch.GetTimestamp()-start)/System.Diagnostics.Stopwatch.Frequency;
        if(same){ViewInput579Status="current view anchor input reused";return viewInput579;}
        start=System.Diagnostics.Stopwatch.GetTimestamp();
        var mf=f.motion.surface.outputs[2];var local=output.vertices;var points=new Vector2[local.Length];var depth=new double[local.Length];var camera=f.motion.camera.worldToCameraMatrix;
        for(int i=0;i<local.Length;i++){var p=mf.transform.TransformPoint(local[i]);points[i]=f.Project(p);depth[i]=-camera.MultiplyPoint3x4(p).z;if(float.IsNaN(points[i].x)||float.IsNaN(points[i].y)||float.IsInfinity(points[i].x)||float.IsInfinity(points[i].y))throw new InvalidOperationException("579 nonfinite projected source");}
        var indices=new int[output.subMeshCount][];for(int s=0;s<indices.Length;s++)indices[s]=output.GetIndices(s);
        var raw=ClosedRegion524.BuildAnchored579(points,indices);
        var curves=CurveInputDesigner579.Fit(raw);
        if(curves.Count==0)throw new InvalidOperationException("579 no closed current-view Hair regions");
        int count=curves.Sum(r=>r.Length);double elapsed=(double)(System.Diagnostics.Stopwatch.GetTimestamp()-start)/System.Diagnostics.Stopwatch.Frequency;
        byte[] prepared;
        using(var stream=new MemoryStream())using(var writer=new BinaryWriter(stream)){
            writer.Write(511);writer.Write(2);writer.Write(source.vertexCount);writer.Write(source.subMeshCount);writer.Write(signature);
            writer.Write(curves.Count);writer.Write(raw.Count);writer.Write(raw.Sum(r=>r.Length));writer.Write(CurveInputDesigner579.LastRepairs);writer.Write(elapsed);
            foreach(var ring in curves){writer.Write(ring.Length);foreach(var node in ring){
                var anchor=node.anchors.OrderBy(p=>p.u*depth[p.a]+p.v*depth[p.b]+p.w*depth[p.c]).ThenBy(p=>p.sm).ThenBy(p=>p.primitive).First();
                double x=anchor.u*points[anchor.a].x+anchor.v*points[anchor.b].x+anchor.w*points[anchor.c].x,y=anchor.u*points[anchor.a].y+anchor.v*points[anchor.b].y+anchor.w*points[anchor.c].y;
                if(Math.Min(anchor.u,Math.Min(anchor.v,anchor.w))<0||Math.Abs(anchor.u+anchor.v+anchor.w-1)>1e-12||Math.Max(Math.Abs(x-node.point.x),Math.Abs(y-node.point.y))>.0005)throw new InvalidOperationException("579 source-edge anchor violates the existing reprojection contract");
                writer.Write(anchor.sm);writer.Write(anchor.primitive);writer.Write(anchor.a);writer.Write(anchor.b);writer.Write(anchor.c);writer.Write(anchor.u);writer.Write(anchor.v);writer.Write(anchor.w);
            }}writer.Flush();prepared=stream.ToArray();
        }
        viewInput579=prepared;viewSource579=source;viewOutput579=output;viewSignature579=signature;viewRotation579=rotation;viewRootScale579=rootScale;viewMeshScale579=meshScale;viewProjection579=projection;
        ViewInput579Revision++;ViewInput579SourceRings=raw.Count;ViewInput579SourcePoints=raw.Sum(r=>r.Length);ViewInput579Controls=count;ViewInput579Repairs=CurveInputDesigner579.LastRepairs;
        ViewInput579GenerationMs=1000.0*(System.Diagnostics.Stopwatch.GetTimestamp()-start)/System.Diagnostics.Stopwatch.Frequency;ViewInput579Status="generated current view input in memory";
        return viewInput579;
    }
    static void ReleaseViewInput579()
    {
        UseViewInput579=false;viewInput579=null;viewSource579=viewOutput579=null;viewSignature579=0;
        ViewInput579Revision=ViewInput579SourceRings=ViewInput579SourcePoints=ViewInput579Controls=ViewInput579Repairs=0;ViewInput579GenerationMs=ViewInput579KeyMs=0;ViewInput579Status="disabled";
    }
}
