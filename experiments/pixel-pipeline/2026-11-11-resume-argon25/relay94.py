from pathlib import Path
import json,sys,relay33
H=Path(__file__).resolve().parent;G=H/'face94';mode=sys.argv[1];verify=mode.startswith('verify-');held=mode.startswith('held-');mode=mode[7:]if verify else mode[5:]if held else mode
if verify:G=G/'verify480'
if held:G=G/'held480'
assert mode in ['final','capture','post','console'];relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid'];relay33.G=G
if mode=='capture':
 s=json.loads((G/'final/STATE.json').read_text());assert s['Edit']and not s['compiling']and s['inputJSONExact']and len(s['dirty'])==31 and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0;assert json.loads((H/'face94/CPU_WINDING94.json').read_text())['exitCode']==0
if mode=='post':relay33.G=G/'post';mode='final'
relay33.TITLE_OVERRIDE={'final':'Read current scene/input/native/resources only','console':'Read errors only','capture':'Instrument one existing normal reciprocal480-frame run to record bounded current public body1 projected coordinates and opacity segments synchronously on524 negative union winding. Existing92 raster only; no new shader/import/compute/115 or union retry. Stop on first error, drain GPU/IO then normal Play exit and full external-state restoration. No product default or InputSettings replacement.'}[mode]
if(verify or held)and mode=='capture':relay33.TITLE_OVERRIDE='Verify the same480 normal reciprocal motion frames after CPU-confirmed three clothing CSharp precision fixes and successful native47/input/global preservation. Existing93 bounded native ribbon/92 finite LUT only,24planes259584B; no new shader/import/GPU algorithm/115. Record actual high-precision public body1 source at baseline/final or first original error. Normal exit/drain/release/full external-state restore; no InputSettings replacement or product77 face/eye default change.'
if held and mode=='capture':
 from observer_transport94 import hold
 relay33.OBSERVATION_HOLD=hold;relay33.TITLE_OVERRIDE+=' Keep this official MCP transport open until owned observer terminal/release; no extra RPC or heartbeat. Explicit420s CPU-IO observation budget from measured291-frame196s throughput; per-frame GPU work/completion/release guards unchanged.'
sys.argv=[sys.argv[0],mode];relay33.main()
