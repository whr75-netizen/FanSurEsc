from pathlib import Path
import json,sys,hashlib
import relay33
H=Path(__file__).resolve().parent;G=H/'face75';mode=sys.argv[1];assert mode in['final','import','capture','post','console'];d=json.loads((G/'CPU_PREPARED75.json').read_text());assert d['CSharp9Compiled']and d['CPUShaderCompiled']and d['tokenAudit']['loops']==0 and d['tokenAudit']['instructions']<24000 and not d['tokenAudit']['privateArrayDeclarations'];assert json.loads((G/'CPU_HISTORY75.json').read_text())['CPUChecks']==17;relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G
if mode=='import':
 s=json.loads((G/'final/STATE.json').read_text());assert s['Edit']and s['inputJSONExact']and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==s['sourceFlatTexturesRemaining67']==0
if mode=='capture':
 assert(G/'import/COMPLETE.json').exists()and hashlib.sha256((G/'capture/RUN.cs.txt').read_bytes()).hexdigest()==d['captureSHA256'];p=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Assets\EUnityValidation01\SourceBoundary60\SourceNativeHull60.compute');assert hashlib.sha256(p.read_bytes()).hexdigest()==d['computeSHA256']
if mode=='post':relay33.G=G/'post';mode='final'
relay33.TITLE_OVERRIDE={'final':'Read stable Editor/input/resource state only','import':'Shader-only hash/GUID-guarded private compute update: source-local previous GPU owner tie preference with current visibility first, fixed24 candidates and no loops/BVH/115; no CSharp import or save','capture':'Six normal walk/turn frames comparing mapped width with/without prior actual GPU owner through evaluated mesh UV projection. No RGB history/readback selection. Previous immutable resources retained until all GPU/consumer ACK; normal exit/restoration, product77 unchanged','console':'Read Console Error/Exception only'}[mode];sys.argv=[sys.argv[0],mode];relay33.main()
