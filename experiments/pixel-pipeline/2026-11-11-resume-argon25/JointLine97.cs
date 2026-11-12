using System;
using System.Collections.Generic;
namespace LineGeometry97 {
 public struct P {
  public double x,y;public P(double x,double y){this.x=x;this.y=y;}
  public static P operator+(P a,P b){return new P(a.x+b.x,a.y+b.y);}public static P operator-(P a,P b){return new P(a.x-b.x,a.y-b.y);}public static P operator*(P a,double b){return new P(a.x*b,a.y*b);}public static double Dot(P a,P b){return a.x*b.x+a.y*b.y;}public static double Cross(P a,P b){return a.x*b.y-a.y*b.x;}public double Length{get{return Math.Sqrt(x*x+y*y);}}
 }
 public sealed class Image {
  public readonly int width,height,filter,wrapU,wrapV;public byte[] alpha;readonly int globalMin,globalMax;
  public Image(int w,int h,int filter,int u,int v,byte[] a){if(w<1||h<1||a==null||a.Length!=(long)w*h||filter<0||filter>1||u<0||u>2||v<0||v>2)throw new ArgumentException("97 source alpha ABI");width=w;height=h;this.filter=filter;wrapU=u;wrapV=v;alpha=a;int low=255,high=0;foreach(byte value in a){low=Math.Min(low,value);high=Math.Max(high,value);}globalMin=low;globalMax=high;}
  int Wrap(int p,int n,int kind){if(kind==0){p%=n;return p<0?p+n:p;}if(kind==1)return Math.Max(0,Math.Min(n-1,p));if(kind==2){p%=2*n;if(p<0)p+=2*n;return p<n?p:2*n-1-p;}throw new InvalidOperationException("97 unsupported source wrap");}
  public int Range(P lo,P hi,double multiplier,double cutoff,bool blend){
   if(alpha==null)throw new ObjectDisposedException("97 source alpha cache");double offset=filter==0?0:.5;int x0=(int)Math.Floor(lo.x*width-offset),x1=(int)Math.Floor(hi.x*width-offset)+(filter==0?0:1),y0=(int)Math.Floor(lo.y*height-offset),y1=(int)Math.Floor(hi.y*height-offset)+(filter==0?0:1);
   if((long)(x1-x0+1)*(y1-y0+1)>65536||multiplier<0)return 0;int low=255,high=0;
   if(globalMin==globalMax){low=globalMin;high=globalMax;}
   else for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++){int a=alpha[Wrap(y,height,wrapV)*width+Wrap(x,width,wrapU)];low=Math.Min(low,a);high=Math.Max(high,a);if(blend&&high*multiplier>0||!blend&&low/255.0*multiplier<=cutoff+1.0/1024&&high/255.0*multiplier>=cutoff-1.0/1024)return 0;}
   // One half-precision ULP around the cutoff is uncertainty, not a depth
   // bias. All actual pixel values remain original source alpha.
   double minimum=low/255.0*multiplier,maximum=high/255.0*multiplier,roundoff=1.0/1024;
   if(blend)return maximum==0?-1:0;
   if(minimum-cutoff>roundoff)return 1;if(cutoff-maximum>roundoff)return -1;return 0;
  }
 }
 public sealed class Material {
  public Image image;public bool test,blend,unresolved;public int cull;public double alpha=1,cutoff;public P scale=new P(1,1),offset;
 }
 public sealed class Triangle {
  public P a,b,c,ab,ac,uvA,uvB,uvC,gradient;public double za,zb,zc,det,zConstant,xyError;public readonly Material material;double lengthAB,lengthBC,lengthCA;
  public Triangle(P a,P b,P c,double za,double zb,double zc,P ua,P ub,P uc,Material m){material=m;Update(a,b,c,za,zb,zc,ua,ub,uc);}
  public void Update(P a,P b,P c,double za,double zb,double zc,P ua,P ub,P uc){this.a=a;this.b=b;this.c=c;ab=b-a;ac=c-a;det=P.Cross(ab,ac);this.za=za;this.zb=zb;this.zc=zc;uvA=ua;uvB=ub;uvC=uc;lengthAB=ab.Length;lengthBC=(c-b).Length;lengthCA=ac.Length;if(det==0){gradient=new P();zConstant=za;}else{gradient=new P(((zb-za)*ac.y-(zc-za)*ab.y)/det,(ab.x*(zc-za)-ac.x*(zb-za))/det);zConstant=za-P.Dot(gradient,a);}}
  public double Outside(P p){double sign=det>0?1:-1;return Math.Max(-sign*P.Cross(ab,p-a)/lengthAB,Math.Max(-sign*P.Cross(c-b,p-b)/lengthBC,-sign*P.Cross(a-c,p-c)/lengthCA));}
  public double Z(P p){return P.Dot(gradient,p)+zConstant;}
  public void Bary(P p,out double u,out double v){P d=p-a;u=P.Cross(d,ac)/det;v=P.Cross(ab,d)/det;}
  public int Alpha(P p,double radius){var m=material;if(m.unresolved)return 0;if(!m.test&&!m.blend)return 1;if(m.image==null)return 0;double u,v;Bary(p,out u,out v);P uv=(uvA+(uvB-uvA)*u+(uvC-uvA)*v);uv=new P(uv.x*m.scale.x+m.offset.x,uv.y*m.scale.y+m.offset.y);
   P du=new P((ac.y*(uvB.x-uvA.x)-ab.y*(uvC.x-uvA.x))/det,(ab.x*(uvC.x-uvA.x)-ac.x*(uvB.x-uvA.x))/det),dv=new P((ac.y*(uvB.y-uvA.y)-ab.y*(uvC.y-uvA.y))/det,(ab.x*(uvC.y-uvA.y)-ac.x*(uvB.y-uvA.y))/det);P e=new P((Math.Abs(du.x)+Math.Abs(du.y))*radius*Math.Abs(m.scale.x),(Math.Abs(dv.x)+Math.Abs(dv.y))*radius*Math.Abs(m.scale.y));return m.image.Range(uv-e,uv+e,m.alpha,m.cutoff,m.blend);
  }
  public bool Culled{get{return det==0||(material.cull==2&&det<0)||(material.cull==1&&det>0);}}
 }
 public struct Probe {public int state;public double clearance;public Probe(int s,double c){state=s;clearance=c;}}
 public sealed class Scene {
  public P origin;readonly int width;readonly List<Triangle>[] cells;public int visits,queries,entries;
  const double FloatEpsilon=1.1920928955078125e-7;
  public Scene(List<Triangle> triangles,P origin,int width){if(width<1||width>64||triangles.Count>65536)throw new ArgumentException("97 source scene limits");this.width=width;cells=new List<Triangle>[width*width];Rebuild(triangles,origin);}
  public void Rebuild(List<Triangle> triangles,P origin){if(triangles.Count>65536)throw new ArgumentException("97 source triangles");this.origin=origin;visits=queries=0;foreach(var cell in cells)if(cell!=null)cell.Clear();int count=0;
   foreach(var t in triangles){if(t.Culled)continue;double e=8*FloatEpsilon*(1+Math.Max(Math.Max(Math.Abs(t.a.x),Math.Abs(t.a.y)),Math.Max(Math.Max(Math.Abs(t.b.x),Math.Abs(t.b.y)),Math.Max(Math.Abs(t.c.x),Math.Abs(t.c.y)))));int x0=Math.Max(0,(int)Math.Floor(Math.Min(t.a.x,Math.Min(t.b.x,t.c.x))-e-origin.x)),x1=Math.Min(width-1,(int)Math.Floor(Math.Max(t.a.x,Math.Max(t.b.x,t.c.x))+e-origin.x)),y0=Math.Max(0,(int)Math.Floor(Math.Min(t.a.y,Math.Min(t.b.y,t.c.y))-e-origin.y)),y1=Math.Min(width-1,(int)Math.Floor(Math.Max(t.a.y,Math.Max(t.b.y,t.c.y))+e-origin.y));
    for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++){if(++count>262144)throw new InvalidOperationException("97 CPU spatial index budget before GPU submit");int at=y*width+x;if(cells[at]==null)cells[at]=new List<Triangle>();cells[at].Add(t);}
   }entries=count;
  }
  public Probe Query(P p,double lineZ,P lineGradient){
   if(++queries>131072)throw new InvalidOperationException("97 bounded CPU point query budget");int x=(int)Math.Floor(p.x-origin.x),y=(int)Math.Floor(p.y-origin.y);if(x<0||y<0||x>=width||y>=width)return new Probe(0,0);var bucket=cells[y*width+x];double error=8*FloatEpsilon*(1+Math.Max(Math.Abs(p.x),Math.Abs(p.y)));double radius=Math.Min(Math.Min(p.x-origin.x-x,origin.x+x+1-p.x),Math.Min(p.y-origin.y-y,origin.y+y+1-p.y));bool unknown=false;
   if(bucket!=null)foreach(var t in bucket){if(++visits>16777216)throw new InvalidOperationException("97 CPU triangle visit budget before GPU submit");double u,v;t.Bary(p,out u,out v);double outside=t.Outside(p);if(outside>error){radius=Math.Min(radius,outside-error);continue;}
    double gap=t.Z(p)-lineZ,zError=32*FloatEpsilon*(1+Math.Max(Math.Abs(lineZ),Math.Max(Math.Abs(t.za),Math.Max(Math.Abs(t.zb),Math.Abs(t.zc)))))+error*(Math.Abs(t.gradient.x)+Math.Abs(t.gradient.y)+Math.Abs(lineGradient.x)+Math.Abs(lineGradient.y));
    if(gap>zError){double slope=(t.gradient-lineGradient).Length;radius=Math.Min(radius,slope==0?radius:(gap-zError)/slope);continue;}
    if(outside>=-error||u<0||v<0||u+v>1){unknown=true;continue;}
    int alpha=t.Alpha(p,error);if(alpha<0)continue;if(alpha==0||gap>=-zError){unknown=true;continue;}return new Probe(-1,0);
   }
   return unknown?new Probe(0,0):new Probe(1,Math.Max(0,radius));
  }
  public bool Covered(List<P> polygon,Triangle strip,P shift){P centre=new P();foreach(P p in polygon)centre+=p;centre=centre*(1.0/polygon.Count);P q=centre-shift;int x=(int)Math.Floor(q.x-origin.x),y=(int)Math.Floor(q.y-origin.y);if(x<0||y<0||x>=width||y>=width)return false;var bucket=cells[y*width+x];if(bucket==null)return false;double error=8*FloatEpsilon*(1+Math.Max(Math.Abs(q.x),Math.Abs(q.y)))+strip.xyError,radius=error;foreach(P p in polygon)radius=Math.Max(radius,(p-centre).Length+error);
   foreach(var t in bucket){if(++visits>16777216)throw new InvalidOperationException("97 CPU triangle visit budget before GPU submit");bool covers=true;double zError=32*FloatEpsilon*(1+Math.Max(Math.Abs(strip.za),Math.Max(Math.Abs(t.za),Math.Max(Math.Abs(t.zb),Math.Abs(t.zc)))))+error*(t.gradient.Length+strip.gradient.Length);
    foreach(P point in polygon){P at=point-shift;if(t.Outside(at)>=-error||t.Z(at)>=strip.Z(point)-zError){covers=false;break;}}
    if(covers&&t.Alpha(q,radius)==1)return true;
   }return false;
  }
 }
 public sealed class Pixel {
  public bool support,unknown,visible,allCovered=true;public P witness,canonical,gradient;public double z,sourceUpper,radius,best=double.PositiveInfinity,t;public int edge;
  public int State{get{return !support?0:visible?1:allCovered?2:3;}} // Empty only when every source piece has a coverage proof.
 }
 public sealed class Raster {
  public readonly Pixel[] pixels;public readonly P origin,shift;public readonly int width;public int fragments;readonly Scene scene;
  public Raster(Scene scene,P origin,int width,P shift){this.scene=scene;this.origin=origin;this.width=width;this.shift=shift;pixels=new Pixel[width*width];for(int i=0;i<pixels.Length;i++)pixels[i]=new Pixel();}
  public static double Area(List<P> p){if(p.Count<3)return 0;double sum=0;P first=p[0];for(int i=1;i<p.Count-1;i++)sum+=P.Cross(p[i]-first,p[i+1]-first);return Math.Abs(sum)*.5;}
  public static List<P> Half(List<P> p,P n,double c){var o=new List<P>();if(p.Count==0)return o;P old=p[p.Count-1];double a=P.Dot(old,n)+c;foreach(P q in p){double b=P.Dot(q,n)+c;if((a<=0)!=(b<=0))o.Add(old+(q-old)*(a/(a-b)));if(b<=0)o.Add(q);old=q;a=b;}return o;}
  public void Add(Triangle strip,int edge,double ta,double tb,double tc){if(strip.det==0)return;int x0=Math.Max(0,(int)Math.Floor(Math.Min(strip.a.x,Math.Min(strip.b.x,strip.c.x))-origin.x)),x1=Math.Min(width-1,(int)Math.Floor(Math.Max(strip.a.x,Math.Max(strip.b.x,strip.c.x))-origin.x)),y0=Math.Max(0,(int)Math.Floor(Math.Min(strip.a.y,Math.Min(strip.b.y,strip.c.y))-origin.y)),y1=Math.Min(width-1,(int)Math.Floor(Math.Max(strip.a.y,Math.Max(strip.b.y,strip.c.y))-origin.y));
   for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++){P lo=origin+new P(x,y),hi=lo+new P(1,1);var p=new List<P>{strip.a,strip.b,strip.c};p=Half(p,new P(-1,0),lo.x);p=Half(p,new P(1,0),-hi.x);p=Half(p,new P(0,-1),lo.y);p=Half(p,new P(0,1),-hi.y);double area=Area(p);if(area<=0)continue;if(++fragments>8192)throw new InvalidOperationException("97 clipped fragment budget");var result=pixels[y*width+x];result.support=true;result.sourceUpper=Math.Min(1,result.sourceUpper+area);bool covered=scene.Covered(p,strip,shift)||scene.Covered(p,strip,new P());result.allCovered&=covered;if(covered)continue;P centre=new P();foreach(P q in p)centre+=q;centre=centre*(1.0/p.Count);var trials=new List<P>{centre};foreach(P q in p)trials.Add((q+centre)*.5);
    foreach(P point in trials){double z=strip.Z(point);Probe source=scene.Query(point-shift,z,strip.gradient);if(source.state!=1){result.unknown=true;continue;}Probe destination=scene.Query(point,z,strip.gradient);if(destination.state!=1){result.unknown=true;continue;}double radius=Math.Min(source.clearance,destination.clearance),distance=P.Dot(point-(lo+new P(.5,.5)),point-(lo+new P(.5,.5))),roundoff=64*2.220446049250313e-16*(1+Math.Max(Math.Abs(point.x),Math.Abs(point.y)))*(1+distance);if(!result.visible||distance<result.best-roundoff||Math.Abs(distance-result.best)<=roundoff&&edge<result.edge){double u,v;strip.Bary(point,out u,out v);result.visible=true;result.best=distance;result.witness=point;result.canonical=point-shift;result.gradient=strip.gradient;result.z=z;result.edge=edge;result.t=(1-u-v)*ta+u*tb+v*tc;result.radius=radius;}}
   }
  }
 }
}
