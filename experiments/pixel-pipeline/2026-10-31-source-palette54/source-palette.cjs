'use strict';
const M=require('./colour-math.cjs');
const finite=v=>Number.isFinite(v);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function sourceColours(family){
 const {source,samples}=family;
 if(!source?.modelSHA256||!source.imageSHA256||source.uvOrigin!=='top-left'||source.encoding!=='srgb8')throw Error('Explicit original model/image/UV/encoding required');
 if(!Array.isArray(source.factorLinear)||source.factorLinear.length!==4||!source.factorLinear.every(x=>finite(x)&&x>=0&&x<=1))throw Error('Linear material factor required');
 return samples.map(s=>{
  if(s.materialId!==source.materialId||s.imageSHA256!==source.imageSHA256)throw Error('Source material/image family mismatch');
  if(!s.id||!Array.isArray(s.uv)||s.uv.length!==2||!s.uv.every(finite)||!s.texel?.every(Number.isInteger))throw Error('Original sample UV/texel missing');
  if(!Array.isArray(s.rgba8)||s.rgba8.length!==4||!s.rgba8.every(x=>Number.isInteger(x)&&x>=0&&x<=255)||!(s.weight>0&&finite(s.weight)))throw Error('Invalid native texel sample');
  const alpha=s.rgba8[3]/255*source.factorLinear[3];
  const linear=s.rgba8.slice(0,3).map((x,i)=>M.decode(x/255)*source.factorLinear[i]);
  return {id:s.id,linear,lab:M.labLinear(linear),rgb8:linear.map(x=>Math.round(255*M.encode(x))),weight:s.weight*alpha,
   provenance:{modelSHA256:source.modelSHA256,materialId:source.materialId,imageSHA256:source.imageSHA256,
    sampleId:s.id,primitiveId:s.primitiveId,triangle:s.triangle,uv:s.uv,texel:s.texel,nativeRGBA8:s.rgba8,factorLinear:source.factorLinear}};
 }).filter(s=>s.weight>0);
}
function extractReference(family){
 const samples=sourceColours(family);if(!samples.length)throw Error('No visible original samples in source domain');
 // Weighted squared-distance medoid: an OBSERVED source/material colour wins.
 // It is not a screenshot average or an automatic semantic-feature detector.
 const ranked=samples.map(candidate=>({candidate,cost:samples.reduce((sum,s)=>sum+s.weight*s.lab.reduce((q,x,i)=>q+(x-candidate.lab[i])**2,0),0)}));
 ranked.sort((a,b)=>a.cost-b.cost||a.candidate.id.localeCompare(b.candidate.id,'en'));
 const {candidate,cost}=ranked[0];return {rgb8:candidate.rgb8.slice(),lab:candidate.lab.slice(),provenance:candidate.provenance,
  extraction:{method:'observed weighted squared-OKLab medoid',sampleCount:samples.length,cost,domainId:family.domainId}};
}
function makePalette(reference,settings){
 const {count,darkLRatio,darkCRatio,gamma,intervalScale}=settings;
 if(!Number.isInteger(count)||count<2||count>256||![darkLRatio,darkCRatio].every(x=>finite(x)&&x>=0&&x<=1)||!(gamma>0&&finite(gamma))||!(intervalScale>=0&&finite(intervalScale)))throw Error('Invalid explicit palette parameters');
 const base=M.lch(reference.rgb8),rows=[];
 for(let k=0;k<count;k++){
  const t=(k/(count-1))**gamma;
  const nativeL=base.L*(darkLRatio+(1-darkLRatio)*t),nativeC=base.C*(darkCRatio+(1-darkCRatio)*t);
  // The only adjustable multiplier scales palette-coordinate DIFFERENCES.
  // g is absent from this function and never multiplies final RGB.
  const L=base.L+intervalScale*(nativeL-base.L),C=base.C+intervalScale*(nativeC-base.C);
  if(L<0||L>1||C<0)throw Error('Requested palette interval exceeds declared L/C domain');
  const out=k===count-1||intervalScale===0?{rgb8:reference.rgb8.slice(),usedC:base.C,gamutReduced:false}:M.gamut(L,C,base.h);
  rows.push({...out,targetL:L,requestedC:C,hue:base.h,anchor:k===count-1});
 }
 const tables=rows.map(r=>r.rgb8),actual=tables.map(M.lch),duplicates=count-new Set(tables.map(JSON.stringify)).size;
 return {rgb8:tables,rows,reference,settings:{...settings},diagnostics:{duplicates,
  actualLabL:actual.map(x=>x.L),LReversals:actual.slice(1).filter((x,i)=>x.L<actual[i].L-1e-9).length,
  adjacentDeltaE:tables.slice(1).map((rgb,i)=>Math.hypot(...M.rgbLab(rgb).map((x,c)=>x-M.rgbLab(tables[i])[c])))}};
}
function shadeIndex(g,thresholds){
 if(!finite(g)||!Array.isArray(thresholds)||!thresholds.every(finite)||thresholds.some((x,i)=>i&&x<=thresholds[i-1]))throw Error('Finite g and strictly sorted shade thresholds required');
 // Float32 is the declared light/threshold interchange with the shader packet.
 // No epsilon and no per-frame range normalization.
 const x=Math.fround(g),cuts=thresholds.map(Math.fround);
 if(!finite(x)||!cuts.every(finite)||cuts.some((t,i)=>i&&t<=cuts[i-1]))throw Error('Shade inputs collapse/exceed Float32 domain');
 return cuts.reduce((k,t)=>k+Number(x>=t),0);
}
function resolve(palette,k){
 if(!Number.isInteger(k)||k<0||k>=palette.rgb8.length)throw Error('Unbound shade index');
 return palette.rgb8[k].slice();
}
function buildBinding(families,settingsByFamily,thresholdsByFamily){
 const rows=families.map(f=>{
  const reference=extractReference(f),palette=makePalette(reference,settingsByFamily[f.id]),thresholds=thresholdsByFamily[f.id];
  shadeIndex(0,thresholds);if(thresholds.length!==palette.rgb8.length-1)throw Error('Palette/cut count mismatch');
  return {id:f.id,source:f.source,reference,palette,thresholds:thresholds.slice()};
 });
 if(new Set(rows.map(r=>r.id)).size!==rows.length)throw Error('Duplicate source-family id');
 return rows;
}
function shade(binding,sourceFamilyId,g){
 const row=binding.find(r=>r.id===sourceFamilyId);if(!row)throw Error('Source family not bound');
 const k=shadeIndex(g,row.thresholds);return {sourceFamilyId,k,rgb8:resolve(row.palette,k),anchorProvenance:row.reference.provenance};
}
module.exports={sourceColours,extractReference,makePalette,shadeIndex,resolve,buildBinding,shade};
