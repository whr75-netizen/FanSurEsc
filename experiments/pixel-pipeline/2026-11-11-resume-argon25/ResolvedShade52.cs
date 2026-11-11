// CPU-only supplier for the existing confirmed-region LUT bridge.
// It does not infer colour regions, stage correspondence, visibility or RGB.
using System;
using System.Linq;

public static class ResolvedShade52
{
    public sealed class Stamp {
        public string actor,view,sourceId,stage,producer;
        public int frame,width,height; public long serial;
    }
    public sealed class Shade {
        public Stamp stamp; public float[] appliedQ; public int[] levels; public bool[] known;
    }
    public sealed class Packet {
        public Stamp stamp; public ResolvedRegionInput.Packet lut; public float[] appliedQ;
    }
    static void Require(bool ok,string why) {if(!ok)throw new ArgumentException(why);}
    static void Valid(Stamp s) {
        Require(s!=null&&!String.IsNullOrEmpty(s.actor)&&!String.IsNullOrEmpty(s.view)&&
            !String.IsNullOrEmpty(s.sourceId)&&!String.IsNullOrEmpty(s.stage)&&!String.IsNullOrEmpty(s.producer)&&
            s.frame>=0&&s.serial>=0&&s.width>0&&s.height>0&&(long)s.width*s.height<=Int32.MaxValue/2,
            "52 exact observed stage/source/view identity and bounded extent required");
    }
    static bool Same(Stamp a,Stamp b) {return a.actor==b.actor&&a.view==b.view&&a.sourceId==b.sourceId&&
        a.stage==b.stage&&a.producer==b.producer&&a.frame==b.frame&&a.serial==b.serial&&a.width==b.width&&a.height==b.height;}
    static Stamp Copy(Stamp s) {return new Stamp{actor=s.actor,view=s.view,sourceId=s.sourceId,stage=s.stage,
        producer=s.producer,frame=s.frame,serial=s.serial,width=s.width,height=s.height};}
    public static Packet Build(Stamp observed,Shade shade,SourcePalette58.Family[] families,
        SourcePalette58.Settings[] settings,ResolvedRegionInput.Region[] regions,ResolvedRegionInput.Cell[] cells)
    {
        Valid(observed);Require(shade!=null,"52 applied shade plane required");Valid(shade.stamp);
        Require(Same(observed,shade.stamp),"52 different frame/view/source/stage/producer/extent; never resample Q");
        int count=checked(observed.width*observed.height);
        Require(shade.appliedQ!=null&&shade.levels!=null&&shade.known!=null&&
            shade.appliedQ.Length==count&&shade.levels.Length==count&&shade.known.Length==count,
            "52 one applied-Q observation per exact stage raster cell required");
        Require(cells!=null&&cells.Length==count&&cells.All(c=>c!=null&&c.sourceId==observed.sourceId),
            "52 region samples must be from the exact observed source");
        var lut=ResolvedRegionInput.Build(observed.width,observed.height,families,settings,regions,cells);
        var q=new float[count];
        for(int i=0;i<count;i++) {
            if(lut.binding[2*i+1]!=1)continue; // Unknown colour semantics stay unknown.
            int family=(int)lut.binding[2*i],levels=shade.levels[i];float value=shade.appliedQ[i];
            Require(shade.known[i]&&!Single.IsNaN(value)&&!Single.IsInfinity(value),"52 unobserved/nonfinite applied Q");
            Require(levels>=2&&levels==settings[family].count,"52 palette and producer level domains need an explicit mapping");
            float expected=(float)lut.index[i]/(float)(levels-1);
            Require(value==expected,"52 LUT k and applied Qprime disagree; proposal/old Q is not a substitute");
            q[i]=value;
        }
        return new Packet{stamp=Copy(observed),lut=lut,appliedQ=q};
    }
}
