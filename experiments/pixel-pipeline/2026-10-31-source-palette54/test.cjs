'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const C=require('./source-palette.cjs'),M=require('./colour-math.cjs'),A=require('./adapter.cjs');
const fixture=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures.json'),'utf8'));
let cases=[];function test(name,fn){fn();cases.push(name);}
const settings={},cuts={};
fixture.families.forEach((f,i)=>{settings[f.id]={count:[4,3,5][i],darkLRatio:.55,darkCRatio:.6,gamma:1,intervalScale:1};cuts[f.id]=Array.from({length:settings[f.id].count-1},(_,k)=>(k+1)/settings[f.id].count);});
const binding=C.buildBinding(fixture.families,settings,cuts),packet=A.packet(binding),output=[];
const gValues=[-.1,0,.1,.249999,.25,.3333333333333333,.5,.75,1,3];
test('sRGB8 decode/encode roundtrip all256 values',()=>{for(let x=0;x<256;x++)assert.equal(Math.round(255*M.encode(M.decode(x/255))),x);});
test('OKLab black/white basis',()=>{assert.deepEqual(M.rgbLab([0,0,0]),[0,0,0]);assert(Math.abs(M.rgbLab([255,255,255])[0]-1)<1e-7);});
test('packet uint4 family offsets match HLSL layout',()=>packet.families.forEach((r,i)=>assert.deepEqual(packet.familyWords[i],[r.paletteOffset,r.paletteCount,r.thresholdOffset,r.thresholdCount])));
for(const row of binding){
 const family=fixture.families.find(f=>f.id===row.id),original=JSON.stringify(family);
 test(row.id+' reference is an observed source/material colour with UV',()=>{
  const observed=C.sourceColours(family),winner=observed.find(s=>s.id===row.reference.provenance.sampleId);
  assert(winner);assert.deepEqual(winner.rgb8,row.reference.rgb8);assert.equal(winner.provenance.imageSHA256,family.source.imageSHA256);
  assert.deepEqual(winner.provenance.uv,family.samples.find(s=>s.id===winner.id).uv);
 });
 test(row.id+' exact source anchor at brightest stage',()=>assert.deepEqual(row.palette.rgb8.at(-1),row.reference.rgb8));
 test(row.id+' RGB8 L order / no duplicate in this diagnostic range',()=>{assert.equal(row.palette.diagnostics.LReversals,0);assert.equal(row.palette.diagnostics.duplicates,0);});
 test(row.id+' same g maps to same k independent of source RGB and palette',()=>{
  const changed=C.makePalette(row.reference,{...row.palette.settings,intervalScale:1.4});
  assert.notDeepEqual(changed.rgb8,row.palette.rgb8);for(const g of gValues){const k=C.shadeIndex(g,row.thresholds);assert.deepEqual(C.resolve(changed,k),changed.rgb8[k]);}
  assert.deepEqual(changed.reference,row.reference);
 });
 test(row.id+' palette and thresholds are independent in binding',()=>{
  const newSettings=structuredClone(settings);newSettings[row.id].intervalScale=1.4;
  const recoloured=C.buildBinding(fixture.families,newSettings,cuts);
  assert.deepEqual(recoloured.map(r=>r.thresholds),binding.map(r=>r.thresholds));
  assert.deepEqual(gValues.map(g=>C.shade(binding,row.id,g).k),gValues.map(g=>C.shade(recoloured,row.id,g).k));
  const newCuts=structuredClone(cuts);newCuts[row.id]=row.thresholds.map(t=>t+.17);
  const reclassified=C.buildBinding(fixture.families,settings,newCuts);
  assert.deepEqual(reclassified.map(r=>r.palette.rgb8),binding.map(r=>r.palette.rgb8));
  assert.notDeepEqual(gValues.map(g=>C.shade(binding,row.id,g).k),gValues.map(g=>C.shade(reclassified,row.id,g).k));
 });
 test(row.id+' final direct P[k], packet equivalence, g cannot scale RGB',()=>{
  for(const g of gValues){const o=C.shade(binding,row.id,g),p=A.replayPacket(packet,row.id,g);
   assert.deepEqual(o.rgb8,row.palette.rgb8[o.k]);assert.deepEqual(p.rgba8,[...o.rgb8,255]);assert.equal(p.k,o.k);
   output.push({family:row.id,g,k:o.k,rgb8:o.rgb8,source:o.anchorProvenance});
  }
  // Two different g in the same band must have bit-identical final colour.
  assert.deepEqual(C.shade(binding,row.id,-.1).rgb8,C.shade(binding,row.id,0).rgb8);
 });
 test(row.id+' interval0 collapses explicitly, not hidden unique-colour enforcement',()=>{
  const p=C.makePalette(row.reference,{...row.palette.settings,intervalScale:0});assert.equal(p.diagnostics.duplicates,p.rgb8.length-1);assert(p.rgb8.every(rgb=>JSON.stringify(rgb)===JSON.stringify(row.reference.rgb8)));
 });
 test(row.id+' threshold equality goes to next band',()=>row.thresholds.forEach((t,k)=>assert.equal(C.shadeIndex(t,row.thresholds),k+1)));
 test(row.id+' legacy final RGB multiply is detected as contract failure',()=>{
  const ref=row.palette.rgb8.at(-1),bad=ref.map(x=>Math.round(x*.72));
  assert(!row.palette.rgb8.some(rgb=>JSON.stringify(rgb)===JSON.stringify(bad)));
 });
 test(row.id+' input/source unchanged',()=>assert.equal(JSON.stringify(family),original));
 test(row.id+' source order does not choose a different reference',()=>assert.deepEqual(C.extractReference({...family,samples:family.samples.slice().reverse()}).rgb8,row.reference.rgb8));
 test(row.id+' Float32 boundary agrees with packet arithmetic',()=>{
  for(const cut of row.thresholds){const v=new Float32Array([cut]),u=new Uint32Array(v.buffer),bits=u[0];
   for(const n of[bits-1,bits,bits+1]){u[0]=n;const g=v[0],expected=packet.thresholds.slice(packet.families.find(f=>f.id===row.id).thresholdOffset,packet.families.find(f=>f.id===row.id).thresholdOffset+row.thresholds.length).filter(t=>g>=t).length;
    assert.equal(C.shadeIndex(g,row.thresholds),expected);
   }
  }
 });
}
test('different materials produce different source-derived anchors',()=>assert.notDeepEqual(binding[0].reference.rgb8,binding[1].reference.rgb8));
test('synthetic independent model/role87 uses same functions',()=>{assert.equal(binding[2].source.materialId,87);assert.notDeepEqual(binding[2].reference.rgb8,binding[0].reference.rgb8);});
test('family mismatch does not borrow a different material colour',()=>{const bad=structuredClone(fixture.families[0]);bad.samples[0].materialId=87;assert.throws(()=>C.extractReference(bad),/mismatch/);});
test('unknown source family rejected',()=>assert.throws(()=>C.shade(binding,'unknown',.5),/not bound/));
test('NaN and non-increasing thresholds rejected',()=>{assert.throws(()=>C.shadeIndex(NaN,[.2]));assert.throws(()=>C.shadeIndex(.2,[.5,.1]));});
test('requested out-of-domain palette interval rejected, not silently brightened',()=>assert.throws(()=>C.makePalette(binding[0].reference,{...settings[binding[0].id],intervalScale:10})));
test('low-chroma and black samples remain explicit cases',()=>{
 for(const rgb of[[0,0,0],[50,50,50]]){const p=C.makePalette({rgb8:rgb},{count:3,darkLRatio:.5,darkCRatio:.5,gamma:1,intervalScale:1});assert.deepEqual(p.rgb8.at(-1),rgb);assert.equal(p.diagnostics.LReversals,0);}
});
test('out-of-gamut dark fixed-hue request reduces chroma explicitly',()=>{
 const p=C.makePalette({rgb8:[0,0,255]},{count:4,darkLRatio:.5,darkCRatio:1,gamma:1,intervalScale:1});
 assert(p.rows.some(r=>r.gamutReduced&&r.usedC<r.requestedC));assert.deepEqual(p.rgb8.at(-1),[0,0,255]);
});
test('Float32-collapsed cuts rejected rather than relabelled silently',()=>assert.throws(()=>C.shadeIndex(.5,[.5,.5+1e-12]),/Float32/));
test('fully transparent source cannot become an invented opaque reference',()=>{
 const f=structuredClone(fixture.families[0]);f.samples.forEach(s=>s.rgba8[3]=0);assert.throws(()=>C.extractReference(f),/No visible/);
});
fs.writeFileSync(path.join(__dirname,'RESULTS.json'),JSON.stringify({cases:cases.length,passed:cases,binding,output,
  paletteOutsideCount:output.filter(o=>!binding.find(r=>r.id===o.family).palette.rgb8.some(p=>JSON.stringify(p)===JSON.stringify(o.rgb8))).length,
  sourceDomainsAutomaticallySegmented:false,regionShapeCorrected:false,UnityRun:false,HLSLCompiled:false,activeProductChanged:false},null,2));
fs.writeFileSync(path.join(__dirname,'PACKET.json'),JSON.stringify(packet,null,2));
console.log(JSON.stringify({tests:cases.length,anchors:binding.map(r=>({family:r.id,rgb8:r.reference.rgb8,source:r.reference.provenance.sampleId})),paletteOutside:0,renderIntegration:false},null,2));
