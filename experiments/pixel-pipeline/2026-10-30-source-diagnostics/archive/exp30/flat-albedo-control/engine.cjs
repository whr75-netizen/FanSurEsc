(function(global){'use strict';
const math=typeof module!=='undefined'&&module.exports?require('./palette_math.cjs'):global.PaletteV2;
const encode=rgba=>rgba.slice(0,3).map(v=>Math.round(255*(v<=.0031308?12.92*v:1.055*v**(1/2.4)-.055)));
function validate(input,model){
 if(input.context.primarySourceId!==model.sourceId)throw Error('Different primary sourceId; no old-source binding reuse');
 if(input.context.modelSHA256!==model.modelSHA256)throw Error('Different model');
 if(input.bindingReceipt.sourceId!==input.context.primarySourceId||input.bindingReceipt.modelSHA256!==input.context.modelSHA256||input.bindingReceipt.packetSHA256!==input.context.packetSHA256)throw Error('Stale capture/binding epoch');
 if(!input.context.packetSHA256||input.cells.length!==input.width*input.height)throw Error('Missing geometry epoch');
 if(input.cells.filter(Boolean).length!==input.hairCells)throw Error('Incomplete known hair geometry mask');
 for(const c of input.cells)if(c){if(!model.originalMaterialIds.includes(c.materialId))throw Error('Unmodelled source material');if(c.Q!==input.thresholds.filter(t=>c.g>=t).length)throw Error('Stale Q/g');}
}
function reference(model,rgba){
 const sourceLab=math.labLinear(rgba.slice(0,3));let id=0,error=Infinity;
 if(model.sourceSelectionKnots){const ks=model.sourceSelectionKnots,L=sourceLab[0];let p=0;while(p+1<ks.length&&L>ks[p+1].sourceL)p++;if(p+1===ks.length)id=ks[p].paletteReferenceId;else{const a=ks[p],b=ks[p+1],f=Math.max(0,Math.min(1,(L-a.sourceL)/(b.sourceL-a.sourceL)));id=Math.round(a.paletteReferenceId+f*(b.paletteReferenceId-a.paletteReferenceId));}}
 else model.references.forEach((r,i)=>{const d=math.rgbLab(r.anchorRGB8).reduce((s,v,k)=>s+(v-sourceLab[k])**2,0);if(d<error){error=d;id=i;}});
 return id;
}
function compileDistinct(model){
 const clone=JSON.parse(JSON.stringify(model)),N=model.references.length,S=4,span=model.fixedShadowTargetGapL,refs=model.references.map(r=>math.rgbLab(r.anchorRGB8)),capacity=[];
 clone.perReferenceShadePaletteIndices=refs.map((anchor,ref)=>{
  if(ref<S-1){capacity.push({reference:ref,reason:'fewer than4 native colours at/below fixed anchor'});return null;}
  const target=Array.from({length:S},(_,k)=>anchor.map((v,j)=>j===0?v-span*(S-1-k)/(S-1):v));
  const cost=(k,j)=>refs[j].reduce((s,v,a)=>s+(v-target[k][a])**2,0),dp=Array.from({length:S},()=>Array(N).fill(Infinity)),prev=Array.from({length:S},()=>Array(N).fill(-1));
  for(let j=0;j<ref;j++)dp[0][j]=cost(0,j);
  for(let k=1;k<S;k++)for(let j=k;j<=ref;j++){if(k===S-1&&j!==ref)continue;for(let h=k-1;h<j;h++){const v=dp[k-1][h]+cost(k,j);if(v<dp[k][j]){dp[k][j]=v;prev[k][j]=h;}}}
  let j=ref,out=[ref];for(let k=S-1;k>0;k--){j=prev[k][j];out.unshift(j);}if(out.some(j=>j<0))throw Error('Distinct-stage palette infeasible');return out;
 });
 clone.kind='diagnostic-distinct-Q-stage-palette';clone.paletteCapacityFailures=capacity;clone.diagnosticOnly=true;clone.legacyFeatureCertificatesNotRevalidated=true;clone.featureConstraintStatus={applied:false,reason:'diagnostic Q-stage table replaces legacy shade table; not an art/feature certification'};clone.constraintScope='Q-stage injectivity at default spacing, active references with sufficient measured native support';clone.shadeRule='4 distinct native entries below unchanged anchor, closest ordered fit across original measured shadow span; no g-dependent RGB multiplication';return clone;
}
function render(input,model,{sourceMode='pattern',lit=true,legacyFallback=false,spacing=1}={}){
 if(!['pattern','flat'].includes(sourceMode)||typeof lit!=='boolean')throw Error('Invalid diagnostic branch');
 validate(input,model);const rgba=Uint8ClampedArray.from(atobCompat(input.originalRGBA),c=>c.charCodeAt(0)),rows=[];
 for(const c of input.cells){if(!c){rows.push(null);continue;}const source=sourceMode==='flat'?input.constant.RGBAlinear:c.sourceRGBAlinear,ref=reference(model,source);let rgb;
  if(legacyFallback&&c.originalFeatureUnknown){const p=((Math.floor(c.index/input.width)*2)*input.displayWidth+(c.index%input.width)*2)*4;rgb=Array.from(rgba.slice(p,p+3));}
  else if(!lit)rgb=encode(source);
  else{if(!model.perReferenceShadePaletteIndices[ref])throw Error('Native palette capacity insufficient at fixed source anchor');rgb=math.paletteValue(model,ref,c.Q,spacing).rgb;}
  for(let dy=0;dy<2;dy++)for(let dx=0;dx<2;dx++){const p=((Math.floor(c.index/input.width)*2+dy)*input.displayWidth+c.index%input.width*2+dx)*4;rgba.set(rgb,p);}
  const emissionKey=lit?[c.sourceFamilyId,ref,c.Q]:[c.sourceFamilyId,'raw-unlit-source',...source.slice(0,3)];
  rows.push({...c,effectiveSourceRGBAlinear:source.slice(),sourceReferenceId:ref,rgb:rgb.slice(),emissionKey:JSON.stringify(emissionKey),passthrough:legacyFallback&&c.originalFeatureUnknown});
 }
 return {pixels:Array.from(rgba),rows};
}
function atobCompat(s){return typeof atob==='function'?atob(s):Buffer.from(s,'base64').toString('latin1');}
function regionColourTable(rows,regionIds){const map=new Map();for(const r of rows)if(r){const id=regionIds[r.index],rgb=r.rgb.join(',');if(map.has(id)&&map.get(id)!==rgb)throw Error('Region label maps to multiple RGBs; source reference missing from emission label');map.set(id,rgb);}return Object.fromEntries(map);}
const api={validate,reference,compileDistinct,render,regionColourTable,encode};if(typeof module!=='undefined'&&module.exports)module.exports=api;else global.FlatControl=api;
})(typeof globalThis!=='undefined'?globalThis:this);
