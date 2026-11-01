using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;

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
