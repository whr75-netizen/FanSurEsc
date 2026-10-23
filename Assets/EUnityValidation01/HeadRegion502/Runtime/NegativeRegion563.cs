using System;
using System.Collections.Generic;

// Source geometry exists independently of a grid centre. Fractional cell
// incidence determines whole-cell ownership; it never edits a rendered mask.
public sealed class NegativeRegion563
{
 public struct Span {public double lo,hi,l0,l1,r0,r1;public long left,right;}
 public sealed class Feature
 {
  public string boundaryId,relationId;public double area;public int centreCount;
  public readonly List<Span> geometry=new();
  public readonly Dictionary<int,double> cellArea=new();
  public int[] OwnedCells(){var cells=new List<int>();foreach(var pair in cellArea)if(pair.Value>.5)cells.Add(pair.Key);cells.Sort();return cells.ToArray();}
 }
 struct PositiveSpan{public double l0,l1,r0,r1;public long left,right;}
 sealed class Node{public int parent;public double lo,hi,l0,l1,r0,r1,area;public long left,right;public int centres;public readonly Dictionary<int,double> cells=new();}
 readonly int x0,y0,width,height,originalWidth;readonly bool transpose;
 readonly List<PositiveSpan> positive=new();readonly List<Node> nodes=new();
 List<int> previous=new();double lo,hi,previousHi=double.NaN;
 public NegativeRegion563(int x0,int y0,int width,int height,bool transpose=false){this.x0=x0;this.y0=y0;this.width=width;this.height=height;this.transpose=transpose;originalWidth=transpose?height:width;}
 public long EdgeId(int ring,int segment,int count)=>((long)ring<<32)|(uint)(transpose?(count-2-segment+count)%count:segment);
 int Root(int i){while(nodes[i].parent!=i){nodes[i].parent=nodes[nodes[i].parent].parent;i=nodes[i].parent;}return i;}
 int Index(int x,int y)=>transpose?(x-x0)*originalWidth+y-y0:(y-y0)*originalWidth+x-x0;
 public void BeginBand(double lo,double hi){this.lo=lo;this.hi=hi;positive.Clear();}
 public void Positive(double l0,double l1,double r0,double r1,long left,long right){positive.Add(new PositiveSpan{l0=l0,l1=l1,r0=r0,r1=r1,left=left,right=right});}
 public void EndBand()
 {
  var current=new List<int>();double dy=hi-lo;int row=(int)Math.Floor((lo+hi)*.5);
  for(int i=0;i+1<positive.Count;i++)
  {
   var a=positive[i];var b=positive[i+1];double l0=a.r0,l1=a.r1,r0=b.l0,r1=b.l1;if((r0+r1-l0-l1)*.5<=1e-12)continue;
   int id=nodes.Count;var n=new Node{parent=id,lo=lo,hi=hi,l0=l0,l1=l1,r0=r0,r1=r1,left=a.right,right=b.left,area=dy*(r0+r1-l0-l1)*.5};nodes.Add(n);current.Add(id);
   if(previousHi==lo)foreach(int other in previous){var p=nodes[other];if(Math.Min(r0,p.r1)-Math.Max(l0,p.l1)>1e-12)nodes[Root(id)].parent=Root(other);}
   // CurveArea already splits at integer-grid crossings. The clipped span is
   // linear within this band, so the trapezoid integral is exact, not sampling.
   int first=Math.Max(x0,(int)Math.Floor((l0+l1)*.5)),last=Math.Min(x0+width-1,(int)Math.Floor((r0+r1)*.5));
   for(int x=first;x<=last;x++){double area=dy*(Math.Max(0,Math.Min(x+1,r0)-Math.Max(x,l0))+Math.Max(0,Math.Min(x+1,r1)-Math.Max(x,l1)))*.5;if(area>0)n.cells[Index(x,row)]=area;}
   for(int y=Math.Max(y0,(int)Math.Ceiling(lo-.5));y<y0+height&&y+.5<hi;y++){double t=(y+.5-lo)/dy,left=l0+(l1-l0)*t,right=r0+(r1-r0)*t;for(int x=Math.Max(x0,(int)Math.Ceiling(left-.5));x<x0+width&&x+.5<right;x++)if(x+.5>left)n.centres++;}
  }
  previous=current;previousHi=hi;
 }
 public List<Feature> Features()
 {
  var components=new Dictionary<int,Feature>();var boundaries=new Dictionary<int,Dictionary<long,bool>>();
  for(int i=0;i<nodes.Count;i++){int root=Root(i);var n=nodes[i];if(!components.TryGetValue(root,out var f)){components.Add(root,f=new Feature());boundaries.Add(root,new());}f.area+=n.area;f.centreCount+=n.centres;f.geometry.Add(new Span{lo=n.lo,hi=n.hi,l0=n.l0,l1=n.l1,r0=n.r0,r1=n.r1,left=n.left,right=n.right});boundaries[root][n.left]=boundaries[root][n.right]=true;foreach(var p in n.cells){f.cellArea.TryGetValue(p.Key,out double old);f.cellArea[p.Key]=old+p.Value;}}
  var result=new List<Feature>();foreach(var p in components){var ids=new List<long>(boundaries[p.Key].Keys);ids.Sort();var words=new List<string>();foreach(long id in ids)words.Add((id>>32)+":"+(uint)id);p.Value.boundaryId=(transpose?"x|":"y|")+string.Join(",",words);var relations=new List<string>();foreach(var s in p.Value.geometry){string q=(s.left>>32)+":"+(uint)s.left+">"+(s.right>>32)+":"+(uint)s.right;if(!relations.Contains(q))relations.Add(q);}relations.Sort(StringComparer.Ordinal);p.Value.relationId=(transpose?"x|":"y|")+string.Join(",",relations);result.Add(p.Value);}result.Sort((a,b)=>string.CompareOrdinal(a.boundaryId,b.boundaryId));return result;
 }
 // Feature records are never discarded. Only the selector's cell constraints
 // omit singleton/empty lists; they are not feature existence or identity.
 public static List<int[]> Groups(List<Feature> first,List<Feature> second)
 {
  var groups=new List<int[]>();foreach(var f in first){var g=f.OwnedCells();if(g.Length>=2)groups.Add(g);}foreach(var f in second){var g=f.OwnedCells();if(g.Length>=2)groups.Add(g);}return groups;
 }
}
