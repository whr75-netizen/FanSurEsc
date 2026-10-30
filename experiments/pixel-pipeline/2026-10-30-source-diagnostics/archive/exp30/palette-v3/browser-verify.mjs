import fs from'node:fs';import path from'node:path';import assert from'node:assert/strict';import{launch}from'../cdp.mjs';
const R=path.dirname(new URL(import.meta.url).pathname.replace(/^\/(\w:)/,'$1')),read=n=>JSON.parse(fs.readFileSync(path.join(R,n),'utf8'));
const expected={preserve:read('preserve-pixels.json').new,simplify:read('simplify-pixels.json').new};let reports=[];
for(const[name,exe]of[['chrome','C:/Program Files/Google/Chrome/Application/chrome.exe'],['edge','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe']]){
 const b=await launch(exe),checks=[];const check=(name,fn)=>{fn();checks.push({name,pass:true});};
 try{
  await b.navigate(path.join(R,'INDEX.html'));await b.wait('Array.from(document.images).every(e=>e.complete&&e.naturalWidth>0)');
  let initial=await b.evaluate('workbench.snapshot()');check('both m1 browser images exact independent saved PNG RGBA',()=>{for(const n of ['preserve','simplify'])assert.deepEqual(initial.results[n].pixels,expected[n]);});
  await b.screenshot(path.join(R,`UI-${name}-comparison.png`));
  await b.drag('preserve-m',.75);let s=await b.evaluate('workbench.snapshot()');check('real preserve slider drag leaves simplify input/pixels fixed',()=>{assert.ok(Math.abs(s.inputs.preserve-1.5)<.02);assert.equal(s.inputs.simplify,1);assert.deepEqual(s.results.simplify,initial.results.simplify);assert.equal(s.sourceAndRegionsUnchanged,true);});
  check('spacing drag never relabels source reference IDs',()=>{assert.deepEqual(s.results.preserve.referenceIds,initial.results.preserve.referenceIds);});
  await b.input('simplify-m',.5);s=await b.evaluate('workbench.snapshot()');check('simplify half interval leaves preserve value independent',()=>assert.ok(Math.abs(s.inputs.preserve-1.5)<.02));
  await b.input('preserve-m',0);s=await b.evaluate('workbench.snapshot()');check('zero interval collapses shade values to own fixed native reference',()=>s.results.preserve.tables.forEach(row=>row.forEach(rgb=>assert.deepEqual(rgb,row[3]))));
  await b.input('preserve-m',1);await b.input('simplify-m',1);s=await b.evaluate('workbench.snapshot()');check('both round trips restore pixels and source/region labels',()=>{for(const n of ['preserve','simplify'])assert.deepEqual(s.results[n].pixels,expected[n]);assert.equal(s.sourceAndRegionsUnchanged,true);});
  await b.evaluate('document.getElementById("preserve-m").scrollIntoView({block:"start"})');await b.screenshot(path.join(R,`UI-${name}-controls.png`));
  reports.push({browser:name,checks,passed:checks.length,normalClose:true});
 }finally{await b.close();}
}
fs.writeFileSync(path.join(R,'BROWSER_VERIFIED.json'),JSON.stringify({reports,scope:'isolated headless profiles; no CUA/user browser profile, Unity launch or product edits'},null,2));console.log(JSON.stringify(reports.map(r=>({browser:r.browser,passed:r.passed,normalClose:r.normalClose}))));
