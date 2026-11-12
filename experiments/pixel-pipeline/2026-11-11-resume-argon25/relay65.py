from pathlib import Path
import sys,json,hashlib
import relay33
H=Path(__file__).resolve().parent;mode=sys.argv[1];assert mode in ['final','capture','console','post']
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=H/'face65'
if mode=='post':
 relay33.G=H/'face65/post';mode='final';out=relay33.G/mode;out.mkdir(exist_ok=True)
 assert not(out/'REQUEST.json').exists()
 (out/'RUN.cs.txt').write_bytes((H/'face65/post/RUN.cs.txt').read_bytes())
if mode=='capture':
 d=json.loads((relay33.G/'final/STATE.json').read_text());assert d['Edit'] and d['inputJSONExact'] and d['diagnosticRTs']==d['diagnosticMaterials']==d['commandUpdateObservers']==0
 d=json.loads((relay33.G/'CPU_PREPARED65.json').read_text());assert d['CSharp9Compiled'] and d['same120SecondDeadline'] and d['maxOnePendingPerOwner']
 assert hashlib.sha256((relay33.G/'capture/RUN.cs.txt').read_bytes()).hexdigest()==d['captureSHA256']
 target=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Assets\EUnityValidation01\SourceBoundary60\SourceNativeHull60.compute');assert target.read_bytes()==(H/'face62/shaders/SourceNativeHull60.compute').read_bytes()
 relay33.TITLE_OVERRIDE='Normal six consecutive Gameplay frames; unchanged proven shaders/draws and120s limit; at most one262144-byte read per immutable frame owner, six owners; normal exit and preservation'
else:relay33.TITLE_OVERRIDE='Read current Editor/input/owned-resource state only'
sys.argv=[sys.argv[0],mode];relay33.main()
