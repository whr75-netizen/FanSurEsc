from pathlib import Path
import json,sys,hashlib
import relay33
H=Path(__file__).resolve().parent;G=H/'face84';mode=sys.argv[1];assert mode in ['final','import','capture','post','console'];relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G
if mode=='capture':
 s=json.loads((G/'final/STATE.json').read_text());assert s['Edit']and s['inputJSONExact']and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0
 imp=json.loads((G/'import/COMPLETE.json').read_text());assert imp['shaderSHA256']==hashlib.sha256((H/'SelectedLight84.shader').read_bytes()).hexdigest()
if mode=='post':relay33.G=G/'post';mode='final'
relay33.TITLE_OVERRIDE={'final':'Read current Edit/input/native/resources only','import':'Create one private read-only fullscreen source-light observer shader, shader-only import; no C# import/Play or existing asset overwrite','capture':'Six normal walk/turn frames reading exact existing Restore335 selected addresses, continuous light/Q/normal/UV plus current mesh geometry. One small standard Graph raster pass/frame, no new compute dispatch/lighting/115/BVH.173056B acknowledged readback/frame and normal exit/full restoration. No input settings replacement or product switch.','console':'Read Console errors only'}[mode];sys.argv=[sys.argv[0],mode];relay33.main()
