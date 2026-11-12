from pathlib import Path
import json,sys,relay33
from observer_transport94 import hold
H=Path(__file__).resolve().parent;mode=sys.argv[1];relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid'];relay33.G=H/'face105/edge64'
if mode in['preflight','post']:relay33.G=relay33.G/mode;mode='final'
if mode=='capture':
 prior=json.loads((H/'face103/long1800/capture/COMPLETE.json').read_text());assert prior['packetComplete']and prior['Edit']and prior['restorationChecksPass']and prior['ownedResourcesReleased']and not prior['errors']
 state=json.loads((relay33.G/'preflight/final/STATE.json').read_text());assert state['Edit']and not state['compiling']and not state['updating']and state['inputJSONExact']and len(state['dirty'])==31 and state['allRTCount']==30 and state['diagnosticRTs']==state['diagnosticMaterials']==state['commandUpdateObservers']==0;relay33.OBSERVATION_HOLD=hold
relay33.TITLE_OVERRIDE='Read current Edit/input/native assets/owned-resource preservation only'if mode=='final'else'Capture64 current normal frames, changing only CPU redundancy across the two triangular halves of the same source edge. Split at their shared diagonal and require source/destination depth/alpha paths. Existing GPU passes, palette, unknown/wide/sole fragments and product77 default unchanged; mandatory CPU join and acknowledged GPU release, normal Play exit and full original state restoration; no115/new compute/import/input replacement.'
sys.argv=[sys.argv[0],mode];relay33.main()
