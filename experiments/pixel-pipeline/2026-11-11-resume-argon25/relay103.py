from pathlib import Path
import json,sys,re,relay33
from observer_transport94 import hold
H=Path(__file__).resolve().parent;mode=sys.argv[1];name=sys.argv[2]if len(sys.argv)>2 else'rows64';relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid'];relay33.G=H/'face103'/name
if mode=='compile':mode='details'
if mode in ['preflight','post']:relay33.G=relay33.G/mode;mode='final'
title='Compile the complete external103 runner only; do not instantiate capture owner, enter Play, submit GPU work, import or change state'if mode=='details'else('Read current Editor/input/assets/owned resources only'if mode=='final'else'Capture64 normal frames on the private current-source path with CPU-only disjoint row work, immutable shared geometry and mandatory join before release. Existing91 LUT and original GPU passes/readback remain unchanged; no115/compute/input replacement/default switch. Back up and restore normal Play/options/input/native/globals; dispose owned resources after acknowledged callbacks.')
if mode=='capture':
 count=int(re.search(r'\["plannedSourceFrames"\]=(\d+)',(relay33.G/'capture/RUN.cs.txt').read_text()).group(1));assert 1<=count<=1800;title=title.replace('Capture64 ',f'Capture{count} ')
 state=json.loads((relay33.G/'preflight/final/STATE.json').read_text());assert state['Edit']and not state['compiling']and not state['updating']and state['inputJSONExact']and len(state['dirty'])==31 and state['allRTCount']==30 and state['diagnosticRTs']==state['diagnosticMaterials']==state['commandUpdateObservers']==0;assert(H/'face101/import-SourceFootprint101B/import/COMPLETE.json').exists();relay33.OBSERVATION_HOLD=hold
assert(relay33.G/mode/'RUN.cs.txt').exists();relay33.TITLE_OVERRIDE=title;sys.argv=[sys.argv[0],mode];relay33.main()
