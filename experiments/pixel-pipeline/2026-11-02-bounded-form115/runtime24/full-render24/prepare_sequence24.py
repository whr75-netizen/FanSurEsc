"""Reuse the validated one-frame runtime for the existing12 evaluated states.
No Unity/import/GPU calls; fresh output directory and explicit next invocation.
"""
from pathlib import Path
import hashlib,json,re,subprocess
H=Path(__file__).resolve().parent;S=H/'sequence24'
assert not S.exists(),'Inspect existing preparation; never replace an execution'
done=sorted(H.glob('STATE113-*-finished.json'));assert len(done)==1
s=json.loads(done[0].read_text());assert s['PlayExited']and not s.get('error')and not s.get('restorationError')
assert all(x['equal']for x in s['nativeComparisons72'])and not s['globalRestoreErrors']
S.mkdir()
code=(H/'RUN_CaptureFull24.cs.txt').read_text()
assert hashlib.sha256(code.encode()).hexdigest()==json.loads((H/'CPU_COMPILE_FULL24.json').read_text())['commandSHA256']
gate='if(captured76>=1){report["firstFrameOnly24"]=true;BeginExit();return;}'
assert code.count(gate)==1
code=code.replace(gate,'').replace(str(H),str(S)).replace('["firstFrameOnly"]=true','["firstFrameOnly"]=false')
assert code.count('EditorApplication.EnterPlaymode();')==1
assert 'new Sequence111('in code and 'if(captured76>=1)'not in code
for bad in ['EvaluateForm115','BoundRun115','Shader.SetGlobalBuffer(','SaveAssets(','ClearDirty(','File.Delete(','File.Move(']:assert bad not in code
assert not re.search(r'InputSystem\.settings\s*=(?!=)',code)
(S/'RUN_CaptureFull24.cs.txt').write_text(code,encoding='utf8',newline='\n')
(S/'GLOBAL_NAMES66.json').write_bytes((H/'GLOBAL_NAMES66.json').read_bytes())
repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');editor=Path(r'C:\Users\15352\Documents\work\6000.5.9f1\Editor\Data')
build=S/'build';build.mkdir()
refs=[editor/'NetStandard/ref/2.1.0/netstandard.dll',editor/'NetStandard/compat/2.1.0/shims/netfx/mscorlib.dll']+sorted((editor/'Managed/UnityEngine').glob('*.dll'))+sorted((repo/'Library/ScriptAssemblies').glob('*.dll'))
args=['/nologo','/nostdlib+','/utf8output','/preferreduilang:en-US','/target:library','/langversion:latest','/out:'+str(build/'Sequence24.dll')]+['/reference:'+str(p)for p in refs]+[str(S/'RUN_CaptureFull24.cs.txt')]
rsp=build/'compile.rsp';rsp.write_text('\n'.join('"'+x+'"'for x in args)+'\n',encoding='utf8')
p=subprocess.run([r'C:\Program Files\dotnet\dotnet.exe','exec',r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll','/noconfig','@'+str(rsp)],capture_output=True,text=True,encoding='utf8')
(S/'CPU_DIAGNOSTICS.txt').write_text(p.stdout+p.stderr,encoding='utf8');assert p.returncode==0,p.stdout+p.stderr
record={'cpuCSharpSuccess':True,'commandSHA256':hashlib.sha256(code.encode()).hexdigest(),'shaderSHA256':json.loads((H/'CPU_COMPILE_FULL24.json').read_text())['shaderSHA256'],'UnityCalls':0,'GPUCalls':0,'states':'existing9 evaluatedClose then3 hair controls','compiledAssemblyExecuted':False}
(S/'CPU_COMPILE_FULL24.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
relay=(H/'relay_full24.py').read_text().replace("imported=json.loads((H/'import/COMPLETE.json')","imported=json.loads((H.parent/'import/COMPLETE.json')").replace("(H/'import/FAILED.json')","(H.parent/'import/FAILED.json')")
relay=relay.replace("assert 'if(captured76>=1)'in text","assert 'if(captured76>=1)'not in text and 'new Sequence111('in text")
relay=relay.replace('one Play/one captured open state; runtime graph dispatches','one Play/existing12 evaluated Close and hair states; runtime graph dispatches')
relay=relay.replace("assert mode in ['ImportFull24','CaptureFull24']","assert mode=='CaptureFull24'")
(S/'relay_full24.py').write_text(relay,encoding='utf8',newline='\n')
print(json.dumps(record,indent=2))
