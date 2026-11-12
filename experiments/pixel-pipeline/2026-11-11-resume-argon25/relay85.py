from pathlib import Path
import json,sys,hashlib
import relay33
H=Path(__file__).resolve().parent;G=H/'face85';mode=sys.argv[1];long=mode.startswith('long-');mode=mode[5:]if long else mode
if long:G=G/'pulse120'
assert mode in ['final','import','capture','post','console']and not(long and mode=='import');relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G
if mode=='capture':
 s=json.loads((G/'final/STATE.json').read_text());assert s['Edit']and s['inputJSONExact']and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0
 imp=json.loads((H/'face85/import/COMPLETE.json').read_text());assert imp['shaderSHA256']==hashlib.sha256((H/'ShadeHistory85.shader').read_bytes()).hexdigest()
if mode=='post':relay33.G=G/'post';mode='final'
relay33.TITLE_OVERRIDE={'final':'Read current Edit/input/native/resources only','import':'Create one private bounded source-Q history shader only; no C# import/Play or existing asset overwrite','capture':('120 bounded normal move/idle frames, same85 shader and existing120s deadline. One movement frame in16 limits displacement; no pose/camera teleport. Source/view/levels/gap invalidation, prior-resource lease, deformed native normals sampled; normal exit/full state restore. 'if long else'Six normal walk/turn frames validating source UV/primitive shade-label history on GPU. ')+'One small raster pass, no new compute/loops/BVH/115/selection readback/RGB averaging. Current source validity and existing335 one-tenth-bin budget first. Prior resources leased before draw,183872B readback and normal exit/full restoration.','console':'Read Console errors only'}[mode];sys.argv=[sys.argv[0],mode];relay33.main()
