'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const R=__dirname,read=n=>JSON.parse(fs.readFileSync(path.join(R,n),'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const api=require('./palette.cjs'),input=read('INPUT_SAMPLES.json'),cert=read('FEATURE_CERTIFICATES.json'),expected=read('BUDGET_BINDINGS.json'),checks=[];
function check(name,fn){fn();checks.push({name,pass:true});}
let perturbations=0;
for(const N of [16,32,64])for(const protectedFlag of [false,true]){
 const key=N+(protectedFlag?'-protected':''),model=read(`${protectedFlag?'CONSTRAINED':'PALETTE'}_${N}.json`),before=JSON.stringify(model),P=api.buildPalette(model,1).tablesRGB8;
 check(key+' original sample RGB/output exact and no Q/UV/source mutation',()=>{
  for(const name of ['preserve','simplify'])for(const r of expected.variants[key][name]){if(!r||r.unresolved)continue;const original=input.variants[name].rows[r.index];assert.equal(r.shadeK,original.shadeK);assert.deepEqual(r.sample,original.sample);assert.equal(r.geometryG,original.geometryG);const v=api.referenceForSample(model,r.sample,{colourGroupId:r.appearance,uncertain:false});assert.equal(v.paletteReferenceId,r.paletteReferenceId);assert.deepEqual(P[v.paletteReferenceId][r.shadeK],r.rgb);}
 });
 if(protectedFlag)check(key+' all8 measured source contrasts and direction survive all equal Q',()=>{
  for(const c of cert.filter(c=>c.protect)){
   const refs=c.sourcePair.map(s=>api.referenceForSample(model,{modelSHA256:model.modelSHA256,materialId:s.materialId,uv:s.uv,baseRGBAlinear:s.RGBAlinear},{colourGroupId:s.appearance,uncertain:false}));
   const sign=Math.sign(refs[1].sourceLab[0]-refs[0].sourceLab[0]);for(let k=0;k<4;k++){const difference=sign*(api.rgbLab(P[refs[1].paletteReferenceId][k])[0]-api.rgbLab(P[refs[0].paletteReferenceId][k])[0]);assert.ok(difference>=c.sourceGapL-1e-12);if(N===64)assert.ok(difference-c.sourceGapL<=model.nativeBandWidthL+1e-12);}
  }
 });
 check(key+' m0/native anchors/half interval and source IDs independent of g and spacing',()=>{
  for(const m of [0,.5,1,2]){const p=api.buildPalette(model,m);model.references.forEach((r,i)=>{assert.deepEqual(p.tablesRGB8[i][3],r.anchorRGB8);if(m===0)p.tablesRGB8[i].forEach(rgb=>assert.deepEqual(rgb,r.anchorRGB8));});}
  for(const r of input.variants.preserve.rows){if(!r||r.unresolved)continue;const a={colourGroupId:r.appearance,uncertain:false},ref=api.referenceForSample(model,r.sample,a);for(const g of [-1,0,1,99]){assert.equal(api.referenceForSample(model,{...r.sample,g,screen:[-5,999],depth:999},a).paletteReferenceId,ref.paletteReferenceId);perturbations++;}}
  assert.equal(JSON.stringify(model),before);
 });
}
check('only64 meets measured contrast excess within one native band',()=>{assert.equal(read('CONSTRAINED_16.json').featureConstraintStatus.excessWithinOneNativeBand,false);assert.equal(read('CONSTRAINED_32.json').featureConstraintStatus.excessWithinOneNativeBand,false);assert.equal(read('CONSTRAINED_64.json').featureConstraintStatus.excessWithinOneNativeBand,true);});
check('unconfirmed pair1 is not forced; different-Q pair4 is separately certified',()=>{assert.equal(cert[1].protect,false);assert.equal(cert[4].review.type,'painted feature with differing illumination stages');});
check('other model, missing material and unresolved reject without fallback',()=>{const m=read('CONSTRAINED_64.json'),r=input.variants.preserve.rows.find(r=>r&&!r.unresolved),a={colourGroupId:r.appearance,uncertain:false};assert.throws(()=>api.referenceForSample(m,{...r.sample,modelSHA256:'wrong'},a));assert.throws(()=>api.referenceForSample(m,{...r.sample,materialId:14},a));assert.throws(()=>api.referenceForSample(m,r.sample,{colourGroupId:null,uncertain:true}));});
check('R6 and v3 unchanged',()=>{assert.equal(sha('C:/Users/15352/Desktop/작업폴더/아트검토/31_머리색_슬라이더/index.html'),'138efb1e484004bf707d0b18e055ac4e41e1eb1072c14cf1f8cfcec30688a206');assert.equal(sha(path.join(R,'../palette-v3/SHARED_NATIVE_PALETTE.json')),'7acc7a4ce281eabe22e9092d4638b1dba063e575b536aceca5085af2d9ba412f');assert.equal(sha(path.join(R,'../palette-v3/BINDINGS.json')),'666c5869757a62658db16a80c9373790033728a4dce72db35c837037fa30bbde');});
fs.writeFileSync(path.join(R,'API_VERIFIED.json'),JSON.stringify({checks,passed:checks.length,perturbations,scope:'eight source certificates/default m1; not all authored features, art or temporal pass'},null,2));console.log(JSON.stringify({passed:checks.length,perturbations}));
