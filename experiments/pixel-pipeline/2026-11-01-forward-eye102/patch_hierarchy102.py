from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;P=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');p=H/'ForwardEye102.compute'
source=p.read_text(encoding='utf-8');old=H/'ForwardEye102_BEFORE.compute';assert not old.exists();old.write_bytes(p.read_bytes())
start=source.index(' int winner=-1;');end=source.index(' _CanonicalColour96[cell]=0;',start);assert 'int4 prior=_Witness96[cell]'in source[start:end]
source=source[:start]+'\n'+(H/'SelectHierarchy102.hlsl').read_text(encoding='utf-8')+source[end:];p.write_text(source,encoding='utf-8')
save={'algorithm':'whole eye union first -> internal part coverage -> unique actual source depth for exact part ties','beforeSHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'afterSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'syntheticPixelBudgets':False,'InputSettingsChanges':False,'assetApplied':False}
(H/'HIERARCHY_PATCH102.json').write_text(json.dumps(save,indent=2),encoding='utf-8');print(json.dumps(save))
