// CPU-only binding boundary. Region confirmation is an input, never inferred here.
// Reuses SourcePalette58; owns no Unity objects, GPU resources, history or static cache.
using System;
using System.Linq;
using System.Collections.Generic;

public static class ResolvedRegionInput
{
    public sealed class Region { public string id,decisionId; public int family; public bool confirmed; }
    public sealed class Cell {
        public string sourceId,regionId;
        public SourcePalette58.Sample witness;
        public int k;
        public bool opaqueInterior;
    }
    public sealed class Packet {
        public int width,height;
        public uint[] binding,index,familyTable,rgb8;
        public string[] regionIds,sourceIds,reasons;
        public int resolved,unresolved,excluded;
    }
    static void Require(bool ok,string why) { if(!ok)throw new ArgumentException(why); }
    public static Packet Build(int width,int height,SourcePalette58.Family[] families,
        SourcePalette58.Settings[] settings,Region[] regions,Cell[] cells)
    {
        Require(width>0&&height>0&&(long)width*height<=int.MaxValue/2,"Invalid stage raster extent");
        Require(families!=null&&settings!=null&&families.Length==settings.Length&&families.Length>0&&families.Length<=int.MaxValue/4,"Explicit family/palette settings required");
        Require(cells!=null&&cells.Length==(long)width*height&&regions!=null,"One binding per stage raster sample required");
        var map=new Dictionary<string,Region>(StringComparer.Ordinal);
        foreach(var r in regions) {
            Require(r!=null&&!String.IsNullOrEmpty(r.id)&&!map.ContainsKey(r.id),"Unique source-region IDs required");
            Require(r.family>=0&&r.family<families.Length,"Region family out of range");
            Require(!r.confirmed||!String.IsNullOrEmpty(r.decisionId),"Confirmed region requires external decision provenance");
            map.Add(r.id,r);
        }
        var p=new Packet{width=width,height=height,binding=new uint[cells.Length*2],index=new uint[cells.Length],
            familyTable=new uint[families.Length*4],regionIds=new string[cells.Length],sourceIds=new string[cells.Length],reasons=new string[cells.Length]};
        var colours=new List<uint>();var palettes=new SourcePalette58.Palette[families.Length];
        for(int f=0;f<families.Length;f++) {
            // Existing source validation, representative selection and palette math only.
            palettes[f]=SourcePalette58.MakePalette(SourcePalette58.ExtractReference(families[f]),settings[f]);
            var palette=palettes[f];
            p.familyTable[4*f]=(uint)(colours.Count/4);p.familyTable[4*f+1]=(uint)palette.rgb8.Length;
            foreach(var c in palette.rgb8) {
                Require(c!=null&&c.Length==3&&c.All(x=>x>=0&&x<=255),"RGB8 palette entry required");
                colours.AddRange(c.Select(x=>(uint)x));colours.Add(255);
            }
        }
        p.rgb8=colours.ToArray();
        string packetSource=null;
        for(int i=0;i<cells.Length;i++) {
            var c=cells[i];Require(c!=null&&!String.IsNullOrEmpty(c.sourceId),"Frame/source identity missing");
            if(packetSource==null)packetSource=c.sourceId;else Require(c.sourceId==packetSource,"Mixed frame/source IDs in one raster packet");
            p.regionIds[i]=c.regionId;p.sourceIds[i]=c.sourceId;
            if(!c.opaqueInterior) {p.excluded++;p.reasons[i]="excluded: boundary/partial/uncovered";continue;}
            Region r;
            if(c.regionId==null||!map.TryGetValue(c.regionId,out r)||!r.confirmed) {
                p.unresolved++;p.reasons[i]="unresolved: no confirmed source region";continue;
            }
            Require(c.witness!=null&&c.witness.rgba8!=null&&c.witness.rgba8.Length==4&&c.witness.rgba8[3]==255,"Opaque native source witness required");
            var source=families[r.family];
            Require(source.source.factorLinear[3]==1,"Partial material alpha is outside opaque LUT contract");
            SourcePalette58.SourceColours(new SourcePalette58.Family{id=source.id,domainId=source.domainId,source=source.source,samples=new[]{c.witness}});
            Require(c.k>=0&&c.k<palettes[r.family].rgb8.Length,"Q index outside region palette");
            p.binding[2*i]=(uint)r.family;p.binding[2*i+1]=1;p.index[i]=(uint)c.k;p.resolved++;p.reasons[i]="resolved";
        }
        return p;
    }
    // CPU reference of the existing lookup + transfer function, not new colour math.
    public static int[] LookupRGB8(Packet p,int pixel) {
        Require(pixel>=0&&pixel<p.index.Length&&p.binding[pixel*2+1]==1,"Unresolved/excluded pixel has no LUT output");
        int family=(int)p.binding[2*pixel],at=4*((int)p.familyTable[4*family]+(int)p.index[pixel]);
        return new[]{(int)p.rgb8[at],(int)p.rgb8[at+1],(int)p.rgb8[at+2]};
    }
}
