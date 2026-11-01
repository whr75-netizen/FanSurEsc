// Compile-only adapter. Does not own/dispose the ComputeBuffer or invoke Unity by itself.
using System;
using UnityEngine;
namespace PixelReadback70
{
 public sealed class UnityEyeBuffer : IBuffer
 {
  readonly ComputeBuffer buffer;
  public UnityEyeBuffer(ComputeBuffer value){if(value==null||!value.IsValid())throw new ArgumentException("Live borrowed buffer required");buffer=value;}
  public int Count{get{return buffer.count;}}
  public int Stride{get{return buffer.stride;}}
  public void GetData(Array destination,int destinationStart,int sourceStart,int count){if(!buffer.IsValid())throw new ObjectDisposedException("Borrowed ComputeBuffer invalidated");buffer.GetData(destination,destinationStart,sourceStart,count);}
 }
}
