import fs from'node:fs';import path from'node:path';import assert from'node:assert/strict';import{launch}from'../cdp.mjs';
const R=path.dirname(new URL(import.meta.url).pathname.replace(/^\/(\w:)/,'$1')),expected=JSON.parse(fs.readFileSync(path.join(R,'EXPECTED_PIXELS.json'),'utf8')),reports=[];
for(const[name,exe]of[['chrome','C:/Program Files/Google/Chrome/Application/chrome.exe'],['edge','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe']]){
 const b=await launch(exe),checks=[];const check=(name,fn)=>{fn();checks.push({name,pass:true});};
 try{
  await b.navigate(path.join(R,'INDEX.html'));await b.wait('Array.from(document.images).every(e=>e.complete&&e.naturalWidth>0)');
  for(const key of Object.keys(expected)){await b.input('case',key,'change');const s=await b.evaluate('workbench.snapshot()');check(key+' browser raw RGBA exact and source/g preserved',()=>{assert.deepEqual(s.pixels,expected[key]);assert.equal(s.sourceAndGUnchanged,true);});}
  await b.input('case','flat-distinct','change');await b.input('cell',935);let s=await b.evaluate('workbench.snapshot()');let t=JSON.parse(s.trace);check('actual cell935 trace maps frozen g/Q/region to fixed P RGB',()=>{assert.equal(t.Q,2);assert.equal(t.g,0.02827419713139534);assert.deepEqual(t.effectiveSourceRGBA,JSON.parse(fs.readFileSync(path.join(R,'CONSTANT_SOURCE.json'),'utf8')).RGBAlinear);assert.deepEqual(t.RGB,[93,61,62]);});
  await b.input('case','flat-unlit','change');s=await b.evaluate('workbench.snapshot()');t=JSON.parse(s.trace);check('unlit control keeps nonconstant lighting data but emits one native colour',()=>{assert.equal(t.Q,2);assert.equal(t.g,0.02827419713139534);assert.deepEqual(t.RGB,[94,64,63]);assert.equal(t.passthrough,false);});
  await b.input('case','pattern-legacy','change');s=await b.evaluate('workbench.snapshot()');check('return to original source restores exact pixels, no stale flat display',()=>assert.deepEqual(s.pixels,expected['pattern-legacy']));
  await b.evaluate('document.querySelector(".inspection").scrollIntoView({block:"center"})');await b.screenshot(path.join(R,`UI-${name}-cell-trace.png`));
  await b.evaluate('scrollTo(0,0)');await b.screenshot(path.join(R,`UI-${name}-pair.png`));reports.push({browser:name,passed:checks.length,checks,normalClose:true});
 }finally{await b.close();}
}
fs.writeFileSync(path.join(R,'BROWSER.json'),JSON.stringify({reports,scope:'isolated headless profiles; saved-frame CPU diagnostic, not live Unity/AA/cache or temporal validation'},null,2));console.log(JSON.stringify(reports.map(r=>({browser:r.browser,passed:r.passed,normalClose:r.normalClose}))));
