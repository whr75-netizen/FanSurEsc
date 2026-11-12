"""Adversarial event orders for77's declared ownership contract, not GPU proof."""
from pathlib import Path
import itertools,json
H=Path(__file__).resolve().parent;G=H/'face77'
class Slot:
 def __init__(self):self.submitted=False;self.gpu=False;self.cpu=False;self.borrow=0
 def free(self):return(not self.submitted or(self.gpu and self.cpu))and self.borrow==0
 def submit(self,prior=None):
  assert self.free();self.submitted=True;self.gpu=self.cpu=False
  if prior:prior.borrow+=1
 def callback(self,prior=None,valid=True):
  if not valid:self.cpu=True;return
  self.gpu=self.cpu=True
  if prior:prior.borrow-=1;assert prior.borrow>=0
def main():
 G.mkdir(exist_ok=True);tests=0
 for order in itertools.permutations(range(3)):
  slots=[Slot()for _ in range(3)];slots[0].submit();slots[1].submit(slots[0]);slots[2].submit(slots[1]);assert not any(s.free()for s in slots)
  completed=set()
  for n in order:
   slots[n].callback(slots[n-1]if n else None);completed.add(n)
   for i,s in enumerate(slots):assert s.free()==(i in completed and(i==2 or i+1 in completed))
  assert all(s.free()for s in slots);tests+=1
 slots=[Slot()for _ in range(6)]
 for i,s in enumerate(slots):s.submit(slots[i-1]if i else None)
 assert not any(s.free()for s in slots);tests+=1
 slots[0].callback();assert not slots[0].free();slots[1].callback(slots[0]);assert slots[0].free();tests+=1
 invalid=Slot();invalid.submit();invalid.callback(valid=False);assert not invalid.free();tests+=1
 unknown=Slot();unknown.submit();assert not unknown.free();tests+=1
 live=Slot();live.submit();live.callback();assert live.free();live.submit();assert not live.free();tests+=1
 result={'CPUChecks':tests,'allThreeCallbackOrders':6,'completedSourceCannotBeReusedWhileBorrowed':True,'sixPendingSlotsRequireBackpressureStop':True,'unknownOrDeviceErrorDoesNotRelease':True,'noGPUCalls':True};(G/'CPU_LEASE77.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
