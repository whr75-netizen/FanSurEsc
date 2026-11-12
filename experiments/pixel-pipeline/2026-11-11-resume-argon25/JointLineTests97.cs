using System;
using System.Collections.Generic;
using LineGeometry97;
public static class JointLineTests97 {
 static int tests;static P P(double x,double y){return new P(x,y);}static Material M(){return new Material{cull=0};}
 static Triangle T(P a,P b,P c,double z,Material m){return new Triangle(a,b,c,z,z,z,P(0,0),P(0,0),P(0,0),m);}
 static Scene S(params Triangle[] t){return new Scene(new List<Triangle>(t),P(-2,-2),6);}
 static void Check(bool b,string message){if(!b)throw new Exception(message);tests++;}
 static Raster R(Scene s){return new Raster(s,P(0,0),1,P(0,0));}
 public static void Main(){
  Triangle line=T(P(.1,.4),P(.9,.4),P(.9,.6),2,null);
  {var r=R(S());r.Add(line,3,0,1,1);Check(r.pixels[0].State==1,"visible source");Check(r.pixels[0].sourceUpper<.1,"thin area is not rewritten as opaque area1");}
  {var r=R(S(T(P(-2,-2),P(5,-2),P(-2,5),1,M())));r.Add(line,3,0,1,1);Check(r.pixels[0].State==2,"all-source-piece coverage proof");}
  {var r=R(S(T(P(-2,-2),P(.5,-2),P(.5,5),1,M())));r.Add(line,3,0,1,1);Check(r.pixels[0].State==1,"partial front cover must retain visible piece");Check(r.pixels[0].witness.x>.5,"selected witness must actually be visible");}
  {var m=M();m.unresolved=true;var r=R(S(T(P(-2,-2),P(5,-2),P(-2,5),1,m)));r.Add(line,3,0,1,1);Check(r.pixels[0].State==3,"unknown alpha must not become empty");}
  {var r=R(S(T(P(-2,-2),P(5,-2),P(-2,5),3,M())));r.Add(line,3,0,1,1);Check(r.pixels[0].State==1,"behind actor");}
  {var scene=S(T(P(-2,-2),P(5,-2),P(-2,5),1,M()));var p=scene.Query(P(10,10),2,P(0,0));Check(p.state==0,"outside captured view unknown");}
  for(int channel=0;channel<2;channel++){var m=M();m.test=true;m.cutoff=.5;m.image=new LineGeometry97.Image(2,2,1,0,0,new byte[]{(byte)(channel*255),(byte)(channel*255),(byte)(channel*255),(byte)(channel*255)});var r=R(S(T(P(-2,-2),P(5,-2),P(-2,5),1,m)));r.Add(line,3,0,1,1);Check(r.pixels[0].State==(channel==0?1:2),"original source alpha");}
  for(int k=0;k<8;k++){Func<P,P> transform=p=>{double x=p.x-.5,y=p.y-.5;if(k>=4)x=-x;for(int j=0;j<k%4;j++){double a=x;x=-y;y=a;}return P(x+.5,y+.5);};var front=T(transform(P(-2,-2)),transform(P(.5,-2)),transform(P(.5,5)),1,M());var strip=T(transform(line.a),transform(line.b),transform(line.c),2,null);var r=R(S(front));r.Add(strip,3,0,1,1);Check(r.pixels[0].State==1,"D4 partial visibility");}
  {var scene=S();var r=R(scene);r.Add(line,7,0,1,1);r.Add(line,3,0,1,1);Check(r.pixels[0].edge==3,"stable source-ID tie independent of submission order");scene.Rebuild(new List<Triangle>{T(P(-2,-2),P(5,-2),P(-2,5),1,M())},P(-2,-2));r=R(scene);r.Add(line,3,0,1,1);Check(r.pixels[0].State==2,"scene rebuild invalidates previous visibility");}
  Console.WriteLine("CPU JointLine97 tests="+tests+"; no Unity/GPU");
 }
}
