using System;
using UnityEngine;
using Unity.Collections;
namespace Unity.Collections {
 public struct NativeArray<T> {readonly T[] values;public NativeArray(T[] source){values=source;}public T this[int i]{get{return values[i];}}}
}
namespace UnityEngine {
 public struct Color {public float a;}
 public static class Mathf {public static int RoundToInt(float f){return(int)Math.Round(f);}}
 public sealed class Texture2D {
  public int width,height,GetterCalls;readonly byte[] logicalAlpha;
  public Texture2D(int n,byte[] a){width=n;height=1;logicalAlpha=a;}
  public Color GetPixel(int x,int y,int mip){if(y!=0||mip!=0)throw new Exception("getter coordinates");GetterCalls++;return new Color{a=logicalAlpha[x]/255f};}
 }
}
public static class AlphaChannelTests96 {
 static void Check(bool value){if(!value)throw new Exception("96 alpha calibration regression");}
 public static void Main(){
  int tests=0;
  for(int channel=0;channel<4;channel++){
   var data=new byte[4096];var alpha=new byte[1024];for(int i=0;i<1024;i++){alpha[i]=(byte)(128+i%128);for(int c=0;c<4;c++)data[4*i+c]=(byte)(c*13);data[4*i+channel]=alpha[i];}
   var texture=new Texture2D(1024,alpha);Check(Unity.AI.Assistant.Agent.Dynamic.Extension.Editor.AlphaChannel96.Find(texture,new NativeArray<byte>(data),4)==channel);Check(texture.GetterCalls<=18);tests++;
  }
  {var bytes=new byte[4096];var alpha=new byte[1024];for(int i=0;i<bytes.Length;i++)bytes[i]=255;for(int i=0;i<alpha.Length;i++)alpha[i]=255;var t=new Texture2D(1024,alpha);Check(Unity.AI.Assistant.Agent.Dynamic.Extension.Editor.AlphaChannel96.Find(t,new NativeArray<byte>(bytes),4)==0);Check(t.GetterCalls==17);tests++;}
  {var t=new Texture2D(1,new byte[]{255});Check(Unity.AI.Assistant.Agent.Dynamic.Extension.Editor.AlphaChannel96.Find(t,new NativeArray<byte>(new byte[]{1,2,3}),3)==-1);Check(t.GetterCalls==0);tests++;}
  {bool failed=false;try{Unity.AI.Assistant.Agent.Dynamic.Extension.Editor.AlphaChannel96.Find(new Texture2D(1,new byte[]{123}),new NativeArray<byte>(new byte[]{1,2,3,4}),4);}catch(InvalidOperationException){failed=true;}Check(failed);tests++;}
  Console.WriteLine("CPU AlphaChannel96 tests="+tests+"; public-getter byte calibration, no Unity/GPU initialized");
 }
}
