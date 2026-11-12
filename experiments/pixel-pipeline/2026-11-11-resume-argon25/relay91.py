from pathlib import Path
import sys,json,hashlib
import relay33
H=Path(__file__).resolve().parent;G=H/'face91';mode=sys.argv[1];bounded=mode.startswith('bounded-');mode=mode[8:]if bounded else mode;long=mode.startswith('long-');mode=mode[5:]if long else mode
if long:G=G/'motion192'
if bounded:G=G/'bounded192'
assert mode in ['final','import','capture','post','console']and not((long or bounded)and mode=='import');relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid'];relay33.G=G
if mode=='capture':
 s=json.loads((G/'final/STATE.json').read_text());assert s['Edit']and not s['compiling']and s['inputJSONExact']and len(s['dirty'])==31 and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0
 imp=json.loads((H/'face91/import/COMPLETE.json').read_text());assert imp['shaderSHA256']==hashlib.sha256((H/'SourceValue91.shader').read_bytes()).hexdigest()
if mode=='post':relay33.G=G/'post';mode='final'
relay33.TITLE_OVERRIDE={'final':'Read current Editor/input/native/resources only','import':'Create-only private SourceValue91 shader: remove current-colour dependency on history-valid flag; no history/occlusion changes, C# import, scene/default change or GPU submit','capture':('192 consecutive actual RGB frames:96 pulse/idle then96 held normal movement in3 directions, existing120s deadline and same91 shader/table. 'if long else'64 normal pulse/idle frames across the observed current/history validity counterexample. ')+'Current source/colour address and exact Q authorize finite LUT even if conservative history is unavailable. Same89 bounded raster, table and237952B readback; no new compute/loops/BVH/115. Preserve invalid diagnostics on rejection, normal exit/full state restore; no product77 switch.','console':'Read Console errors only'}[mode]
if bounded and mode=='capture':relay33.TITLE_OVERRIDE='192 actual RGB normal reciprocal walk/turn frames:4 input frames out,4 opposite,24 idle; change direction each32 frames. Bound displacement with normal input instead of changing position/camera/speed/settings. Same91 shader/table/history/visibility,237952B per frame,6 slots, existing120s deadline. Normal exit and full state restore; no product77 switch/new GPU kernel/import.'
sys.argv=[sys.argv[0],mode];relay33.main()
