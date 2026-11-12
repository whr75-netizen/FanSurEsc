using System;
using System.Collections.Generic;
using LineGeometry97;
public static class OpacityCases105 {
 static P Transform(P p,int rotation,bool reflect){p=p-new P(4,4);if(reflect)p.x=-p.x;for(int i=0;i<rotation;i++)p=new P(-p.y,p.x);return p+new P(4,4);}
 public static void Main(){
  for(int phase=0;phase<4;phase++)for(int rotation=0;rotation<4;rotation++)for(int reflect=0;reflect<2;reflect++)foreach(double width in new[]{.2,.7,1.2})for(int cover=0;cover<3;cover++){
   var geometry=new List<Triangle>();var material=new Material{cull=0};if(cover!=0){double right=cover==1?8:4;P a=Transform(new P(0,0),rotation,reflect==1),b=Transform(new P(right,0),rotation,reflect==1),c=Transform(new P(right,8),rotation,reflect==1),d=Transform(new P(0,8),rotation,reflect==1);geometry.Add(new Triangle(a,b,c,0,0,0,new P(),new P(),new P(),material));geometry.Add(new Triangle(a,c,d,0,0,0,new P(),new P(),new P(),material));}
   var scene=new Scene(geometry,new P(-1,-1),10);var raster=new Raster(scene,new P(),8,new P());var collector=new CurveOpacity98(scene,raster);double y=2.1+.25*phase;var raw=new[]{new P(2.1,y),new P(5.7,y),new P(2.1,y+width),new P(5.7,y+width)};var p=new P[4];for(int i=0;i<4;i++)p[i]=Transform(raw[i],rotation,reflect==1);collector.Register(1,(p[0]+p[2])*.5,(p[1]+p[3])*.5,width);var strips=new List<Strip103>{new Strip103(new Triangle(p[0],p[1],p[3],1,1,1,new P(),new P(),new P(),null),1,0,1,1),new Strip103(new Triangle(p[0],p[3],p[2],1,1,1,new P(),new P(),new P(),null),1,0,1,0)};
   var stats=RowParallel103.Run(scene,raster,collector,strips);if(!stats.allWorkersCompleted||!stats.queryViewsReleased)throw new Exception("105 pending CPU lease");raster.FinishClearance99();var proof=new float[8*8*8];for(int i=0;i<64;i++)proof[((i/8)*16+i%8)*4]=raster.pixels[i].State;collector.Finish(proof);Console.Write(phase+","+rotation+","+reflect+","+width+","+cover+":");for(int i=0;i<64;i++)Console.Write(collector.masks[i]+(i==63?"\n":","));
  }
 }
}
