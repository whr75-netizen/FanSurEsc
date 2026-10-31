using System;
using System.IO;
using System.Linq;

internal class CommandScript : IRunCommand
{
    const string Output=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\source-palette58";
    public void Execute(ExecutionResult result) {
        var report=new Obj58 {["memoryBefore"]=State58.Memory()};Obj58 before=null;
        try {
            before=State58.Read();State58.RequireEdit(before);report["before"]=before;
            var config=Obj58.Parse(File.ReadAllText(Path.Combine(Output,"CONFIG58.json")));
            long peak;string sha;var families=OriginalMaterialUv58.Read((string)config["modelPath"],(string)config["modelSHA256"],(Arr58)config["domains"],(int)config["sampleCount"],16*1024*1024,out peak,out sha);
            if(sha!=(string)config["modelSHA256"])throw new InvalidOperationException("Source model hash changed");
            var records=new Arr58();var cases=new Arr58();var colours=new Arr58();var cuts=new Arr58();var familyWords=new Arr58();
            for(int i=0;i<families.Length;i++) {
                var family=families[i];var settings=SourceJson58.ReadSettings(config["domains"][i]["settings"]);
                var reference=SourcePalette58.ExtractReference(family);var palette=SourcePalette58.MakePalette(reference,settings);
                var thresholds=config["domains"][i]["thresholds"].Values<double>().ToArray();
                if(thresholds.Length!=palette.rgb8.Length-1)throw new InvalidOperationException("Threshold count");
                int po=colours.Count,to=cuts.Count;foreach(var rgb in palette.rgb8)colours.Add(new Arr58(rgb.Concat(new[]{255})));
                foreach(var t in thresholds)cuts.Add((float)t);familyWords.Add(new Arr58(po,palette.rgb8.Length,to,thresholds.Length));
                records.Add(new Obj58 {["family"]=SourceJson58.Family(family),["reference"]=SourceJson58.Reference(reference),["settings"]=SourceJson58.Settings(settings),["palette"]=SourceJson58.Palette(palette),["thresholds"]=new Arr58(thresholds)});
                for(int j=0;j<family.samples.Length;j++) {
                    var source=family.samples[j];int ordinal=OriginalMaterialUv58.ResolveFamily(families,sha,(int)config["domains"][i]["meshIndex"],source.primitiveId,source.materialId,source.uv);
                    double g=(double)j/Math.Max(1,family.samples.Length-1);int k=SourcePalette58.ShadeIndex(g,thresholds),corrected=j%7==0?(k+1)%palette.rgb8.Length:k;
                    cases.Add(new Obj58 {["family"]=ordinal,["sourceSampleId"]=source.id,["sourceUV"]=new Arr58(source.uv),["g"]=(float)g,["k"]=k,["kPrime"]=corrected,
                        ["bound"]=true,["sourceRGB8"]=new Arr58(source.rgba8.Take(3)),["initialRGB8"]=new Arr58(SourcePalette58.Resolve(palette,k)),["finalRGB8"]=new Arr58(SourcePalette58.Resolve(palette,corrected))});
                }
            }
            // Diagnostic unbound cell checks scope/alpha preservation, not source colour.
            cases.Add(new Obj58 {["family"]=0,["g"]=.5,["k"]=0,["kPrime"]=0,["bound"]=false,["initialRGB8"]=new Arr58(17,93,141),["finalRGB8"]=new Arr58(17,93,141)});
            report["modelSHA256"]=sha;report["records"]=records;report["rgb8"]=colours;report["thresholds"]=cuts;report["familyWords"]=familyWords;report["cases"]=cases;
            report["peakOwnedDecodedTextureBytes"]=peak;report["automaticSemanticSegmentation"]=false;report["sampleRule"]="Original selected primitive local triangle area weights/UV centroids, native PNG point samples; not visible frame cells";
            report["status"]="source-generated";
        } catch(Exception e) {report["error"]=e.GetType().Name+": "+e.Message;}
        finally {
            var after=State58.Read();report["after"]=after;report["memoryAfter"]=State58.Memory();
            if(before!=null)report["stateChanges"]=new Arr58(State58.Changes(before,after));
            report["ownedTextureIdentitiesRestored"]=before!=null&&Json58.DeepEquals(before["texture2DIds"],after["texture2DIds"]);
            File.WriteAllText(Path.Combine(Output,"SOURCE58.json"),report.ToString());
        }
        result.Log("SOURCE58 status="+report["status"]+" error="+report["error"]+" changes="+report["stateChanges"]);
    }
}
