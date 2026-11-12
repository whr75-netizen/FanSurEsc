using System;using System.IO;using System.Linq;using System.Web.Script.Serialization;
public static class SelectedShadeTests65 {
 public sealed class Record {public SourcePalette58.Family family;public SourcePalette58.Settings settings;}
 public sealed class Fixture {public Record[] records;}
 static int tests;static void Check(bool b,string why){tests++;if(!b)throw new Exception(why);}
 static void Reject(Action a,string why){bool rejected=false;try{a();}catch(ArgumentException){rejected=true;}Check(rejected,why);}
 public static void Main(string[] args){
  var json=new JavaScriptSerializer{MaxJsonLength=4000000};var all=json.Deserialize<SelectedShade65.Observed[]>(File.ReadAllText(args[0]));int total=0;
  var paletteFixture=json.Deserialize<Fixture>(File.ReadAllText(args[1]));var families=paletteFixture.records.Select(x=>x.family).ToArray();var settings=paletteFixture.records.Select(x=>x.settings).ToArray();
  foreach(var f in all){var p=SelectedShade65.Build(f);Check(p.observed>0,"no positive actual carrier");for(int i=0;i<p.shade.known.Length;i++)if(p.shade.known[i])Check(p.shade.appliedQ[i]==f.selectedUV[4*i+2],"Q not observed");total+=p.observed;
   // Negative full-face integration: observed shade is real, but these saved58
   // families are NOT a confirmed face region mapping. No RGB may be emitted.
   var cells=Enumerable.Range(0,p.k.Length).Select(i=>new ResolvedRegionInput.Cell{sourceId=p.shade.stamp.sourceId,regionId=null,k=p.k[i],opaqueInterior=p.shade.known[i]}).ToArray();
   var withheld=ResolvedShade52.Build(p.shade.stamp,p.shade,families,settings,new ResolvedRegionInput.Region[0],cells);
   Check(withheld.lut.resolved==0&&withheld.lut.unresolved==p.observed&&withheld.lut.binding.All(x=>x==0),"known shade fabricated a colour family");
  }
  var pristine=json.Serialize(all[0]);Func<SelectedShade65.Observed> fresh=()=>json.Deserialize<SelectedShade65.Observed>(pristine);
  int first=Enumerable.Range(0,all[0].stamp.width*all[0].stamp.height).First(i=>all[0].carrier[4*i]==all[0].registeredRole);int j=first*4;
  var q=fresh();q.selectedUV[j+2]=.25f;Reject(()=>SelectedShade65.Build(q),"nonlevel repaired");q=fresh();q.selectedUV[j+2]=Single.NaN;Reject(()=>SelectedShade65.Build(q),"NaN repaired");
  q=fresh();q.selectedSource[j]+=1;Reject(()=>SelectedShade65.Build(q),"depth mismatch");q=fresh();q.selectedSource[j+3]=q.triangleCount+1;Reject(()=>SelectedShade65.Build(q),"primitive mismatch");
  q=fresh();q.nativeCell[j+2]=0;Reject(()=>SelectedShade65.Build(q),"world owner mistaken for actor");q=fresh();q.headRegionEnabled=true;Reject(()=>SelectedShade65.Build(q),"unverified alternate producer");
  q=fresh();q.stamp.stage="initial/Q";Reject(()=>SelectedShade65.Build(q),"initial Q substitute");q=fresh();q.selectedUV=new float[4];Reject(()=>SelectedShade65.Build(q),"wrong raster accepted");
  q=fresh();q.carrier[j]=-4;var excluded=SelectedShade65.Build(q);Check(!excluded.shade.known[first],"designed feature promoted to source triangle");
  q=fresh();q.carrier[j]=0;q.selectedUV[j+2]=Single.NaN;excluded=SelectedShade65.Build(q);Check(!excluded.shade.known[first],"missing carrier silently supplied");
  q=fresh();var owned=SelectedShade65.Build(q);float saved=owned.shade.appliedQ[first];q.selectedUV[j+2]=99;q.stamp.sourceId="changed";Check(owned.shade.appliedQ[first]==saved&&owned.shade.stamp.sourceId!="changed","mutable source retained");
  Check(total==240&&all.Length==6,"actual saved six-frame coverage changed");
  Console.WriteLine(json.Serialize(new{tests,actualFrames=6,observedOrdinaryFaceQ=total,existingResolvedShade52Called=true,colourRegionsInferred=0,paletteOutputsCreated=0,actualRuntimeLUTApplied=false,newUnityGPUCalls=0}));
 }
}
