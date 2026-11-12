// Pure CPU construction. Final runtime RGB is a finite table lookup only.
// Linear-brightness floor and OKLab L/C ratios have different units. The
// neutral-floor adapter uses cbrt(floor) (OKLab homogeneity), not the same number.
namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {
#if CAPTURE89
using P89=SourceMath67.SourcePalette58;
#else
using P89=global::SourcePalette58;
#endif
using System;using System.Collections.Generic;using System.Linq;
public static class PaletteRuntime89 {
 public sealed class Result {public byte[] rgb8;public float[] linear;public double floor,labRatio,maxCodeError;public int roundingChanges,sourceContrastPairs92,contrastCorrections92;}
 static void Need(bool b,string why){if(!b)throw new ArgumentException(why);}
 internal static double Y(int rgb){return .2126*P89.Decode((rgb>>16)/255.0)+.7152*P89.Decode(((rgb>>8)&255)/255.0)+.0722*P89.Decode((rgb&255)/255.0);}
 static int Key(int r,int g,int b){return(r<<16)|(g<<8)|b;}
 static int Channel(int key,int j){return(key>>(16-8*j))&255;}
 public static Result Build(byte[] references,int[] pairs,int levels,double floor){
  Need(references!=null&&references.Length>0&&references.Length%3==0&&references.Length<=16384*3&&pairs!=null&&pairs.Length%2==0&&pairs.Length<=131072&&levels>=2&&levels<=256&&P89.Finite(floor)&&floor>=0&&floor<=1,"89 bounded source/contrast/floor ABI");
  int n=references.Length/3;var next=new List<int>[n];var previous=new List<int>[n];var degree=new int[n];for(int i=0;i<n;i++){next[i]=new List<int>();previous[i]=new List<int>();}var unique=new Dictionary<long,byte>();
  for(int j=0;j<pairs.Length;j+=2){int a=pairs[j],b=pairs[j+1];Need(a>=0&&b>=0&&a<n&&b<n&&a!=b,"89 source contrast endpoint");long edgeKey=((long)a<<32)|(uint)b;if(!unique.ContainsKey(edgeKey)){unique.Add(edgeKey,0);next[a].Add(b);previous[b].Add(a);degree[b]++;}}
  var ready=new List<int>();for(int i=0;i<n;i++)if(degree[i]==0)ready.Add(i);var order=new List<int>();while(ready.Count>0){int i=ready[0];foreach(int item in ready)i=Math.Min(i,item);ready.Remove(i);order.Add(i);foreach(int j in next[i])if(--degree[j]==0)ready.Add(j);}Need(order.Count==n,"89 cyclic contrast graph");
  double ratio=Math.Pow(floor,1.0/3.0);var settings=new P89.Settings{count=levels,darkLRatio=ratio,darkCRatio=ratio,gamma=1,intervalScale=1};var target=new double[n,levels,3];var old=new byte[n*levels*3];
  for(int i=0;i<n;i++){var rgb=new[]{(int)references[3*i],(int)references[3*i+1],(int)references[3*i+2]};var lab=P89.LabRGB(rgb);var p=P89.MakePalette(new P89.Reference{rgb8=rgb},settings);for(int k=0;k<levels;k++){var c=P89.LinearLch(p.targetL[k],p.usedC[k],Math.Atan2(lab[2],lab[1]));for(int j=0;j<3;j++){target[i,k,j]=k==levels-1?rgb[j]:Math.Max(0,Math.Min(255,255*P89.Encode(c[j])));old[(i*levels+k)*3+j]=(byte)p.rgb8[k][j];}}}
  var result=new Result{rgb8=new byte[n*levels*3],linear=new float[n*levels*4],floor=floor,labRatio=ratio};var shared=new Dictionary<int,double>();
  for(int k=0;k<levels;k++){
   var keys=new int[n][];var values=new double[n][];
   for(int i=0;i<n;i++){var combinations=new List<int>();for(int a=0;a<8;a++){int r=(int)((a&1)==0?Math.Floor(target[i,k,0]):Math.Ceiling(target[i,k,0])),g=(int)((a&2)==0?Math.Floor(target[i,k,1]):Math.Ceiling(target[i,k,1])),b=(int)((a&4)==0?Math.Floor(target[i,k,2]):Math.Ceiling(target[i,k,2]));int encoded=Key(r,g,b);if(!combinations.Contains(encoded))combinations.Add(encoded);}combinations.Sort();keys[i]=combinations.ToArray();values[i]=new double[keys[i].Length];for(int j=0;j<keys[i].Length;j++){double y;if(!shared.TryGetValue(keys[i][j],out y)){y=Y(keys[i][j]);shared.Add(keys[i][j],y);}values[i][j]=y;}}
   var upper=new double[n];for(int j=order.Count-1;j>=0;j--){int i=order[j];double bound=Double.PositiveInfinity;foreach(int q in next[i])bound=Math.Min(bound,upper[q]);double best=Double.NegativeInfinity;foreach(double y in values[i])if(y<bound)best=Math.Max(best,y);Need(!Double.IsNegativeInfinity(best),"89 floor/ceil domains cannot preserve observed source contrast; do not change targets or submit GPU");upper[i]=best;}
   var selected=new double[n];foreach(int i in order){double lower=Double.NegativeInfinity;foreach(int p in previous[i])lower=Math.Max(lower,selected[p]);int key=-1;double cost=Double.PositiveInfinity,yChosen=0;for(int j=0;j<keys[i].Length;j++){double y=values[i][j];if(y<=lower||y>upper[i])continue;double error=0;for(int c=0;c<3;c++){double d=Channel(keys[i][j],c)-target[i,k,c];error+=d*d;}if(error<cost||(error==cost&&keys[i][j]<key)){key=keys[i][j];cost=error;yChosen=y;}}Need(key>=0,"89 exhausted palette domain");selected[i]=yChosen;bool changed=false;for(int c=0;c<3;c++){byte b=(byte)Channel(key,c);result.rgb8[(i*levels+k)*3+c]=b;result.linear[(i*levels+k)*4+c]=(float)P89.Decode(b/255.0);result.maxCodeError=Math.Max(result.maxCodeError,Math.Abs(b-target[i,k,c]));changed|=b!=old[(i*levels+k)*3+c];}result.linear[(i*levels+k)*4+3]=1;if(changed)result.roundingChanges++;}
   foreach(long e in unique.Keys){int a=(int)(e>>32),b=(int)(e&0xFFFFFFFF);Need(selected[a]<selected[b],"89 palette source-order invariant");}
  }
  Need(result.maxCodeError<1+1e-10,"89 palette exceeds floor/ceil quantization domain");return result;
 }
 // Optional measured-RGB constraints are CPU preprocessing only. The original
 // four-argument builder remains unchanged and reproduces the actual89 table.
 public static Result BuildConstrained92(byte[] references,int[] pairs,int levels,double floor,int[] nativeContrasts){
  var original=Build(references,pairs,levels,floor);int n=references.Length/3;var target=new double[n,levels,3];double ratio=Math.Pow(floor,1.0/3.0);var settings=new P89.Settings{count=levels,darkLRatio=ratio,darkCRatio=ratio,gamma=1,intervalScale=1};
  for(int i=0;i<n;i++){var rgb=new[]{(int)references[3*i],(int)references[3*i+1],(int)references[3*i+2]};var lab=P89.LabRGB(rgb);var palette=P89.MakePalette(new P89.Reference{rgb8=rgb},settings);for(int k=0;k<levels;k++){var c=P89.LinearLch(palette.targetL[k],palette.usedC[k],Math.Atan2(lab[2],lab[1]));for(int j=0;j<3;j++)target[i,k,j]=k==levels-1?rgb[j]:Math.Max(0,Math.Min(255,255*P89.Encode(c[j])));}}
  var before=original.rgb8;var corrected=PaletteConstraints92.Solve(target,before,pairs,nativeContrasts);original.rgb8=corrected;original.maxCodeError=0;original.sourceContrastPairs92=nativeContrasts.Length/5;
  for(int i=0;i<n;i++)for(int k=0;k<levels;k++){bool changed=false;for(int j=0;j<3;j++){int at=(i*levels+k)*3+j;changed|=corrected[at]!=before[at];original.maxCodeError=Math.Max(original.maxCodeError,Math.Abs(corrected[at]-target[i,k,j]));original.linear[(i*levels+k)*4+j]=(float)P89.Decode(corrected[at]/255.0);}if(changed)original.contrastCorrections92++;}
  return original;
 }
}
}
