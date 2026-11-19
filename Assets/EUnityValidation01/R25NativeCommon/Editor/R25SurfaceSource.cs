using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.IO;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using Unity.Collections;
using UnityEngine.Rendering.Universal;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Experimental.Rendering;
using UnityEngine.InputSystem;
using FantasySurvival.Controls;
using FantasySurvival.SceneFlow;
using UnityEngine.InputSystem.LowLevel;

namespace FantasySurvival.EditorTools.NativeGridR25
{
public class Json40 : IEnumerable<Json40>
{
    protected Dictionary<string,Json40> fields;protected List<Json40> items;protected object value;
    public Json40 this[string key] {get {Json40 v;return fields!=null&&fields.TryGetValue(key,out v)?v:null;}set {fields[key]=value;}}
    public Json40 this[int i] {get {return items[i];}}
    public int Count {get {return items!=null?items.Count:fields!=null?fields.Count:0;}}
    public void Add(Json40 v) {items.Add(v);}
    public IEnumerable<T> Values<T>() {return this.Select(v=>(T)Convert.ChangeType(v.value,typeof(T),CultureInfo.InvariantCulture));}
    public IEnumerator<Json40> GetEnumerator() {return (items??(fields==null?new List<Json40>():fields.Values.ToList())).GetEnumerator();}
    IEnumerator IEnumerable.GetEnumerator() {return GetEnumerator();}
    public static implicit operator Json40(string v) {return v==null?null:new Json40{value=v};}
    public static implicit operator Json40(int v) {return new Json40{value=v};}
    public static implicit operator Json40(long v) {return new Json40{value=v};}
    public static implicit operator Json40(float v) {return new Json40{value=(double)v};}
    public static implicit operator Json40(double v) {return new Json40{value=v};}
    public static implicit operator Json40(bool v) {return new Json40{value=v};}
    public static explicit operator string(Json40 v) {return v==null?null:Convert.ToString(v.value,CultureInfo.InvariantCulture);}
    public static explicit operator int(Json40 v) {return Convert.ToInt32(v.value,CultureInfo.InvariantCulture);}
    public static explicit operator long(Json40 v) {return Convert.ToInt64(v.value,CultureInfo.InvariantCulture);}
    public static explicit operator double(Json40 v) {return Convert.ToDouble(v.value,CultureInfo.InvariantCulture);}
    public static explicit operator bool(Json40 v) {return Convert.ToBoolean(v.value,CultureInfo.InvariantCulture);}
    public static Json40 Wrap(object v) {
        if(v==null)return null;if(v is Json40)return(Json40)v;if(v is string)return(string)v;if(v is bool)return(bool)v;
        if(v is double)return(double)v;if(v is float)return(float)v;if(v is int)return(int)v;if(v is long)return(long)v;
        if(v is IEnumerable){var a=new Arr40();foreach(var x in(IEnumerable)v)a.Add(Wrap(x));return a;}
        throw new ArgumentException("Unsupported JSON boundary value: "+v.GetType().Name);
    }
    static string Quote(string text) {
        var b=new StringBuilder("\"");foreach(char c in text){switch(c){case '"':b.Append("\\\"");break;case '\\':b.Append("\\\\");break;case '\b':b.Append("\\b");break;case '\f':b.Append("\\f");break;case '\n':b.Append("\\n");break;case '\r':b.Append("\\r");break;case '\t':b.Append("\\t");break;default:if(c<32)b.Append("\\u"+((int)c).ToString("x4"));else b.Append(c);break;}}return b.Append('"').ToString();
    }
    public override string ToString() {
        if(fields!=null)return "{"+string.Join(",",fields.OrderBy(p=>p.Key,StringComparer.Ordinal).Select(p=>Quote(p.Key)+":"+(p.Value==null?"null":p.Value.ToString())))+"}";
        if(items!=null)return "["+string.Join(",",items.Select(v=>v==null?"null":v.ToString()))+"]";
        if(value==null)return "null";if(value is string)return Quote((string)value);if(value is bool)return(bool)value?"true":"false";
        if(value is double){double x=(double)value;if(double.IsNaN(x)||double.IsInfinity(x))throw new ArgumentException("Nonfinite JSON number");return x.ToString("R",CultureInfo.InvariantCulture);}
        return Convert.ToString(value,CultureInfo.InvariantCulture);
    }
    public static bool DeepEquals(Json40 a,Json40 b) {return a==null?b==null:b!=null&&a.ToString()==b.ToString();}
    public const int MaxInputChars66=65536;
    public static Json40 Parse(string text) {if(text.Length>MaxInputChars66)throw new ArgumentException("Small JSON budget exceeded; use streaming verification");int p=0;var result=ParseValue(text,ref p,0);Space(text,ref p);if(p!=text.Length)throw new ArgumentException("Trailing JSON data");return result;}
    static void Space(string s,ref int p) {while(p<s.Length&&char.IsWhiteSpace(s[p]))p++;}
    static string ParseString(string s,ref int p) {
        if(s[p++]!='"')throw new ArgumentException("JSON string expected");var b=new StringBuilder();
        while(p<s.Length){char c=s[p++];if(c=='"')return b.ToString();if(c=='\\'){char e=s[p++];switch(e){case '"':case '\\':case '/':b.Append(e);break;case 'b':b.Append('\b');break;case 'f':b.Append('\f');break;case 'n':b.Append('\n');break;case 'r':b.Append('\r');break;case 't':b.Append('\t');break;case 'u':b.Append((char)int.Parse(s.Substring(p,4),NumberStyles.HexNumber,CultureInfo.InvariantCulture));p+=4;break;default:throw new ArgumentException("JSON escape");}}else{if(c<32)throw new ArgumentException("JSON control character");b.Append(c);}}
        throw new ArgumentException("Unterminated JSON string");
    }
    static Json40 ParseValue(string s,ref int p,int depth) {
        if(depth>128)throw new ArgumentException("JSON nesting limit");Space(s,ref p);if(p>=s.Length)throw new ArgumentException("JSON value expected");char c=s[p];
        if(c=='"')return ParseString(s,ref p);
        if(c=='{'||c=='['){bool obj=c=='{';p++;Json40 result=obj?(Json40)new Obj40():new Arr40();Space(s,ref p);if(p<s.Length&&s[p]==(obj?'}':']')){p++;return result;}
            while(true){Space(s,ref p);string key=null;if(obj){key=ParseString(s,ref p);if(result.fields.ContainsKey(key))throw new ArgumentException("Duplicate JSON member");Space(s,ref p);if(s[p++]!=':')throw new ArgumentException("JSON colon");}var v=ParseValue(s,ref p,depth+1);if(obj)result[key]=v;else result.Add(v);Space(s,ref p);char end=s[p++];if(end==(obj?'}':']'))break;if(end!=',')throw new ArgumentException("JSON separator");}return result;}
        foreach(string word in new[]{"true","false","null"})if(p+word.Length<=s.Length&&string.CompareOrdinal(s,p,word,0,word.Length)==0){p+=word.Length;return word=="null"?null:(Json40)(word=="true");}
        int start=p;while(p<s.Length&&"-+0123456789.eE".IndexOf(s[p])>=0)p++;if(start==p)throw new ArgumentException("JSON token");return double.Parse(s.Substring(start,p-start),CultureInfo.InvariantCulture);
    }
}
public sealed class Obj40 : Json40 {public Obj40(){fields=new Dictionary<string,Json40>(StringComparer.Ordinal);}public new static Obj40 Parse(string text){return(Obj40)Json40.Parse(text);}}
public sealed class Arr40 : Json40 {public Arr40(params object[] values){items=new List<Json40>();if(values.Length==1&&values[0] is IEnumerable&&!(values[0] is string)&&!(values[0] is Json40)){foreach(var v in(IEnumerable)values[0])Add(Wrap(v));}else foreach(var v in values)Add(Wrap(v));}}

// Offline66 candidate: no Unity/API/thread/process/GC actions.

public class Json58 : IEnumerable<Json58>
{
    protected Dictionary<string,Json58> fields;protected List<Json58> items;protected object value;
    public Json58 this[string key] {get {Json58 v;return fields!=null&&fields.TryGetValue(key,out v)?v:null;}set {fields[key]=value;}}
    public Json58 this[int i] {get {return items[i];}}
    public int Count {get {return items!=null?items.Count:fields!=null?fields.Count:0;}}
    public void Add(Json58 v) {items.Add(v);}
    public IEnumerable<T> Values<T>() {return this.Select(v=>(T)Convert.ChangeType(v.value,typeof(T),CultureInfo.InvariantCulture));}
    public IEnumerator<Json58> GetEnumerator() {return (items??(fields==null?new List<Json58>():fields.Values.ToList())).GetEnumerator();}
    IEnumerator IEnumerable.GetEnumerator() {return GetEnumerator();}
    public static implicit operator Json58(string v) {return v==null?null:new Json58{value=v};}
    public static implicit operator Json58(int v) {return new Json58{value=v};}
    public static implicit operator Json58(long v) {return new Json58{value=v};}
    public static implicit operator Json58(float v) {return new Json58{value=(double)v};}
    public static implicit operator Json58(double v) {return new Json58{value=v};}
    public static implicit operator Json58(bool v) {return new Json58{value=v};}
    public static explicit operator string(Json58 v) {return v==null?null:Convert.ToString(v.value,CultureInfo.InvariantCulture);}
    public static explicit operator int(Json58 v) {return Convert.ToInt32(v.value,CultureInfo.InvariantCulture);}
    public static explicit operator long(Json58 v) {return Convert.ToInt64(v.value,CultureInfo.InvariantCulture);}
    public static explicit operator double(Json58 v) {return Convert.ToDouble(v.value,CultureInfo.InvariantCulture);}
    public static explicit operator bool(Json58 v) {return Convert.ToBoolean(v.value,CultureInfo.InvariantCulture);}
    public static Json58 Wrap(object v) {
        if(v==null)return null;if(v is Json58)return(Json58)v;if(v is string)return(string)v;if(v is bool)return(bool)v;
        if(v is double)return(double)v;if(v is float)return(float)v;if(v is int)return(int)v;if(v is long)return(long)v;
        if(v is IEnumerable){var a=new Arr58();foreach(var x in(IEnumerable)v)a.Add(Wrap(x));return a;}
        throw new ArgumentException("Unsupported JSON boundary value: "+v.GetType().Name);
    }
    static string Quote(string text) {
        var b=new StringBuilder("\"");foreach(char c in text){switch(c){case '"':b.Append("\\\"");break;case '\\':b.Append("\\\\");break;case '\b':b.Append("\\b");break;case '\f':b.Append("\\f");break;case '\n':b.Append("\\n");break;case '\r':b.Append("\\r");break;case '\t':b.Append("\\t");break;default:if(c<32)b.Append("\\u"+((int)c).ToString("x4"));else b.Append(c);break;}}return b.Append('"').ToString();
    }
    public override string ToString() {
        if(fields!=null)return "{"+string.Join(",",fields.OrderBy(p=>p.Key,StringComparer.Ordinal).Select(p=>Quote(p.Key)+":"+(p.Value==null?"null":p.Value.ToString())))+"}";
        if(items!=null)return "["+string.Join(",",items.Select(v=>v==null?"null":v.ToString()))+"]";
        if(value==null)return "null";if(value is string)return Quote((string)value);if(value is bool)return(bool)value?"true":"false";
        if(value is double){double x=(double)value;if(double.IsNaN(x)||double.IsInfinity(x))throw new ArgumentException("Nonfinite JSON number");return x.ToString("R",CultureInfo.InvariantCulture);}
        return Convert.ToString(value,CultureInfo.InvariantCulture);
    }
    public static bool DeepEquals(Json58 a,Json58 b) {return a==null?b==null:b!=null&&a.ToString()==b.ToString();}
    public const int MaxInputChars66=65536;
    public static Json58 Parse(string text) {if(text.Length>MaxInputChars66)throw new ArgumentException("Small JSON budget exceeded; use streaming verification");int p=0;var result=ParseValue(text,ref p,0);Space(text,ref p);if(p!=text.Length)throw new ArgumentException("Trailing JSON data");return result;}
    static void Space(string s,ref int p) {while(p<s.Length&&char.IsWhiteSpace(s[p]))p++;}
    static string ParseString(string s,ref int p) {
        if(s[p++]!='"')throw new ArgumentException("JSON string expected");var b=new StringBuilder();
        while(p<s.Length){char c=s[p++];if(c=='"')return b.ToString();if(c=='\\'){char e=s[p++];switch(e){case '"':case '\\':case '/':b.Append(e);break;case 'b':b.Append('\b');break;case 'f':b.Append('\f');break;case 'n':b.Append('\n');break;case 'r':b.Append('\r');break;case 't':b.Append('\t');break;case 'u':b.Append((char)int.Parse(s.Substring(p,4),NumberStyles.HexNumber,CultureInfo.InvariantCulture));p+=4;break;default:throw new ArgumentException("JSON escape");}}else{if(c<32)throw new ArgumentException("JSON control character");b.Append(c);}}
        throw new ArgumentException("Unterminated JSON string");
    }
    static Json58 ParseValue(string s,ref int p,int depth) {
        if(depth>128)throw new ArgumentException("JSON nesting limit");Space(s,ref p);if(p>=s.Length)throw new ArgumentException("JSON value expected");char c=s[p];
        if(c=='"')return ParseString(s,ref p);
        if(c=='{'||c=='['){bool obj=c=='{';p++;Json58 result=obj?(Json58)new Obj58():new Arr58();Space(s,ref p);if(p<s.Length&&s[p]==(obj?'}':']')){p++;return result;}
            while(true){Space(s,ref p);string key=null;if(obj){key=ParseString(s,ref p);if(result.fields.ContainsKey(key))throw new ArgumentException("Duplicate JSON member");Space(s,ref p);if(s[p++]!=':')throw new ArgumentException("JSON colon");}var v=ParseValue(s,ref p,depth+1);if(obj)result[key]=v;else result.Add(v);Space(s,ref p);char end=s[p++];if(end==(obj?'}':']'))break;if(end!=',')throw new ArgumentException("JSON separator");}return result;}
        foreach(string word in new[]{"true","false","null"})if(p+word.Length<=s.Length&&string.CompareOrdinal(s,p,word,0,word.Length)==0){p+=word.Length;return word=="null"?null:(Json58)(word=="true");}
        int start=p;while(p<s.Length&&"-+0123456789.eE".IndexOf(s[p])>=0)p++;if(start==p)throw new ArgumentException("JSON token");return double.Parse(s.Substring(start,p-start),CultureInfo.InvariantCulture);
    }
}
public sealed class Obj58 : Json58 {public Obj58(){fields=new Dictionary<string,Json58>(StringComparer.Ordinal);}public new static Obj58 Parse(string text){return(Obj58)Json58.Parse(text);}}
public sealed class Arr58 : Json58 {public Arr58(params object[] values){items=new List<Json58>();if(values.Length==1&&values[0] is IEnumerable&&!(values[0] is string)&&!(values[0] is Json58)){foreach(var v in(IEnumerable)values[0])Add(Wrap(v));}else foreach(var v in values)Add(Wrap(v));}}

// Offline66 candidate: no Unity/API/thread/process/GC actions.

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

// Source binding only. No camera, renderer mutation, RGB fallback or role constants.

public sealed class RendererFamily59
{
    public sealed class Spec {public int rendererOrdinal,subMesh,bindingOrdinal,triangleCount,materialId;public string sourceFamilyId,meshUVSHA256,indexSHA256;}
    public sealed class Draw {public Spec source;public Material material;public Texture2D texture;public Color factor;public Vector2 scale,offset;}
    readonly Draw[] draws;
    public Draw[] Draws {get{return draws;}}
    static string Hash(byte[] b){using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(b)).Replace("-","").ToLowerInvariant();}
    public RendererFamily59(SkinnedMeshRenderer[] sources,Spec[] specs){
        var uvHashes=new Dictionary<UnityEngine.Mesh,string>();draws=new Draw[specs.Length];
        foreach(var s in specs){
            var renderer=sources[s.rendererOrdinal];var mesh=renderer.sharedMesh;if(!mesh||!mesh.isReadable)throw new InvalidOperationException("Source mesh unavailable");
            if(!uvHashes.ContainsKey(mesh)){var uv=new List<Vector2>();mesh.GetUVs(0,uv);using(var memory=new MemoryStream()){using(var w=new BinaryWriter(memory,System.Text.Encoding.UTF8,true))foreach(var v in uv){w.Write(v.x);w.Write(v.y);}uvHashes[mesh]=Hash(memory.ToArray());}}
            var indices=mesh.GetIndices(s.subMesh);string indexHash;using(var memory=new MemoryStream()){using(var w=new BinaryWriter(memory,System.Text.Encoding.UTF8,true))foreach(int v in indices)w.Write((uint)v);indexHash=Hash(memory.ToArray());}
            if(uvHashes[mesh]!=s.meshUVSHA256||indexHash!=s.indexSHA256||indices.Length/3!=s.triangleCount)throw new InvalidOperationException("Source geometry identity changed");
            var material=renderer.sharedMaterials[s.subMesh];var texture=material.mainTexture as Texture2D;
            if(!material.HasProperty("_Color")||!material.HasProperty("_MainTex"))throw new NotSupportedException("Source base-colour/UV shader contract unavailable");
            draws[s.bindingOrdinal]=new Draw {source=s,material=material,texture=texture,factor=material.GetColor("_Color"),
                scale=material.GetTextureScale("_MainTex"),offset=material.GetTextureOffset("_MainTex")};
        }
    }
    static double Wrap(double v,TextureWrapMode mode){if(mode==TextureWrapMode.Repeat)return v-Math.Floor(v);if(mode==TextureWrapMode.Clamp)return Math.Max(0,Math.Min(1,v));if(mode==TextureWrapMode.Mirror){v-=2*Math.Floor(v/2);return v<=1?v:2-v;}throw new NotSupportedException("Texture wrap mode");}
    // UV must already be the effective shader UV (ST/animation applied by producer).
    public bool TryReadSourcePoint(int draw,int localPrimitive,Vector2 uv,out Color32 rgba,out Vector2Int texel,out string reason){
        rgba=new Color32();texel=new Vector2Int();reason=null;
        if(draw<0||draw>=draws.Length||draws[draw]==null){reason="unbound-draw";return false;}var d=draws[draw];
        if(localPrimitive<0||localPrimitive>=d.source.triangleCount){reason="primitive-out-of-range";return false;}
        if(float.IsNaN(uv.x)||float.IsInfinity(uv.x)||float.IsNaN(uv.y)||float.IsInfinity(uv.y)){reason="nonfinite-uv";return false;}
        if(!d.texture||!d.texture.isReadable){reason="source-texture-unreadable";return false;}
        try{int x=Math.Min(d.texture.width-1,(int)Math.Floor(Wrap(uv.x,d.texture.wrapModeU)*d.texture.width)),y=Math.Min(d.texture.height-1,(int)Math.Floor(Wrap(uv.y,d.texture.wrapModeV)*d.texture.height));texel=new Vector2Int(x,y);rgba=d.texture.GetPixel(x,y);return true;}
        catch(Exception e){reason=e.GetType().Name;return false;}
    }
    // Actual flattened draw order. Material/primitive IDs are provenance, not palette constants.
    public uint[] PackDrawDescriptors(){var words=new uint[draws.Length*4];for(int i=0;i<draws.Length;i++){var d=draws[i];words[i*4]=(uint)i+1;words[i*4+1]=(uint)d.source.rendererOrdinal;words[i*4+2]=(uint)d.source.subMesh;words[i*4+3]=(uint)d.source.triangleCount;}return words;}
}


