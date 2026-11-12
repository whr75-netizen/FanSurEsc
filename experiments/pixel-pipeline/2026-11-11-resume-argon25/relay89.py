from pathlib import Path
import sys,json,hashlib
import relay33
H=Path(__file__).resolve().parent;G=H/'face89';mode=sys.argv[1];lookup=mode.startswith('lookup-');mode=mode[7:]if lookup else mode;long=mode.startswith('long-');mode=mode[5:]if long else mode;fix=mode.startswith('fix-')or mode.startswith('fix2-');folder='fix2'if mode.startswith('fix2-')else'fix1';mode=mode[5:]if mode.startswith('fix2-')else mode[4:]if fix else mode
if fix:G=G/folder
if long:G=G/'motion192'
if lookup:G=G/'lookup64'
assert mode in ['final','import','capture','post','console']and not((fix or long or lookup)and mode=='import');relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid'];relay33.G=G
if mode=='capture':
 s=json.loads((G/'final/STATE.json').read_text());assert s['Edit']and not s['compiling']and s['inputJSONExact']and len(s['dirty'])==31 and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0
 imp=json.loads((H/'face89/import/COMPLETE.json').read_text());assert imp['shaderSHA256']==hashlib.sha256((H/'SourceValue89.shader').read_bytes()).hexdigest()
if mode=='post':relay33.G=G/'post';mode='final'
relay33.TITLE_OVERRIDE={'final':'Read current Editor, input/native/resources only','import':'Create one new private source-value palette shader only; Unity-generated meta, no C# Assets import or default/scene changes','capture':('192 consecutive actual RGB frames within existing120s deadline:96 pulse/idle then96 normal held movement in3 directions. Same89 shader/table/lifetimes; no new import. 'if long else'Six normal input frames: ')+'Same-frame native RGB, old-unit LUT control and source89 finite LUT current/prior actual GPU Q. One237952B raster atlas per frame, no new compute/loops/BVH/115. Static source UV addresses; CPU table creation uses live brightness-floor unit adapter, not GPU selection readback. Existing prior-texture lease and full normal exit/input/native/global/options restoration.','console':'Read Console errors only'}[mode]
if lookup and mode=='capture':relay33.TITLE_OVERRIDE='Same89 shader/table and initial normal pulse input,64-frame maximum, no new GPU readback or algorithm change. Preserve the already-completed rejected readback as an explicitly invalid diagnostic to distinguish UV-address from current/history validity failure. No successful marker on failure; normal exit/drain and full input/native/global/options restoration.'
sys.argv=[sys.argv[0],mode];relay33.main()
