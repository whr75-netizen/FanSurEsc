using System;
using System.Collections.Generic;

// Closed-boundary construction, not a rendered-mask repair. Source rings and
// source hole families retain their IDs. The exterior grid contour is decided
// before internal KEEP/FILL, colour, depth and outline generation.
public static class HairRegions574
{
 public const double MinimumBroadWidth=2.0; // logical pixels: thinner features occupy at most one pixel across.
 [Serializable]public sealed class Family
 {
  public string id,kind,mode;public double width,sourceArea;public bool sourceOpen,referenceOpen;public int pixelCount,owner;
  public long[] sourceEdges;public List<CurveArea511.P[]> polygons=new();
 }
 public sealed class Layout
 {
  public readonly List<Family> families=new();public readonly List<CurveArea511.P[]> envelopeCurves=new();
  public readonly List<string> aliasCapSources=new();
  public float[] areas;public bool[] envelope,selected,protectedPositive;public int[] owner;public int filledAliasCells,filledFamilies,keptFamilies;
 }
 static double Signed(CurveArea511.P[] p){double a=0;var o=p[0];for(int i=1;i+1<p.Length;i++)a+=(p[i].x-o.x)*(p[i+1].y-o.y)-(p[i].y-o.y)*(p[i+1].x-o.x);return a*.5;}
 static double Cross(CurveArea511.P a,CurveArea511.P b,CurveArea511.P c)=>(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);
 static double Width(List<CurveArea511.P[]> polygons)
 {
  var points=new List<CurveArea511.P>();foreach(var p in polygons)points.AddRange(p);points.Sort((a,b)=>a.x==b.x?a.y.CompareTo(b.y):a.x.CompareTo(b.x));
  var unique=new List<CurveArea511.P>();foreach(var p in points)if(unique.Count==0||p.x!=unique[unique.Count-1].x||p.y!=unique[unique.Count-1].y)unique.Add(p);
  if(unique.Count<3)return 0;var lower=new List<CurveArea511.P>();var upper=new List<CurveArea511.P>();
  foreach(var p in unique){while(lower.Count>=2&&Cross(lower[lower.Count-2],lower[lower.Count-1],p)<=0)lower.RemoveAt(lower.Count-1);lower.Add(p);}
  for(int i=unique.Count-1;i>=0;i--){var p=unique[i];while(upper.Count>=2&&Cross(upper[upper.Count-2],upper[upper.Count-1],p)<=0)upper.RemoveAt(upper.Count-1);upper.Add(p);}
  lower.RemoveAt(lower.Count-1);upper.RemoveAt(upper.Count-1);lower.AddRange(upper);double width=double.PositiveInfinity;
  for(int i=0;i<lower.Count;i++){var a=lower[i];var b=lower[(i+1)%lower.Count];double dx=b.x-a.x,dy=b.y-a.y,length=Math.Sqrt(dx*dx+dy*dy),lo=double.PositiveInfinity,hi=double.NegativeInfinity;foreach(var p in lower){double t=(-dy*p.x+dx*p.y)/length;lo=Math.Min(lo,t);hi=Math.Max(hi,t);}width=Math.Min(width,hi-lo);}
  return width; // Hull is used only for this measurement, never as a render boundary.
 }
 static List<CurveArea511.P[]> Parts(NegativeRegion563.Feature f)
 {
  var groups=new Dictionary<(long,long),List<NegativeRegion563.Span>>();foreach(var s in f.geometry){var key=(s.left,s.right);if(!groups.TryGetValue(key,out var list))groups.Add(key,list=new());list.Add(s);}
  var output=new List<CurveArea511.P[]>();
  void Add(NegativeRegion563.Span s){var p=new[]{new CurveArea511.P(s.l0,s.lo),new CurveArea511.P(s.r0,s.lo),new CurveArea511.P(s.r1,s.hi),new CurveArea511.P(s.l1,s.hi)};if(Signed(p)>0)output.Add(p);}
  foreach(var list in groups.Values){list.Sort((a,b)=>a.lo.CompareTo(b.lo));var s=list[0];for(int i=1;i<list.Count;i++){var q=list[i];if(s.hi==q.lo&&s.l1==q.l0&&s.r1==q.r0){s.hi=q.hi;s.l1=q.l1;s.r1=q.r1;}else{Add(s);s=q;}}Add(s);}
  return output;
 }
 static List<long> Edges(NegativeRegion563.Feature f,List<int> original)
 {
  var result=new List<long>();foreach(var s in f.geometry)foreach(long edge in new[]{s.left,s.right}){long mapped=((long)original[(int)(edge>>32)]<<32)|(uint)edge;if(!result.Contains(mapped))result.Add(mapped);}result.Sort();return result;
 }
 static void NarrowCaps(NegativeRegion563.Feature branch,int x0,int y0,int w,int h,double[] area)
 {
  for(int side=0;side<2;side++)
  {
   if((side==0?branch.start566:branch.end566).kind!="cap")continue;
   for(int at=0;at<branch.geometry.Count;at++)
   {
    var s=branch.geometry[side==0?at:branch.geometry.Count-1-at];double near=side==0?s.r0-s.l0:s.r1-s.l1,far=side==0?s.r1-s.l1:s.r0-s.l0;if(near>=MinimumBroadWidth)break;bool last=far>=MinimumBroadWidth;
    if(last){double t=(MinimumBroadWidth-near)/(far-near);if(side==0){s.hi=s.lo+(s.hi-s.lo)*t;s.l1=s.l0+(s.l1-s.l0)*t;s.r1=s.r0+(s.r1-s.r0)*t;}else{s.lo=s.hi+(s.lo-s.hi)*t;s.l0=s.l1+(s.l0-s.l1)*t;s.r0=s.r1+(s.r0-s.r1)*t;}}
    int row=(int)Math.Floor((s.lo+s.hi)*.5)-y0;if(row>=0&&row<h)for(int u=Math.Max(x0,(int)Math.Floor((s.l0+s.l1)*.5));u<=Math.Min(x0+w-1,(int)Math.Floor((s.r0+s.r1)*.5));u++)area[row*w+u-x0]+=(s.hi-s.lo)*(Math.Max(0,Math.Min(u+1,s.r0)-Math.Max(u,s.l0))+Math.Max(0,Math.Min(u+1,s.r1)-Math.Max(u,s.l1)))*.5;
    if(last)break;
   }
  }
 }
 static bool[] Exterior(bool[] selected,int w,int h)
 {
  var outside=new bool[selected.Length];var q=new List<int>();void Add(int i){if(!selected[i]&&!outside[i]){outside[i]=true;q.Add(i);}}
  for(int i=0;i<selected.Length;i++)if(i%w==0||i%w==w-1||i/w==0||i/w==h-1)Add(i);
  for(int k=0;k<q.Count;k++){int i=q[k],x=i%w,y=i/w;if(x>0)Add(i-1);if(x+1<w)Add(i+1);if(y>0)Add(i-w);if(y+1<h)Add(i+w);}return outside;
 }
 static int Components(bool[] mask,int w,int h)
 {
  var seen=new bool[mask.Length];var q=new List<int>();int count=0;void Add(int i){if(mask[i]&&!seen[i]){seen[i]=true;q.Add(i);}}
  for(int i=0;i<mask.Length;i++){if(!mask[i]||seen[i])continue;count++;q.Clear();Add(i);for(int k=0;k<q.Count;k++){int n=q[k],x=n%w,y=n/w;if(x>0)Add(n-1);if(x+1<w)Add(n+1);if(y>0)Add(n-w);if(y+1<h)Add(n+w);}}return count;
 }
 static bool[] SourcePositive(IList<CurveArea511.P[]> source,int x,int y,int w,int h,out float[] sourceAreas,out List<int[]> sourceGroups)
 {
  // Current-pose canonical curves and the existing source grouping decide which
  // positive shape is already retained. FILL may expand it, never erase it.
  // The complementary empty cells are not pinned: they remain design choices.
  var first=new NegativeRegion563(x,y,w,h,false,true);var area=CurveArea511.Compute(source,x,y,w,h,first);
  var swapped=new List<CurveArea511.P[]>();foreach(var ring in source){var p=new CurveArea511.P[ring.Length];for(int i=0;i<p.Length;i++){var q=ring[ring.Length-1-i];p[i]=new CurveArea511.P(q.y,q.x);}swapped.Add(p);}
  var second=new NegativeRegion563(y,x,h,w,true,true);CurveArea511.Compute(swapped,y,x,h,w,second);
  sourceAreas=area;sourceGroups=NegativeRegion563.Groups(first.Branches566(),second.Branches566(),w,h);return HeadRegion502.SelectRegions543(area,w,h,sourceGroups);
 }
 // A grid bridge is admissible only when the original negative geometry joins
 // its two faces inside the same cell. Mere proximity/diagonal contact is not enough.
 static bool SourceCrosses577(NegativeRegion563.Feature f,int x,int y,int fromFaces,int toFaces)
 {
  const double epsilon=1e-12;var nodes=new List<NegativeRegion563.Span>();var faces=new List<int>();
  foreach(var s in f.geometry){if((int)Math.Floor((s.lo+s.hi)*.5)!=y)continue;var q=s;q.l0=Math.Max(x,s.l0);q.l1=Math.Max(x,s.l1);q.r0=Math.Min(x+1,s.r0);q.r1=Math.Min(x+1,s.r1);if((q.r0-q.l0+q.r1-q.l1)*(q.hi-q.lo)<=epsilon)continue;
   int mask=0;double left=(s.l0+s.l1)*.5,right=(s.r0+s.r1)*.5;if(left<x&&right>x)mask|=1;if(left<x+1&&right>x+1)mask|=2;if(s.lo==y&&q.r0-q.l0>epsilon)mask|=4;if(s.hi==y+1&&q.r1-q.l1>epsilon)mask|=8;nodes.Add(q);faces.Add(mask);
  }
  var parent=new int[nodes.Count];for(int i=0;i<parent.Length;i++)parent[i]=i;int Root(int a){while(parent[a]!=a)a=parent[a];return a;}
  for(int i=0;i<nodes.Count;i++)for(int j=0;j<i;j++){var a=nodes[j];var b=nodes[i];if(a.hi==b.lo&&Math.Min(a.r1,b.r0)-Math.Max(a.l1,b.l0)>epsilon)parent[Root(i)]=Root(j);else if(b.hi==a.lo&&Math.Min(b.r1,a.r0)-Math.Max(b.l1,a.l0)>epsilon)parent[Root(i)]=Root(j);}
  var combined=new int[nodes.Count];for(int i=0;i<nodes.Count;i++)combined[Root(i)]|=faces[i];foreach(int mask in combined)if((mask&fromFaces)!=0&&(mask&toFaces)!=0)return true;return false;
 }
 static double OmitCost577(int i,float[] area,bool[] selected,int w,int h)
 {
  double cost=2*(double)area[i]-1;int x=i%w,y=i/w;for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){if(dx==0&&dy==0)continue;int u=x+dx,v=y+dy;if(u<0||u>=w||v<0||v>=h)continue;float weight=HeadRegion502.BoundaryCost*(dx!=0&&dy!=0?.29289322f:.58578644f);cost+=(selected[v*w+u]?1:-1)*(double)weight;}return cost;
 }
 static bool[] SourcePassages577(List<NegativeRegion563.Feature> features,List<NegativeRegion563.Feature> branches,bool[] closed,int x0,int y0,int w,int h,float[] area,List<int[]> groups,ref bool[] positive)
 {
  bool any=false;var selected=positive;var outside=Exterior(selected,w,h);var label=new int[selected.Length];Array.Fill(label,-1);int count=0;var queue=new List<int>();
  for(int i=0;i<selected.Length;i++)if(!selected[i]&&!outside[i]&&label[i]<0){queue.Clear();queue.Add(i);label[i]=count;for(int k=0;k<queue.Count;k++){int n=queue[k],x=n%w,y=n/w;void Add(int j){if(!selected[j]&&!outside[j]&&label[j]<0){label[j]=count;queue.Add(j);}}if(x>0)Add(n-1);if(x+1<w)Add(n+1);if(y>0)Add(n-w);if(y+1<h)Add(n+w);}count++;}
  if(count==0)return null;var required=new bool[selected.Length];
  for(int f=0;f<features.Count;f++)if(!closed[f]&&Width(Parts(features[f]))>=MinimumBroadWidth){var feature=features[f];var cap=new double[selected.Length];foreach(var branch in branches)if(feature.geometry.Contains(branch.geometry[0]))NarrowCaps(branch,x0,y0,w,h,cap);
   var needs=new HashSet<int>();foreach(var cell in feature.cellArea)if(label[cell.Key]>=0&&cell.Value-cap[cell.Key]>1e-9)needs.Add(label[cell.Key]);
   foreach(int component in needs){int best=-1;double least=double.PositiveInfinity;foreach(var cell in feature.cellArea){int i=cell.Key,x=i%w,y=i/w;if(!selected[i]||cell.Value<=0)continue;int from=0,to=0;
     void Face(int j,int bit){if(!feature.cellArea.TryGetValue(j,out double a)||a<=0||selected[j])return;if(label[j]==component)from|=bit;if(outside[j])to|=bit;}
     if(x>0)Face(i-1,1);if(x+1<w)Face(i+1,2);if(y>0)Face(i-w,4);if(y+1<h)Face(i+w,8);if(from==0||to==0||!SourceCrosses577(feature,x+x0,y+y0,from,to))continue;
     double cost=OmitCost577(i,area,selected,w,h);if(cost<least||(cost==least&&i<best)){best=i;least=cost;}
    }
    if(best<0)throw new InvalidOperationException("577 broad source passage requires more than one source-supported cell: "+feature.boundaryId);
    required[best]=true;any=true;
   }
  }
  if(!any)return null;
  positive=HeadRegion502.SelectRegions543(area,w,h,groups,null,required);return required;
 }
 static bool KeepConnected577(bool[] visible,bool[] envelope,int w,int h,bool open)
 {
  bool any=false;foreach(bool v in visible)any|=v;if(!any)return false;
  if(!open)return Components(visible,w,h)==1;
  // Clipping an open source region to the head can yield several visible arcs.
  // They must all connect through the SAME exterior, not become interior holes.
  var complete=new bool[visible.Length];for(int i=0;i<complete.Length;i++)complete[i]=visible[i]||!envelope[i];return Components(complete,w,h)==1;
 }
 public static Layout Build(IList<CurveArea511.P[]> source,int x,int y,int w,int h)
 {
  if(source.Count==0)throw new InvalidOperationException("574 source boundary missing");
  var output=new Layout();var positive=new List<CurveArea511.P[]>();var original=new List<int>();double largest=0,largestSigned=0;
  for(int i=0;i<source.Count;i++){double a=Signed(source[i]);if(Math.Abs(a)>largest){largest=Math.Abs(a);largestSigned=a;}if(a>0){positive.Add(source[i]);original.Add(i);}else if(a<0){var p=(CurveArea511.P[])source[i].Clone();Array.Reverse(p);var f=new Family{id="hole-ring:"+i,kind="source-internal-ring",sourceEdges=new long[p.Length]};for(int j=0;j<p.Length;j++)f.sourceEdges[j]=((long)i<<32)|(uint)j;f.polygons.Add(p);output.families.Add(f);}}
  if(largestSigned<=0||positive.Count==0)throw new InvalidOperationException("574 source chart orientation differs; automatic curve input must be rebuilt");
  var negative=new NegativeRegion563(x,y,w,h,false,true);CurveArea511.Compute(positive,x,y,w,h,negative);
  var features=negative.Features();var membership=new Dictionary<NegativeRegion563.Span,int>();var closed=new bool[features.Count];for(int i=0;i<features.Count;i++){closed[i]=true;foreach(var s in features[i].geometry)membership.Add(s,i);}
  var sourceBranches=negative.Branches566();foreach(var b in sourceBranches)if(b.start566.kind=="open-mouth"||b.end566.kind=="open-mouth")closed[membership[b.geometry[0]]]=false;
  output.envelopeCurves.AddRange(positive);
  for(int i=0;i<features.Count;i++)if(closed[i]){var edge=Edges(features[i],original);var f=new Family{id="enclosed:"+string.Join(",",edge),kind="source-enclosed-component",sourceEdges=edge.ToArray(),polygons=Parts(features[i])};output.envelopeCurves.AddRange(f.polygons);output.families.Add(f);}
  output.protectedPositive=SourcePositive(source,x,y,w,h,out var sourceAreas,out var sourceGroups);var requiredNegative=SourcePassages577(features,sourceBranches,closed,x,y,w,h,sourceAreas,sourceGroups,ref output.protectedPositive);var referenceOutside=Exterior(output.protectedPositive,w,h);
  var rootAreas=CurveArea511.Compute(output.envelopeCurves,x,y,w,h);var proposal=HeadRegion502.SelectRegions543(rootAreas,w,h,null,output.protectedPositive,requiredNegative);var outside=Exterior(proposal,w,h);output.envelope=new bool[proposal.Length];
  for(int i=0;i<proposal.Length;i++)if(output.protectedPositive[i]&&!proposal[i])throw new InvalidOperationException("575 internal FILL erased the protected positive boundary");
  for(int i=0;i<proposal.Length;i++){output.envelope[i]=!outside[i];if(!proposal[i]&&!outside[i])output.filledAliasCells++;}
  // Interior fill of the chosen exterior contour must not silently erase a broad,
  // source-open parting which the spatial proposal accidentally sealed.
  if(output.filledAliasCells>0)for(int f=0;f<features.Count;f++)if(!closed[f]&&Width(Parts(features[f]))>=MinimumBroadWidth)
  {
   var capArea=new double[w*h];foreach(var branch in sourceBranches)if(membership[branch.geometry[0]]==f)NarrowCaps(branch,x,y,w,h,capArea);
   foreach(var cell in features[f].cellArea)if(cell.Value>0&&!proposal[cell.Key]&&!outside[cell.Key])
   {
    if(cell.Value-capArea[cell.Key]>1e-9)throw new InvalidOperationException("574 broad source parting sealed outside its narrow cap: "+features[f].boundaryId);
    if(!output.aliasCapSources.Contains(features[f].boundaryId))output.aliasCapSources.Add(features[f].boundaryId);
   }
  }
  output.selected=(bool[])output.envelope.Clone();output.owner=new int[proposal.Length];for(int i=0;i<proposal.Length;i++)output.owner[i]=output.selected[i]?1:0;
  output.areas=(float[])rootAreas.Clone();output.families.Sort((a,b)=>string.CompareOrdinal(a.id,b.id));int nextOwner=2;
  foreach(var family in output.families)
  {
   family.width=Width(family.polygons);family.mode=family.width<MinimumBroadWidth?"FILL":"KEEP";family.owner=nextOwner++;
   var holeAreas=CurveArea511.Compute(family.polygons,x,y,w,h);var union=new List<CurveArea511.P[]>(output.envelopeCurves);union.AddRange(family.polygons);var combined=CurveArea511.Compute(union,x,y,w,h);double outsideArea=0;var clipped=new float[rootAreas.Length];
   for(int i=0;i<clipped.Length;i++){double a=rootAreas[i]+(double)holeAreas[i]-combined[i];if(a < -2e-6||a>Math.Min(rootAreas[i],holeAreas[i])+2e-6)throw new InvalidOperationException("574 noncanonical winding/area overlap");clipped[i]=(float)Math.Max(0,Math.Min(Math.Min(rootAreas[i],holeAreas[i]),a));family.sourceArea+=clipped[i];outsideArea+=Math.Max(0,holeAreas[i]-clipped[i]);}
   family.sourceOpen=outsideArea>1e-6;
   if(family.mode=="FILL"){output.filledFamilies++;continue;}
   output.keptFamilies++;var hole=new bool[holeAreas.Length];for(int i=0;i<hole.Length;i++)if(!output.protectedPositive[i]&&clipped[i]>0){hole[i]=true;if(referenceOutside[i])family.referenceOpen=true;}var visible=new bool[hole.Length];bool touches=false;
   for(int i=0;i<hole.Length;i++)if(hole[i]&&output.envelope[i]){visible[i]=true;family.pixelCount++;int xx=i%w,yy=i/w;if(xx==0||yy==0||xx==w-1||yy==h-1||!output.envelope[i-1]||!output.envelope[i+1]||!output.envelope[i-w]||!output.envelope[i+w])touches=true;if(output.owner[i]>1)throw new InvalidOperationException("574 KEEP families compete for one cell; source union is required");output.owner[i]=family.owner;output.selected[i]=false;}
   if(!KeepConnected577(visible,output.envelope,w,h,family.referenceOpen)||touches!=family.referenceOpen)throw new InvalidOperationException("576 KEEP differs from the canonical signed region: "+family.id);
   for(int i=0;i<clipped.Length;i++)output.areas[i]=Math.Max(0,output.areas[i]-clipped[i]);
  }
  for(int i=0;i<proposal.Length;i++)if(output.selected[i]&&!output.envelope[i])throw new InvalidOperationException("574 family changed the authoritative exterior");
  return output;
 }
}
