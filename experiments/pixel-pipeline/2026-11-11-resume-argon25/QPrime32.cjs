function reviewQ32(){
 const F=Math.fround, A=(a,b)=>F(F(a)+F(b)), S=(a,b)=>F(F(a)-F(b)), M=(a,b)=>F(F(a)*F(b)), E=F(.01);
 const checks=[], check=(v,n)=>{if(!v)throw Error(n);checks.push(n)};
 const pixel=(q=1,c=.75)=>({q:F(q),c:F(c),depth:F(1),alpha:F(1),metaDepth:F(1),role:3,owner:0,region:3,normal:[0,0,1]});
 const copy=g=>g.map(r=>r.map(p=>({...p,normal:[...p.normal]})));
 const make=()=>Array.from({length:7},()=>Array.from({length:7},()=>pixel()));
 const tip=()=>{let g=make();g[3][3]=pixel(0,.45);g[2][3]=pixel(0,.25);g[1][3]=pixel(0,.25);return g};
 const dirs=[[-1,0],[1,0],[0,-1],[0,1]],ring=[[-1,-1],[0,-1],[1,-1],[1,0],[1,1],[0,1],[-1,1],[-1,0]];
 function normalize(n){let l=F(Math.sqrt(A(A(M(n[0],n[0]),M(n[1],n[1])),M(n[2],n[2]))));if(!(l>0))throw Error("invalid normal outside oracle contract");return n.map(v=>F(v/l))}
 function dot(a,b){return A(A(M(a[0],b[0]),M(a[1],b[1])),M(a[2],b[2]))}
 const role=p=>p.metaDepth>0&&(p.role===3||(p.role>=7&&p.role<=14));
 function proposal(g,x,y,opt={}){
  const w=g[0].length,h=g.length,p=g[y][x],stride=opt.stride||1,steps=p.role===3?(opt.faceSteps||2):(opt.surfaceSteps||2),step=F(1/(Math.max(2,steps)-1));
  const sample=(a,b)=>g[Math.min(h-1,Math.max(0,b))][Math.min(w-1,Math.max(0,a))];
  function neighbour(a,b,n){
   if(a<0||b<0||a>=w||b>=h)return false;
   const t=g[b][a];if(t.region==null||p.region==null)throw Error("unobserved membership, not a default region");
   if(t.metaDepth<=0||Math.abs((t.role+1)-(p.role+1))>F(.1)||Math.abs(t.owner-p.owner)>F(.1)||t.alpha<F(.5)||t.region!==p.region)return false;
   return dot(n,normalize(t.normal))>F(.94)&&Math.abs(S(t.depth,p.depth))<M(opt.worldPixel==null?.1:opt.worldPixel,2);
  }
  let q=p.q;
  if(opt.curvature!==false&&role(p)&&p.alpha>F(.5)){
   const n=normalize(p.normal);let safe=true,lo=q,hi=q,same=0,opposite=q;
   for(let yy=-1;yy<=1;yy++)for(let xx=-1;xx<=1;xx++)if(xx||yy){
    let a=x+xx*stride,b=y+yy*stride;safe=safe&&neighbour(a,b,n);
    let v=sample(a,b).q;lo=Math.min(lo,v);hi=Math.max(hi,v);
    if(Math.abs(xx)+Math.abs(yy)===1){if(Math.abs(S(v,q))<E)same++;else opposite=v}
   }
   let transitions=0;
   for(let i=0;i<8;i++){let a=ring[i],b=ring[(i+1)%8];if(Math.abs(S(sample(x+a[0]*stride,y+a[1]*stride).q,sample(x+b[0]*stride,y+b[1]*stride).q))>E)transitions++}
   if(safe&&same===1&&transitions===2&&Math.abs(S(S(hi,lo),step))<E){
    let threshold=M(A(q,opposite),.5),uncertain=Math.abs(S(p.c,threshold))<=M(step,.1);
    if(Math.abs(S(Math.abs(S(opposite,q)),step))<E&&uncertain){
     for(let axis=0;axis<2;axis++)for(let sign=-1;sign<=1;sign+=2){
      let dx=(axis===0?sign:0)*stride,dy=(axis===1?sign:0)*stride;
      if(neighbour(x+dx,y+dy,n)&&neighbour(x+2*dx,y+2*dy,n)&&Math.abs(S(sample(x+dx,y+dy).q,q))<E&&Math.abs(S(sample(x+2*dx,y+2*dy).q,q))<E)q=opposite;
     }
    }
   }
  }
  return q;
 }
 const masks=(g,o)=>g.map((row,y)=>row.map((p,x)=>proposal(g,x,y,o)));
 function apply(g,m,opt={}){return g.map((row,y)=>row.map((p,x)=>({...p,normal:[...p.normal],q:opt.apply!==false&&role(p)&&Math.abs(S(p.q,m[y][x]))>=E?m[y][x]:p.q})))}
 const quantize=(v,n)=>F(Math.floor(A(M(Math.max(0,Math.min(1,v)),n-1),.5))/(n-1));
 const labels=g=>g.map(r=>r.map(p=>p.q)), equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
 const rotate=g=>g[0].map((_,i)=>g.map(r=>({...r[i],normal:[...r[i].normal]})).reverse());
 const reflect=g=>g.map(r=>r.slice().reverse().map(p=>({...p,normal:[...p.normal]})));
 let g=tip(),before=JSON.stringify(g),mask=masks(g),qp=apply(g,mask);
 check(g[3][3].q===quantize(g[3][3].c,2),"tip fixture initial label agrees with original quantizer");
 check(mask[3][3]===1&&qp[3][3].q===1,"valid one-width tip changes Q0=0 to proposal/applied Qprime=1");
 check(JSON.stringify(g)===before,"two-stage oracle reads immutable Q0 instead of in-place updates");
 check(qp[3][3].c===g[3][3].c&&qp[3][3].depth===g[3][3].depth&&qp[3][3].alpha===g[3][3].alpha,"Apply changes only classifier.x");
 check(equal(labels(apply(g,masks(g,{curvature:false}))),labels(g)),"curvature disabled implies Qprime=Q0 for matched input");
 check(mask[3][3]!==g[3][3].q&&apply(g,mask,{apply:false})[3][3].q===g[3][3].q,"proposal can differ while Apply disabled keeps Qprime=Q0");
 let flat=make();check(equal(labels(apply(flat,masks(flat))),labels(flat)),"flat label field is a fixed point");
 let singleton=make();singleton[3][3]=pixel(0,.45);check(proposal(singleton,3,3)===0,"singleton is not a same==1 tip");

 let legacy502=tip();for(let row of legacy502)for(let p of row)p.c=F(p.role+1);
 check(proposal(legacy502,3,3)===0&&proposal(g,3,3)===1,"Legacy502 role+1 in classifier.y is not continuous-light input");
 let kindRangeChecks=0;
 for(let r of [3,7,8,9,10,11,12,13,14])for(let q of [0,1])for(let other of [0,1])for(let levels of [2,3,8]){
  let step=F(1/(levels-1)),threshold=M(A(q,other),.5);
  if(Math.abs(S(r+1,threshold))<=M(step,.1))throw Error("legacy502 ambiguity");kindRangeChecks++;
 }
 check(kindRangeChecks===108,"all108 supported-role/binary-label/level cases violate uncertainty bound with role+1 Y");
 let stable=tip();stable[3][3].c=F(.2);check(proposal(stable,3,3)===0,"confident quantizer interior stays fixed");
 const mutations=[
 ["different role",p=>p.role=4],["different owner",p=>p.owner=1],["different source region",p=>p.region=9],
 ["normal discontinuity",p=>p.normal=[1,0,0]],["depth discontinuity",p=>{p.depth=F(1.2);p.metaDepth=F(1.2)}],
 ["low neighbour coverage",p=>p.alpha=F(.49)],["missing surface",p=>p.metaDepth=0]
 ];
 for(let [name,fn] of mutations){let t=tip();fn(t[3][2]);check(proposal(t,3,3)===0,name+" blocks spatial proposal")}
 let half=tip();half[3][3].alpha=F(.5);check(proposal(half,3,3)===0,"centre alpha==.5 is excluded by strict >.5 guard");
 let nh=tip();nh[3][2].alpha=F(.5);check(proposal(nh,3,3)===1,"neighbour alpha==.5 passes its different <.5 guard");
 let back=tip();back[1][3]=pixel(1,.75);check(proposal(back,3,3)===0,"same-label support must extend to distance2");
 check(proposal(g,3,3,{worldPixel:0})===0,"zero world-pixel depth budget rejects neighbours");
 let crop=g.slice(2,5).map(r=>r.slice(2,5).map(p=>({...p,normal:[...p.normal]})));
 check(proposal(crop,1,1)===0&&proposal(g,3,3)===1,"ROI+1 halo loses distance2 evidence and is not a Qprime substitute");
 let cube=g.slice(1,6).map(r=>r.slice(1,6).map(p=>({...p,normal:[...p.normal]})));
 check(proposal(cube,2,2)===proposal(g,3,3),"radius2 context suffices for one centre proposal in this counterexample");
 let transformed=g,expected=labels(qp);
 for(let i=0;i<4;i++){check(equal(labels(apply(transformed,masks(transformed))),expected),"D4 rotation"+i+" preserves output labels in binary valid-input fixture");let f=reflect(transformed);check(equal(labels(apply(f,masks(f))),expected.map(r=>r.slice().reverse())),"D4 reflection"+i+" preserves output labels in binary valid-input fixture");transformed=rotate(transformed);expected=rotate(expected.map(r=>r.map(q=>pixel(q)))).map(r=>r.map(p=>p.q))}
 let halo=stage=>({initialQ:1,boundaryProposal:3,appliedQprime:3}[stage]);
 check(halo("initialQ")===1&&halo("appliedQprime")===3,"transition query needs halo1 for initial Q and halo3 for one corrected pass");
 let eps=make(),em=eps.map(r=>r.map(p=>p.q));eps[3][3].q=0;em[3][3]=F(.005);check(apply(eps,em)[3][3].q===0,"Apply tolerance may keep old Q although proposal is numerically different");
 const lit=[.3,.4,.5],factor=q=>1;
 check(g[3][3].q!==qp[3][3].q&&equal(lit.map(v=>v*factor(g[3][3].q)),lit.map(v=>v*factor(qp[3][3].q))),"shade disabled permits identical RGB while Q labels differ");

 // Independent circular-component criterion, exhaustively compared with the
 // HLSL-branch oracle for all binary rings. No repeated per-cell tautologies.
 function components(bits,value){
  let left=new Set(bits.map((b,i)=>b===value?i:-1).filter(i=>i>=0)),count=0;
  while(left.size){count++;let stack=[left.values().next().value];left.delete(stack[0]);
   while(stack.length){let i=stack.pop();for(let j of [(i+7)%8,(i+1)%8])if(left.has(j)){left.delete(j);stack.push(j)}}}
  return count;
 }
 let expectedTipPatterns=0,actualTipPatterns=0;
 for(let maskBits=0;maskBits<256;maskBits++){
  let t=make(),bits=ring.map((_,i)=>(maskBits>>i)&1);t[3][3]=pixel(0,.45);
  for(let i=0;i<8;i++)t[3+ring[i][1]][3+ring[i][0]]=pixel(bits[i],bits[i]?.75:.25);
  for(let [dx,dy]of dirs)t[3+2*dy][3+2*dx]=pixel(0,.25);
  let cardZero=[1,3,5,7].filter(i=>bits[i]===0).length;
  let expect=cardZero===1&&components(bits,0)===1&&components(bits,1)===1;
  let actual=proposal(t,3,3)===1;if(expect)expectedTipPatterns++;if(actual)actualTipPatterns++;
  if(actual!==expect)throw Error("ring component counterexample "+maskBits);
 }
 check(expectedTipPatterns===16&&actualTipPatterns===16,"all256 binary rings match independent component criterion:16 tips");
 const requiredHalo=(stage,stride,queryRadius)=>(stage==="initialQ"?0:2*stride)+queryRadius;
 check(requiredHalo("appliedQprime",2,2)===6,"native stride2 plus logical-neighbour query needs6 native texels");

 return {checks:checks.length,passed:checks,exhaustiveRingPatterns:256,expectedTipPatterns,actualTipPatterns,legacySchemaRangeCases:kindRangeChecks,observations:{tipQ0:g[3][3].q,tipProposal:mask[3][3],tipQprime:qp[3][3].q,croppedHalo1Proposal:proposal(crop,1,1),fullProposal:proposal(g,3,3)},limits:["Synthetic finite float32-input CPU oracle from read RestoreStyle335 source; no shader execution or bitwise GPU equivalence.","Inspected saved27 frame99 has no initial-Q/proposal/Qprime classification planes or HeadRegion502 route flag; real-frame deltas remain unmeasured.","Binary D4 fixtures do not prove all float tolerance/region cases.","Same-fragment31 initial Q still needs geometry/material/lighting/state equivalence to existing initial Q0."],UnityGPUCalls:0,hostProcessCreated:false};
}
if(typeof module!=='undefined'){module.exports={reviewQ32};if(typeof require!=='undefined'&&require.main===module)console.log(JSON.stringify(reviewQ32(),null,2));}
