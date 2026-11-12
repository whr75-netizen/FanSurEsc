from pathlib import Path
import sys,json,hashlib
import relay33
H=Path(__file__).resolve().parent;mode=sys.argv[1]
assert mode in ['preflight','capture']
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid']
if mode=='capture':
 r=json.loads((H/'face64/final/STATE.json').read_text());assert r['Edit'] and r['inputJSONExact'] and r['diagnosticRTs']==r['diagnosticMaterials']==r['commandUpdateObservers']==0
 p=H/'face64';d=json.loads((p/'CPU_PREPARED64.json').read_text());assert d['CSharp9Compiled'] and d['noTimeoutExtension'] and d['sameMaxInFlightReadbacks']==1
 assert hashlib.sha256((p/'capture/RUN.cs.txt').read_bytes()).hexdigest()==d['captureSHA256']
 target=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Assets\EUnityValidation01\SourceBoundary60\SourceNativeHull60.compute');assert hashlib.sha256(target.read_bytes()).digest()==hashlib.sha256((H/'face62/shaders/SourceNativeHull60.compute').read_bytes()).digest()
 relay33.G=p;selected='capture';relay33.TITLE_OVERRIDE='Six consecutive normal Gameplay frames with same proven source-width and eye-parent path; eliminate one idle tick per completed read, unchanged120s deadline and single bounded readback; normal exit and restoration'
else:
 relay33.G=H/'face64';selected='final';relay33.TITLE_OVERRIDE='Read current Editor/input/resource state after normal observer timeout; create only a new result file'
sys.argv=[sys.argv[0],selected];relay33.main()
