using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

// Geometry-defined leading spans replace independent pixel choices inside the
// existing cut. No mask cleanup, temporal state or part/frame-specific rule.
public static class BoundarySpan543
{
 struct P{public double x,y;public P(double x,double y){this.x=x;this.y=y;}public double Axis(int axis)=>axis==0?x:y;}
 static int Mod(int a,int n)=>(a%n+n)%n;
 static double Area(IList<P> r){double s=0;for(int i=0;i<r.Count;i++){var a=r[i];var b=r[(i+1)%r.Count];s+=a.x*b.y-a.y*b.x;}return s*.5;}
 static P Lerp(P a,P b,double t)=>new P(a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t);
 public static List<int[]> Groups(IList<Vector2[]> curves,float[] areas,RectInt bounds)
 {
  var groups=new List<int[]>();
  float At(int x,int y)=>bounds.Contains(new Vector2Int(x,y))?areas[(y-bounds.y)*bounds.width+x-bounds.x]:0;
  foreach(var ring in curves)
  {
   var r=ring.Select(v=>new P(v.x,v.y)).ToArray();int n=r.Length;if(n<3||Area(r)<=0)continue;
   for(int axis=0;axis<2;axis++)foreach(int sign in new[]{1,-1})for(int i=0;i<n;i++)
   {
    double V(int k)=>r[Mod(k,n)].Axis(axis)*sign;
    double v=V(i),prev=V(i-1),next=V(i+1);if(v>prev+1e-10||v>next+1e-10||Math.Max(prev-v,next-v)<=1e-10)continue;
    var peaks=new double[2];int side=0;
    foreach(int step in new[]{-1,1}){int at=i;for(int count=0;count<n-1;count++){int to=Mod(at+step,n);if(V(to)<V(at)-1e-10)break;at=to;}peaks[side++]=V(at);}
    double level=Math.Min(peaks[0],peaks[1]);if(level-v<=1e-9)continue;var paths=new List<P>[2];bool valid=true;side=0;
    foreach(int step in new[]{-1,1})
    {
     var path=paths[side++]=new List<P>{r[i]};int at=i;bool found=false;
     for(int count=0;count<n;count++){int to=Mod(at+step,n);if(V(to)>=level-1e-10){path.Add(Lerp(r[at],r[to],(level-V(at))/(V(to)-V(at))));found=true;break;}path.Add(r[to]);at=to;}
     valid&=found;
    }
    if(!valid)continue;var arc=paths[0].AsEnumerable().Reverse().Concat(paths[1].Skip(1)).ToArray();bool up=true,down=true,anyUp=false,anyDown=false;
    for(int k=1;k<arc.Length;k++){double d=arc[k].Axis(1-axis)-arc[k-1].Axis(1-axis);up&=d>=-1e-9;down&=d<=1e-9;anyUp|=d>1e-9;anyDown|=d<-1e-9;}
    if(!(up&&anyUp||down&&anyDown)||Area(arc)<=1)continue;
    int edge=sign==1?(int)Math.Floor(arc.Min(p=>p.Axis(axis))):(int)Math.Ceiling(arc.Max(p=>p.Axis(axis)))-1;
    int start=(int)Math.Floor(arc.Min(p=>p.Axis(1-axis))),end=(int)Math.Ceiling(arc.Max(p=>p.Axis(1-axis)));double best=double.NegativeInfinity;int[] chosen=null;
    for(int t=start;t<end-2;t++)
    {
     var indices=new int[3];double score=0;bool eligible=true;
     for(int j=0;j<3;j++){int x=axis==0?edge:t+j,y=axis==0?t+j:edge;float a=At(x,y);int dx=axis==0?sign:0,dy=axis==1?sign:0;if(a<=0||At(x+dx,y+dy)!=1||At(x+2*dx,y+2*dy)!=1){eligible=false;break;}indices[j]=(y-bounds.y)*bounds.width+x-bounds.x;score+=a;}
     if(eligible&&score>best){best=score;chosen=indices;}
    }
    if(chosen!=null&&!groups.Any(g=>g.SequenceEqual(chosen)))groups.Add(chosen);
   }
  }
  return groups;
 }
}
