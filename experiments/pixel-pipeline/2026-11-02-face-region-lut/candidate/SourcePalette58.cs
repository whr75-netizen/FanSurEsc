// Pure CPU port of source-palette54. No model/material-role constants or Unity state.
using System;
using System.Linq;
using System.Collections.Generic;

public static class SourcePalette58
{
    public sealed class Source { public string modelSHA256,imageSHA256,uvOrigin="top-left",encoding="srgb8";public int materialId;public double[] factorLinear; }
    public sealed class Sample { public string id,imageSHA256;public int materialId,primitiveId,triangle;public double[] uv;public int[] texel,rgba8;public double weight; }
    public sealed class Family { public string id,domainId;public Source source;public Sample[] samples; }
    public sealed class Colour { public Sample sample;public double[] linear,lab;public int[] rgb8;public double weight; }
    public sealed class Reference { public int[] rgb8;public double[] lab;public Sample sample;public double cost;public int sampleCount; }
    public sealed class Settings { public int count;public double darkLRatio,darkCRatio,gamma,intervalScale; }
    public sealed class Palette { public int[][] rgb8;public double[] targetL,requestedC,usedC,actualL;public bool[] gamutReduced;public int duplicates,LReversals; }
    public static bool Finite(double v) {return !double.IsNaN(v)&&!double.IsInfinity(v);}
    static void Require(bool ok,string message) {if(!ok)throw new ArgumentException(message);}
    public static double Decode(double x) {return x<=.04045?x/12.92:Math.Pow((x+.055)/1.055,2.4);}
    public static double Encode(double x) {return x<=.0031308?12.92*x:1.055*Math.Pow(x,1.0/2.4)-.055;}
    static double Cbrt(double x) {return Math.Sign(x)*Math.Pow(Math.Abs(x),1.0/3);}
    static int RGB8(double x) {return (int)Math.Floor(255*Encode(x)+.5);}
    public static double[] LabLinear(double[] c) {
        double r=c[0],g=c[1],b=c[2];
        double l=Cbrt(.4122214708*r+.5363325363*g+.0514459929*b),m=Cbrt(.2119034982*r+.6806995451*g+.1073969566*b),s=Cbrt(.0883024619*r+.2817188376*g+.6299787005*b);
        return new[]{.2104542553*l+.793617785*m-.0040720468*s,1.9779984951*l-2.428592205*m+.4505937099*s,.0259040371*l+.7827717662*m-.808675766*s};
    }
    public static double[] LabRGB(int[] rgb) {return LabLinear(rgb.Select(v=>Decode(v/255.0)).ToArray());}
    public static double[] LinearLch(double L,double C,double h) {
        double a=C*Math.Cos(h),b=C*Math.Sin(h),l=Math.Pow(L+.3963377774*a+.2158037573*b,3),m=Math.Pow(L-.1055613458*a-.0638541728*b,3),s=Math.Pow(L-.0894841775*a-1.291485548*b,3);
        return new[]{4.0767416621*l-3.3077115913*m+.2309699292*s,-1.2684380046*l+2.6097574011*m-.3413193965*s,-.0041960863*l-.7034186147*m+1.707614701*s};
    }
    static bool Valid(double[] v) {return v.All(x=>x>=-1e-9&&x<=1+1e-9);}
    public static int[] Gamut(double L,double C,double h,out double usedC) {
        usedC=C;var v=LinearLch(L,C,h);
        if(!Valid(v)) {double lo=0,hi=C;for(int i=0;i<28;i++){double mid=(lo+hi)/2;if(Valid(LinearLch(L,mid,h)))lo=mid;else hi=mid;}usedC=lo;v=LinearLch(L,usedC,h);}
        return v.Select(x=>RGB8(Math.Max(0,Math.Min(1,x)))).ToArray();
    }
    public static Colour[] SourceColours(Family f) {
        Require(f!=null&&f.source!=null&&f.samples!=null,"Explicit source family required");var s=f.source;
        Require(!string.IsNullOrEmpty(s.modelSHA256)&&!string.IsNullOrEmpty(s.imageSHA256)&&s.uvOrigin=="top-left"&&s.encoding=="srgb8","Original source/encoding required");
        Require(s.factorLinear!=null&&s.factorLinear.Length==4&&s.factorLinear.All(x=>Finite(x)&&x>=0&&x<=1),"Linear material factor required");
        var result=new List<Colour>();
        foreach(var v in f.samples) {
            Require(v.materialId==s.materialId&&v.imageSHA256==s.imageSHA256,"Source family mismatch");
            Require(!string.IsNullOrEmpty(v.id)&&v.uv!=null&&v.uv.Length==2&&v.uv.All(Finite)&&v.texel!=null&&v.texel.Length==2,"Original UV/texel missing");
            Require(v.rgba8!=null&&v.rgba8.Length==4&&v.rgba8.All(x=>x>=0&&x<=255)&&v.weight>0&&Finite(v.weight),"Invalid source sample");
            double weight=v.weight*v.rgba8[3]/255.0*s.factorLinear[3];
            if(weight<=0)continue;
            var linear=Enumerable.Range(0,3).Select(i=>Decode(v.rgba8[i]/255.0)*s.factorLinear[i]).ToArray();
            result.Add(new Colour {sample=v,linear=linear,lab=LabLinear(linear),rgb8=linear.Select(RGB8).ToArray(),weight=weight});
        }
        return result.ToArray();
    }
    public static Reference ExtractReference(Family f) {
        var samples=SourceColours(f);Require(samples.Length>0,"No visible source samples");Colour best=null;double cost=double.PositiveInfinity;
        foreach(var c in samples) {
            double sum=0;foreach(var s in samples){double q=0;for(int i=0;i<3;i++)q+=(s.lab[i]-c.lab[i])*(s.lab[i]-c.lab[i]);sum+=s.weight*q;}
            // Stable original ASCII sample IDs in this provider; see portability limit.
            if(sum<cost||(sum==cost&&(best==null||StringComparer.Ordinal.Compare(c.sample.id,best.sample.id)<0))){best=c;cost=sum;}
        }
        return new Reference {rgb8=(int[])best.rgb8.Clone(),lab=(double[])best.lab.Clone(),sample=best.sample,cost=cost,sampleCount=samples.Length};
    }
    public static Palette MakePalette(Reference reference,Settings p) {
        Require(p.count>=2&&p.count<=256&&Finite(p.darkLRatio)&&Finite(p.darkCRatio)&&p.darkLRatio>=0&&p.darkLRatio<=1&&p.darkCRatio>=0&&p.darkCRatio<=1&&p.gamma>0&&Finite(p.gamma)&&p.intervalScale>=0&&Finite(p.intervalScale),"Invalid palette settings");
        var lab=LabRGB(reference.rgb8);double L0=lab[0],C0=Math.Sqrt(lab[1]*lab[1]+lab[2]*lab[2]),h=Math.Atan2(lab[2],lab[1]);
        var result=new Palette {rgb8=new int[p.count][],targetL=new double[p.count],requestedC=new double[p.count],usedC=new double[p.count],actualL=new double[p.count],gamutReduced=new bool[p.count]};
        for(int k=0;k<p.count;k++) {
            double t=Math.Pow((double)k/(p.count-1),p.gamma),L=L0+p.intervalScale*(L0*(p.darkLRatio+(1-p.darkLRatio)*t)-L0),C=C0+p.intervalScale*(C0*(p.darkCRatio+(1-p.darkCRatio)*t)-C0);
            Require(L>=0&&L<=1&&C>=0,"Palette interval exceeds L/C domain");result.targetL[k]=L;result.requestedC[k]=C;
            if(k==p.count-1||p.intervalScale==0){result.rgb8[k]=(int[])reference.rgb8.Clone();result.usedC[k]=C0;}
            else {double used;result.rgb8[k]=Gamut(L,C,h,out used);result.usedC[k]=used;result.gamutReduced[k]=C-used>1e-7;}
            result.actualL[k]=LabRGB(result.rgb8[k])[0];if(k>0&&result.actualL[k]<result.actualL[k-1]-1e-9)result.LReversals++;
        }
        result.duplicates=p.count-result.rgb8.Select(v=>string.Join(",",v)).Distinct().Count();return result;
    }
    public static int ShadeIndex(double g,double[] thresholds) {
        Require(Finite(g)&&thresholds!=null&&thresholds.All(Finite),"Finite shade inputs required");
        float x=(float)g;Require(!float.IsInfinity(x),"Shade exceeds Float32");int k=0;float previous=float.NegativeInfinity;
        foreach(double value in thresholds){float cut=(float)value;Require(!float.IsInfinity(cut)&&cut>previous,"Sorted distinct Float32 thresholds required");if(x>=cut)k++;previous=cut;}return k;
    }
    public static int[] Resolve(Palette p,int k) {Require(k>=0&&k<p.rgb8.Length,"Unbound shade index");return (int[])p.rgb8[k].Clone();}
}
