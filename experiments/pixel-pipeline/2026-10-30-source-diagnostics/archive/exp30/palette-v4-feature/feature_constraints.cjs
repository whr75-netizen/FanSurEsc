'use strict';
const fs=require('node:fs'),path=require('node:path'),R=__dirname,read=n=>JSON.parse(fs.readFileSync(path.join(R,n),'utf8'));
const base=require('./palette.cjs'),audit=read('NINE_NATIVE_AUDIT.json'),decisions=read('AUDIT_DECISIONS.json');
// These are source audit certificates, not screen-coordinate shader exceptions.
// Pair1 has no convincing local colour boundary at final pixel size. Pair4 is
// protected at equal illumination; differing actual Q may legitimately cancel.
const certificate=audit.map(e=>({id:e.id,sourcePair:e.endpoints.map(q=>({materialId:q.sample.materialId,uv:q.sample.uv,RGBAlinear:q.sample.baseRGBAlinear,appearance:q.appearance})),
 sourceGapL:e.sourceGapL,sourceGapLab:e.sourceGapLab,review:decisions.find(d=>d.id===e.id),
 protect:decisions.find(d=>d.id===e.id).protect,requiredContrastRule:'measured original unlit L difference, at every equal shade stage; no epsilon RGB separation'}));
fs.writeFileSync(path.join(R,'FEATURE_CERTIFICATES.json'),JSON.stringify(certificate,null,2));
for(const N of [16,32,64]){
 const model=read(`PALETTE_${N}.json`),P=base.buildPalette(model,1).tablesRGB8,levels=P.map(row=>[base.rgbLab(row[0])[0],base.rgbLab(row[3])[0]]),knots=[],edges=[];
 const add=s=>{const L=base.labLinear(s.RGBAlinear.slice(0,3))[0];let i=knots.findIndex(q=>Math.abs(q.sourceL-L)<1e-13);if(i<0){i=knots.length;knots.push({sourceL:L,sample:s});}return i;};
 for(const e of certificate)if(e.protect){let a=add(e.sourcePair[0]),b=add(e.sourcePair[1]);if(knots[a].sourceL>knots[b].sourceL)[a,b]=[b,a];edges.push({a,b,gap:e.sourceGapL,certificateId:e.id});}
 const order=knots.map((_,i)=>i).sort((a,b)=>knots[a].sourceL-knots[b].sourceL),rank=new Map(order.map((i,j)=>[i,j])),ks=order.map(i=>knots[i]);
 const es=edges.map(e=>({...e,a:rank.get(e.a),b:rank.get(e.b)}));for(let i=1;i<ks.length;i++)es.push({a:i-1,b:i,gap:0,orderOnly:true});
 const incoming=ks.map((_,i)=>es.filter(e=>e.b===i)),outgoing=ks.map((_,i)=>es.filter(e=>e.a===i));
 const ok=(a,b,gap)=>levels[b].every((v,k)=>v-levels[a][k]>=gap-1e-12),ids=ks.map(()=>0);let feasible=true;
 for(let i=0;i<ks.length;i++){const choices=levels.map((_,j)=>j).filter(j=>incoming[i].every(e=>ok(ids[e.a],j,e.gap)));if(!choices.length){feasible=false;break;}ids[i]=choices[0];}
 if(!feasible){fs.writeFileSync(path.join(R,`CONSTRAINED_${N}.json`),JSON.stringify({budget:N,feasible:false,reason:'measured feature contrasts exceed shared native palette capacity',certificates:certificate},null,2));continue;}
 // Constrained coordinate descent to nearest measured source colour. All
 // accepted states preserve every certified equal-Q contrast and global order.
 let moves=0,passes=0;
 while(true){let changed=false;passes++;
  for(let i=0;i<ks.length;i++){
   const sourceLab=base.labLinear(ks[i].sample.RGBAlinear.slice(0,3));
   const cost=j=>base.rgbLab(model.references[j].anchorRGB8).reduce((s,v,k)=>s+(v-sourceLab[k])**2,0);
   const choices=levels.map((_,j)=>j).filter(j=>incoming[i].every(e=>ok(ids[e.a],j,e.gap))&&outgoing[i].every(e=>ok(j,ids[e.b],e.gap)));
   const best=choices.sort((a,b)=>cost(a)-cost(b)||a-b)[0];if(cost(best)<cost(ids[i])-1e-15){ids[i]=best;moves++;changed=true;}
  }if(!changed)break;if(passes>10000)throw Error('Feature assignment did not converge');
 }
 const protectedPairs=es.filter(e=>!e.orderOnly).map(e=>({...e,sourceL:[ks[e.a].sourceL,ks[e.b].sourceL],referenceIds:[ids[e.a],ids[e.b]],outputContrastAtEqualQ:levels[ids[e.b]].map((v,k)=>v-levels[ids[e.a]][k])}));
 const fit=read(`PALETTE_${N}.json`);
 model.sourceSelectionKnots=[{sourceL:fit.nativeLBounds[0],paletteReferenceId:0},...ks.map((k,i)=>({sourceL:k.sourceL,paletteReferenceId:ids[i]})),{sourceL:fit.nativeLBounds[1],paletteReferenceId:N-1}];
 model.sourceReferenceRule='monotone source-L quantizer through native feature contrast certificates; warm-family only; source metadata and Q remain independent';
 model.kind='source-feature-contrast-constrained-palette';model.constraintScope='eight reviewed native source contrast pairs; default m=1, equal Q; not full authored-feature discovery';
 model.featureContrastCertificates=protectedPairs;model.featureConstraintStatus={feasible:true,passes,moves,scope:'source-certified painted features at equal Q; sourceFeatureId remains inferred/null'};
 model.featureConstraintStatus.excessWithinOneNativeBand=protectedPairs.every(e=>e.outputContrastAtEqualQ.every(v=>v-e.gap<=model.nativeBandWidthL+1e-12));
 fs.writeFileSync(path.join(R,`CONSTRAINED_${N}.json`),JSON.stringify(model,null,2));
 console.log(JSON.stringify({budget:N,knots:ks.length,feasible:true,passes,moves,contrasts:protectedPairs.map(e=>({id:e.certificateId,source:e.gap,output:e.outputContrastAtEqualQ}))}));
}
