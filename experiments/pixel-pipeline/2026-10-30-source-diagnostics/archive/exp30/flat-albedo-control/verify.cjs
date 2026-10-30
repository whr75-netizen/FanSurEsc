'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const R=__dirname,read=n=>JSON.parse(fs.readFileSync(path.join(R,n),'utf8')),engine=require('./engine.cjs'),math=require('./palette_math.cjs'),sourceAPI=require('../palette-v4-feature/palette.cjs');
const input=read('INPUT.json'),legacy=read('PALETTE_LEGACY.json'),fixed=read('PALETTE_DISTINCT.json'),results=read('RESULTS.json'),audit=read('MAPPING_AUDIT.json'),summary=read('SUMMARY.json'),checks=[];const snapshot=JSON.stringify({input,legacy,fixed});
function check(name,fn){fn();checks.push({name,pass:true});}
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
check('paired original/flat use identical geometry/g/Q/threshold and palette',()=>{
 for(const prefix of ['legacy','distinct']){const a=results.outputs['pattern-'+prefix],b=results.outputs['flat-'+prefix];for(const field of ['geometryPayloadSHA256','thresholdsSHA256','packetSHA256','paletteIndexSHA256','paletteRecipeSHA256','sourceSelectorSHA256','maskSHA256','paletteKind','spacing'])assert.deepEqual(a.epoch[field],b.epoch[field]);for(let i=0;i<input.cells.length;i++)if(input.cells[i]){assert.equal(a.rows[i].g,b.rows[i].g);assert.equal(a.rows[i].Q,b.rows[i].Q);assert.deepEqual(a.rows[i].uv,b.rows[i].uv);assert.equal(a.rows[i].depth,b.rows[i].depth);}assert.notEqual(a.epoch.effectiveAlbedoInputSHA256,b.epoch.effectiveAlbedoInputSHA256);}
});
check('flat unlit all368 mask cells exactly one original-native test colour',()=>{const r=results.outputs['flat-unlit'];assert.equal(r.rows.filter(Boolean).length,input.hairCells);r.rows.filter(Boolean).forEach(c=>{assert.deepEqual(c.rgb,input.constant.RGB8);assert.deepEqual(c.effectiveSourceRGBAlinear,input.constant.RGBAlinear);assert.equal(c.passthrough,false);});assert.equal(summary['flat-unlit'].finalRGBUnique,1);assert.equal(summary['flat-unlit'].finalRGBComponents4,1);});
check('legacy merges active Q2/Q3, corrected table distinguishes all four fixed-Q probes',()=>{
 const ref=engine.reference(legacy,input.constant.RGBAlinear),old=legacy.perReferenceShadePaletteIndices[ref],now=fixed.perReferenceShadePaletteIndices[ref];assert.equal(old[2],old[3]);assert.equal(new Set(now).size,4);assert.ok(now.every((j,k)=>!k||j>now[k-1]));
 assert.equal(summary['flat-legacy'].QOccupiedBins,3);assert.equal(summary['flat-legacy'].finalRGBUnique,2);assert.equal(summary['flat-distinct'].finalRGBUnique,3);
});
check('active references have native capacity without moving source anchor',()=>{
 for(const row of results.outputs['pattern-distinct'].rows.filter(Boolean)){assert.ok(fixed.perReferenceShadePaletteIndices[row.sourceReferenceId]);assert.equal(new Set(fixed.perReferenceShadePaletteIndices[row.sourceReferenceId]).size,4);assert.deepEqual(fixed.references[row.sourceReferenceId],legacy.references[row.sourceReferenceId]);}
 assert.throws(()=>engine.render({...input,constant:{...input.constant,RGBAlinear:[0,0,0,1]}},fixed,{sourceMode:'flat'}),/capacity/);
});
check('lit emission always directly selects the complete precomputed palette',()=>{for(const name of ['pattern-legacy','flat-legacy','pattern-distinct','flat-distinct']){const model=name.endsWith('distinct')?fixed:legacy;for(const r of results.outputs[name].rows.filter(Boolean)){assert.deepEqual(r.rgb,model.compactPaletteRGB8[model.perReferenceShadePaletteIndices[r.sourceReferenceId][r.Q]]);}assert.equal(summary[name].offExpectedPaletteCells,0);assert.equal(audit[name].relations.completeEmissionKey.multiRGBGroups,0);}});
check('unlit raw-source emission key includes raw source, not a coarser palette ID',()=>assert.equal(audit['pattern-unlit'].relations.completeEmissionKey.multiRGBGroups,0));
check('inherited10 original-colour passthrough fails flat-region invariant and is absent from corrected branch',()=>{
 assert.equal(summary['flat-unlit-inherited-fallback'].offExpectedPaletteCells,10);assert.equal(summary['flat-unlit-inherited-fallback'].finalRGBUnique,8);
 const ids=audit['flat-unlit-inherited-fallback'].emissionRegion4;assert.throws(()=>engine.regionColourTable(results.outputs['flat-unlit-inherited-fallback'].rows,ids),/multiple RGB/);
 engine.regionColourTable(results.outputs['flat-unlit'].rows,audit['flat-unlit'].emissionRegion4);assert.equal(summary['flat-distinct'].offExpectedPaletteCells,0);
});
check('raw Q region is not used as flat colour-region label for multi-source input',()=>{assert.throws(()=>engine.regionColourTable(results.outputs['pattern-legacy'].rows,audit['pattern-legacy'].QRegion4),/multiple RGB/);engine.regionColourTable(results.outputs['flat-distinct'].rows,audit['flat-distinct'].QRegion4);});
check('new family-only diagnostic selector equals legacy selector on validated source samples',()=>{for(const c of input.cells.filter(Boolean)){const s={modelSHA256:legacy.modelSHA256,materialId:c.materialId,uv:c.uv,baseRGBAlinear:c.sourceRGBAlinear};const ref=sourceAPI.referenceForSample(legacy,s,{colourGroupId:0,uncertain:false});assert.equal(engine.reference(legacy,c.sourceRGBAlinear),ref.paletteReferenceId);}});
check('wrong old primary capture, stale binding and stale Q reject',()=>{
 const a=structuredClone(input);a.context.primarySourceId='8d6a0a4cb858aab8e95db46aa5113cfd7bdaec7682c4c4f1bfa2618c0d4a8aa6';assert.throws(()=>engine.render(a,legacy),/sourceId/);
 const b=structuredClone(input);b.bindingReceipt.packetSHA256='old';assert.throws(()=>engine.render(b,legacy),/Stale/);
 const c=structuredClone(input);c.cells.find(Boolean).Q=0;assert.throws(()=>engine.render(c,legacy),/Stale Q/);
});
check('cache epochs change for albedo, palette/lighting and fallback, while original capture is preserved',()=>{const epochs=Object.values(results.outputs).map(o=>o.epochSHA256);assert.equal(new Set(epochs).size,epochs.length);const captures=Object.values(results.outputs).map(o=>o.epoch.primarySourceId);assert.equal(new Set(captures).size,1);});
check('spacing alters palette intervals, never g/Q/source labels',()=>{
 const a=engine.render(input,fixed,{sourceMode:'flat',spacing:.5}),b=engine.render(input,fixed,{sourceMode:'flat',spacing:1});for(let i=0;i<input.cells.length;i++)if(input.cells[i]){assert.equal(a.rows[i].Q,b.rows[i].Q);assert.equal(a.rows[i].sourceReferenceId,b.rows[i].sourceReferenceId);assert.deepEqual(a.rows[i].effectiveSourceRGBAlinear,b.rows[i].effectiveSourceRGBAlinear);}
});
check('all original inputs/models remain unchanged',()=>assert.equal(JSON.stringify({input,legacy,fixed}),snapshot));
check('R6 and previous v4 remain byte-exact',()=>{assert.equal(hash('C:/Users/15352/Desktop/작업폴더/아트검토/31_머리색_슬라이더/index.html'),'138efb1e484004bf707d0b18e055ac4e41e1eb1072c14cf1f8cfcec30688a206');assert.equal(hash(path.join(R,'../palette-v4-feature/CONSTRAINED_64.json')),'03b7147e90782bd0fd68a5b7271d2df57bf09a0fdd731f6b556acdf70ee17979');});
fs.writeFileSync(path.join(R,'API_VERIFIED.json'),JSON.stringify({checks,passed:checks.length,scope:'fixed frame controlled albedo experiment and mapping consistency, not art/temporal/Unity validation'},null,2));console.log(JSON.stringify({passed:checks.length}));