// Source registration is independent of visible raster, lighting and hair.
// This is an eye-socket skin region, NOT one family for the entire skin material.
public sealed class SkinSource101 {
 public readonly Vector4[] linearPalette=new Vector4[16];
 public readonly Obj58 Info; public readonly int Steps;
 public SkinSource101(EyeFeature348 eye,string registry){
  var root=Json58.Parse(File.ReadAllText(registry));var specs=root["bindings"].Select(b=>new RendererFamily59.Spec{rendererOrdinal=(int)b["rendererOrdinal"],subMesh=(int)b["subMesh"],bindingOrdinal=(int)b["bindingOrdinal"],triangleCount=(int)b["triangleCount"],materialId=(int)b["materialId"],sourceFamilyId=(string)b["sourceFamilyId"],meshUVSHA256=(string)b["meshUVSHA256"],indexSHA256=(string)b["indexSHA256"]}).ToArray();
  var binding=new RendererFamily59(eye.full.motion.surface.source,specs);
  // Resolve the existing source role contract; do not infer role from RGB/name.
  int skinRole=3,sourceRenderer=1;var source=eye.full.motion.surface.source[sourceRenderer];
  var skinDraw=binding.Draws.Select((d,i)=>new{d,i}).Where(x=>x.d.source.rendererOrdinal==sourceRenderer&&Mathf.RoundToInt(eye.full.independentMats[x.d.source.bindingOrdinal].GetFloat("_Auto245Role"))==skinRole).ToArray();
  if(skinDraw.Length!=1)throw new InvalidOperationException("101 source skin semantic binding is ambiguous");
  var selected=skinDraw[0];var draw=selected.d;var mesh=source.sharedMesh;var indices=mesh.GetIndices(draw.source.subMesh);var uv=mesh.uv;
  Steps=eye.full.faceShadeSteps;if(Steps<2||Steps>8)throw new InvalidOperationException("101 bounded palette needs 2..8 configured face steps");
  var all=new Arr58();
  foreach(var modelEye in eye.modelEyes.OrderBy(e=>e.stableId)){
   if(!modelEye.boundaryClosed||modelEye.closedBoundary==null)throw new InvalidOperationException("101 needs actual native closed skin boundary");
   var samples=new List<SourcePalette58.Sample>();var rows=new Arr58();
   foreach(int vertex in modelEye.closedBoundary.Distinct().OrderBy(v=>v)){
    int at=Array.IndexOf(indices,vertex);if(at<0)throw new InvalidOperationException("101 eye boundary is not in source skin domain");int triangle=at/3;
    var effective=Vector2.Scale(uv[vertex],draw.scale)+draw.offset;Color32 colour;Vector2Int texel;string reason;
    if(!binding.TryReadSourcePoint(selected.i,triangle,effective,out colour,out texel,out reason))throw new InvalidOperationException("101 source point unavailable: "+reason);
    var sample=new SourcePalette58.Sample{id="native-vertex-"+vertex.ToString("D6"),imageSHA256=(string)root["bindings"][selected.i]["imageSHA256"],materialId=draw.source.materialId,primitiveId=draw.source.subMesh,triangle=triangle,uv=new double[]{effective.x,1-effective.y},texel=new[]{texel.x,draw.texture.height-1-texel.y},rgba8=new[]{(int)colour.r,colour.g,colour.b,colour.a},weight=1};samples.Add(sample);
    rows.Add(new Obj58{["vertex"]=vertex,["triangle"]=triangle,["effectiveUVBottomLeft"]=new Arr58(effective.x,effective.y),["texelTopLeft"]=new Arr58(sample.texel),["sourceRGBA8"]=new Arr58(sample.rgba8)});
   }
   var family=new SourcePalette58.Family{id=draw.source.sourceFamilyId+"/native-socket-ring/"+modelEye.stableId,domainId="native-skin-boundary/"+modelEye.stableId,source=new SourcePalette58.Source{modelSHA256=(string)root["modelSHA256"],imageSHA256=(string)root["bindings"][selected.i]["imageSHA256"],materialId=draw.source.materialId,factorLinear=new double[]{draw.factor.r,draw.factor.g,draw.factor.b,draw.factor.a}},samples=samples.ToArray()};
   var reference=SourcePalette58.ExtractReference(family);var lin=reference.rgb8.Select(v=>SourcePalette58.Decode(v/255.0)).ToArray();var tint=eye.full.faceShadeChromaticity;
   var endpoint=new[]{lin[0]*.72*tint.x,lin[1]*.72*tint.y,lin[2]*.72*tint.z};var dark=SourcePalette58.LabLinear(endpoint);var bright=SourcePalette58.LabRGB(reference.rgb8);double c0=Math.Sqrt(bright[1]*bright[1]+bright[2]*bright[2]),c1=Math.Sqrt(dark[1]*dark[1]+dark[2]*dark[2]);
   var settings=new SourcePalette58.Settings{count=Steps,darkLRatio=Math.Min(1,dark[0]/bright[0]),darkCRatio=c0>1e-12?Math.Min(1,c1/c0):1,gamma=1,intervalScale=1};
   var palette=SourcePalette58.MakePalette(reference,settings);if(palette.LReversals!=0)throw new InvalidOperationException("101 source palette L reversed");
   int offset=(modelEye.stableId-1)*8;if(offset<0||offset+Steps>linearPalette.Length)throw new InvalidOperationException("101 unsupported stable eye slot");
   for(int k=0;k<Steps;k++){var rgb=palette.rgb8[k];linearPalette[offset+k]=new Vector4((float)SourcePalette58.Decode(rgb[0]/255.0),(float)SourcePalette58.Decode(rgb[1]/255.0),(float)SourcePalette58.Decode(rgb[2]/255.0),1);}
   all.Add(new Obj58{["eyeId"]=modelEye.stableId,["sourceFamily"]=family.id,["sourceMaterialId"]=family.source.materialId,["sourceImageSHA256"]=family.source.imageSHA256,["ringSamples"]=rows,["referenceSampleId"]=reference.sample.id,["referenceRGB8"]=new Arr58(reference.rgb8),["paletteRGB8"]=new Arr58(palette.rgb8.Select(p=>new Arr58(p))),["darkLRatio"]=settings.darkLRatio,["darkCRatio"]=settings.darkCRatio,["gamma"]=1,["intervalScale"]=1,["duplicates"]=palette.duplicates,["LReversals"]=palette.LReversals});
  }
  Info=new Obj58{["sourceModelSHA256"]=root["modelSHA256"],["skinDrawBinding"]=selected.i,["skinSourceSubmesh"]=draw.source.subMesh,["sourceRoleContract"]=skinRole,["eyes"]=all,["spacingProvenance"]="Existing face .72 floor and faceShadeChromaticity converted to OKLCH endpoint; fixed source hue, no final RGB lighting multiplication",["steps"]=Steps,["indexRange"]=new Arr58(0,Steps-1),["outlineSlots"]=0,["scope"]="socket skin only; full-face region resolver not implemented by this adapter",["sourceSampling"]="original native skin boundary vertices; point UV; exact source factor; no screenshot colour"};
 }
}


