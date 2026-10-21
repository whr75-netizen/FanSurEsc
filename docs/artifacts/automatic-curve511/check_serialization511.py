from pathlib import Path
import json,hashlib,importlib.util
W=Path(__file__).parent;spec=importlib.util.spec_from_file_location('curve511',W/'compile_curve511.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=json.loads((W/'Auto511/Compiled02/CURVES511.json').read_text());target=W/'Auto511/SERIALIZATION511_V2_CHECK.bytes';m.write_asset(r,target)
actual=Path('C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets/EUnityValidation01/HeadRegion502/Resources/HeadCurve511.bytes');assert target.read_bytes()==actual.read_bytes()
out={'formatVersion':2,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'actualUnityResourceByteDifference':0,'preprocessingRepeated':False,'inputReportSHA256':hashlib.sha256((W/'Auto511/Compiled02/CURVES511.json').read_bytes()).hexdigest()}
(W/'Auto511/SERIALIZATION511.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
