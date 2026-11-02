// Offline CPU tests only. Confirmed regions below are TEST CONTRACTS, not inferred face labels.
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Web.Script.Serialization;

public static class RegionBridgeTests
{
    public static void Main(string[] args) {Console.OutputEncoding=new System.Text.UTF8Encoding(false);Console.WriteLine(Run(args[0]));}
    public sealed class Record { public SourcePalette58.Family family;public SourcePalette58.Settings settings;public SourcePalette58.Reference reference;public SourcePalette58.Palette palette;public double[] thresholds; }
    public sealed class Row {public bool boundOpaque;public int family,k,kPrime,nativeAlpha8;public int[] initialRGB8,finalRGB8;public string sourceSampleId;}
    public sealed class FaceProbe {public string id,regionId;public int[] rgba8;}
    public sealed class Fixture {public Record[] records;public Row[] rows;public FaceProbe[] faceProbes;}
    static List<string> passed;
    static void Check(bool ok,string message) {if(!ok)throw new Exception(message);}
    static bool Same(int[] a,int[] b){return a.SequenceEqual(b);}
    static void Reject(Action action,string message){bool failed=false;try{action();}catch(ArgumentException){failed=true;}Check(failed,message);}
    public static string Run(string path) {
        passed=new List<string>();var json=new JavaScriptSerializer();var f=json.Deserialize<Fixture>(File.ReadAllText(path));
        var families=f.records.Select(x=>x.family).ToArray();var settings=f.records.Select(x=>x.settings).ToArray();
        var regions=f.records.Select((x,i)=>new ResolvedRegionInput.Region{id="test-only/58-domain/"+i,decisionId="test-contract-only-not-face-segmentation",family=i,confirmed=true}).ToArray();
        int samples=0;
        foreach(var r in f.records){var reference=SourcePalette58.ExtractReference(r.family);var palette=SourcePalette58.MakePalette(reference,r.settings);
            Check(Same(reference.rgb8,r.reference.rgb8)&&reference.sample.id==r.reference.sample.id,"58 original source reference regression");
            Check(palette.rgb8.Zip(r.palette.rgb8,Same).All(x=>x),"58 palette regression");samples+=r.family.samples.Length;}
        passed.Add("reused58: two native materials / 63 source samples / original reference and palette exact");
        Func<bool,ResolvedRegionInput.Cell[]> cells=final=>f.rows.Select(row=>new ResolvedRegionInput.Cell{
            sourceId="saved58/diagnostic-g-k-not-live-frame",regionId=regions[row.family].id,k=final?row.kPrime:row.k,opaqueInterior=row.boundOpaque,
            witness=row.boundOpaque?families[row.family].samples.Single(s=>s.id==row.sourceSampleId):null}).ToArray();
        Func<ResolvedRegionInput.Cell[],ResolvedRegionInput.Packet> build=c=>ResolvedRegionInput.Build(c.Length,1,families,settings,regions,c);
        var initial=build(cells(false));var finalPacket=build(cells(true));int sameQ=0;
        for(int i=0;i<f.rows.Length;i++){var row=f.rows[i];if(!row.boundOpaque)continue;
            Check(Same(ResolvedRegionInput.LookupRGB8(initial,i),row.initialRGB8),"saved58 initial GPU RGB disagreement");
            Check(Same(ResolvedRegionInput.LookupRGB8(finalPacket,i),row.finalRGB8),"saved58 final GPU RGB disagreement");
            if(row.k==row.kPrime)sameQ++;
            foreach(var v in ResolvedRegionInput.LookupRGB8(finalPacket,i))Check(SourcePalette58.Finite(SourcePalette58.Decode(v/255.0)),"decode invalid");}
        Check(initial.resolved==62&&sameQ==52&&initial.excluded==2,"saved58 coverage count regression");
        passed.Add("saved58 actual GPU evidence rechecked on CPU: 62 resolved / 52 old==q / initial-final RGB8 exact");
        foreach(double scale in new[]{0.0,0.5,1.0,1.1}){
            var changed=settings.Select(s=>new SourcePalette58.Settings{count=s.count,darkLRatio=s.darkLRatio,darkCRatio=s.darkCRatio,gamma=s.gamma,intervalScale=scale}).ToArray();
            var p=ResolvedRegionInput.Build(64,1,families,changed,regions,cells(true));
            Check(p.binding.SequenceEqual(finalPacket.binding)&&p.index.SequenceEqual(finalPacket.index)&&p.regionIds.SequenceEqual(finalPacket.regionIds),"palette spacing changed region or Q");
            for(int i=0;i<64;i++)if(p.binding[2*i+1]==1){int family=(int)p.binding[2*i];var palette=SourcePalette58.MakePalette(SourcePalette58.ExtractReference(families[family]),changed[family]);
                Check(palette.rgb8.Any(c=>Same(c,ResolvedRegionInput.LookupRGB8(p,i))),"RGB outside exact finite palette");}}
        passed.Add("palette interval changes preserve source-region bindings and Q; all resolved outputs remain in their own palette");
        foreach(var rec in f.records){var alternate=rec.thresholds.Select(t=>t*.8).ToArray();foreach(double g in new[]{0.0,.2,.3,.5,.7,.8,1.0}){
            int a=SourcePalette58.ShadeIndex(g,rec.thresholds),b=SourcePalette58.ShadeIndex(g,alternate);
            Check(a>=0&&b>=0&&a<rec.palette.rgb8.Length&&b<rec.palette.rgb8.Length,"threshold Q bounds");
            Check(Same(SourcePalette58.Resolve(rec.palette,b),rec.palette.rgb8[b]),"threshold changed palette entries");}}
        passed.Add("threshold reclassification uses existing ShadeIndex and Resolve without regenerating palette or regions");
        var unknown=cells(true);unknown[0].regionId="unconfirmed-face-parent8";
        var unknownRegions=regions.Concat(new[]{new ResolvedRegionInput.Region{id="unconfirmed-face-parent8",family=1,confirmed=false}}).ToArray();
        var unresolved=ResolvedRegionInput.Build(64,1,families,settings,unknownRegions,unknown);
        Check(unresolved.binding[1]==0&&unresolved.unresolved==1,"unconfirmed parent promoted");
        Reject(()=>ResolvedRegionInput.LookupRGB8(unresolved,0),"unresolved region invented a LUT colour");
        passed.Add("unconfirmed/missing region stays unbound and is excluded from LUT success");
        var faceRegions=f.faceProbes.Select(x=>x.regionId).Distinct().Select(id=>new ResolvedRegionInput.Region{id=id,family=1,confirmed=false}).ToArray();
        var faceCells=f.faceProbes.Select(x=>new ResolvedRegionInput.Cell{sourceId="saved103/native-UV-not-rendered-frame",regionId=x.regionId,k=0,opaqueInterior=true}).ToArray();
        var face=ResolvedRegionInput.Build(faceCells.Length,1,families,settings,faceRegions,faceCells);
        Check(face.resolved==0&&face.unresolved==faceCells.Length,"actual104 parent/AA/paint evidence promoted to confirmed family");
        passed.Add("saved actual face/scalp/cheek/transition probes: 0 inferred LUT bindings; unresolved remains explicit");
        var partial=cells(true);partial[0].opaqueInterior=false;var excluded=build(partial);
        Check(excluded.binding[1]==0&&excluded.excluded==3,"partial boundary forced into opaque LUT");
        passed.Add("partial/AA/coverage boundary requires separate contract; existing output retained, not claimed quantized");
        var bad=cells(true);bad[0].k=999;Reject(()=>build(bad),"invalid Q not rejected");
        bad=cells(true);bad[0].sourceId="different-frame";Reject(()=>build(bad),"mixed frame source IDs accepted");
        Reject(()=>ResolvedRegionInput.Build(63,1,families,settings,regions,cells(true)),"raster mismatch not rejected");
        regions[0].decisionId=null;Reject(()=>build(cells(true)),"confirmation without external provenance accepted");regions[0].decisionId="test-only";
        passed.Add("invalid Q, mixed frame IDs, stage extent and missing decision provenance rejected before upload");
        var witness=cells(true)[0].witness;string image=witness.imageSHA256;
        try{witness.imageSHA256="mismatched-original-image";Reject(()=>build(cells(true)),"source contamination accepted");}finally{witness.imageSHA256=image;}
        passed.Add("original source image/material/UV witness checked by existing SourcePalette58 validation");
        var separate=new[]{new ResolvedRegionInput.Region{id="test-shape-A",family=0,confirmed=true,decisionId="test-only"},new ResolvedRegionInput.Region{id="test-shape-B",family=0,confirmed=true,decisionId="test-only"}};
        var pair=cells(true).Take(2).ToArray();pair[0].regionId=separate[0].id;pair[1].regionId=separate[1].id;pair[1].witness=pair[0].witness;pair[1].k=pair[0].k;
        var pairPacket=ResolvedRegionInput.Build(2,1,families,settings,separate,pair);
        Check(pairPacket.regionIds[0]!=pairPacket.regionIds[1]&&Same(ResolvedRegionInput.LookupRGB8(pairPacket,0),ResolvedRegionInput.LookupRGB8(pairPacket,1)),"same colour collapsed distinct structure IDs");
        passed.Add("same palette/colour does not merge distinct source-region IDs");
        var rgb=ResolvedRegionInput.LookupRGB8(finalPacket,0);rgb[0]^=255;
        Check(Same(ResolvedRegionInput.LookupRGB8(finalPacket,0),f.rows[0].finalRGB8),"lookup alias mutated table");
        Check(build(cells(true)).binding.SequenceEqual(finalPacket.binding),"repeat build retained mutable history");
        passed.Add("fresh CPU packet per build / independent returned RGB / no static frame cache");
        return json.Serialize(new{tests=passed.Count,passed,sourceSamples=samples,resolved=62,oldEqualsQ=52,newGPUExecuted=false,productActivated=false,semanticRegionTruthValidated=false});
    }
}
