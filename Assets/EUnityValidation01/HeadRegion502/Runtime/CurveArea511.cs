using System;
using System.Collections.Generic;

// Continuous positive-winding region of closed polygonal control graphs.
// Sweep critical curve/grid events once; no mesh triangles or source raster.
public static class CurveArea511
{
    public struct P {public double x,y;public P(double x,double y){this.x=x;this.y=y;}}
    struct Edge {public P a,b;public long sourceId;public double X(double y)=>a.x+(y-a.y)*(b.x-a.x)/(b.y-a.y);}
    struct Crossing {public double x;public int edge,delta;}
    public static int LastCrossings,LastEvents;
    static double Cross(P a,P b)=>a.x*b.y-a.y*b.x;
    static P Sub(P a,P b)=>new P(a.x-b.x,a.y-b.y);
    public static float[] Compute(IList<P[]> rings,int x0,int y0,int width,int height,NegativeRegion563 negative=null)
    {
        var edges=new List<Edge>();var levels=new List<double>();LastCrossings=0;
        for(int ringId=0;ringId<rings.Count;ringId++)for(int i=0;i<rings[ringId].Length;i++)
        {
            var ring=rings[ringId];var a=ring[i];var b=ring[(i+1)%ring.Length];levels.Add(a.y);
            if(a.y!=b.y)edges.Add(new Edge{a=a,b=b,sourceId=negative!=null?negative.EdgeId(ringId,i,ring.Length):0});
            if(a.x!=b.x)
            {
                int lo=Math.Max(x0,(int)Math.Ceiling(Math.Min(a.x,b.x))),hi=Math.Min(x0+width,(int)Math.Floor(Math.Max(a.x,b.x)));
                for(int x=lo;x<=hi;x++){double t=(x-a.x)/(b.x-a.x);if(t>0&&t<1)levels.Add(a.y+t*(b.y-a.y));}
            }
        }
        for(int y=y0;y<=y0+height;y++)levels.Add(y);
        for(int i=0;i<edges.Count;i++)for(int j=i+1;j<edges.Count;j++)
        {
            var a=edges[i];var b=edges[j];var r=Sub(a.b,a.a);var s=Sub(b.b,b.a);double den=Cross(r,s);
            if(den==0)continue;var q=Sub(b.a,a.a);double t=Cross(q,s)/den,u=Cross(q,r)/den;
            if(t>0&&t<1&&u>0&&u<1){levels.Add(a.a.y+t*r.y);LastCrossings++;}
        }
        levels.Sort();LastEvents=levels.Count;var result=new double[width*height];var crossings=new List<Crossing>(edges.Count);
        for(int band=0;band+1<levels.Count;band++)
        {
            double lo=levels[band],hi=levels[band+1],dy=hi-lo;if(!(dy>1e-12))continue;
            double middle=(lo+hi)*.5;int row=(int)Math.Floor(middle);if(row<y0||row>=y0+height)continue;
            negative?.BeginBand(lo,hi);crossings.Clear();
            for(int i=0;i<edges.Count;i++)
            {
                var e=edges[i];if((e.a.y<=middle&&middle<e.b.y)||(e.b.y<=middle&&middle<e.a.y))crossings.Add(new Crossing{x=e.X(middle),edge=i,delta=e.b.y>e.a.y?1:-1});
            }
            crossings.Sort((a,b)=>{int c=a.x.CompareTo(b.x);return c!=0?c:a.edge.CompareTo(b.edge);});
            int winding=0,left=-1;
            foreach(var crossing in crossings)
            {
                int before=winding;winding-=crossing.delta;
                if(before<=0&&winding>0)left=crossing.edge;
                else if(before>0&&winding<=0)
                {
                    var l=edges[left];var r=edges[crossing.edge];double lm=l.X(middle),rm=r.X(middle);
                    int first=Math.Max(x0,(int)Math.Floor(lm)),last=Math.Min(x0+width-1,(int)Math.Floor(rm));
                    double l0=l.X(lo),l1=l.X(hi),r0=r.X(lo),r1=r.X(hi);negative?.Positive(l0,l1,r0,r1,l.sourceId,r.sourceId);
                    for(int x=first;x<=last;x++)
                    {
                        double a=Math.Max(0,Math.Min(x+1,r0)-Math.Max(x,l0)),b=Math.Max(0,Math.Min(x+1,r1)-Math.Max(x,l1));
                        result[(row-y0)*width+x-x0]+=dy*(a+b)*.5;
                    }
                }
            }
            negative?.EndBand();if(winding!=0)throw new InvalidOperationException("511 control graph winding is not closed");
        }
        var output=new float[result.Length];for(int i=0;i<output.Length;i++)output[i]=(float)Math.Max(0,Math.Min(1,result[i]));return output;
    }
    public static void Fixtures()
    {
        P[] R(double x,double y,double xx,double yy,bool reverse=false){var r=new[]{new P(x,y),new P(xx,y),new P(xx,yy),new P(x,yy)};if(reverse)Array.Reverse(r);return r;}
        void Check(string name,P[][] rings,double expected){double sum=0;foreach(float a in Compute(rings,0,0,4,4))sum+=a;if(Math.Abs(sum-expected)>1e-7)throw new Exception(name+" area="+sum+" expected="+expected);}
        Check("one",new[]{R(0,0,1,1)},1);
        Check("duplicate",new[]{R(0,0,1,1),R(0,0,1,1)},1);
        Check("overlap",new[]{R(0,0,2,2),R(1,0,3,2)},6);
        Check("hole",new[]{R(0,0,3,3),R(1,1,2,2,true)},8);
        Check("outside-negative",new[]{R(0,0,1,1),R(2,2,3,3,true)},1);
        Check("touch",new[]{R(0,0,1,1),R(1,1,2,2)},2);
        Check("crossed-graph",new[]{new[]{new P(0,0),new P(1,1),new P(0,1),new P(1,0)}},.25);
        Check("fractional-grid-crossing",new[]{new[]{new P(.1,.1),new P(2.9,.2),new P(.2,2.9)}},3.915);
    }
}
