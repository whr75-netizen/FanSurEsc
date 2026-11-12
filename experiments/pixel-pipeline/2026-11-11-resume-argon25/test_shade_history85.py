from pathlib import Path
import json,numpy as np
from shade_history85 import choose,prior_address
def main():
 checks=0
 for g,old,now,expected in[(.249,.5,0,.5),(.251,0,.5,0),(.1,.5,0,0),(.4,0,.5,.5),(.76,0,1,1)]:
  q,used=choose(now,g,old,3);assert q==expected;checks+=1
 for current,previous in[(False,True),(True,False),(False,False)]:assert choose(0,.249,.5,3,current,previous)==(0,False);checks+=1
 for g in np.linspace(0,1,101):
  now=float(np.rint(g*2)/2)
  for old in [0,.5,1]:
   q,used=choose(now,g,old,3);assert q in[0,.5,1]
   if used:assert abs(g-(now+old)*.5)<=.05+1e-7
   checks+=1
 # Same UV point is transported by the registered previous geometry, including
 # subpixel translation; no current screen coordinate indexes history.
 t=np.array([[0,0,0,0,0,10.5,20.5],[0,0,0,1,0,12.5,20.5],[0,0,0,0,1,10.5,22.5]],float);geom={'v':t,'tri':np.array([[0,1,2]])};q,why=prior_address(geom,1,[.1,.1],[5,15,20,20]);assert why=='mapped'and q==(5,14);checks+=1
 geom['v'][:,5]+=.2;q2,why=prior_address(geom,1,[.1,.1],[5,15,20,20]);assert q2==q;checks+=1
 result={'CPUChecks':checks,'existing335OneTenthBinBudget':True,'invalidCurrentNeverRestored':True,'registeredUVCarrierTransport':True,'RGBHistory':False};(Path(__file__).resolve().parent/'face84/CPU_HISTORY85.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