// Own offscreen forward canvas. It never reads product77/295/348/98 colour.

public sealed class StaticPalette154:IDisposable {
 public sealed class Binding {public int ordinal,renderer,submesh,material,regionBase;public Texture2D address,palette;public int width,height,levels;public string image,addressPath;public float[] paletteLinear;public Texture source;public Material original;public Vector2 scale,offset;}
 public readonly Binding[] bindings;public readonly Obj40 Info;public int RegionCount{get;}bool disposed;
 static string Hash(byte[] b){using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(b)).Replace("-","").ToLowerInvariant();}
 public StaticPalette154(EyeFeature348 eye,string root,SkinSource101 originalSkin){
  var spec=Json40.Parse(File.ReadAllText(Path.Combine(root,"STATIC154.json")));
  if(Hash(File.ReadAllBytes(Path.GetFullPath((string)spec["sourceModel"])))!=(string)spec["modelSHA256"]||eye.full.motion.surface.source.Length!=3)throw new InvalidOperationException("154 actual source model mismatch");
  var rows=spec["bindings"].ToArray();bindings=new Binding[rows.Length];var evidence=new Arr40();
  var skinSettings=originalSkin.Info["eyes"].First();double faceL=(double)skinSettings["darkLRatio"],faceC=(double)skinSettings["darkCRatio"],floor=eye.full.motion.animation.shadeProfile.x;
  if(floor<0||floor>1||!SourcePalette58.Finite(floor))throw new InvalidOperationException("154 actual surface spacing outside palette contract");
  int regionBase=0;
  try{for(int i=0;i<rows.Length;i++){
   var r=rows[i];int renderer=(int)r["rendererOrdinal"],sub=(int)r["subMesh"];var original=eye.full.motion.surface.source[renderer].sharedMaterials[sub];var tex=original.GetTexture("_MainTex");
   int levels=renderer==1?eye.full.faceShadeSteps:eye.full.surfaceShadeSteps;int w=(int)r["width"],h=(int)r["height"];
   if((int)r["bindingOrdinal"]!=i||!tex||tex.width!=w||tex.height!=h||levels<2||levels>8||original.GetColor("_Color")!=Color.white||original.mainTextureScale!=Vector2.one||original.mainTextureOffset!=Vector2.zero||AssetDatabase.GetAssetPath(tex)!=(string)spec["sourceModel"])throw new InvalidOperationException("154 material/image/factor/sampler contract changed");
   foreach(string key in new[]{"_UvAnimScrollXSpeed","_UvAnimScrollYSpeed","_UvAnimRotationSpeed"})if(original.HasProperty(key)&&original.GetFloat(key)!=0)throw new InvalidOperationException("154 animated UV needs cache invalidation");
   var binding=new Binding{ordinal=i,renderer=renderer,submesh=sub,material=(int)r["materialId"],width=w,height=h,levels=levels,image=(string)r["imageSHA256"],source=tex,original=original,scale=original.mainTextureScale,offset=original.mainTextureOffset};bindings[i]=binding;
   binding.addressPath=Path.Combine(root,"static",(string)r["addressFile"]);var bytes=File.ReadAllBytes(binding.addressPath);if(bytes.Length!=(long)w*h||Hash(bytes)!=(string)r["addressSHA256"])throw new InvalidOperationException("154 immutable UV map hash");
   binding.address=new Texture2D(w,h,TextureFormat.R8,false,true){name="154 owned original UV prototypes "+i,hideFlags=HideFlags.HideAndDontSave,filterMode=FilterMode.Point,wrapModeU=tex.wrapModeU,wrapModeV=tex.wrapModeV};binding.address.SetPixelData(bytes,0);binding.address.Apply(false,true);
   var prototypes=r["prototypes"].ToArray();var rgba=new float[levels*prototypes.Length*4];var actualTables=new Arr40();
   // Leave 0 for an empty/unbound sample; every material-local row has a distinct canvas ID.
   binding.regionBase=regionBase;
   regionBase+=prototypes.Length;
   var settings=new SourcePalette58.Settings{count=levels,darkLRatio=renderer==1?faceL:Math.Pow(floor,1.0/3),darkCRatio=renderer==1?faceC:Math.Pow(floor,1.0/3),gamma=1,intervalScale=1};
   for(int f=0;f<prototypes.Length;f++){
    string id=(string)prototypes[f]["family"];var rgb=prototypes[f]["rgb8"].Select(x=>(int)x).ToArray();var reference=new SourcePalette58.Reference{rgb8=rgb,lab=SourcePalette58.LabRGB(rgb)};var table=SourcePalette58.MakePalette(reference,settings);actualTables.Add(new Obj40{["family"]=id,["rgb8"]=new Arr40(table.rgb8.Select(v=>new Arr40(v)))});
    // Reuse SourcePalette58's conversion; shader performs Load, no RGB*light.
    for(int k=0;k<levels;k++){for(int c=0;c<3;c++)rgba[4*(f*levels+k)+c]=(float)SourcePalette58.Decode(table.rgb8[k][c]/255.0);rgba[4*(f*levels+k)+3]=1;}
   }
   binding.paletteLinear=rgba;binding.palette=new Texture2D(levels,prototypes.Length,TextureFormat.RGBAFloat,false,true){name="154 owned SourcePalette58 LUT "+i,hideFlags=HideFlags.HideAndDontSave,filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp};binding.palette.SetPixelData(rgba,0);binding.palette.Apply(false,true);
   evidence.Add(new Obj40{["binding"]=i,["renderer"]=renderer,["submesh"]=sub,["material"]=binding.material,["imageSHA256"]=binding.image,["prototypes"]=prototypes.Length,["levels"]=levels,["firstCanvasRegion"]=binding.regionBase+1,["addressSHA256"]=r["addressSHA256"],["darkLRatio"]=settings.darkLRatio,["darkCRatio"]=settings.darkCRatio,["paletteRGB8"]=actualTables});
  }}catch{Dispose();throw;}
  RegionCount=regionBase;
  Info=new Obj40{["sourceModelSHA256"]=spec["modelSHA256"],["bindings"]=evidence,["perFrameColourIntegration"]=false,["RGBLightingMultiply"]=false,["staticPaletteAllocatedOnce"]=true,["colourRegionIsVisibilityOwner"]=false,["surfaceLinearFloorProvenance"]=floor,["faceSpacingProvenance"]="unchanged SkinSource101/SourcePalette58 actual native skin reference settings",["AAAndWeakTonePolicy"]="Argon2.2 hard nearest observed medoid; not every source gradient preserved"};
 }
 public Binding Get(int renderer,int submesh){if(disposed)throw new ObjectDisposedException(nameof(StaticPalette154));return bindings.Single(b=>b.renderer==renderer&&b.submesh==submesh);}
 static void BindShade(Material owned,int levels){
  if(levels<2||levels>8)throw new ArgumentOutOfRangeException(nameof(levels));
  var a=Vector4.one*2;var b=Vector4.one*2;
  for(int i=0;i<levels-1;i++){float cut=(float)((i+.5)/(levels-1));if(i<4)a[i]=cut;else b[i-4]=cut;}
  owned.SetVector("_ShadeCuts154A",a);owned.SetVector("_ShadeCuts154B",b);
 }
 public void BindSocket(Material white,Material iris,SkinSource101 original){
  var skin=Get(1,3);var bytes=File.ReadAllBytes(skin.addressPath);var palette=new Vector4[16];var evidence=new Arr40();
  if(original.Steps!=skin.levels)throw new InvalidOperationException("154 socket and native skin shade labels differ");
  foreach(var e in original.Info["eyes"]){int eye=(int)e["eyeId"];string sid=(string)e["referenceSampleId"];int vertex=Int32.Parse(sid.Substring("native-vertex-".Length),CultureInfo.InvariantCulture);var sample=e["ringSamples"].Single(t=>(int)t["vertex"]==vertex);int x=(int)sample["texelTopLeft"][0],y=skin.height-1-(int)sample["texelTopLeft"][1];int family=bytes[y*skin.width+x]-1;if(family<0||family>=skin.palette.height)throw new InvalidOperationException("154 socket true-skin witness has no region");for(int q=0;q<skin.levels;q++){int j=4*(family*skin.levels+q);palette[(eye-1)*8+q]=new Vector4(skin.paletteLinear[j],skin.paletteLinear[j+1],skin.paletteLinear[j+2],1);}evidence.Add(new Obj40{["eye"]=eye,["sourceSkinVertex"]=vertex,["texelBottomLeft"]=new Arr40(x,y),["sourceColourRegion"]=family+1});}
  white.SetVectorArray("_Palette101",palette);iris.SetVectorArray("_Palette101",palette);BindShade(white,skin.levels);BindShade(iris,skin.levels);Info["socketSourceWitnesses"]=evidence;Info["socketUsesSameSkinRegionLUT"]=true;
 }
 public void Bind(Material owned,int renderer,int submesh){var b=Get(renderer,submesh);if(b.original.GetTexture("_MainTex")!=b.source||b.original.mainTextureScale!=b.scale||b.original.mainTextureOffset!=b.offset)throw new InvalidOperationException("154 source changed; recreate model/view owner");owned.SetTexture("_Region154",b.address);owned.SetTexture("_Palette154",b.palette);owned.SetVector("_Size154",new Vector4(b.width,b.height,b.levels,b.palette.height));owned.SetVector("_Wrap154",new Vector4((int)b.source.wrapModeU,(int)b.source.wrapModeV,0,0));owned.SetInt("_Binding154",b.ordinal);owned.SetInt("_Static154",1);if(owned.HasProperty("_RegionBase154"))owned.SetInt("_RegionBase154",b.regionBase);BindShade(owned,b.levels);}
 public IEnumerable<UnityEngine.Object> OwnedTextures() =>
  bindings.Where(b=>b!=null).SelectMany(b=>new UnityEngine.Object[]{b.address,b.palette});
 public void Dispose(){if(disposed)return;disposed=true;if(bindings!=null)foreach(var b in bindings)if(b!=null){if(b.address)UnityEngine.Object.DestroyImmediate(b.address);if(b.palette)UnityEngine.Object.DestroyImmediate(b.palette);b.address=null;b.palette=null;}}
}

