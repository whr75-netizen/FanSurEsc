from pathlib import Path
import hashlib,json,sys
import relay33
H=Path(__file__).resolve().parent;G=H/'face83';mode=sys.argv[1];fix=mode.startswith('fix1-');mode=mode[5:]if fix else mode
if fix:G=G/'fix1'
assert mode in ['final','import','capture','post','console']and not(fix and mode=='import');relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G
if mode=='capture':
 s=json.loads((G/'final/STATE.json').read_text());assert s['Edit']and s['inputJSONExact']and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0
 imp=json.loads((H/'face83/import/COMPLETE.json').read_text());assert imp['afterSHA']==hashlib.sha256((H/'FeatureCurve83.shader').read_bytes()).hexdigest();r=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');assert hashlib.sha256((r/'Assets/EUnityValidation01/FeatureCurve81/FeatureCurve81.shader').read_bytes()).hexdigest()==imp['afterSHA']
if mode=='post':relay33.G=G/'post';mode='final'
relay33.TITLE_OVERRIDE={'final':'Read current Edit/input/native/resource state only','import':'Update owned tiny raster shader only, preserve meta/GUID/native/input/options, no C# import or Play','capture':'Six normal walk/turn frames: current native meshes alpha/cull/depth in each source curve raster frame, then independent actor/world exterior gate. Eight standard Graph raster passes, at most32 native mesh draws,1024 existing compute threads and248768B acknowledged readback/frame. No BVH/115, no input settings replacement; normal exit and full restore.','console':'Read Console Error/Exception only'}[mode];sys.argv=[sys.argv[0],mode];relay33.main()
