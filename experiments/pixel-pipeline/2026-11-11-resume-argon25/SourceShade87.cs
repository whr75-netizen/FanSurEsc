// Pure candidate consumer. Support identity does not choose a colour family.
// No Unity objects, hidden static cache, RGB lighting multiplication or fallback.
using System;
using System.Collections.Generic;
public sealed class SourceShade87 {
 public sealed class Input {
  public string sourceContract;
  public bool[] sourceMask;
  public int[] support,sourceRGBKey,colourAddress;
  public int levels;
  public float[] finiteLinearRGBA;
 }
 public sealed class Packet {
  public string sourceContract,sourceId,shadeSourceId;
  public int frame,shadeFrame;
  public bool[] currentVisibleFace;
  public int[] sourceTexel;
  public float[] selectedQ,currentLinearRGBA;
 }
 readonly string contract;
 readonly bool[] mask;
 readonly int[] support,address;
 readonly float[] palette;
 readonly int levels,families;
 public readonly int sourceTexels,unassignedSourceTexels;
 public bool Ready {get {return unassignedSourceTexels==0;}}
 static void Require(bool value,string why){if(!value)throw new ArgumentException(why);}
 static bool Finite(float v){return !Single.IsInfinity(v)&&!Single.IsNaN(v);}
 public SourceShade87(Input input){
  Require(input!=null&&!String.IsNullOrEmpty(input.sourceContract),"87 source provenance contract missing");
  Require(input.sourceMask!=null&&input.sourceMask.Length>0&&input.sourceMask.Length<=1100000,"87 bounded original UV domain");
  int n=input.sourceMask.Length;
  Require(input.support!=null&&input.support.Length==n&&input.sourceRGBKey!=null&&input.sourceRGBKey.Length==n&&input.colourAddress!=null&&input.colourAddress.Length==n,"87 source address arrays differ");
  levels=input.levels;Require(levels>=2&&levels<=256&&input.finiteLinearRGBA!=null&&input.finiteLinearRGBA.Length>0&&input.finiteLinearRGBA.Length%(4*levels)==0,"87 finite LUT ABI");
  families=input.finiteLinearRGBA.Length/(4*levels);Require(families<=16384,"87 bounded source colour table");
  foreach(float v in input.finiteLinearRGBA)Require(Finite(v)&&v>=0&&v<=1,"87 invalid linear LUT entry");
  contract=input.sourceContract;mask=(bool[])input.sourceMask.Clone();support=(int[])input.support.Clone();address=(int[])input.colourAddress.Clone();palette=(float[])input.finiteLinearRGBA.Clone();
  var sameSource=new Dictionary<int,int>();
  for(int i=0;i<n;i++)if(mask[i]){
   sourceTexels++;Require(support[i]>0,"87 source support missing; never fill gaps");
   int a=address[i];if(a<0){unassignedSourceTexels++;continue;}
   Require(a<families,"87 palette address out of range");int key=input.sourceRGBKey[i];Require(key>=0&&key<=0xFFFFFF,"87 observed RGB key ABI");
   int previous;if(sameSource.TryGetValue(key,out previous)){
    for(int j=0;j<4*levels;j++)Require(palette[a*4*levels+j]==palette[previous*4*levels+j],"87 same source colour/policy must share output; region/material anchor cannot change RGB");
   }else sameSource.Add(key,a);
  }
  Require(sourceTexels>0,"87 empty source domain");
 }
 // Atomic preflight: output remains null on any unresolved source or stamp.
 // A caller must not substitute the old RGB for only those missing cells.
 public bool TryCompose(Packet p,out float[] output,out string reason){
  output=null;reason=null;
  if(!Ready){reason="incomplete-source-colour-contract";return false;}
  if(p==null||p.sourceContract!=contract||String.IsNullOrEmpty(p.sourceId)||p.sourceId!=p.shadeSourceId||p.frame<0||p.frame!=p.shadeFrame){reason="source-shade-identity-mismatch";return false;}
  int n=p.currentVisibleFace==null?0:p.currentVisibleFace.Length;
  if(n<1||n>262144||p.sourceTexel==null||p.sourceTexel.Length!=n||p.selectedQ==null||p.selectedQ.Length!=n||p.currentLinearRGBA==null||p.currentLinearRGBA.Length!=4*n){reason="bounded-packet-ABI";return false;}
  for(int i=0;i<n;i++)if(p.currentVisibleFace[i]){
   int t=p.sourceTexel[i];float q=p.selectedQ[i];
   if(t<0||t>=mask.Length||!mask[t]||address[t]<0){reason="unresolved-visible-source";return false;}
   int k=Finite(q)?(int)Math.Round((double)q*(levels-1)):-1;
   if(k<0||k>=levels||q!=(float)k/(levels-1)){reason="selected-Q-outside-exact-labels";return false;}
   for(int j=0;j<4;j++)if(!Finite(p.currentLinearRGBA[4*i+j])){reason="nonfinite-current-surface";return false;}
  }
  output=(float[])p.currentLinearRGBA.Clone();
  for(int i=0;i<n;i++)if(p.currentVisibleFace[i]){
   int k=(int)Math.Round((double)p.selectedQ[i]*(levels-1));int a=(address[p.sourceTexel[i]]*levels+k)*4;
   for(int j=0;j<3;j++)output[4*i+j]=palette[a+j];
   // Current alpha, depth and owner are not inferred from support or history.
  }
  return true;
 }
}
