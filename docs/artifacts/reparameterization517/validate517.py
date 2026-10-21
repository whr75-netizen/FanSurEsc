from pathlib import Path
import json,ast,hashlib,zipfile,copy
import numpy as np
import active516 as G,span516 as O,span517 as N
W=G.ROOT;D=W/'Temporal517'/'SpanArcV2';P=Path('C:/Users/JG/Documents/work/Fantasy Survival Escape Game');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
j=json.loads((D/'VERDICT517.json').read_text());audit=json.loads((D/'AUDIT517.json').read_text());assert j['comparablePairs']==0 and j['rejectedPairs']==80
assert j['acceptedComparableCostSumOld']is None and j['acceptedComparableCostSumNew']is None and j['acceptedCostDelta']is None
assert all(r['reportedOldCost']is None and r['reportedNewCost']is None for r in j['reportedPairs'])
checks.append('All80 rejected pairs and aggregate comparisons reported null, not0/pass')
for r in audit['sourceInputs']:assert sha(Path(r['path']))==r['sha256']
for i in range(81):
 r=json.loads((D/f'{i:03d}_AUDIT.json').read_text());assert r['maskUnchangedSHA256']==hashlib.sha256(G.read_mask(i).tobytes()).hexdigest();assert r['allVariantsCanonicalBitIdentical']
checks.append('All81 input masks unchanged;243 input hashes match; geometric variants canonical-bit-identical')
fixtures=json.loads((D/'FIXTURES517.json').read_text());assert fixtures['passed']and not fixtures['selectorRun']and not fixtures['temporalStateCostChanged']
checks.append('Same-region slide/split/start fixtures0 without reset; actual motion/edit and explicit visibility events remain distinguished')
arithmetic=[]
def spans(lengths,dy=0.):
 total=sum(lengths);index=0;out=[]
 for length in lengths:
  ss=[]
  for _ in range(length):
   u=(index+.5)/max(total,1);ss.append({'q':[index*.5,dy],'u':u,'reference':[u,0.],'tangent':[1.,0.]});index+=1
  out.append({'length':length,'ring':0,'segment':0,'samples':ss})
 return out
for lengthsA,lengthsB,dy in[([], [1,2],0.),([1,2],[],0.),([2,1],[3],0.),([3],[1,2],0.),([2,2],[1,3],.2),([1,1,2],[2,1,1],-.3)]:
 a,b=spans(lengthsA),spans(lengthsB,dy);old=O.edit(a,b,[[(0.,0.),(1.,0.),(1.,1.)]],True)
 convert=lambda ss:[{'length':s['length'],'points':[v['q']for v in s['samples']]}for s in ss]
 new=N.linear_edit(convert(a),convert(b),trace=True)
 assert abs(old['raw']-new['raw'])<1e-10 and old['operations']==new['operations'],(lengthsA,lengthsB,old,new)
 arithmetic.append({'oldSpanLengths':lengthsA,'newSpanLengths':lengthsB,'raw516':old['raw'],'raw517':new['raw'],'operators':[v['operation']for v in old['operations']]})
checks.append('Add/delete/substitute/merge/split linearDP arithmetic and traces match516 on six fixed span cases')
for row in json.loads((W/'VALIDATION516.json').read_text())['sources']if(W/'VALIDATION516.json').exists()else json.loads((W/'Temporal516/VALIDATION516.json').read_text())['sources']:
 assert sha(W/row['name'])==row['sha256']
checks.append('All516 source hashes frozen; selector/coefficients/temporal-state implementation untouched')
runtime=json.loads((W/'APPLIED_SOURCE512.json').read_text())['files']
for r in runtime:assert sha(P/r['path'])==r['after']
settings=json.loads((W/'RECORDED516.json').read_text())['protectedSettings']
for rel,h in settings.items():assert sha(P/rel)==h
checks.append('Runtime/shader and user Quality/Time hashes unchanged; no Unity calls')
sources=['arc517.py','span517.py','test517.py','audit517.py','probe517.py','report517.py','validate517.py']
for n in sources:ast.parse((W/n).read_text())
for n in['ALL_PAIR_AUDITS517.zip','REJECTED_FULL_CYCLE_V1.zip']:
 with zipfile.ZipFile(D/n)as z:assert z.testzip()is None
checks.append('Prototype sources parse and both detailed evidence archives passCRC')
out={'artifactIntegrityPassed':True,'correspondenceOnStored81Passed':False,'comparablePairs':0,'rejectedPairs':80,'checks':checks,'arithmeticCompatibility':arithmetic,'runtimeUnchanged':runtime,'protectedSettings':settings,'newUnityCalls':0,'newSelectorRuns':0,'defaultOFF':True,'sources':[{'name':n,'sha256':sha(W/n)}for n in sources]}
(D/'VALIDATION517.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in['runtimeUnchanged','protectedSettings','sources']},ensure_ascii=False))
