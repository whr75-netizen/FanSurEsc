'use strict';
// Relocatable replay. Historical sources stay byte-exact and are never executed
// as CLI entry points with their old machine paths or publication side effects.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm'),assert=require('node:assert/strict'),{createRequire}=require('node:module');
const root=__dirname,A=path.join(root,'archive/exp30'),read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');let checks=[];
function check(name,ok){assert.ok(ok,name);checks.push(name);}
function reject(name,fn){assert.throws(fn);checks.push(name);}
function virtualRun(file){
 const base=path.dirname(file),writes=new Map(),requireAt=createRequire(file);
 const safeFS={...fs,writeFileSync(p,data){
   assert.equal(path.dirname(path.resolve(p)),path.resolve(base));
   writes.set(path.basename(p),Buffer.from(data));
 },readFileSync(p,...rest){
   assert.ok(path.resolve(p).startsWith(path.resolve(root)+path.sep),'External data reads are forbidden by the portable replay');
   return writes.has(path.basename(p))&&path.dirname(path.resolve(p))===path.resolve(base)?(rest.length?writes.get(path.basename(p)).toString(rest[0]):writes.get(path.basename(p))):fs.readFileSync(p,...rest);
 }};
 vm.runInNewContext(fs.readFileSync(file,'utf8'),{__dirname:base,require:n=>n==='node:fs'||n==='fs'?safeFS:requireAt(n),console:{log(){}},Buffer},{filename:file,timeout:30000});return writes;
}

const flat=path.join(A,'flat-albedo-control'),input=read(path.join(flat,'INPUT.json')),legacy=read(path.join(flat,'PALETTE_LEGACY.json')),engine=require(path.join(flat,'engine.cjs'));
const writes=virtualRun(path.join(flat,'run.cjs')),out=JSON.parse(writes.get('RESULTS.json')),expected=read(path.join(root,'fixtures/flat-expected.json'));
check('original distinct-Q compiler reproduces archived contract bytes',writes.get('PALETTE_DISTINCT.json').equals(fs.readFileSync(path.join(flat,'PALETTE_DISTINCT.json'))));
for(const [name,ref] of Object.entries(expected)){
 const r=out.outputs[name];check(name+': full RGBA equals frozen frame result',digest(Buffer.from(r.pixels))===ref.pixelsSHA256);
 check(name+': every cell source-reference choice preserved',JSON.stringify(r.rows.map(c=>c?c.sourceReferenceId:null))===JSON.stringify(ref.references));
 check(name+': final hair RGB count preserved',new Set(r.rows.filter(Boolean).map(c=>c.rgb.join(','))).size===ref.hairRGBUnique);
}
for(const [name,edit] of [
 ['old sourceId',x=>x.context.primarySourceId='old'],['stale packet binding',x=>x.bindingReceipt.packetSHA256='stale'],
 ['different model',x=>x.context.modelSHA256='wrong'],['stale Q label',x=>{const c=x.cells.find(Boolean);c.Q=(c.Q+1)%4;}]
]){const x=structuredClone(input);edit(x);reject('reject '+name,()=>engine.render(x,legacy));}
check('flat override includes all 368 cells',out.outputs['flat-unlit'].rows.filter(Boolean).length===368&&out.outputs['flat-unlit'].rows.filter(Boolean).every(c=>!c.passthrough));
check('intentional original-colour passthrough reproduces failure',new Set(out.outputs['flat-unlit-inherited-fallback'].rows.filter(Boolean).map(c=>c.rgb.join(','))).size===8);

const v4=path.join(A,'palette-v4-feature'),constraintWrites=virtualRun(path.join(v4,'feature_constraints.cjs'));
for(const name of ['FEATURE_CERTIFICATES.json','CONSTRAINED_16.json','CONSTRAINED_32.json','CONSTRAINED_64.json'])
 check('original feature-constraint solver reproduces '+name,constraintWrites.get(name).equals(fs.readFileSync(path.join(v4,name))));
const samples=read(path.join(v4,'NINE_NATIVE_AUDIT.json')).flatMap(e=>e.endpoints),models=[
 ['v3',require(path.join(A,'palette-v3/palette.cjs')),read(path.join(A,'palette-v3/SHARED_NATIVE_PALETTE.json'))],
 ...[16,32,64].map(n=>['v4-'+n,require(path.join(v4,'palette.cjs')),read(path.join(v4,`CONSTRAINED_${n}.json`))])];
for(const [name,api,model]of models){
 if(model.feasible===false){check(name+': infeasibility remains explicit',!!model.reason);continue;}
 const before=JSON.stringify(model),ids=samples.map(e=>api.referenceForSample(model,e.sample,{colourGroupId:e.appearanceGroupId??e.appearance,uncertain:false}).paletteReferenceId);
 check(name+': every saved native pair remains bindable',ids.every(i=>Number.isInteger(i)&&i>=0&&i<model.references.length));
 for(const m of [0,.5,1,1.5]){
  const p=api.buildPalette(model,m).tablesRGB8;
  check(name+': bounded integer palette at spacing '+m,p.every(row=>row.length===4&&row.every(rgb=>rgb.length===3&&rgb.every(v=>Number.isInteger(v)&&v>=0&&v<=255))));
  if(m===0)check(name+': zero interval keeps one colour per reference',p.every(row=>row.every(rgb=>rgb.join(',')===row[0].join(','))));
 }
 check(name+': interval changes do not mutate source/anchor/Q contracts',before===JSON.stringify(model));
 reject(name+': unknown model cannot silently bind',()=>api.referenceForSample(model,{...samples[0].sample,modelSHA256:'other'},{colourGroupId:samples[0].appearanceGroupId??samples[0].appearance,uncertain:false}));
 reject(name+': unresolved appearance cannot silently bind',()=>api.referenceForSample(model,samples[0].sample,{colourGroupId:1,uncertain:true}));
}
console.log(JSON.stringify({suite:'portable palette/flat replay',passed:checks.length,cases:checks,externalFileReads:0,productChanges:0},null,2));
