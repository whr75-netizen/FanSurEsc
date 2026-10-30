'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const R=__dirname,read=n=>JSON.parse(fs.readFileSync(path.join(R,n),'utf8').replace(/^\uFEFF/,'')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const model=read('SHARED_NATIVE_PALETTE.json'),bindings=read('BINDINGS.json'),fit=read('NATIVE_COVERAGE_FIT.json'),base=fs.readFileSync(path.join(R,'../palette-v2/PATTERN_REFERENCE_PALETTE.json'),'utf8');
const{buildPalette,referenceForSample,rgbLab}=require('./palette.cjs'),original=JSON.stringify({model,bindings,fit}),checks=[];
function check(name,fn){fn();checks.push({name,pass:true});}
const P=buildPalette(model,1).tablesRGB8;
check('same16 measured budget, monotone measured native palette and bounded adjacent gap',()=>{
 assert.equal(model.compactPaletteRGB8.length,JSON.parse(base).compactPaletteRGB8.length);const L=model.references.map(r=>rgbLab(r.anchorRGB8)[0]);
 for(let i=1;i<L.length;i++){assert.ok(L[i]>L[i-1]);assert.ok(L[i]-L[i-1]<=2*fit.nativeBandWidthL);}
});
let samples=0,perturbations=0;
for(const name of ['preserve','simplify']){
 const rows=bindings.variants[name].rows.filter(r=>r&&!r.unresolved);samples+=rows.length;
 check(name+' actual source samples give stored new output',()=>{for(const r of rows){const v=referenceForSample(model,r.sample,{colourGroupId:r.appearance,uncertain:false});assert.equal(v.paletteReferenceId,r.paletteReferenceId);assert.deepEqual(P[v.paletteReferenceId][r.shadeK],r.rgb);}});
 check(name+' g/depth/screen and role bank cannot change source reference',()=>{for(const r of rows){
  for(const a of [0,1,2,3]){const sample={...r.sample,g:a*100,screen:[999,-999],depth:0};assert.equal(referenceForSample(model,sample,{colourGroupId:a,uncertain:false}).paletteReferenceId,r.paletteReferenceId);perturbations++;}
 }});
 check(name+' original appearance/shade/source/geometry values unchanged',()=>{
  const latest=JSON.parse(fs.readFileSync('C:/Users/15352/Documents/Codex/2026-10-27/task-2/render-fix21/author33/feature34/ribbon-path/PALETTE_V2_BINDING.json','utf8')).variants[name];
  for(const r of rows){const q=latest[r.index];assert.equal(r.appearance,q.appearanceGroup);assert.equal(r.shadeK,q.shade);assert.deepEqual(r.sample.baseRGBAlinear,q.sourceRGBAlinear);assert.deepEqual(r.sample.uv,q.sourceUV);assert.deepEqual(r.geometryUV,q.geometryUV);assert.equal(r.geometryG,q.geometryG);}
 });
}
check('zero interval, seven multiplier reference anchors and exact half-gap',()=>{
 for(const m of [0,.25,.5,1,1.5,2,16]){const p=buildPalette(model,m);model.references.forEach((r,i)=>{assert.deepEqual(p.tablesRGB8[i][3],r.anchorRGB8);if(m===0)p.tablesRGB8[i].forEach(rgb=>assert.deepEqual(rgb,r.anchorRGB8));});}
 const a=buildPalette(model,0),b=buildPalette(model,.5),c=buildPalette(model,1);
 model.references.forEach((r,i)=>[0,1,2,3].forEach(k=>[0,1,2].forEach(j=>assert.ok(Math.abs(b.diagnostics[i][k].requestedLab[j]-(a.diagnostics[i][k].requestedLab[j]+c.diagnostics[i][k].requestedLab[j])/2)<1e-12))));
});
check('independent shade labels index the completed palette, not continuous g multiplication',()=>{
 for(const v of Object.values(bindings.variants))for(const r of v.rows){if(!r||r.unresolved)continue;assert.deepEqual(r.rgb,P[r.paletteReferenceId][r.shadeK]);}
});
check('other model, unmodelled material and unresolved source reject without colour fallback',()=>{
 const r=bindings.variants.preserve.rows.find(r=>r&&!r.unresolved),a={colourGroupId:r.appearance,uncertain:false};
 assert.throws(()=>referenceForSample(model,{...r.sample,modelSHA256:'wrong'},a));assert.throws(()=>referenceForSample(model,{...r.sample,materialId:14},a));
 assert.throws(()=>referenceForSample(model,r.sample,{colourGroupId:null,uncertain:true}));assert.throws(()=>referenceForSample(model,r.sample,{colourGroupId:-2,uncertain:false}));
});
check('source/model/control objects not mutated',()=>assert.equal(JSON.stringify({model,bindings,fit}),original));
check('active R6 and v2 candidate preserved',()=>{
 assert.equal(sha('C:/Users/15352/Desktop/작업폴더/아트검토/31_머리색_슬라이더/index.html'),'138efb1e484004bf707d0b18e055ac4e41e1eb1072c14cf1f8cfcec30688a206');
 assert.equal(sha(path.join(R,'../palette-v2/PATTERN_REFERENCE_PALETTE.json')),'75368163de04ab6267486e7e0dc900e8e43c468234d101aaad6e461642d9094e');
});
fs.writeFileSync(path.join(R,'API_VERIFIED.json'),JSON.stringify({checks,passed:checks.length,samples,perturbations,scope:'source mapping/spacing contract, not art/temporal approval'},null,2));console.log(JSON.stringify({passed:checks.length,samples,perturbations}));
