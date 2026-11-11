// Exact Crop arithmetic reused from OutputSupport26; no legacy host dependency.
using System;using UnityEngine;
namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {
public static class Projection31 {
 public static Matrix4x4 Crop(RectInt roi,Matrix4x4 physical){
  if(roi.width<=0||roi.height<=0)throw new InvalidOperationException("26 empty output crop");
  var crop=Matrix4x4.identity;crop.m00=480f/roi.width;crop.m03=(480f-2*roi.x-roi.width)/roi.width;
  crop.m11=272f/roi.height;crop.m13=(2*roi.y+roi.height-272f)/roi.height;
  return crop*physical;
 }
}
}
