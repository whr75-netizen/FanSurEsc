from pathlib import Path
import json,sys,relay33
from observer_transport94 import hold
H=Path(__file__).resolve().parent;mode=sys.argv[1];relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid'];relay33.G=H/'face101/source32'
if mode.startswith('import-'):relay33.G=H/'face101'/mode;mode='import';title='Create only private bounded source/provenance raster shader with Unity generated meta. No CSharp Assets, existing overwrite, Play, SaveAssets or default change.'
else:
 if mode in ['preflight','post']:relay33.G=relay33.G/mode;mode='final'
 title='Read stable current Editor, input and owned-resource state only'if mode=='final'else'Record32 normal current-frame private candidate frames: retain original91 source selection; connect a main-view alternative only when original material UV, owner, primitive, shade and transported depth match exactly. No geometry or palette changes, new compute,115 or input replacement. Bounded packet, normal exit, owned disposal and state restoration.'
 if mode=='capture':
  s=json.loads((relay33.G/'preflight/final/STATE.json').read_text());assert s['Edit']and not s['compiling']and not s['updating']and s['inputJSONExact']and len(s['dirty'])==31 and s['allRTCount']==30 and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0;assert all((H/'face101'/('import-'+n)/'import/COMPLETE.json').exists()for n in ['SourceValue101','SourceFootprint101B']);relay33.OBSERVATION_HOLD=hold
assert(relay33.G/mode/'RUN.cs.txt').is_file();relay33.TITLE_OVERRIDE=title;sys.argv=[sys.argv[0],mode];relay33.main()
