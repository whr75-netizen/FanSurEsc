from pathlib import Path
import json,sys,time
import numpy as np
from geometry_oracle585 import Frame,R,table
case=int(sys.argv[1]);run={2:'OneCase2',5:'OneCase5B',16:'OneCase16'}[case];old=R.with_name('EyeFollow584')/'Runtime584'/run;geo=R/f'Runtime585/Geometry{case}'
result=[]
prior=json.loads((R/'GRID5_585.json').read_text()) if case==5 else None
for i in range(3):
 f=Frame(i,old,geo);parity=table(Path(str(f.prefix)+'_PARITY585.tsv'));changed=sum(not np.array_equal(np.array([q[k]for k in ['r','g','b','a']],float),f.cells[int(q['x']),int(q['y']),q['buffer']]) for q in parity);assert changed==0
 row={'queryFrame':i,'sourceFrame':json.loads(Path(str(f.prefix)+'_PARAMS.json').read_text())['sourceFrame'],'triangles':len(f.tr),'GPUReplayParityRecords':len(parity),'GPUReplayChanges':changed,'area4':f.area4(),'grid':prior[i]['grid'].copy() if prior else []};assert row['area4']['weightMismatches']==0,row['area4']
 for n in [8,16,32,64,128,256]:
  if any(q['n']==n and q['offset']==[.5,.5] for q in row['grid']):continue
  q=f.integrate_grid(n);row['grid'].append(q);print(json.dumps({'case':case,'frame':i,**q}),flush=True)
 q=f.integrate_grid(256,(.25,.75));row['grid'].append(q);print(json.dumps({'case':case,'frame':i,**q}),flush=True)
 def estimate(n):
  center=next(q['area']for q in row['grid']if q['n']==n and q['offset']==[.5,.5]);coarse=next(q['area']for q in row['grid']if q['n']==n//2 and q['offset']==[.5,.5]);shift=next(q['area']for q in row['grid']if q['n']==n and q['offset']==[.25,.75]);err=2*max(abs(center-coarse),abs(center-shift));return center,err,min(center,shift)-err,max(center,shift)+err
 area,err,lo,hi=estimate(256)
 if err>.003 or abs(area-.5)<=3*err:
  for offset in [(.5,.5),(.25,.75)]:
   q=f.integrate_grid(512,offset);row['grid'].append(q);print(json.dumps({'case':case,'frame':i,**q}),flush=True)
  area,err,lo,hi=estimate(512)
 row.update({'areaEstimate':area,'numericalErrorEstimate':err,'empiricalRange':[lo,hi],'errorIsFormalBound':False,'convergenceCriterion':'Two finest refinements and a shifted lattice; error estimate2*max(refinementDelta,phaseDelta). Must be<=.003 and margin>3error. A conservative independent upper certificate is separate.','classification':'BELOW_HALF'if hi<.5 and err<=.003 else 'ABOVE_HALF'if lo>.5 and err<=.003 else 'UNRESOLVED','sampleAreaError':row['area4']['savedArea4']-area})
 result.append(row);(R/f'CONVERGENCE{case}_PROGRESS585.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'case':case,'completedFrame':i,'area':area,'errorEstimate':err,'classification':row['classification']}),flush=True)
(R/f'CONVERGENCE{case}_585.json').write_text(json.dumps({'case':case,'method':'Recorded projected triangle/UV/alpha/ray model, continuous reference. Packet HairMETA is held identical to actual selection input, not replaced by native raw hair. Uniform midpoint and shifted numerical integration; source/input replay verified.','records':result},indent=2)+'\n')