public sealed class IntegratedCanvas154:IDisposable {
 readonly EyeFeature348 eye;readonly StaticPalette154 source;readonly Material[] materials;
 readonly bool useStockRamp,lightTrace;
 readonly Vector4[] stockRamp=new Vector4[8];
 Vector4 boundStockLit,boundStockShade;int boundStockLevels;
 // IDs in the alpha component of the existing full-canvas light attachment.
 // SourceHair is a material binding only. The rasterized sample emits FrontHair or BackHair.
 enum PartGroup { Unassigned=0, BackHair=1, BodySkin=2, Stocking=3, Top=4, Bottom=5, Shoes=6, FaceSkin=7, Eye=8, Eyebrow=9, FrontHair=10, SourceHair=11 }
 public RTHandle[] fields;RTHandle depth,nonHairMeta;public bool Hair=true;public bool Disposed{get;private set;}
 RTHandle directionalWorld,directionalSelf;
 public RTHandle NonHairMeta=>Hair?nonHairMeta:fields[1];
 public Rect? ObservationWindow {get;set;}
 public int RenderedFrame{get;private set;}=-1;public double RecordCPUms{get;private set;}
 sealed class Data{public IntegratedCanvas154 owner;public bool hair,clear,complete;public Rect? window;}
 sealed class CopyData{public TextureHandle source,destination;}
 public IntegratedCanvas154(EyeFeature348 e,StaticPalette154 src,bool lightTrace=false,bool useStockRamp=true,Shader validationShader=null,bool deferTargets=false){eye=e;source=src;this.useStockRamp=useStockRamp;this.lightTrace=lightTrace;materials=new Material[src.bindings.Length];
  var shader=validationShader?validationShader:AssetDatabase.LoadAssetAtPath<Shader>("Assets/EUnityValidation01/Integrated154/LayerZero157.shader");
  if(!shader||!shader.isSupported||ShaderUtil.ShaderHasError(shader))throw new InvalidOperationException("154 imported source/final shader unavailable");
  try{
   for(int i=0;i<materials.Length;i++){var b=src.bindings[i];var m=new Material(b.original){shader=shader,name="154 owned source material "+i,hideFlags=HideFlags.HideAndDontSave};materials[i]=m;m.shaderKeywords=b.original.shaderKeywords;if(lightTrace&&shader.keywordSpace.FindKeyword("_T2_LIGHT_TRACE154").isValid)m.EnableKeyword("_T2_LIGHT_TRACE154");source.Bind(m,b.renderer,b.submesh);m.SetInt("_Full154",1);m.SetInt("_Proxy101",0);m.SetInt("_Steps101",b.levels);m.SetInt("_PartGroup154",(int)SourceGroup(b.material));}
   if(deferTargets){
    if(!lightTrace||!shader.keywordSpace.FindKeyword("_T2_SPLIT_DIRECTIONAL154").isValid)
     throw new InvalidOperationException("154 split raster variant is unavailable before target allocation");
    foreach(var material in materials){
     material.EnableKeyword("_T2_SPLIT_DIRECTIONAL154");
     ShaderUtil.CompilePass(material,0,true);
     if(!ShaderUtil.IsPassCompiled(material,0)||ShaderUtil.ShaderHasError(shader))
      throw new InvalidOperationException("154 split raster variant failed before target allocation");
    }
   }else AllocateTargets();
  }catch{Dispose();throw;}
 }
  RectInt? nativeCrop154;
  public void AllocateTargets(RectInt? nativeCrop = null){
  if(Disposed||fields!=null||nonHairMeta!=null)throw new InvalidOperationException("154 targets cannot be allocated twice");
   if(nativeCrop.HasValue){
    var c=nativeCrop.Value;
    if(SystemInfo.graphicsDeviceType!=GraphicsDeviceType.Direct3D11 ||
        c.x<0||c.y<0||c.width<1||c.height<1||c.xMax>960||c.yMax>544||
        (long)c.width*c.height>480L*272)
     throw new InvalidOperationException("154 native character crop is outside the D3D11 allocation budget");
   }
   nativeCrop154=nativeCrop;
   var rasterSize=nativeCrop?.size??new Vector2Int(480,272);
   try{
    nonHairMeta=Target("154 owned same-ray non-hair depth and binding");
   for(int i=0;i<materials.Length;i++)if(source.bindings[i].renderer==2)materials[i].SetTexture("_UnderHair154",nonHairMeta);
   fields=new RTHandle[lightTrace?7:4];
   for(int i=0;i<fields.Length;i++)fields[i]=Target("154 owned full source "+i);
   depth=RTHandles.Alloc(rasterSize.x,rasterSize.y,depthBufferBits:DepthBits.Depth32,name:"154 owned full source depth");
  }catch{Dispose();throw;}
 }
  RTHandle Target(string name){
   var size=nativeCrop154?.size??new Vector2Int(480,272);
   return RTHandles.Alloc(size.x,size.y,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,filterMode:FilterMode.Point,name:name);
  }

