from pathlib import Path
import sys,json,relay33
from observer_transport94 import hold
H=Path(__file__).resolve().parent;name=sys.argv[1];mode=sys.argv[2];G=H/'face95'/name if name!='import'else H/'face95'
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid'];relay33.G=G
if mode=='post':relay33.G=G/'post';mode='final'
if mode=='capture':
 s=json.loads((G/'final/STATE.json').read_text());assert s['Edit']and not s['compiling']and s['inputJSONExact']and len(s['dirty'])==31 and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0;assert(H/'face95/import/COMPLETE.json').exists();relay33.OBSERVATION_HOLD=hold
relay33.TITLE_OVERRIDE={'final':'Read current scene, input, native and owned resource state only','console':'Read errors without clearing','import':'Create and import one private read-only SourceFootprint95 raster shader. No CSharp import, product default, Play, dispatch, save or existing asset overwrite. Preserve current native/input/options.','capture':'One bounded normal Play source observation using the existing93/94 lifecycle and one read-only pre-Present raw raster gather. Exactly259584B/frame in the existing single callback; no new compute,115, InputSettings replacement, product default or borrowed resource release. Same-frame source2x2/meta/UV/line/LUT receipts; normal exit after GPU/IO/borrower completion and full state restoration. Keep official transport open until owned terminal.'}[mode]
sys.argv=[sys.argv[0],mode];relay33.main()
