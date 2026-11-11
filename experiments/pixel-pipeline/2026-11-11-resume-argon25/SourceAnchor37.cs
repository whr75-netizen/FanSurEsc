using System;
// Pure source-coordinate math. No Unity/GPU device, cache singleton or RGB data.
public static class SourceAnchorMath37 {
 public static double[] World(double[][] triangle,double[] bary,double[] localToWorld){
  if(triangle==null||triangle.Length!=3||bary==null||bary.Length!=3||localToWorld==null||localToWorld.Length!=16)throw new ArgumentException("source anchor shape");
  double sum=bary[0]+bary[1]+bary[2];if(Math.Abs(sum-1)>1e-8||Array.Exists(bary,v=>Double.IsNaN(v)||Double.IsInfinity(v)||v<0||v>1))throw new ArgumentException("source barycentric domain");
  if(Array.Exists(localToWorld,v=>Double.IsNaN(v)||Double.IsInfinity(v))||localToWorld[3]!=0||localToWorld[7]!=0||localToWorld[11]!=0||localToWorld[15]!=1)throw new ArgumentException("affine source transform");
  var p=new double[3];for(int c=0;c<3;c++){if(triangle[c]==null||triangle[c].Length!=3||Array.Exists(triangle[c],v=>Double.IsNaN(v)||Double.IsInfinity(v)))throw new ArgumentException("source triangle");for(int k=0;k<3;k++)p[k]+=bary[c]*triangle[c][k];}
  var w=new double[3];for(int k=0;k<3;k++)w[k]=localToWorld[k]*p[0]+localToWorld[4+k]*p[1]+localToWorld[8+k]*p[2]+localToWorld[12+k];return w;
 }
}
