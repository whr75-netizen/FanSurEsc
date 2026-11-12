using System;
using System.Collections.Generic;
using LineGeometry97;
public static class WorldSampleCases104 {
 public static void Main(){
  var material=new Material{cull=0};var empty=new Scene(new List<Triangle>(),new P(),2);
  var triangle=new Triangle(new P(.1,.1),new P(.3,.1),new P(.2,.3),.5,.5,.5,new P(),new P(),new P(),material);var occluded=new Scene(new List<Triangle>{triangle},new P(),2);int samples=0;
  foreach(double y in new[]{.5,1.5})foreach(double x in new[]{.5,1.5}){P p=new P(x,y);if(empty.QueryVisible99(p,1,new P()).state!=1||occluded.QueryVisible99(p,1,new P()).state!=1)throw new Exception("104 native tile samples differ");samples++;}
  P witness=new P(.2,.17);if(empty.QueryVisible99(witness,1,new P()).state!=1||occluded.QueryVisible99(witness,1,new P()).state!=-1)throw new Exception("104 continuous witness not distinguished");
  if(occluded.QueryVisible99(new P(.8,.8),1,new P()).state!=1)throw new Exception("104 partial visibility lost");
  var source=new Triangle(new P(0,0),new P(1,0),new P(0,1),1,1,1,new P(),new P(),new P(),null);if(occluded.Covered(new List<P>{new P(.05,.05),new P(.9,.05),new P(.05,.9)},source,new P()))throw new Exception("104 partial occlusion promoted to full coverage");
  Console.WriteLine("Four identical native-world sample depths permit different visibility at one line witness; other line support stays visible. samples="+samples+"; opaque triangles only; no Unity/GPU");
 }
}
