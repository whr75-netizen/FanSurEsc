(function(global){
'use strict';
function labLinear([r,g,b]){const l=Math.cbrt(.4122214708*r+.5363325363*g+.0514459929*b),m=Math.cbrt(.2119034982*r+.6806995451*g+.1073969566*b),s=Math.cbrt(.0883024619*r+.2817188376*g+.6299787005*b);return [.2104542553*l+.793617785*m-.0040720468*s,1.9779984951*l-2.428592205*m+.4505937099*s,.0259040371*l+.7827717662*m-.808675766*s];}
function rgbLab(rgb){return labLinear(rgb.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;}));}
function referenceForSample(model,sample,appearance){
 if(typeof sample.modelSHA256!=='string'||sample.modelSHA256.toLowerCase()!==model.modelSHA256.toLowerCase())throw Error('Different model; no fallback');
 if(!model.originalMaterialIds.includes(sample.materialId))throw Error('Unmodelled original material; no fallback');
 const g=appearance?.colourGroupId;
 if(appearance?.uncertain||g===null||!Number.isInteger(g)||g<0||g>3)throw Error('Unresolved original appearance; no palette fallback');
 if(!Array.isArray(sample.baseRGBAlinear)||sample.baseRGBAlinear.length!==4||!sample.baseRGBAlinear.every(v=>Number.isFinite(v)&&v>=0&&v<=1))throw Error('Invalid original colour');
 const L=labLinear(sample.baseRGBAlinear.slice(0,3))[0];
 const tone=model.sourceToneClassCutsLabL?Number(L>=model.sourceToneClassCutsLabL[g]):null;
 return {appearanceGroupId:g,sourceToneClass:tone,paletteReferenceId:tone===null?g:2*g+tone,sourceLabL:L};
}
function paletteValue(model,referenceId,shade,m=1){
 if(!Number.isInteger(referenceId)||referenceId<0||!model.references[referenceId])throw Error('Invalid or unresolved palette reference');
 if(!Number.isInteger(shade)||shade<0||shade>3)throw Error('Invalid shade stage');
 if(!Number.isFinite(m)||m<0)throw Error('Invalid palette interval scale');
 const ref=model.references[referenceId],anchor=rgbLab(ref.anchorRGB8),native=model.compactPaletteRGB8[model.perReferenceShadePaletteIndices[referenceId][shade]],end=rgbLab(native);
 const requestedLab=end.map((v,i)=>anchor[i]+m*(v-anchor[i]));
 // Anchor remains the exact observed texel, including zero interval and ref stage.
 if(m===0||shade===model.referenceShadeK)return {rgb:ref.anchorRGB8.slice(),requestedLab,intervalScale:m,gamutReduced:false,clampedL:false};
 if(m===1)return {rgb:native.slice(),requestedLab,intervalScale:m,gamutReduced:false,clampedL:false};
 const L=Math.min(1,Math.max(0,requestedLab[0])),h=Math.atan2(requestedLab[2],requestedLab[1]),requestedC=Math.hypot(requestedLab[1],requestedLab[2]);
 const linear=C=>{const a=C*Math.cos(h),b=C*Math.sin(h),l=(L+.3963377774*a+.2158037573*b)**3,m=(L-.1055613458*a-.0638541728*b)**3,s=(L-.0894841775*a-1.291485548*b)**3;return [4.0767416621*l-3.3077115913*m+.2309699292*s,-1.2684380046*l+2.6097574011*m-.3413193965*s,-.0041960863*l-.7034186147*m+1.707614701*s];};
 const valid=a=>a.every(x=>x>=-1e-9&&x<=1+1e-9);let usedC=requestedC,channels=linear(usedC);
 if(!valid(channels)){let lo=0,hi=requestedC;for(let n=0;n<28;n++){const c=(lo+hi)/2;if(valid(linear(c)))lo=c;else hi=c;}usedC=lo;channels=linear(usedC);}
 const rgb=channels.map(x=>{x=Math.max(0,Math.min(1,x));return Math.round(255*(x<=.0031308?12.92*x:1.055*x**(1/2.4)-.055));});
 return {rgb,requestedLab,usedL:L,requestedC,usedC,intervalScale:m,gamutReduced:requestedC-usedC>1e-7,clampedL:L!==requestedLab[0]};
}
function buildPalette(model,m=1){const diagnostics=model.references.map((_,r)=>[0,1,2,3].map(k=>paletteValue(model,r,k,m)));return {tablesRGB8:diagnostics.map(row=>row.map(v=>v.rgb)),diagnostics};}
const api={labLinear,rgbLab,referenceForSample,paletteValue,buildPalette};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else global.PaletteV2=api;
})(typeof globalThis!=='undefined'?globalThis:this);
