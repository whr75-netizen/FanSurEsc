"""CPU fake-clock transport lifecycle tests; no real process or Unity."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from observer_transport94 import hold,terminal
def main():
 checks=0
 with TemporaryDirectory()as d:
  p=Path(d);assert hold(p)['armed']is False;checks+=1;(p/'STARTED.json').write_text('test');ticks=[0]
  def pause(_):
   ticks[0]+=1
   if ticks[0]==1:(p/'FAILED.json').write_text(json.dumps({'ownedResourcesReleased':False,'Edit':False,'packetComplete':False}))
   if ticks[0]==3:(p/'FAILED.json').write_text(json.dumps({'ownedResourcesReleased':True,'Edit':True,'packetComplete':False}))
  r=hold(p,pause,lambda:ticks[0]);assert ticks[0]==3 and r['marker']=='FAILED.json'and not r['packetComplete'];checks+=1
 with TemporaryDirectory()as d:
  p=Path(d);(p/'STARTED.json').write_text('test');(p/'COMPLETE.json').write_text(json.dumps({'ownedResourcesReleased':True,'Edit':True,'packetComplete':True}));r=hold(p);assert r['packetComplete'];checks+=1;(p/'FAILED.json').write_text('{}')
  try:terminal(p)
  except RuntimeError:checks+=1
  else:raise AssertionError('ambiguous result accepted')
 print(json.dumps({'CPUOnly':True,'checks':checks,'noRPCOrGPUOrProcessStarted':True,'releaseRequiredBeforeDisconnect':True}))
if __name__=='__main__':main()
