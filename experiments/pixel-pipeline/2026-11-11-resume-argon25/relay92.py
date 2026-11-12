from pathlib import Path
import sys,json,hashlib
import relay33
H=Path(__file__).resolve().parent;G=H/'face92/gpu';mode=sys.argv[1];motion=mode.startswith('motion-');mode=mode[7:]if motion else mode
if motion:G=H/'face92/motion240'
assert mode in ['final','capture','post','console'];relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid'];relay33.G=G
if mode=='capture':
 s=json.loads((G/'final/STATE.json').read_text());assert s['Edit']and not s['compiling']and s['inputJSONExact']and len(s['dirty'])==31 and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0
 r=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');shader=r/'Assets/EUnityValidation01/SourceValue91/SourceValue91.shader';assert hashlib.sha256(shader.read_bytes()).hexdigest()==json.loads((H/'face92/gpu/CPU_PREPARED92.json').read_text())['existingShader91SHA']
if mode=='post':relay33.G=G/'post';mode='final'
relay33.TITLE_OVERRIDE={'final':'Read current Editor/input/native/resources only','capture':('240 normal reciprocal move/turn frames,4 simulated seconds,existing120s deadline; same validated192-frame input and source92 CPU builder. 'if motion else'Six actual normal-input frames. ')+'Same compiled91 bounded raster and current visibility/history. Runtime C# builds226-address LUT from native source RGB and3822 measured contrast constraints using CPU-only bounded floor/ceil rounding. No new shader/compute/Assets import/expected GPU output upload/default switch.237952B per frame,normal exit/full external-state restore.','console':'Read Console errors only'}[mode];sys.argv=[sys.argv[0],mode];relay33.main()
