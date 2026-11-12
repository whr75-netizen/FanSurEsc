using System;
using System.Collections.Generic;
using LineGeometry97;
public static class CurveOpacityTests98 {
 static int tests;static P P(double x,double y){return new P(x,y);}static Triangle T(P a,P b,P c,double z){return new Triangle(a,b,c,z,z,z,new P(),new P(),new P(),new Material{cull=0});}
 static void Check(bool b,string why){if(!b)throw new Exception(why);tests++;}
 static int Run(Func<P,P> transform,double outerY,List<Triangle> actors){var scene=new Scene(actors,P(-2,-2),8);var raster=new Raster(scene,P(0,0),4,new P());var collector=new CurveOpacity98(scene,raster);P a=transform(P(.2,.96)),b=transform(P(2.8,.96)),ea=transform(P(.2,outerY)),eb=transform(P(2.8,outerY));collector.Register(7,(a+ea)*.5,(b+eb)*.5,(ea-a).Length);raster.Add(T(a,b,eb,2),7,0,1,1);raster.Add(T(a,eb,ea,2),7,0,1,0);var proof=new float[4*4*8];for(int y=0;y<4;y++)for(int x=0;x<4;x++)proof[(y*8+x)*4]=raster.pixels[y*4+x].State;collector.Finish(proof);int count=0;for(int i=0;i<collector.masks.Length;i++){if(collector.masks[i]!=0){Check(raster.pixels[i].State==1,"opacity removal does not call visible geometry occluded");Check(collector.selected[i]==null,"only off-centreline duplicate cells");count++;}}return count;}
 public static void Main(){
  int expected=Run(p=>p,1.02,new List<Triangle>());Check(expected>0,"thin duplicate source cells should be found");
  for(int k=0;k<8;k++){int rotation=k%4;bool reflect=k>=4;Func<P,P> transform=p=>{double x=p.x-2,y=p.y-2;if(reflect)x=-x;for(int j=0;j<rotation;j++){double old=x;x=-y;y=old;}return P(x+2,y+2);};Check(Run(transform,1.02,new List<Triangle>())==expected,"D4 redundancy certificate");}
  Check(Run(p=>p,2.3,new List<Triangle>())==0,"wide support must not be collapsed to a thin centreline");
  var front=new List<Triangle>{T(P(-2,-2),P(6,-2),P(-2,1),1),T(P(6,-2),P(6,1),P(-2,1),1)};Check(Run(p=>p,1.02,front)==0,"sole visible outer fringe survives an occluded centreline");
  var blocker=new Scene(new List<Triangle>{T(P(.8,-1),P(1.2,-1),P(.8,3),1),T(P(1.2,-1),P(1.2,3),P(.8,3),1)},P(-2,-2),8);var strip=T(P(0,0),P(3,0),P(3,2),2);Check(!blocker.ClearSegment(P(.3,.9),P(1.7,.9),strip,new P()),"do not couple source fragments across a real occluder");
  Console.WriteLine("CPU CurveOpacity98 tests="+tests+"; duplicate cells="+expected+"; no Unity/GPU");
 }
}
