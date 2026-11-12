from pathlib import Path
import json,numpy as np
from source_value88 import constraints
from palette_round88 import solve
from audit_polarity76 import luminance

def main():
 checks=0;rgb=np.full((5,7,3),180,np.uint8);rgb[:,2:5]=[160,150,140];mask=np.ones((5,7),bool);fg=np.zeros_like(mask);fg[:,2:5]=1;island=np.ones_like(mask,int);rows=np.array([[2,3],[2,2]]);flanks=np.array([[[2,2],[4,2]],[[1,2],[5,2]]]);d=constraints(rgb,mask,fg,island,rows,flanks);assert len(d['accepted'])==1 and d['rejected']['flank-inside-pigment']==1 and len(d['orders'])==1;checks+=1
 # Transform source geometry and profile points together, not RGB/source IDs.
 for reflect in [False,True]:
  for rotation in range(4):
   coords=np.array([[[x,y]for x in range(7)]for y in range(5)]);rr=rgb.copy();mm=mask.copy();ff=fg.copy();ii=island.copy();cc=coords.copy()
   if reflect:rr=rr[:,::-1];mm=mm[:,::-1];ff=ff[:,::-1];ii=ii[:,::-1];cc=cc[:,::-1]
   rr=np.rot90(rr,rotation);mm=np.rot90(mm,rotation);ff=np.rot90(ff,rotation);ii=np.rot90(ii,rotation);cc=np.rot90(cc,rotation);mapping={tuple(cc[y,x]):[x,y]for y,x in np.ndindex(mm.shape)};newrows=np.array([mapping[(x,y)][::-1]for y,x in rows]);newflanks=np.array([[mapping[tuple(p)]for p in pair]for pair in flanks]);e=constraints(rr,mm,ff,ii,newrows,newflanks);assert e['orders']==d['orders']and e['rejected']==d['rejected'];checks+=1
 for n in range(1,10):
  t=np.tile([100.49,100.49,100.49],(n,1));edges=[(i,i+1)for i in range(n-1)];s=solve(t,edges);assert s['feasible']==(n<=8)
  if s['feasible']:assert np.all(np.diff(luminance(s['rgb8']))>0)
  checks+=1
 t=np.array([[90.1,100.1,110.1],[130.7,140.7,150.7]]);s=solve(t,[(0,1)]);assert s['feasible']and np.max(abs(s['rgb8']-t))<1;checks+=1
 assert not solve(np.tile([100.,100.,100.],(2,1)),[(0,1)])['feasible'];checks+=1
 result={'CPUChecks':checks,'D4ProfileClassificationInvariant':True,'internalPigmentFlankNotBackground':True,'roundingOnlyWithinFloorCeilCube':True,'infeasiblePaletteNotForced':True};G=Path(__file__).resolve().parent/'face88';G.mkdir(exist_ok=True);(G/'CPU_SOURCE_VALUE88.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
