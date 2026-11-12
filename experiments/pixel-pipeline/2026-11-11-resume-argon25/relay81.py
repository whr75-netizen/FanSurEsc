from pathlib import Path
import json,sys,hashlib
import relay33
H=Path(__file__).resolve().parent;G=H/'face81';mode=sys.argv[1];probe=mode.startswith('probe-');fixed=mode.startswith('fixed-');mode=mode[6:]if(probe or fixed)else mode
if probe:G=G/'depth-probe'
if fixed:G=G/'fixed6'
assert mode in['final','import','capture','post','console','widthfix'];relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G
if mode=='widthfix':relay33.G=G/'width-fix';mode='import'
if mode=='capture':
 s=json.loads((G/'final/STATE.json').read_text());assert s['Edit']and s['inputJSONExact']and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==s['sourceFlatTexturesRemaining67']==0
 d=json.loads((G/'CPU_PREPARED81.json').read_text());assert d['externalCSharp9Compiled']and d['readbackBytes']==248768 and d['normalFrames']==(1 if probe else 6);imp=json.loads(((G/'import/COMPLETE.json')if fixed else(H/'face81/width-fix/import/COMPLETE.json')).read_text());assert imp['afterSHA']==hashlib.sha256((H/'FeatureCurve81.shader').read_bytes()).hexdigest();r=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');assert hashlib.sha256((r/'Assets/EUnityValidation01/FeatureCurve81/FeatureCurve81.shader').read_bytes()).hexdigest()==imp['afterSHA']
if mode=='post':relay33.G=G/'post';mode='final'
relay33.TITLE_OVERRIDE={'final':'Read stable Edit/input/resources before or after current-curve test','import':'Create/import one new tiny private raster shader only; no overwrite/C# import/Play, preserve native/input/options','capture':'Six normal walk/turn frames, same-frame raw and whole-curve anchor layout. Bounded3 MRT raster passes,1024 old compute threads/frame, one248768-byte readback, current registered source sample/world depth and all actor protection. Standard RenderGraph attachments, no unsafe target changes, no115. Normal exit and full restoration. Minimal line prototype, not full variable-width/whole-footprint proof.','console':'Read current Console Error/Exception only'}[mode];sys.argv=[sys.argv[0],mode];relay33.main()
