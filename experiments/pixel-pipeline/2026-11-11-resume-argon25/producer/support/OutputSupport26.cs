using System;
using UnityEngine;

// Candidate-only output domain. Never changes EyeFeature348.roi/product77.
public static class OutputSupport26 {
 public static RectInt Union(RectInt original,Vector2 origin,int fineWidth,int fineHeight){
  if(!float.IsFinite(origin.x)||!float.IsFinite(origin.y)||fineWidth<=0||fineHeight<=0||fineWidth%4!=0||fineHeight%4!=0)
   throw new InvalidOperationException("26 finite canonical source grid required");
  int x=Mathf.CeilToInt(origin.x-.5f),y=Mathf.CeilToInt(origin.y-.5f);
  int x0=Mathf.Clamp(Math.Min(original.xMin,x),0,480),y0=Mathf.Clamp(Math.Min(original.yMin,y),0,272);
  int x1=Mathf.Clamp(Math.Max(original.xMax,x+fineWidth/4),0,480),y1=Mathf.Clamp(Math.Max(original.yMax,y+fineHeight/4),0,272);
  var r=new RectInt(x0,y0,x1-x0,y1-y0);
  if(r.width<=0||r.height<=0||(long)r.width*r.height>512)throw new InvalidOperationException("26 candidate output exceeds existing512-cell budget");
  return r;
 }
 public static Matrix4x4 Crop(RectInt roi,Matrix4x4 physical){
  if(roi.width<=0||roi.height<=0)throw new InvalidOperationException("26 empty output crop");
  var crop=Matrix4x4.identity;crop.m00=480f/roi.width;crop.m03=(480f-2*roi.x-roi.width)/roi.width;
  crop.m11=272f/roi.height;crop.m13=(2*roi.y+roi.height-272f)/roi.height;
  return crop*physical;
 }
}
