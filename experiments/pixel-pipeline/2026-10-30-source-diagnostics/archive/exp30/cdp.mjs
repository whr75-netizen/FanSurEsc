import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {pathToFileURL} from 'node:url';

export const target = 'C:/Users/15352/Desktop/작업폴더/아트검토/31_머리색_슬라이더/index.html';
export async function launch(exe='C:/Program Files/Google/Chrome/Application/chrome.exe') {
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),'hair31-r4-'));
  const proc=spawn(exe,['--headless=new','--remote-debugging-port=0','--no-first-run','--no-default-browser-check',`--user-data-dir=${profile}`,'about:blank'],{windowsHide:true,stdio:'ignore'});
  const started=Date.now();
  while(!fs.existsSync(path.join(profile,'DevToolsActivePort'))){if(Date.now()-started>20000)throw new Error('Browser startup timeout');await new Promise(r=>setTimeout(r,100));}
  const port=fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0];
  const tabs=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const ws=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
  let serial=0;const pending=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);if(m.error)p.reject(new Error(JSON.stringify(m.error)));else p.resolve(m.result);}};
  const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
  await send('Runtime.enable');await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:1500,height:1100,deviceScaleFactor:1,mobile:false});
  const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
  const wait=async expression=>{const t=Date.now();while(!(await evaluate(expression))){if(Date.now()-t>15000)throw new Error('Wait timeout: '+expression);await new Promise(r=>setTimeout(r,40));}};
  const navigate=async file=>{const url=pathToFileURL(file).href;const old=await evaluate('performance.timeOrigin');await send('Page.navigate',{url});await wait(`location.href===${JSON.stringify(url)}&&performance.timeOrigin!==${old}&&window.workbench?.ready===true`);};
  const input=async(id,value,event='input')=>evaluate(`(()=>{let e=document.getElementById(${JSON.stringify(id)});e.value=${JSON.stringify(String(value))};e.dispatchEvent(new Event(${JSON.stringify(event)},{bubbles:true}));return e.value;})()`);
  const click=async id=>evaluate(`document.getElementById(${JSON.stringify(id)}).click()`);
  const snapshot=()=>evaluate(`(()=>{let controls={};for(let e of document.querySelectorAll('input,select,output'))if(e.id)controls[e.id]={value:e.type==='checkbox'?e.checked:e.value,min:e.min??null,max:e.max??null,disabled:e.disabled??false,visible:!!e.getClientRects().length};return {controls,state:workbench.getState(),palette:workbench.getPalette(),region:workbench.getRegion(),metrics:workbench.verify(),status:document.getElementById('status').textContent,storage:{...localStorage},pixels:Array.from(document.getElementById('result').getContext('2d').getImageData(0,0,64,80).data)};})()`);
  const screenshot=async filename=>{const r=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync(filename,Buffer.from(r.data,'base64'));};
  const drag=async(id,fraction)=>{await evaluate(`document.getElementById(${JSON.stringify(id)}).scrollIntoView({block:'center'})`);const p=await evaluate(`(()=>{let e=document.getElementById(${JSON.stringify(id)}),b=e.getBoundingClientRect();return {x:b.x+8+(b.width-16)*(Number(e.value)-Number(e.min))/(Number(e.max)-Number(e.min)),end:b.x+8+(b.width-16)*${fraction},y:b.y+b.height/2}})()`);await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x,y:p.y});await send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,x:p.x,y:p.y});for(let i=1;i<=6;i++)await send('Input.dispatchMouseEvent',{type:'mouseMoved',button:'left',buttons:1,x:p.x+(p.end-p.x)*i/6,y:p.y});await send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,x:p.end,y:p.y});};
  const close=async()=>{try{await send('Browser.close');}catch{}ws.close();await Promise.race([new Promise(r=>proc.once('exit',r)),new Promise(r=>setTimeout(r,1500))]);};
  return {profile,send,evaluate,wait,navigate,input,click,snapshot,screenshot,drag,close};
}
