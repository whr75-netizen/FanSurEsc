from pathlib import Path
import sys,json,hashlib
import relay33
H=Path(__file__).resolve().parent;G=H/'face66';mode=sys.argv[1];assert mode in ['final','import','capture','console','post']
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G
if mode=='post':relay33.G=G/'post';mode='final'
d=json.loads((G/'CPU_PREPARED66.json').read_text());assert d['CSharp9Compiled'] and d['CPUShaderCompiled'] and d['tokenAudit']['loops']==0
if mode=='import':
 s=json.loads((G/'final/STATE.json').read_text());assert s['Edit'] and s['inputJSONExact'] and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0
if mode=='capture':
 assert(G/'import/COMPLETE.json').exists()and hashlib.sha256((G/'capture/RUN.cs.txt').read_bytes()).hexdigest()==d['captureSHA256']
 target=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Assets\EUnityValidation01\SourceBoundary60\SourceNativeHull60.compute');assert hashlib.sha256(target.read_bytes()).hexdigest()==d['computeSHA256']
relay33.TITLE_OVERRIDE={'final':'Read current Editor/input/resource state; no rendering','import':'Update only owned SourceBoundary60 compute with explicit native-reference/exterior class; preserve exact meta/GUID and user state; shader-only import, no C# or Play','capture':'Six normal consecutive frames; exterior silhouette excludes same-actor occupancy, with same-frame original hull reference; bounded existing8x8 loop-free shader and reads; normal exit/restoration','console':'Read current Console only'}[mode]
sys.argv=[sys.argv[0],mode];relay33.main()
