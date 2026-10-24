using System;
using System.Collections.Generic;

// Stored-input prototype only. No runtime integration, history or mask editing.
// Existing closed rings remain at their original indices: original arc IDs survive.
public static class CapContract572
{
 [Serializable] public sealed class Port
 {
  public string kind;public double level,left,right;public long leftId,rightId;
 }
 [Serializable] public sealed class Decision
 {
  public string sourceBranch,axis,mode,splitRule;
  public double pitch,sourceLo,sourceHi,fillLo,fillHi,keepLo,keepHi;
  public int insertedRing;public long[] positiveLeftBoundary,positiveRightBoundary;
  public Port sourceStart,sourceEnd;
  public int[] selectedPortCells;public string selectedPortStatus;
  public string selectedMode,validationScope;public int[] retainedCells;public int invalidComponents;
  public SelectedPort[] selectedPorts;
 }
 [Serializable] public sealed class SelectedPort{public string sourceSide;public Port source;public int from,to;}
 public sealed class Build
 {
  public readonly List<CurveArea511.P[]> rings=new();
  public readonly List<Decision> decisions=new();
  public readonly List<NegativeRegion563.Feature> sourceBranches=new();
  public readonly List<bool> transposed=new();
 }
 static Port Copy(NegativeRegion563.BoundaryEvent566 p)=>new Port{kind=p.kind,level=p.level,left=p.left,right=p.right,leftId=p.leftId,rightId=p.rightId};
 static CurveArea511.P Convert(double x,double y,bool transpose)=>transpose?new CurveArea511.P(y,x):new CurveArea511.P(x,y);
 public static Build Create(IList<CurveArea511.P[]> source,int x0,int y0,int width,int height,double pitch)
 {
  if(!(pitch>0))throw new ArgumentOutOfRangeException(nameof(pitch));
  var output=new Build();foreach(var ring in source)output.rings.Add(ring);
  for(int axis=0;axis<2;axis++)
  {
   bool transpose=axis!=0;var graph=new List<CurveArea511.P[]>();
   foreach(var ring in source){if(!transpose){graph.Add(ring);continue;}var p=new CurveArea511.P[ring.Length];for(int j=0;j<p.Length;j++){var a=ring[ring.Length-1-j];p[j]=new CurveArea511.P(a.y,a.x);}graph.Add(p);}
   var domain=new NegativeRegion563(transpose?y0:x0,transpose?x0:y0,transpose?height:width,transpose?width:height,transpose,true);
   CurveArea511.Compute(graph,transpose?y0:x0,transpose?x0:y0,transpose?height:width,transpose?width:height,domain);
   foreach(var branch in domain.Branches566())
   {
    output.sourceBranches.Add(branch);output.transposed.Add(transpose);
    bool filledAll=false;
    for(int end=0;end<2;end++)
    {
     if(filledAll)break;
     if((end==0?branch.start566:branch.end566).kind!="cap")continue;
     var prefix=new List<NegativeRegion563.Span>();bool reachedPitch=false;
     for(int n=0;n<branch.geometry.Count;n++)
     {
      int j=end==0?n:branch.geometry.Count-1-n;var s=branch.geometry[j];
      double near=end==0?s.r0-s.l0:s.r1-s.l1,far=end==0?s.r1-s.l1:s.r0-s.l0;
      if(near>=pitch){reachedPitch=true;break;}
      if(far>=pitch)
      {
       double t=(pitch-near)/(far-near);
       if(end==0){s.hi=s.lo+(s.hi-s.lo)*t;s.l1=s.l0+(s.l1-s.l0)*t;s.r1=s.r0+(s.r1-s.r0)*t;}
       else{s.lo=s.hi+(s.lo-s.hi)*t;s.l0=s.l1+(s.l0-s.l1)*t;s.r0=s.r1+(s.r0-s.r1)*t;}
       if(s.hi>s.lo)prefix.Add(s);reachedPitch=true;break;
      }
      prefix.Add(s);
     }
     if(prefix.Count==0)continue;if(end!=0)prefix.Reverse();
     var left=new List<CurveArea511.P>();var right=new List<CurveArea511.P>();
     var first=prefix[0];left.Add(Convert(first.l0,first.lo,transpose));right.Add(Convert(first.r0,first.lo,transpose));
     for(int n=0;n<prefix.Count;n++)
     {
      var s=prefix[n];bool last=n+1==prefix.Count;
      if(last||prefix[n+1].left!=s.left)left.Add(Convert(s.l1,s.hi,transpose));
      if(last||prefix[n+1].right!=s.right)right.Add(Convert(s.r1,s.hi,transpose));
     }
     var polygon=new List<CurveArea511.P>(left);right.Reverse();polygon.AddRange(right);
     for(int n=polygon.Count-1;n>0;n--)if(polygon[n].x==polygon[n-1].x&&polygon[n].y==polygon[n-1].y)polygon.RemoveAt(n);
     if(polygon.Count>1&&polygon[0].x==polygon[polygon.Count-1].x&&polygon[0].y==polygon[polygon.Count-1].y)polygon.RemoveAt(polygon.Count-1);
     double signed=0;for(int n=0;n<polygon.Count;n++){var a=polygon[n];var b=polygon[(n+1)%polygon.Count];signed+=a.x*b.y-a.y*b.x;}
     if(polygon.Count<3||signed==0)continue;if(signed<0)polygon.Reverse();
     double lo=branch.geometry[0].lo,hi=branch.geometry[branch.geometry.Count-1].hi,fl=prefix[0].lo,fh=prefix[prefix.Count-1].hi;
     output.decisions.Add(new Decision{sourceBranch=branch.boundaryId,axis=transpose?"x":"y",mode=reachedPitch?"FILL_CAP_KEEP_REMAINDER":"FILL_SOURCE_BRANCH",splitRule="first continuous cap width reaches one grid pitch; no cell-count or centre threshold",pitch=pitch,sourceLo=lo,sourceHi=hi,fillLo=fl,fillHi=fh,keepLo=end==0?fh:lo,keepHi=end==0?hi:fl,insertedRing=output.rings.Count,positiveLeftBoundary=branch.leftPath566.ToArray(),positiveRightBoundary=branch.rightPath566.ToArray(),sourceStart=Copy(branch.start566),sourceEnd=Copy(branch.end566),selectedPortStatus="NOT_RESOLVED"});
     output.rings.Add(polygon.ToArray());filledAll=!reachedPitch;
    }
   }
  }
  return output;
 }
 static void Footprint(NegativeRegion563.Feature f,double low,double high,bool transpose,int x0,int y0,int width,int height,bool[] output)
 {
  foreach(var z in f.geometry)
  {
   double a=Math.Max(low,z.lo),b=Math.Min(high,z.hi);if(b<=a)continue;
   double ta=(a-z.lo)/(z.hi-z.lo),tb=(b-z.lo)/(z.hi-z.lo),l0=z.l0+(z.l1-z.l0)*ta,l1=z.l0+(z.l1-z.l0)*tb,r0=z.r0+(z.r1-z.r0)*ta,r1=z.r0+(z.r1-z.r0)*tb;int v=(int)Math.Floor((a+b)*.5);
   for(int u=(int)Math.Floor(Math.Min(l0,l1));u<(int)Math.Ceiling(Math.Max(r0,r1));u++)
   {
    double area=(b-a)*(Math.Max(0,Math.Min(u+1,r0)-Math.Max(u,l0))+Math.Max(0,Math.Min(u+1,r1)-Math.Max(u,l1)))*.5;if(area<=0)continue;
    int x=(transpose?v:u)-x0,y=(transpose?u:v)-y0;if(x>=0&&y>=0&&x<width&&y<height)output[y*width+x]=true;
   }
  }
 }
 // Selector output contract only. This method never edits a mask or adds a cost.
 // A source port may turn through any pixel edge; its original axis is not a gate.
 public static void Finish(Build build,bool[] selected,int x0,int y0,int width,int height)
 {
  int[] dx={1,-1,0,0},dy={0,0,1,-1};var exterior=new bool[selected.Length];var queue=new List<int>();
  void Outside(int i){if(!selected[i]&&!exterior[i]){exterior[i]=true;queue.Add(i);}}
  for(int i=0;i<selected.Length;i++){int x=i%width,y=i/width;if(x==0||y==0||x==width-1||y==height-1)Outside(i);}
  for(int k=0;k<queue.Count;k++){int i=queue[k],x=i%width,y=i/width;for(int n=0;n<4;n++){int xx=x+dx[n],yy=y+dy[n];if(xx>=0&&yy>=0&&xx<width&&yy<height)Outside(yy*width+xx);}}
  foreach(var d in build.decisions)
  {
   int source=build.sourceBranches.FindIndex(f=>f.boundaryId==d.sourceBranch);if(source<0)throw new InvalidOperationException("572 source provenance missing");var f=build.sourceBranches[source];bool transpose=build.transposed[source];
   var full=new bool[selected.Length];var keep=new bool[selected.Length];Footprint(f,d.sourceLo,d.sourceHi,transpose,x0,y0,width,height,full);
   if(d.mode=="FILL_CAP_KEEP_REMAINDER")Footprint(f,d.keepLo,d.keepHi,transpose,x0,y0,width,height,keep);
   var active=new List<int>();for(int i=0;i<keep.Length;i++)if(keep[i]&&!selected[i])active.Add(i);d.retainedCells=active.ToArray();d.selectedMode=active.Count==0?"FILL_BY_CAP_AND_SPATIAL_CUT":"KEEP_WITH_FILLED_CAP";
   var ports=new List<SelectedPort>();bool open=false;
   for(int side=0;side<2;side++)
   {
    var p=side==0?d.sourceStart:d.sourceEnd;if(p.kind!="open-mouth")continue;open=true;int v=side==0?(int)Math.Floor(p.level):(int)Math.Ceiling(p.level)-1;
    for(int u=(int)Math.Floor(p.left);u<(int)Math.Ceiling(p.right);u++)
    {
     if(Math.Min(u+1,p.right)<=Math.Max(u,p.left))continue;int x=(transpose?v:u)-x0,y=(transpose?u:v)-y0;if(x<0||y<0||x>=width||y>=height)continue;int i=y*width+x;if(selected[i])continue;
     for(int n=0;n<4;n++){int xx=x+dx[n],yy=y+dy[n];if(xx<0||yy<0||xx>=width||yy>=height)continue;int next=yy*width+xx;if(!full[next]&&!selected[next]&&exterior[next])ports.Add(new SelectedPort{sourceSide=side==0?"start":"end",source=p,from=i,to=next});}
    }
   }
   d.selectedPorts=ports.ToArray();d.selectedPortCells=new int[ports.Count];for(int i=0;i<ports.Count;i++)d.selectedPortCells[i]=ports[i].from;
   d.validationScope=open?"OPEN_CAP_SOURCE_PORTS_ONLY":"NON_OPEN_EVENTS_NOT_VALIDATED";d.selectedPortStatus=ports.Count>0?"MAPPED_GRID_EDGE":active.Count==0?"NO_RETAINED_NEGATIVE_CELLS":"NO_SELECTED_PORT";
   d.invalidComponents=open?0:-1;if(!open)continue;
   var seen=new bool[selected.Length];foreach(int start in active)
   {
    if(seen[start])continue;seen[start]=true;queue.Clear();queue.Add(start);bool reached=false;
    for(int k=0;k<queue.Count;k++){int i=queue[k],x=i%width,y=i/width;foreach(var p in ports)if(p.from==i)reached=true;for(int n=0;n<4;n++){int xx=x+dx[n],yy=y+dy[n];if(xx<0||yy<0||xx>=width||yy>=height)continue;int next=yy*width+xx;if(keep[next]&&!selected[next]&&!seen[next]){seen[next]=true;queue.Add(next);}}}
    if(!reached)d.invalidComponents++;
   }
  }
 }
}
