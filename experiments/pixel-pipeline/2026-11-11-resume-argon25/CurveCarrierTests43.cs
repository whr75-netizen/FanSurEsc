using System;using System.Linq;using UnityEngine;
public static class CurveCarrierTests43 {
 public static void Main(){
  string m=new string('a',64);var uv=new[]{Vector2.zero,Vector2.right,Vector2.up,new Vector2(.5f,.5f),Vector2.one};var tri=new[]{0,1,2,3,2,4};var weld=new[]{0,1,2,0,1};var world=new[]{Vector3.zero,Vector3.right,Vector3.up,Vector3.zero,Vector3.right};var c=new CurveCarrier43(m,1,3,tri,weld,uv);var s=c.At(m,2,.25f,world);if(!s.known||s.uniqueUV||s.triangles.Length!=2)throw new Exception("seam pair not preserved");
  var key=s.key;for(int i=0;i<world.Length;i++)world[i]+=new Vector3(.1f,.2f,.3f);var moved=c.At(m,2,.25f,world);if(!moved.known||moved.key!=key||!moved.world.Equals(Vector3.LerpUnclamped(world[0],world[2],.25f)))throw new Exception("source identity/current deformation");
  if(c.At(m,2,-.1f,world).known||c.At(m,2,1.1f,world).known||c.At(m,0,0,world).known||c.At(new string('b',64),2,0,world).known)throw new Exception("invalid source extrapolation/model accepted");world[3].x+=.01f;if(c.At(m,2,.25f,world).known)throw new Exception("stale weld accepted");
  bool modelRejected=false,uvRejected=false;try{c.Require(new string('b',64),tri,weld,uv);}catch(InvalidOperationException){modelRejected=true;}uv[0].x=.1f;try{c.Require(m,tri,weld,uv);}catch(InvalidOperationException){uvRejected=true;}if(!modelRejected||!uvRejected)throw new Exception("cache invalidation");
  var clean=new CurveCarrier43(m,1,3,tri,weld,new[]{Vector2.zero,Vector2.right,Vector2.up,new Vector2(.5f,.5f),Vector2.one});var points=new[]{Vector3.zero,Vector3.right,Vector3.up,Vector3.zero,Vector3.right};
  for(int flip=0;flip<2;flip++)for(int angle=0;angle<4;angle++){int ff=flip,aa=angle;Func<Vector2,Vector2> transform=p=>{float x=ff==0?p.x:-p.x,y=p.y;for(int k=0;k<aa;k++){float old=x;x=-y;y=old;}return new Vector2(x,y);};var pixel=transform(new Vector2(.2f,.4f));var near=clean.Nearest(m,2,points,pixel,p=>transform(new Vector2(p.x,p.y)));if(!near.known||near.t!=.4f)throw new Exception("nearest source point D4 invariance");}
  if(clean.Nearest(m,2,points,Vector2.zero,p=>Vector2.zero).known)throw new Exception("degenerate projected support inferred");
  Console.WriteLine("{\"assertionGroups\":14,\"sourceSeamPairPreserved\":true,\"modelUVInvalidation\":true,\"nearestD4Cases\":8,\"degenerateRejected\":true,\"GPUCalls\":0,\"UnityObjectsCreated\":0}");
 }
}
