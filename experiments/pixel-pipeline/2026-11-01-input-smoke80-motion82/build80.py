from pathlib import Path
import sys,json,hashlib,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'run';BASE=ROOT/'apply-capture66';O73=ROOT/'eye-observer73'
assert not (OUT/'Smoke80_REQUEST.json').exists(),'Inspect dispatched source; do not overwrite uncertain execution'
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
source=(HERE/'Smoke80.cs').read_text(encoding='utf-8').replace('ROOT80',str(OUT));(OUT/'Smoke80.cs').write_bytes(source.encode())
deps=[BASE/'Json58Linear66.cs',BASE/'SerializedContent66.cs',O73/'CreateOnly73.cs',O73/'NativeSnapshot73.cs',ROOT/'uv-features64/GlobalJournal64.cs']
bundle(deps+[OUT/'Smoke80.cs'],OUT/'RUN_Smoke80.cs.txt')
code=source.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("80 full smoke runner compiled only; no Play or mutation");return;}\n void Prepared80(ExecutionResult result)\n {',1)
(OUT/'Compile80.cs').write_bytes(code.encode());bundle(deps+[OUT/'Compile80.cs'],OUT/'RUN_Compile80.cs.txt')
for bad in ['InputSystem.settings=','InputSystem.settings =','InputSystem.Update(','DestroyImmediate(','Instantiate(','SaveAssets(','File.Delete(','File.Move(','Directory.Delete(']:assert bad not in source,bad
print('Full80 runner built; settings setter/clone/destroy/manualUpdate absent')
