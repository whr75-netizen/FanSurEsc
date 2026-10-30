(function(global){
'use strict';
const base=typeof module!=='undefined'&&module.exports?require('./palette_math.cjs'):global.PaletteV2;
const cachedLabs=new WeakMap();
function referenceForSample(model,sample,appearance){
 if(typeof sample.modelSHA256!=='string'||sample.modelSHA256.toLowerCase()!==model.modelSHA256.toLowerCase())throw Error('Different source model; no colour fallback');
 if(!model.originalMaterialIds.includes(sample.materialId))throw Error('Unmodelled source material; no colour fallback');
 if(appearance?.uncertain||!Number.isInteger(appearance?.colourGroupId)||!model.originalAppearanceGroupIds.includes(appearance.colourGroupId))throw Error('Unresolved source appearance; no colour fallback');
 if(!Array.isArray(sample.baseRGBAlinear)||sample.baseRGBAlinear.length!==4||!sample.baseRGBAlinear.every(v=>Number.isFinite(v)&&v>=0&&v<=1))throw Error('Invalid unlit source colour');
 const sourceLab=base.labLinear(sample.baseRGBAlinear.slice(0,3));let labs=cachedLabs.get(model);
 if(!labs){labs=model.references.map(r=>base.rgbLab(r.anchorRGB8));cachedLabs.set(model,labs);}
 let best=0,error=Infinity;
 for(let i=0;i<labs.length;i++){const d=labs[i].reduce((s,v,j)=>s+(v-sourceLab[j])**2,0);if(d<error){best=i;error=d;}}
 const unconstrainedReferenceId=best;
 if(model.sourceSelectionKnots){
  const knots=model.sourceSelectionKnots,L=sourceLab[0];let p=0;
  while(p+1<knots.length&&L>knots[p+1].sourceL)p++;
  if(p+1===knots.length)best=knots[p].paletteReferenceId;
  else{const a=knots[p],b=knots[p+1],f=Math.max(0,Math.min(1,(L-a.sourceL)/(b.sourceL-a.sourceL)));best=Math.round(a.paletteReferenceId+f*(b.paletteReferenceId-a.paletteReferenceId));}
  error=labs[best].reduce((s,v,j)=>s+(v-sourceLab[j])**2,0);
 }
 return {appearanceGroupId:appearance.colourGroupId,paletteReferenceId:best,unconstrainedReferenceId,sourceLab,quantizationErrorLab:Math.sqrt(error),sourceToneClass:null};
}
const api={referenceForSample,buildPalette:base.buildPalette,paletteValue:base.paletteValue,rgbLab:base.rgbLab,labLinear:base.labLinear};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else global.PaletteV4=api;
})(typeof globalThis!=='undefined'?globalThis:this);
