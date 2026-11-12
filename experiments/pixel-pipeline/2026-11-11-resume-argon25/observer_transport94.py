"""Keep one official MCP session alive until owned observation terminates.

No RPC, heartbeat, relaunch, GPU operation, timeout alteration or state write.
The captured observer retains authority over normal exit and resource release.
"""
from pathlib import Path
import json,time
def terminal(root):
 root=Path(root);present=[p for p in [root/'COMPLETE.json',root/'FAILED.json']if p.exists()]
 if len(present)>1:raise RuntimeError('conflicting terminal markers; no resubmit')
 if not present:return None
 r=json.loads(present[0].read_text());return {'marker':present[0].name,'ownedResourcesReleased':r.get('ownedResourcesReleased')is True,'Edit':r.get('Edit')is True,'packetComplete':r.get('packetComplete')is True}
def hold(root,pause=time.sleep,clock=time.monotonic):
 root=Path(root)
 if not(root/'STARTED.json').exists():return {'armed':False,'reason':'no executed observer; do not wait or submit'}
 start=clock();reported=0
 while True:
  r=terminal(root)
  if r is not None and r['ownedResourcesReleased']and r['Edit']:return {'armed':True,'heldSeconds':clock()-start,**r}
  if clock()-start>=reported+30:
   print(json.dumps({'observerTransportAlive':True,'elapsed':round(clock()-start,1),'terminal':r}),flush=True);reported=clock()-start
  pause(.25)
