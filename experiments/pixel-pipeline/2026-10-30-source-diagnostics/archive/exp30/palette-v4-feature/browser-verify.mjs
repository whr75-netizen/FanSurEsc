import fs from'node:fs';import path from'node:path';import assert from'node:assert/strict';import{pathToFileURL}from'node:url';import{launch}from'../cdp.mjs';
const R=path.dirname(new URL(import.meta.url).pathname.replace(/^\/(\w:)/,'$1')),published=process.argv.includes('published'),folder=published?'C:/Users/15352/Desktop/작업폴더/아트검토/35_특징영역_공유경계후보/palette-feature-v4':R;
const expected=JSON.parse(fs.readFileSync(path.join(R,'EXPECTED_PIXELS.json'),'utf8')),reports=[];
for(const[browser,exe]of[['chrome','C:/Program Files/Google/Chrome/Application/chrome.exe'],['edge','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe']]){
 const b=await launch(exe),checks=[];const check=(name,fn)=>{fn();checks.push({name,pass:true});};
 try{
  await b.navigate(path.join(folder,'INDEX.html'));await b.wait('Array.from(document.images).every(e=>e.complete&&e.naturalWidth>0)');
  const initial=await b.evaluate('workbench.snapshot()');check('default64 protected both images exact PNG',()=>{for(const n of ['preserve','simplify'])assert.deepEqual(initial.results[n].pixels,expected['64-protected'][n]);});
  await b.screenshot(path.join(R,`UI-${published?'published-':''}${browser}-comparison.png`));
  await b.drag('preserve-m',.75);let s=await b.evaluate('workbench.snapshot()');check('actual slider drag independent and original labels fixed',()=>{assert.ok(Math.abs(s.inputs.preserve-1.5)<.02);assert.equal(s.inputs.simplify,1);assert.deepEqual(s.results.simplify,initial.results.simplify);assert.deepEqual(s.results.preserve.referenceIds,initial.results.preserve.referenceIds);assert.equal(s.sourceAndLabelsUnchanged,true);});
  await b.input('preserve-m',1);
  for(const N of [16,32,64])for(const protect of [false,true]){
   await b.input('budget',N,'change');await b.evaluate(`(()=>{const e=document.getElementById('protected');e.checked=${protect};e.dispatchEvent(new Event('change',{bubbles:true}));})()`);s=await b.evaluate('workbench.snapshot()');const key=N+(protect?'-protected':'');check(key+' real browser output equals saved pixel fixture',()=>{for(const n of ['preserve','simplify'])assert.deepEqual(s.results[n].pixels,expected[key][n]);assert.equal(s.sourceAndLabelsUnchanged,true);});
  }
  await b.input('simplify-m',0);s=await b.evaluate('workbench.snapshot()');check('zero interval folds only own shade steps to native reference',()=>{s.results.simplify.tables.forEach(row=>row.forEach(rgb=>assert.deepEqual(rgb,row[3])));assert.equal(s.inputs.preserve,1);});
  await b.input('simplify-m',1);await b.evaluate('document.querySelector(".controls").scrollIntoView({block:"start"})');await b.screenshot(path.join(R,`UI-${published?'published-':''}${browser}-controls.png`));
  if(published){
   const root=path.resolve(folder,'../INDEX.html'),start=path.resolve(folder,'../../시작.html'),rootURL=pathToFileURL(root).href,targetURL=pathToFileURL(path.join(folder,'INDEX.html')).href;
   await b.send('Page.navigate',{url:pathToFileURL(start).href});await b.wait(`location.href===${JSON.stringify(pathToFileURL(start).href)}&&document.readyState==="complete"`);
   const found=await b.evaluate(`(()=>{const a=Array.from(document.links).find(a=>a.href===${JSON.stringify(rootURL)});if(!a)throw Error('No existing35 link from 시작.html');a.click();return a.href;})()`);check('actual 시작.html link navigates to Desktop35',()=>assert.equal(found,rootURL));
   await b.wait(`location.href===${JSON.stringify(rootURL)}&&document.readyState==="complete"&&document.getElementById("palette-feature-v4")!==null`);
   const href=await b.evaluate('(()=>{const a=document.querySelector("#palette-feature-v4 a");a.click();return a.href;})()');check('Desktop35 new comparison link preserves relative target',()=>assert.equal(href,targetURL));
   await b.wait(`location.href===${JSON.stringify(targetURL)}&&window.workbench?.ready===true&&Array.from(document.images).every(e=>e.complete&&e.naturalWidth>0)`);
   const final=await b.evaluate('workbench.snapshot()');check('actual two-link navigation loads all assets and exact default RGB',()=>{for(const n of ['preserve','simplify'])assert.deepEqual(final.results[n].pixels,expected['64-protected'][n]);});
   await b.screenshot(path.join(R,`UI-published-${browser}-navigation.png`));
  }
  reports.push({browser,checks,passed:checks.length,normalClose:true});
 }finally{await b.close();}
}
fs.writeFileSync(path.join(R,published?'PUBLISHED_BROWSER.json':'BROWSER.json'),JSON.stringify({page:folder,reports,scope:'headless temporary profiles; no CUA/Unity/user browser profile; no art/temporal pass'},null,2));console.log(JSON.stringify(reports.map(r=>({browser:r.browser,passed:r.passed,normalClose:r.normalClose}))));