  Matrix4x4 CropNativeCharacter154(Matrix4x4 fullGpuVP,RectInt region){
   // Use the evaluated, pre-quantization vertices. A crop that could cut
   // a surface may not be submitted even if last frame's silhouette fitted.
   foreach(var surface in eye.full.motion.surface.outputs){
    if(!surface||!surface.sharedMesh)throw new InvalidOperationException("154 native input surface is missing");
    var objectToClip=fullGpuVP*surface.transform.localToWorldMatrix;
    var bounds=surface.sharedMesh.bounds;
    for(int corner=0;corner<8;corner++){
     var v=bounds.center+Vector3.Scale(bounds.extents,new Vector3(
      (corner&1)==0?-1:1,(corner&2)==0?-1:1,(corner&4)==0?-1:1));
     var clip=objectToClip*new Vector4(v.x,v.y,v.z,1);
     if(!(clip.w>0)||!float.IsFinite(clip.w))
      throw new InvalidOperationException("154 native input has no valid conservative projection");
     float x=(1+clip.x/clip.w)*480, y=(1-clip.y/clip.w)*272;
     if(!float.IsFinite(x)||!float.IsFinite(y)||x<region.x+1||x>=region.xMax-1||y<region.y+1||y>=region.yMax-1)
      throw new InvalidOperationException("154 native input crop would cut a character surface");
    }
   }
   var crop=Matrix4x4.identity;
   crop.m00=960f/region.width;
   crop.m03=(960f-2*region.x-region.width)/region.width;
   crop.m11=544f/region.height;
   crop.m13=(2*region.y+region.height-544f)/region.height;
   return crop*fullGpuVP;
  }
 public void BindDirectionalShadows(RTHandle world,RTHandle self,Matrix4x4 worldToShadow,Matrix4x4 selfToShadow){
  if(Disposed||fields.Length!=7||!materials[0].shader.keywordSpace.FindKeyword("_T2_SPLIT_DIRECTIONAL154").isValid)
   throw new InvalidOperationException("154 isolated directional shadow variant is unavailable");
  int dimension=world.rt.width;
  if(dimension!=world.rt.height||dimension!=self.rt.width||dimension!=self.rt.height)
   throw new InvalidOperationException("154 directional map dimensions differ");
  directionalWorld=world;directionalSelf=self;
  foreach(var material in materials){
   material.EnableKeyword("_T2_SPLIT_DIRECTIONAL154");
   material.SetTexture("_DirectionalWorld154",world);material.SetTexture("_DirectionalSelf154",self);
   material.SetFloat("_DirectionalMapSize154",dimension);
   material.SetMatrix("_WorldToDirectional154",worldToShadow);material.SetMatrix("_SelfToDirectional154",selfToShadow);
  }
 }
 static PartGroup SourceGroup(int role)=>role switch {
  0 => PartGroup.Unassigned, // Mouth has no approved group in this node.
  1 or 2 or 4 or 6 => PartGroup.Eye,
  3 => PartGroup.FaceSkin,
  5 => PartGroup.Eyebrow,
  7 => PartGroup.BodySkin, // Shader uses the original per-UV stocking membership.
  8 => PartGroup.Bottom,
  9 => PartGroup.Shoes,
  10 => PartGroup.Top,
  11 or 12 or 13 or 14 => PartGroup.SourceHair,
  _ => throw new InvalidOperationException("154 source material role has no part-group binding")
 };
 public Matrix4x4 RasterVP {get;private set;}
 void BindStock(Material material,Full319View335 main,int levels){
  material.SetTexture("_StockPartMember154",main.stockMember);
  if(!useStockRamp||!material.HasProperty("_StockRampReady154"))return;
  if(levels==boundStockLevels&&main.stockShade.Equals(boundStockShade)&&main.stockLit.Equals(boundStockLit))return;
  if(levels<2||levels>stockRamp.Length||source.RegionCount>=71)throw new InvalidOperationException("154 stocking LUT address conflict");
  var lit=main.stockLit;var shade=main.stockShade;
  for(int i=0;i<3;i++)if(!float.IsFinite(lit[i])||!float.IsFinite(shade[i])||shade[i]<0||lit[i]<shade[i])
   throw new InvalidOperationException("154 invalid authored stocking endpoints");
  if(lit.x==shade.x&&lit.y==shade.y&&lit.z==shade.z)throw new InvalidOperationException("154 stocking endpoints do not distinguish shade");
  for(int q=0;q<stockRamp.Length;q++){
   int last=levels-1;
   stockRamp[q]=q==0?shade:q>=last?lit:Vector4.LerpUnclamped(shade,lit,q/(float)last);
  }
  material.SetVectorArray("_StockRamp154",stockRamp);material.SetInt("_StockRampReady154",1);
  boundStockLit=lit;boundStockShade=shade;boundStockLevels=levels;
 }
 Matrix4x4 CanvasDepthProjection(Matrix4x4 view,Camera camera){
  // The canvas contains only the character. Keep hardware Z within the evaluated
  // character bounds; world/occluder comparisons still use the unmodified view depth.
  var surfaces=eye.full.motion.surface.outputs;
  float min=float.PositiveInfinity,max=float.NegativeInfinity;
  foreach(var surface in surfaces){
   var bounds=surface.sharedMesh.bounds;
   var localToView=view*surface.transform.localToWorldMatrix;
   float centre=localToView.MultiplyPoint3x4(bounds.center).z;
   var extents=bounds.extents;
   float radius=Mathf.Abs(localToView.m20)*extents.x+Mathf.Abs(localToView.m21)*extents.y+Mathf.Abs(localToView.m22)*extents.z;
   min=Mathf.Min(min,centre-radius);max=Mathf.Max(max,centre+radius);
  }
  float span=max-min;
  if(!float.IsFinite(span)||span<=0)throw new InvalidOperationException("154 evaluated depth bounds are empty");
  if(max>=-camera.nearClipPlane||min<=-camera.farClipPlane)return RasterVP;
  // Include rounding slack around the conservative box, with no depth clip at a box face.
  float centreZ=min+span*.5f;
  float scale=(SystemInfo.usesReversedZBuffer?1f:-1f)/(span*1.5f);
  var depthVP=RasterVP;
  depthVP.SetRow(2,view.GetRow(2)*scale+new Vector4(0,0,0,.5f-centreZ*scale));
  return depthVP;
 }
 public void Record(RenderGraph graph,UniversalResourceData res,bool hairOnlyEvidence=false){if(Disposed)throw new ObjectDisposedException(nameof(IntegratedCanvas154));double start=EditorApplication.timeSinceStartup;var main=NativePlayer395.Active.host.main;var mainCamera=main.motion.camera;var mainView=mainCamera.worldToCameraMatrix;
  if(main.motion.mode!=2||!main.motion.actorLocalGrid||!mainCamera.orthographic||!main.stockMember)
   throw new InvalidOperationException("154 requires the actor-local orthographic grid and source stocking membership");
  // effectiveProjection already has the inverse root phase from MotionView331.
  // Submit body and head to that same clip matrix, without a second head pivot
  // or rounded join. This canvas uses the same evaluated surface for all parts.
  RasterVP=GL.GetGPUProjectionMatrix(main.effectiveProjection,true)*mainView;
   float rasterScale=1f;
   var rasterROI=new Vector4(0,0,480,272);
   if(nativeCrop154.HasValue){
    var region=nativeCrop154.Value;
    if(ObservationWindow.HasValue)throw new InvalidOperationException("154 low-resolution scissor cannot be applied to the native crop");
    RasterVP=CropNativeCharacter154(RasterVP,region);
    rasterScale=2f;
    // The lighting helpers expect the same 480-space screen UV and derivative scale.
    rasterROI=new Vector4(region.x*.5f,region.y*.5f,region.width*.5f,region.height*.5f);
   }
   var depthVP=CanvasDepthProjection(mainView,mainCamera);
  foreach(var b in source.bindings){var m=materials[b.ordinal];source.Bind(m,b.renderer,b.submesh);m.SetMatrix("_ProbeGPUVP91",RasterVP);m.SetMatrix("_DepthGPU154",depthVP);m.SetMatrix("_View154",mainView);m.SetVector("_Shift154",Vector4.zero);if(b.material==7)BindStock(m,main,b.levels);m.SetFloat("_RasterScale91",rasterScale);m.SetVector("_ROI348",rasterROI);m.SetVector("_SurfaceInvRaster335",new Vector4(1f/480,1f/272,0,0));m.SetFloat("_FaceShadeSteps335",main.faceShadeSteps);m.SetFloat("_SurfaceShadeSteps335",main.surfaceShadeSteps);m.SetInt("_SurfaceMaskReady335",0);m.SetFloat("_BindSH91",0);}
  RecordSurfaces(graph,res,hair:false,clear:true,complete:!Hair,skipSurfaces:hairOnlyEvidence);
  if(Hair){
   // Copy the exact shader-produced z/binding texel before the shared depth is
   // continued. A texture cannot be sampled while it is also a colour attachment.
   using(var copy=graph.AddUnsafePass<CopyData>("154 preserve same-ray non-hair metadata",out var d)){
    d.source=graph.ImportTexture(fields[1]);d.destination=graph.ImportTexture(nonHairMeta);
    copy.UseTexture(d.source,AccessFlags.Read);copy.UseTexture(d.destination,AccessFlags.Write);
    copy.SetRenderFunc(static(CopyData p,UnsafeGraphContext ctx)=>
     CommandBufferHelpers.GetNativeCommandBuffer(ctx.cmd).CopyTexture(p.source,p.destination));
   }
   RecordSurfaces(graph,res,hair:true,clear:false,complete:true,skipSurfaces:false);
  }
  RecordCPUms=(EditorApplication.timeSinceStartup-start)*1000;
 }
 void RecordSurfaces(RenderGraph graph,UniversalResourceData res,bool hair,bool clear,bool complete,bool skipSurfaces){
  using var pass=graph.AddRasterRenderPass<Data>(hair?"154 resolve hair against same-ray character depth":"154 original surface and finite SourcePalette58",out var d);
  d.owner=skipSurfaces?null:this;d.hair=hair;d.clear=clear;d.complete=complete;d.window=ObservationWindow;
  var access=clear?AccessFlags.WriteAll:AccessFlags.ReadWrite;
  for(int i=0;i<fields.Length;i++)pass.SetRenderAttachment(graph.ImportTexture(fields[i]),i,access);
  pass.SetRenderAttachmentDepth(graph.ImportTexture(depth),access);
  if(hair)pass.UseTexture(graph.ImportTexture(nonHairMeta),AccessFlags.Read);
  if(directionalWorld!=null){pass.UseTexture(graph.ImportTexture(directionalWorld),AccessFlags.Read);pass.UseTexture(graph.ImportTexture(directionalSelf),AccessFlags.Read);}
  pass.UseAllGlobalTextures(true);if(res.mainShadowsTexture.IsValid())pass.UseTexture(res.mainShadowsTexture);if(res.additionalShadowsTexture.IsValid())pass.UseTexture(res.additionalShadowsTexture);
  pass.AllowPassCulling(false);
  pass.SetRenderFunc(static(Data p,RasterGraphContext ctx)=>{
   if(p.clear)ctx.cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1,0);
   p.owner?.Draw(ctx,p.hair,p.complete,p.window);
  });
 }
 void Draw(RasterGraphContext ctx,bool hair,bool complete,Rect? window){
  if(window.HasValue)ctx.cmd.EnableScissorRect(window.Value);
  try{
   foreach(var b in source.bindings){
    if((b.renderer==2)!=hair)continue;
    var mf=eye.full.motion.surface.outputs[b.renderer];
    ctx.cmd.DrawMesh(mf.sharedMesh,mf.transform.localToWorldMatrix,materials[b.ordinal],b.submesh,0);
   }
   if(complete)RenderedFrame=Time.frameCount;
  }finally{if(window.HasValue)ctx.cmd.DisableScissorRect();}
 }
 public IEnumerable<UnityEngine.Object> OwnedTextures() =>
  (fields??Array.Empty<RTHandle>()).Concat(new[]{depth,nonHairMeta}).Where(t=>t!=null).Select(t=>(UnityEngine.Object)t.rt);
 public void Dispose(){if(Disposed)return;Disposed=true;if(materials!=null)foreach(var m in materials)if(m)UnityEngine.Object.DestroyImmediate(m);if(fields!=null)foreach(var t in fields)t?.Release();depth?.Release();nonHairMeta?.Release();fields=null;depth=null;nonHairMeta=null;}
}

