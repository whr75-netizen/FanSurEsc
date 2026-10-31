// Small dependency-free JSON boundary for the existing RunCommand reference set.
// No reflection, package loading, runtime serialization of arbitrary objects.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;

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
    public static Json58 Parse(string text) {int p=0;var result=ParseValue(text,ref p,0);Space(text,ref p);if(p!=text.Length)throw new ArgumentException("Trailing JSON data");return result;}
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
            while(true){Space(s,ref p);string key=null;if(obj){key=ParseString(s,ref p);Space(s,ref p);if(s[p++]!=':')throw new ArgumentException("JSON colon");}var v=ParseValue(s,ref p,depth+1);if(obj)result[key]=v;else result.Add(v);Space(s,ref p);char end=s[p++];if(end==(obj?'}':']'))break;if(end!=',')throw new ArgumentException("JSON separator");}return result;}
        foreach(string word in new[]{"true","false","null"})if(s.Substring(p).StartsWith(word,StringComparison.Ordinal)){p+=word.Length;return word=="null"?null:(Json58)(word=="true");}
        int start=p;while(p<s.Length&&"-+0123456789.eE".IndexOf(s[p])>=0)p++;if(start==p)throw new ArgumentException("JSON token");return double.Parse(s.Substring(start,p-start),CultureInfo.InvariantCulture);
    }
}
public sealed class Obj58 : Json58 {public Obj58(){fields=new Dictionary<string,Json58>(StringComparer.Ordinal);}public new static Obj58 Parse(string text){return(Obj58)Json58.Parse(text);}}
public sealed class Arr58 : Json58 {public Arr58(params object[] values){items=new List<Json58>();if(values.Length==1&&values[0] is IEnumerable&&!(values[0] is string)&&!(values[0] is Json58)){foreach(var v in(IEnumerable)values[0])Add(Wrap(v));}else foreach(var v in values)Add(Wrap(v));}}
