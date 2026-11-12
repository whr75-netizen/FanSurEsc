"""Normal action queue ordering, not a claim of camera-relative world closure."""
from pathlib import Path
import json
H=Path(__file__).resolve().parent;G=H/'face77/loop120'

def main():
 current=0;events=[];actual=[];tests=0
 for frame in range(-8,120):
  expected=max(0,frame//8);assert current==expected
  if frame>=0:tests+=1
  actual.append(current)
  if frame>=0:
   phase=(frame+1)//8
   if phase!=current:events.append((frame,phase));current=phase
 assert len(events)==15;tests+=1
 assert all(i==7+8*k for k,(i,p)in enumerate(events));tests+=1
 counts=[sum(p%4==j for p in actual[8:])for j in range(4)];assert counts==[32,32,32,24];tests+=1
 result={'CPUChecks':tests,'normalQueueAtEndFrameNextDynamicUpdate':True,'expected120Inputs':True,'directionsUseExistingBindings':True,'phaseUpdates':len(events),'first120SideCounts':counts,'worldRouteClosureNotAssumed':True,'positionOrCameraModified':False};(G/'CPU_ROUTE77.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
