from pathlib import Path
import json,sys,relay33
from observer_transport94 import hold
H=Path(__file__).resolve().parent;mode=sys.argv[1];relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid'];relay33.G=H/'face100/reasons32'
if mode=='import':relay33.G=H/'face100/import';title='Create only private SourceFootprint100 raster observer shader, Unity generates metadata. No CSharp Assets, existing overwrite, Play, SaveAssets or defaults.'
else:
 if mode in ['preflight','post']:relay33.G=relay33.G/mode;mode='final'
 title='Read stable current Editor, input and owned-resource state only'if mode=='final'else'Record32 normal consecutive source frames with unchanged99C/98B output and read-only palette exclusion flags in existing packet padding. No new compute,115,input replacement,defaults or RGB smoothing. Normal exit and exact temporary-state restoration.'
 if mode=='capture':
  state=json.loads((relay33.G/'preflight/final/STATE.json').read_text());assert state['Edit']and not state['compiling']and not state['updating']and state['inputJSONExact']and len(state['dirty'])==31 and state['allRTCount']==30 and state['diagnosticRTs']==state['diagnosticMaterials']==state['commandUpdateObservers']==0;assert(H/'face100/import/import/COMPLETE.json').is_file();relay33.OBSERVATION_HOLD=hold
assert(relay33.G/mode/'RUN.cs.txt').is_file();relay33.TITLE_OVERRIDE=title;sys.argv=[sys.argv[0],mode];relay33.main()
