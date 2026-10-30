'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const R=__dirname,old=path.join(R,'../palette-v2'),main='C:/Users/15352/Documents/Codex/2026-10-27/task-2/render-fix21/author33/feature34';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,'')),write=(n,v)=>fs.writeFileSync(path.join(R,n),JSON.stringify(v,null,2)),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const source=read(path.join(old,'PATTERN_REFERENCE_PALETTE.json')),binding=read(path.join(main,'ribbon-path/PALETTE_V2_BINDING.json')),packets=read(path.join(main,'ribbon-path/GEOMETRY_PACKETS.json'));
const{rgbLab,referenceForSample,buildPalette}=require('./palette.cjs');
const origins=new Map();for(const ref of source.references){origins.set(ref.anchorRGB8.join(','),ref.anchorOrigin);origins.set(ref.lowerSupportRGB8.join(','),ref.lowerSupportOrigin);}
const native=source.compactPaletteRGB8.map((rgb,oldIndex)=>({rgb,oldIndex,origin:origins.get(rgb.join(',')),L:rgbLab(rgb)[0]})).sort((a,b)=>a.L-b.L||a.oldIndex-b.oldIndex);
function makeModel(refs,status){return {kind:'shared-native-palette-reference-candidate',version:3,sourceId:source.sourceId,modelSHA256:source.modelSHA256,originalMaterialIds:source.originalMaterialIds,
 originalAppearanceGroupIds:[...new Set(source.references.map(r=>r.appearanceGroupId))].sort((a,b)=>a-b),
 status,
 paletteInputSHA256:sha(path.join(old,'PATTERN_REFERENCE_PALETTE.json')),referenceShadeK:3,
 sourceReferenceRule:'nearest full OKLab native colour in one verified warm chromatic family; appearance remains metadata and geometry signal, not an independent far-apart palette bank',
 shadeRule:'same fixed shadeK; stages0/1 use immediately preceding shared native colour, stages2/3 use source reference; no per-appearance tone cut or far-bank jump',
 intervalRule:'Lab(native anchor)+m*(Lab(measured shade colour)-Lab(native anchor)); source selection and Q(g) labels never use m',
 references:refs,compactPaletteRGB8:refs.map(v=>v.anchorRGB8),
 perReferenceShadePaletteIndices:refs.map((_,i)=>[Math.max(0,i-1),Math.max(0,i-1),i,i]),
 sourceFeatureIdRemainsNull:true,sourceToneClassRemovedFromPaletteSelection:true,originalAppearanceClassifierUnchanged:true,
 limitations:['finite16-colour quantization creates new tone boundaries and can merge small real colour differences; inspect edge evidence, not only pixel errors',
 'adjacent native colour gaps are data-derived and unequal; common predecessor rule is a candidate shading model, not an approved art style',
 'material14 and other model SHA are unmodelled; no source colour fallback','continuous source gradient versus normalization remains unchosen; this mapping reads whichever legitimate source sample upstream supplies']};}
const existing=makeModel(native.map((v,i)=>({id:i,anchorRGB8:v.rgb,anchorOrigin:v.origin,originalPaletteIndex:v.oldIndex})),'unapproved mapping-only ablation using exact previous16 colours');
const coverage=read(path.join(R,'NATIVE_COVERAGE_FIT.json'));
if(coverage.sourceId!==source.sourceId||coverage.modelSHA256!==source.modelSHA256)throw Error('Native fit belongs to another source/model');
const model=makeModel(coverage.references,'unapproved candidate with same16 colour budget, measured native support coverage and shared reference mapping');
model.nativeCoverageFitSHA256=sha(path.join(R,'NATIVE_COVERAGE_FIT.json'));model.fitRule=coverage.fitRule;
model.chromaticFamilyScope='one source-evidenced warm family in current materials11/12/13; other colour families require separate source fit and classification, never a warm fallback';
write('SHARED_EXISTING16_ABLATION.json',existing);write('SHARED_NATIVE_PALETTE.json',model);
function bind(m){const P=buildPalette(m,1).tablesRGB8,variants={};
for(const name of ['preserve','simplify']){
 const rows=binding.variants[name].map((q,i)=>{
  if(!q)return null;if(q.unresolved)return{index:i,unresolved:true};
  const sample={modelSHA256:m.modelSHA256,materialId:packets[i].role,uv:q.sourceUV,baseRGBAlinear:q.sourceRGBAlinear};
  const ref=referenceForSample(m,sample,{colourGroupId:q.appearanceGroup,uncertain:false});
  return {index:i,sample,appearance:q.appearanceGroup,shadeK:q.shade,geometryG:q.geometryG,geometryUV:q.geometryUV,oldToneClass:q.sourceToneClass,
   oldReferenceId:q.paletteReferenceId,oldRGB8:q.rgb,...ref,rgb:P[ref.paletteReferenceId][q.shade]};
 });variants[name]={rows};
}return variants;}
const variants=bind(model),ablation=bind(existing);
write('BINDINGS.json',{sourceId:model.sourceId,modelSHA256:model.modelSHA256,mainBindingSHA256:sha(path.join(main,'ribbon-path/PALETTE_V2_BINDING.json')),
 packetSHA256:sha(path.join(main,'ribbon-path/GEOMETRY_PACKETS.json')),inputPolicy:'unadopted tone-boundary after trial not used; preserve-before/simplify-before samples held fixed',
 variants,existing16Ablation:ablation});
const newL=model.references.map(v=>rgbLab(v.anchorRGB8)[0]);
console.log(JSON.stringify({paletteColours:newL.length,maxExistingNativeGapL:Math.max(...native.slice(1).map((v,i)=>v.L-native[i].L)),maxCoverageGapL:Math.max(...newL.slice(1).map((v,i)=>v-newL[i])),variants:Object.fromEntries(Object.entries(variants).map(([k,v])=>[k,v.rows.filter(r=>r&&!r.unresolved).length]))}));
