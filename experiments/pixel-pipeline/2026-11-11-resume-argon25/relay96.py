from pathlib import Path
import json,sys,relay33
from observer_transport94 import hold
H=Path(__file__).resolve().parent;mode=sys.argv[1];name=sys.argv[2]if len(sys.argv)>2 else'geometry64';relay33.G=H/'face96'if mode=='import'else H/'face96'/name;relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid']
if mode=='post':relay33.G=relay33.G/'post';mode='final'
if mode=='capture':
 pre=relay33.G/'pre2/final/STATE.json';pre=pre if pre.exists()else relay33.G/'final/STATE.json';s=json.loads(pre.read_text());assert s['Edit']and not s['compiling']and s['inputJSONExact']and len(s['dirty'])==31 and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0;assert(H/'face96/import/COMPLETE.json').exists();relay33.OBSERVATION_HOLD=hold
relay33.TITLE_OVERRIDE={'final':'Read current Editor, native/input and owned resource state only','console':'Read errors without clearing','import':'Create-only private SourceFootprint96 read-only halo-copy shader; no CSharp import, default, Play, save or existing asset overwrite','capture':'Same64 normal reciprocal frames with one existing259584B acknowledged packet. Read pre-Present world depth/RGBA halo plus source UV/meta/Q and existing ribbon; bounded CPU export of current actor meshes and publicly readable source alpha only. No new compute/BVH/115/texture readback/import/borrowed release/InputSettings replacement/default change. Normal exit and full preservation after GPU/IO completion; hold official transport until terminal.'}[mode]
sys.argv=[sys.argv[0],mode];relay33.main()
