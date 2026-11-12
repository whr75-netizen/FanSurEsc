using System;
using System.Collections.Generic;
using LineGeometry97;
public static class VisibilityOracle99 {
 public static void Main(){var rng=new Random(9991);int tests=0;var triangles=new List<Triangle>();
  for(int i=0;i<16;i++){double x=rng.NextDouble()*4,y=rng.NextDouble()*4;var material=new Material{cull=0,unresolved=i%7==0};triangles.Add(new Triangle(new P(x,y),new P(x+1+rng.NextDouble(),y+.01),new P(x+.02,y+1+rng.NextDouble()),1+i*.05,1.2+i*.05,1.1+i*.05,new P(),new P(),new P(),material));}
  var scene=new Scene(triangles,new P(-1,-1),8);
  for(int i=0;i<10000;i++){P p=new P(rng.NextDouble()*6-1,rng.NextDouble()*6-1),gradient=new P(rng.NextDouble()*.1,rng.NextDouble()*.1);double z=rng.NextDouble()*3;var expected=scene.Query(p,z,gradient);var actual=scene.QueryVisible99(p,z,gradient);if(actual.state!=expected.state)throw new Exception("99 optimized visibility changed reference state");tests++;}
  foreach(var t in triangles)for(int i=0;i<129;i++){double fraction=i/128.0;P edge=t.a+(t.b-t.a)*fraction;foreach(double offset in new[]{-.0001,0,.0001}){P p=edge+new P(0,offset);if(scene.Query(p,3,new P()).state!=scene.QueryVisible99(p,3,new P()).state)throw new Exception("99 boundary fallback changed reference state");tests++;}}
  Console.WriteLine("CPU exact visibility states="+tests+"; random/front/behind/unknown/edge/corner; no Unity/GPU");
 }
}
