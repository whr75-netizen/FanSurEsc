'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const r=__dirname,source54=process.argv[2]?path.resolve(process.argv[2]):path.join(r,'../source-palette54'),C=require(path.join(source54,'source-palette.cjs'));
const d=JSON.parse(fs.readFileSync(path.join(r,'SOURCE58.json'),'utf8'));assert.equal(d.status,'source-generated');assert(!d.error);assert.deepEqual(d.stateChanges,[]);
let maxLab=0,maxCost=0,maxRow=0,total=0;const results=[];
for(const rec of d.records){
 const ref=C.extractReference(rec.family),p=C.makePalette(ref,rec.settings);
 assert.deepEqual(ref.rgb8,rec.reference.rgb8);assert.equal(ref.provenance.sampleId,rec.reference.sample.id);assert.deepEqual(p.rgb8,rec.palette.rgb8);
 maxLab=Math.max(maxLab,...ref.lab.map((v,i)=>Math.abs(v-rec.reference.lab[i])));maxCost=Math.max(maxCost,Math.abs(ref.extraction.cost-rec.reference.cost));
 maxRow=Math.max(maxRow,...p.rows.map((v,i)=>Math.abs(v.targetL-rec.palette.targetL[i])),...p.rows.map((v,i)=>Math.abs(v.usedC-rec.palette.usedC[i])));
 assert.equal(p.diagnostics.duplicates,rec.palette.duplicates);assert.equal(p.diagnostics.LReversals,rec.palette.LReversals);
 total+=rec.family.samples.length;results.push({family:rec.family.id,sourceSamples:rec.family.samples.length,reference:ref.rgb8,sampleId:ref.provenance.sampleId,palette:p.rgb8});
}
for(const s of d.cases.filter(v=>v.bound)){
 const rec=d.records[s.family],k=C.shadeIndex(s.g,rec.thresholds);assert.equal(k,s.k);assert.deepEqual(C.resolve(rec.palette,k),s.initialRGB8);assert.deepEqual(C.resolve(rec.palette,s.kPrime),s.finalRGB8);
}
assert(maxLab<1e-12&&maxCost<1e-12&&maxRow<1e-12);
let variants=0;
if(fs.existsSync(path.join(r,'GPU58.json'))){
 const gpu=JSON.parse(fs.readFileSync(path.join(r,'GPU58.json'),'utf8'));
 for(let i=0;i<gpu.variants.length;i++){
  const v=gpu.variants[i],rec=d.records[i],ref=C.extractReference(rec.family),p=C.makePalette(ref,{...rec.settings,intervalScale:.5});
  assert.deepEqual(p.rgb8,v.palette.rgb8);assert.deepEqual(v.g.map(g=>C.shadeIndex(g,rec.thresholds)),v.baseK);
  assert.deepEqual(v.baseK,v.paletteChangedK);assert.deepEqual(v.g.map(g=>C.shadeIndex(g,v.changedThresholds)),v.changedK);assert(v.independent);variants++;
 }
}
const out={actualSourceSamples:total,realMaterials:d.records.length,paletteRGBExact:true,referenceProvenanceExact:true,maxLabError:maxLab,maxMedoidCostError:maxCost,maxPaletteCoordinateError:maxRow,results,sourcePalette54Reference:true,CSHarpVariantFamiliesChecked:variants};
fs.writeFileSync(path.join(r,'JS_CSHARP58.json'),JSON.stringify(out,null,2));console.log(JSON.stringify(out));
