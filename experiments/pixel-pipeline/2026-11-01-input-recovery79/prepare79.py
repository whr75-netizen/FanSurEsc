from pathlib import Path
import sys,hashlib,json
HERE=Path(__file__).resolve().parent;OUT=HERE/'run';OUT.mkdir(exist_ok=True);assert not list(OUT.glob('*_REQUEST.json'))and not (OUT/'RECOVERY_STARTED79.marker').exists(),'Existing execution must be inspected';OLD=HERE.parent/'eye-motion78/run';BASE=HERE.parent/'apply-capture66';O73=HERE.parent/'eye-observer73'
sys.path.insert(0,str(HERE.parent/'boundary-input69'));from prepare73 import bundle
payload=(HERE.parent/'eye-motion78/INPUT_SETTINGS_RECOVERED78.json').read_bytes();assert hashlib.sha256(payload).hexdigest()=='ca3f68bea248d3f95f9daef0889228a710740dd1efc8867ffda63b97b07f4286';assert len(json.loads(payload))==22;(OUT/'PAYLOAD79.json').write_bytes(payload)
r=(OLD/'relay76.py').read_text().replace("'ManagedInput78')","'ManagedInput78','Restore79','Compile79','Verify79')");assert 'Restore79'in r;(OUT/'relay76.py').write_text(r,encoding='utf8')
source=(HERE/'Restore79.cs').read_text().replace('ROOT79',str(OUT));(OUT/'Restore79.cs').write_text(source,encoding='utf8');deps=[BASE/'Json58Linear66.cs',BASE/'SerializedContent66.cs',O73/'CreateOnly73.cs',O73/'NativeSnapshot73.cs'];bundle(deps+[OUT/'Restore79.cs'],OUT/'RUN_Restore79.cs.txt')
compiled=source.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("79 recovery runner compiled only; no mutation");return;}\n void Prepared79(ExecutionResult result)\n {',1);(OUT/'Compile79.cs').write_text(compiled,encoding='utf8');bundle(deps+[OUT/'Compile79.cs'],OUT/'RUN_Compile79.cs.txt')
for mode,stem in [('Read76','Read77'),('Post76','Post77')]:
 code=(OLD/(stem+'.cs')).read_text().replace(str(OLD),str(OUT)).replace('CURRENT78.json','CURRENT79.json').replace('POST78.json','POST79.json');(OUT/(stem+'.cs')).write_text(code,encoding='utf8');bundle([BASE/'Json58Linear66.cs',O73/'CreateOnly73.cs',OUT/(stem+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
print('Prepared exact22-field native reconstruction and compile-only guard; not executed')
