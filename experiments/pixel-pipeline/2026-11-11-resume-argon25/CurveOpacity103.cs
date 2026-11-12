using System;
using System.Collections.Generic;
namespace LineGeometry97 {
 public sealed class CurveOpacity98 {
  public sealed class Witness {public P point,gradient;public double z,t;public int edge;public Triangle strip;}
  sealed class Feature {public P a,b;public double width;}
  sealed class Part {public Triangle strip;public int edge;public bool known;public P witness;}
  readonly Scene scene;readonly Raster raster;readonly Dictionary<int,Feature> features=new Dictionary<int,Feature>();readonly List<Part>[] parts;readonly Dictionary<Triangle,Witness>[] curve;public readonly int[] masks;public readonly Witness[] selected;public readonly double[] maximumCurveDepth;public int curveWitnesses,continuityChecks;public Func<int,Scene> QueryForRow103;bool featuresSealed103;
  public void SealFeatures103(){featuresSealed103=true;}
  public CurveOpacity98(Scene scene,Raster raster){this.scene=scene;this.raster=raster;int n=raster.pixels.Length;parts=new List<Part>[n];curve=new Dictionary<Triangle,Witness>[n];masks=new int[n];selected=new Witness[n];maximumCurveDepth=new double[n];raster.fragmentVisitor=Visit;}
  public void Register(int edge,P a,P b,double width){if(featuresSealed103)throw new InvalidOperationException("103 immutable feature table during row work");if(features.Count>=1024)throw new InvalidOperationException("98 source feature budget");features.Add(edge,new Feature{a=a,b=b,width=width});}
  static bool Segment(List<P> polygon,P a,P b,double sign,out double lo,out double hi){lo=0;hi=1;for(int i=0;i<polygon.Count;i++){P start=polygon[i],e=polygon[(i+1)%polygon.Count]-start;double x=sign*P.Cross(e,a-start),y=sign*P.Cross(e,b-start);if(x<0&&y<0)return false;if((x<0)!=(y<0)){double cut=x/(x-y);if(x<0)lo=Math.Max(lo,cut);else hi=Math.Min(hi,cut);}}return lo<hi;}
  public void Visit(Triangle strip,int edge,List<P> polygon,bool covered,int x,int y,bool visible,P witness){Scene query103=QueryForRow103==null?scene:QueryForRow103(y);if(covered)return;int at=y*raster.width+x;if(parts[at]==null)parts[at]=new List<Part>();parts[at].Add(new Part{strip=strip,edge=edge,known=visible,witness=witness});Feature f=features[edge];double lo,hi;if(!Segment(polygon,f.a,f.b,strip.det>0?1:-1,out lo,out hi))return;
   foreach(double fraction in new[]{.5,.25,.75}){P p=f.a+(f.b-f.a)*(lo+(hi-lo)*fraction);double epsilon=64*2.220446049250313e-16*(1+Math.Max(Math.Abs(p.x),Math.Abs(p.y)));P relative=p-(raster.origin+new P(x,y));if(relative.x<=epsilon||relative.y<=epsilon||relative.x>=1-epsilon||relative.y>=1-epsilon)continue;p=new P((float)p.x,(float)p.y);double z=(float)strip.Z(p);if(query103.QueryVisible99(p-raster.shift,z,strip.gradient).state!=1||query103.QueryVisible99(p,z,strip.gradient).state!=1)continue;double u,v;strip.Bary(p,out u,out v);double t=P.Dot(p-f.a,f.b-f.a)/P.Dot(f.b-f.a,f.b-f.a);var w=new Witness{point=p,z=z,gradient=strip.gradient,t=t,edge=edge,strip=strip};if(curve[at]==null)curve[at]=new Dictionary<Triangle,Witness>();Witness prior;
    if(!curve[at].TryGetValue(strip,out prior)||Distance(w,x,y)<Distance(prior,x,y)||Distance(w,x,y)==Distance(prior,x,y)&&w.t<prior.t)curve[at][strip]=w;
   }
  }
  double Distance(Witness p,int x,int y){P d=p.point-(raster.origin+new P(x+.5,y+.5));return P.Dot(d,d);}
  public void Finish(float[] currentStateProof){int width=raster.width;
   for(int at=0;at<parts.Length;at++){int x=at%width,y=at/width;if(currentStateProof[(y*width*2+x)*4]!=1||curve[at]==null){curve[at]=null;continue;}foreach(var w in curve[at].Values){curveWitnesses++;maximumCurveDepth[at]=Math.Max(maximumCurveDepth[at],w.z);Witness old=selected[at];double a=Distance(w,x,y),b=old==null?double.PositiveInfinity:Distance(old,x,y),error=64*2.220446049250313e-16*(1+Math.Max(Math.Abs(w.point.x),Math.Abs(w.point.y)))*(1+a);if(old==null||a<b-error||Math.Abs(a-b)<=error&&(w.edge<old.edge||w.edge==old.edge&&w.t<old.t))selected[at]=w;}}
   for(int at=0;at<parts.Length;at++){int x=at%width,y=at/width;if(currentStateProof[(y*width*2+x)*4]!=1||selected[at]!=null||parts[at]==null)continue;int required=511^16;bool all=true;
    foreach(var part in parts[at]){if(!part.known||features[part.edge].width+2*part.strip.xyError>=1){all=false;break;}int suitable=0;
     for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){if(dx==0&&dy==0)continue;int nx=x+dx,ny=y+dy;if(nx<0||ny<0||nx>=width||ny>=width)continue;int target=ny*width+nx;Witness w;if(curve[target]==null||!curve[target].TryGetValue(part.strip,out w))continue;continuityChecks++;if(scene.ClearSegment(part.witness,w.point,part.strip,raster.shift)&&scene.ClearSegment(part.witness,w.point,part.strip,new P()))suitable|=1<<((dy+1)*3+dx+1);}
     if(suitable==0){all=false;break;}required&=suitable;
    }if(all)masks[at]=required;
   }
  }
 }
}
