'use strict';
const C=require('./source-palette.cjs');
// Explicit family ordinal -> material/source receipt. No model-role numbers.
function packet(binding){
 const rgb8=[],thresholds=[],families=[];
 for(const r of binding){
  families.push({id:r.id,materialId:r.source.materialId,paletteOffset:rgb8.length,
   paletteCount:r.palette.rgb8.length,thresholdOffset:thresholds.length,thresholdCount:r.thresholds.length,
   source:r.reference.provenance});
  rgb8.push(...r.palette.rgb8.map(v=>[...v,255]));thresholds.push(...r.thresholds.map(Math.fround));
 }
 return {format:'source-palette54-rgb8-point/v1',rgb8,thresholds,families,
  familyWords:families.map(r=>[r.paletteOffset,r.paletteCount,r.thresholdOffset,r.thresholdCount]),
  outputContract:'Opaque RGB8 direct lookup; no subsequent light/G/colour interpolation. Shader linear/sRGB target roundtrip must be validated before integration.'};
}
function replayPacket(p,familyId,g){
 const r=p.families.find(x=>x.id===familyId);if(!r)throw Error('Unbound family');
 const k=C.shadeIndex(g,p.thresholds.slice(r.thresholdOffset,r.thresholdOffset+r.thresholdCount));
 return {k,rgba8:p.rgb8[r.paletteOffset+k].slice()};
}
module.exports={packet,replayPacket};