public static class ShadowCropAxis154 {
    public static bool TryPlan(float centre, float minimum, float maximum,
        int tileSize, int size, int padding, out float worldStart, out float selfStart) {
        worldStart = selfStart = 0;
        if (!float.IsFinite(centre) || !float.IsFinite(minimum) || !float.IsFinite(maximum) ||
            minimum > maximum || padding < 0 || size <= 2L * padding || tileSize < size)
            return false;
        selfStart = centre - size * .5f;
        worldStart = Math.Clamp(MathF.Floor(selfStart), 0, tileSize - size);
        return Fits(worldStart) && Fits(selfStart);

        bool Fits(float start) => minimum - start >= padding && maximum - start < size - padding;
    }
}

// Each receipt belongs to one presentation and its final output use.

public sealed class SplitDirectionalShadow154:IDisposable {
 const int Padding=8;
 readonly int size;
 const float SelfDepthSpan=8;
 readonly NativePlayer395 native;
 readonly MeshFilter[] surfaces;
 readonly Renderer[] casters;
 readonly Material[][] originalMaterials;
 readonly Material[][] casterMaterials;
 readonly int[][] casterPasses;
 readonly RTHandle world,self;
 static readonly int WorldPass=Shader.PropertyToID("_T2WorldOnly154");
 static readonly int CasterOffset=Shader.PropertyToID("_T2CasterOffset154");
 static readonly int ShadowBias=Shader.PropertyToID("_ShadowBias");
 static readonly int LightDirection=Shader.PropertyToID("_LightDirection");
 static readonly int LightPosition=Shader.PropertyToID("_LightPosition");
 public Matrix4x4 WorldToShadow{get;private set;}
 public Matrix4x4 SelfToShadow{get;private set;}
 public RTHandle World=>world;
 public RTHandle Self=>self;
 public int Cascade{get;private set;}
 public int RecordedFrame{get;private set;}=-1;
 public int RecordedBatches{get;private set;}
 public int SelfDraws{get;private set;}
 public bool TraceCoverage{get;set;}
 public object LastCoverage{get;private set;}
 sealed class Data {
  public SplitDirectionalShadow154 owner;
  public bool self,oldPunctual;
  public RendererListHandle list;
  public float oldWorldPass;
  public Matrix4x4 view,projection,cameraView,cameraProjection;
  public Vector4 bias,direction,lightPosition,oldBias,oldDirection,oldPosition;
 }
 public SplitDirectionalShadow154(NativePlayer395 n,Shader body,Shader toon,int mapSize=256){
  native=n;
  if(mapSize!=256&&mapSize!=512&&mapSize!=1024)
   throw new ArgumentOutOfRangeException(nameof(mapSize));
  size=mapSize;
  surfaces=n.host.main.motion.surface.outputs;
  if(surfaces.Length!=3)throw new InvalidOperationException("154 directional test requires the three current actor meshes");
  casters=surfaces.Select(m=>m.GetComponent<Renderer>()).ToArray();
  originalMaterials=new Material[casters.Length][];
  casterMaterials=new Material[casters.Length][];
  casterPasses=new int[casters.Length][];
  if(Shader.GetGlobalFloat(WorldPass)!=0)throw new InvalidOperationException("154 exclusive world pass flag is busy");
  try{
   for(int i=0;i<casters.Length;i++){
    var caster=casters[i];
    if(!caster||!caster.enabled||caster.shadowCastingMode!=ShadowCastingMode.ShadowsOnly||caster.GetComponent<Collider>())
     throw new InvalidOperationException("154 actor caster identity changed");
    var original=originalMaterials[i]=caster.sharedMaterials;
    if(original.Length!=surfaces[i].sharedMesh.subMeshCount)throw new InvalidOperationException("154 caster slots changed");
    var owned=casterMaterials[i]=new Material[original.Length];
    casterPasses[i]=new int[original.Length];
    for(int j=0;j<original.Length;j++){
     var material=original[j];
     var shader=material.shader.name switch {
      "EValidation/CommonSurface329"=>body,
      "VRM10/Universal Render Pipeline/MToon10"=>toon,
      _=>throw new InvalidOperationException("154 unrecognized actor shadow caster shader")
     };
     owned[j]=new Material(material){shader=shader,name="154 owned directional caster "+i+"/"+j,hideFlags=HideFlags.HideAndDontSave};
     owned[j].shaderKeywords=material.shaderKeywords;
     owned[j].renderQueue=material.renderQueue;
     int pass=casterPasses[i][j]=owned[j].FindPass("ShadowCaster");
     if(pass<0||pass!=material.FindPass("ShadowCaster"))
      throw new InvalidOperationException("154 original ShadowCaster pass layout changed");
     ShaderUtil.CompilePass(owned[j],pass,true);
     if(ShaderUtil.ShaderHasError(shader))throw new InvalidOperationException("154 actor shadow variant failed");
     SelfDraws++;
    }
   }
   if(SelfDraws!=15)throw new InvalidOperationException("154 actor directional pass budget changed");
   world=RTHandles.Alloc(size,size,depthBufferBits:DepthBits.Depth16,filterMode:FilterMode.Bilinear,isShadowMap:true,name:"154 owned cropped directional world shadow");
   self=RTHandles.Alloc(size,size,depthBufferBits:DepthBits.Depth32,filterMode:FilterMode.Bilinear,isShadowMap:true,name:"154 owned cropped directional actor shadow");
  }catch{Dispose();throw;}
 }
 public void BindCasterMaterials(){
  for(int i=0;i<casters.Length;i++)
   if(!casters[i]||!casters[i].sharedMaterials.SequenceEqual(originalMaterials[i]))
    throw new InvalidOperationException("154 original caster materials changed before binding");
  for(int i=0;i<casters.Length;i++)casters[i].sharedMaterials=casterMaterials[i];
 }
 public void SetHairCasterOffset(Vector3 offset){
  foreach(var material in casterMaterials[2])material.SetVector(CasterOffset,offset);
 }
 Bounds ActorBounds(){
  var corners=new Vector3[8];Bounds total=default;bool first=true;
  foreach(var surface in surfaces){
   var b=surface.sharedMesh.bounds;
   Corners(b,corners);
   foreach(var local in corners){
    var worldPoint=surface.transform.TransformPoint(local);
    if(first){total=new Bounds(worldPoint,Vector3.zero);first=false;}else total.Encapsulate(worldPoint);
   }
  }
  return total;
 }
 static void Corners(Bounds b,Vector3[] points){
  for(int i=0;i<8;i++)points[i]=b.center+Vector3.Scale(b.extents,new Vector3((i&1)==0?-1:1,(i&2)==0?-1:1,(i&4)==0?-1:1));
 }
 Matrix4x4 Crop(Matrix4x4 original,Vector2 start,int tileSize){
  float scale=tileSize/(float)size;
  var w=original.GetRow(3);
  var p=original;
  p.SetRow(0,original.GetRow(0)*scale+w*(scale-1-2*start.x/size));
  p.SetRow(1,original.GetRow(1)*scale+w*(scale-1-2*start.y/size));
  return p;
 }
 static Matrix4x4 ShadowTransform(Matrix4x4 projection,Matrix4x4 view){
  if(SystemInfo.usesReversedZBuffer)projection.SetRow(2,-projection.GetRow(2));
  var bias=Matrix4x4.identity;
  bias.m00=bias.m11=bias.m22=bias.m03=bias.m13=bias.m23=.5f;
  return bias*projection*view;
 }
 public void Record(RenderGraph graph,ContextContainer frame){
  var shadows=frame.Get<UniversalShadowData>();
  var lighting=frame.Get<UniversalLightData>();
  var rendering=frame.Get<UniversalRenderingData>();
  var camera=frame.Get<UniversalCameraData>().camera;
  int lightIndex=lighting.mainLightIndex;
  if(camera!=native.localCamera||!shadows.supportsMainLightShadows||lightIndex<0)
   throw new InvalidOperationException("154 no original directional shadow data");
  var main=lighting.visibleLights[lightIndex];
  if(main.lightType!=LightType.Directional||!main.light||main.light.shadows==LightShadows.None)
   throw new InvalidOperationException("154 main light is not an actual directional caster");
  int tiles=shadows.mainLightShadowCascadesCount;
  int atlasWidth=shadows.mainLightShadowmapWidth,atlasHeight=shadows.mainLightShadowmapHeight;
  int tileSize=ShadowUtils.GetMaxTileResolutionInAtlas(atlasWidth,atlasHeight,tiles);
  if(tileSize<size||tiles<1||tiles>4)throw new InvalidOperationException("154 original shadow tile not supported");
  var cull=rendering.cullResults;
  var bounds=ActorBounds();var points=new Vector3[8];Corners(bounds,points);
  var tried=TraceCoverage?new List<object>():null;
  float[] XYZ(Vector3 v)=>new[]{v.x,v.y,v.z};
  if(TraceCoverage)LastCoverage=new {
   camera=camera.name,cameraPosition=XYZ(camera.transform.position),
   cameraRotation=new[]{camera.transform.rotation.x,camera.transform.rotation.y,camera.transform.rotation.z,camera.transform.rotation.w},
   camera.nearClipPlane,camera.farClipPlane,camera.orthographicSize,
   player=XYZ(native.player.position), actorMin=XYZ(bounds.min),actorMax=XYZ(bounds.max),
   cascadeCount=tiles,cascades=tried
  };
  ShadowSliceData slice=default;
  Cascade=-1;
  for(int i=0;i<tiles;i++){
   if(!ShadowUtils.ExtractDirectionalLightMatrix(ref cull,shadows,lightIndex,i,atlasWidth,
     tiles==2?atlasHeight/2:atlasHeight,tileSize,main.light.shadowNearPlane,out var sphere,out var next))
    throw new InvalidOperationException("154 original cascade matrix unavailable");
   float closest=bounds.SqrDistance(sphere),radiusSquared=sphere.w*sphere.w;
   if(tried!=null)tried.Add(new {index=i,center=XYZ(sphere),radius=sphere.w,closest,
       farthest=points.Max(q=>((Vector3)sphere-q).sqrMagnitude),radiusSquared});
   if(tiles==1||closest<radiusSquared){
    if(tiles>1&&points.Any(q=>((Vector3)sphere-q).sqrMagnitude>=sphere.w*sphere.w))
     throw new InvalidOperationException("154 actor crosses original cascade boundary; bounded proof uses one slice");
    Cascade=i;slice=next;break;
   }
  }
  if(Cascade<0)throw new InvalidOperationException("154 actor is outside the original shadow cascades");
  var view=slice.viewMatrix;var projection=slice.projectionMatrix;var clip=projection*view;
  Vector2 Pixel(Vector3 worldPoint){
   var q=clip.MultiplyPoint(worldPoint);return new Vector2((q.x*.5f+.5f)*tileSize,(q.y*.5f+.5f)*tileSize);
  }
  var root=native.player.position;
  // A constant vertical reference in the actor frame avoids pose-dependent grid drift.
  var anchor=root+Vector3.up*(native.bodyHeight*.5f);
  var centre=Pixel(anchor);
  var min=new Vector2(float.PositiveInfinity,float.PositiveInfinity);
  var max=new Vector2(float.NegativeInfinity,float.NegativeInfinity);
  foreach(var corner in points){
   var p=Pixel(corner);
   if(!float.IsFinite(p.x)||!float.IsFinite(p.y))
    throw new InvalidOperationException("154 non-finite shadow projection");
   min=Vector2.Min(min,p);max=Vector2.Max(max,p);
  }
  if(!ShadowCropAxis154.TryPlan(centre.x,min.x,max.x,tileSize,size,Padding,out float wx,out float sx)||
     !ShadowCropAxis154.TryPlan(centre.y,min.y,max.y,tileSize,size,Padding,out float wy,out float sy))
   throw new InvalidOperationException($"154 {size} shadow crop cannot contain the actor and PCF margin");
  var startWorld=new Vector2(wx,wy);
  var startSelf=new Vector2(sx,sy);
  var worldProj=Crop(projection,startWorld,tileSize);
  var selfProj=Crop(projection,startSelf,tileSize);
  float centreZ=view.MultiplyPoint(anchor).z;
  if(!float.IsFinite(centreZ)||points.Any(q=>{
   float z=view.MultiplyPoint(q).z;
   return !float.IsFinite(z)||Mathf.Abs(z-centreZ)>=SelfDepthSpan*.45f;
  }))
   throw new InvalidOperationException("154 actor exceeds bounded root shadow depth span");
  selfProj.SetRow(2,new Vector4(0,0,-2f/SelfDepthSpan,2f*centreZ/SelfDepthSpan));
  WorldToShadow=ShadowTransform(worldProj,view);SelfToShadow=ShadowTransform(selfProj,view);
  var settings=new ShadowDrawingSettings(cull,lightIndex){
   useRenderingLayerMaskTest=UniversalRenderPipeline.asset.useRenderingLayers,splitIndex=Cascade
  };
  RecordedFrame=Time.frameCount;
  RecordedBatches++;
  var worldList=graph.CreateShadowRendererList(ref settings);
  var bias=ShadowUtils.GetShadowBias(ref main,lightIndex,shadows,projection,tileSize);
  RecordAtlas(graph,camera,world,worldList,view,worldProj,main,bias,false);
  RecordAtlas(graph,camera,self,default,view,selfProj,main,bias,true);
 }
 void RecordAtlas(RenderGraph graph,Camera camera,RTHandle target,RendererListHandle list,Matrix4x4 view,Matrix4x4 projection,VisibleLight light,Vector4 bias,bool actor){
  using var pass=graph.AddRasterRenderPass<Data>(actor?"154 directional actor-only root crop":"154 directional world-only physical crop",out var d);
  d.owner=this;d.self=actor;d.list=list;d.oldWorldPass=Shader.GetGlobalFloat(WorldPass);d.view=view;d.projection=projection;
  d.cameraView=camera.worldToCameraMatrix;d.cameraProjection=camera.projectionMatrix;
  d.bias=bias;d.direction=-light.localToWorldMatrix.GetColumn(2);d.lightPosition=light.localToWorldMatrix.GetColumn(3);
  d.oldBias=Shader.GetGlobalVector(ShadowBias);d.oldDirection=Shader.GetGlobalVector(LightDirection);d.oldPosition=Shader.GetGlobalVector(LightPosition);
  d.oldPunctual=Shader.IsKeywordEnabled("_CASTING_PUNCTUAL_LIGHT_SHADOW");
  pass.SetRenderAttachmentDepth(graph.ImportTexture(target),AccessFlags.WriteAll);
  if(!actor)pass.UseRendererList(list);
  pass.AllowGlobalStateModification(true);pass.AllowPassCulling(false);
  pass.SetRenderFunc(static(Data p,RasterGraphContext ctx)=>{
   var cmd=ctx.cmd;
   cmd.ClearRenderTarget(RTClearFlags.Depth,Color.clear,1,0);
   cmd.SetViewport(new Rect(0,0,p.owner.size,p.owner.size));cmd.SetViewProjectionMatrices(p.view,p.projection);
   cmd.SetGlobalVector(ShadowBias,p.bias);cmd.SetGlobalVector(LightDirection,p.direction);cmd.SetGlobalVector(LightPosition,p.lightPosition);
   cmd.DisableShaderKeyword("_CASTING_PUNCTUAL_LIGHT_SHADOW");cmd.SetGlobalDepthBias(1,2.5f);
   cmd.SetGlobalFloat(WorldPass,p.self?0:1);
   try{
    if(p.self)p.owner.DrawActor(cmd);
    else cmd.DrawRendererList(p.list);
   }finally{
    cmd.SetGlobalFloat(WorldPass,p.oldWorldPass);
    cmd.SetGlobalDepthBias(0,0);cmd.SetGlobalVector(ShadowBias,p.oldBias);cmd.SetGlobalVector(LightDirection,p.oldDirection);cmd.SetGlobalVector(LightPosition,p.oldPosition);
    if(p.oldPunctual)cmd.EnableShaderKeyword("_CASTING_PUNCTUAL_LIGHT_SHADOW");
    cmd.SetViewProjectionMatrices(p.cameraView,p.cameraProjection);
   }
  });
 }
 void DrawActor(RasterCommandBuffer cmd){
  for(int i=0;i<surfaces.Length;i++)
   for(int j=0;j<casterPasses[i].Length;j++)
    cmd.DrawMesh(surfaces[i].sharedMesh,surfaces[i].transform.localToWorldMatrix,casterMaterials[i][j],j,casterPasses[i][j]);
 }
 public IEnumerable<UnityEngine.Object> OwnedTextures() =>
  new[]{world,self}.Where(t=>t!=null).Select(t=>(UnityEngine.Object)t.rt);
 public void RestoreCasterMaterials(){
  for(int i=0;i<casters.Length;i++)
   if(casters[i]&&originalMaterials[i]!=null&&casterMaterials[i]!=null&&
      casters[i].sharedMaterials.SequenceEqual(casterMaterials[i]))casters[i].sharedMaterials=originalMaterials[i];
 }
 public void Dispose(){
  RestoreCasterMaterials();
  world?.Release();self?.Release();
  for(int i=0;i<casters.Length;i++){
   if(casters[i]&&originalMaterials[i]!=null&&casterMaterials[i]!=null&&
      casters[i].sharedMaterials.SequenceEqual(casterMaterials[i]))casters[i].sharedMaterials=originalMaterials[i];
   if(casterMaterials[i]==null)continue;
   foreach(var material in casterMaterials[i])if(material)UnityEngine.Object.DestroyImmediate(material);
  }
 }
}
}
